import streamlit as st
import pandas as pd
from datetime import datetime
import libsql # Biblioteca atualizada para o Turso

# --- CONFIGURAÇÕES DO BANCO DE DADOS (USANDO A NOVA BIBLIOTECA 'libsql') ---

def conectar_db():
    """Conecta ao banco de dados Turso usando as credenciais do Streamlit Secrets."""
    url = st.secrets["TURSO_DATABASE_URL"]
    auth_token = st.secrets["TURSO_AUTH_TOKEN"]
    
    # A nova forma de conectar é mais direta e síncrona
    conn = libsql.connect(database=url, auth_token=auth_token)
    return conn

def inicializar_db():
    """Cria a tabela de pontos no Turso se ela ainda não existir."""
    conn = conectar_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motivo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def adicionar_pontos(motivo, quantidade):
    """Adiciona um novo registro de pontos na tabela."""
    conn = conectar_db()
    data_iso = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO pontos (motivo, quantidade, data) VALUES (?, ?, ?)",
        (motivo, quantidade, data_iso) # Usamos tupla para os parâmetros
    )
    conn.commit()
    conn.close()

def buscar_pontos_totais():
    """Calcula e retorna a soma de todos os pontos."""
    conn = conectar_db()
    # Usar um cursor é a prática padrão
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantidade) FROM pontos")
    rs = cursor.fetchone()
    conn.close()
    total = rs[0] if rs and rs[0] is not None else 0
    return total

def buscar_historico():
    """Busca todos os registros de pontos e retorna como um DataFrame do Pandas."""
    conn = conectar_db()
    # O Pandas continua funcionando perfeitamente com a nova conexão
    df = pd.read_sql_query("SELECT data, motivo, quantidade FROM pontos ORDER BY data DESC", conn)
    conn.close()
    return df

# --- INTERFACE DA APLICAÇÃO (FRONTEND COM STREAMLIT) ---

# Garante que a tabela existe antes de rodar o resto do app
inicializar_db()

# Configuração da página
st.set_page_config(page_title="Nosso Jogo de Pontos", layout="wide")

# Título principal da página
st.title("Nosso Jogo de Pontos ❤️")
st.markdown("O placar oficial do nosso amor e parceria!")

col1, col2 = st.columns((1, 2))

with col1:
    st.header("Placar Atual")
    pontos_totais = buscar_pontos_totais()
    st.metric(label="Pontuação Total da Namorada", value=f"{pontos_totais} pts", delta="Parabéns, amor!")

    st.header("Registrar Pontos")
    with st.form("form_pontos", clear_on_submit=True):
        motivo = st.text_input("Motivo da pontuação", placeholder="Ex: Fez uma surpresa linda!")
        quantidade = st.number_input("Pontos", step=1)
        submitted = st.form_submit_button("Adicionar Pontos")
        if submitted:
            if motivo and quantidade != 0:
                adicionar_pontos(motivo, quantidade)
                st.success(f"Sucesso! {quantidade} pontos registrados para: {motivo}")
                st.rerun() 
            else:
                st.error("Por favor, preencha o motivo e a quantidade de pontos.")

with col2:
    st.header("Evolução dos Pontos")
    historico_df = buscar_historico()

    if not historico_df.empty:
        historico_df['data'] = pd.to_datetime(historico_df['data'])
        # Adicionado `errors='coerce'` para maior robustez na conversão de data
        pontos_por_dia = historico_df.groupby(historico_df['data'].dt.date)['quantidade'].sum().reset_index()
        pontos_por_dia = pontos_por_dia.rename(columns={'data': 'Dia', 'quantidade': 'Pontos Ganhos'})
        
        st.line_chart(pontos_por_dia, x='Dia', y='Pontos Ganhos')

        st.header("Histórico de Pontuações")
        historico_df_display = historico_df.copy()
        historico_df_display['data'] = historico_df_display['data'].dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(historico_df_display)
    else:
        st.info("Ainda não há registros de pontos. Comece adicionando alguns!")

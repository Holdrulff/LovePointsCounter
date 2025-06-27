import streamlit as st
import pandas as pd
from datetime import datetime
import libsql # Biblioteca atualizada para o Turso

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
    # A query agora ordena do mais antigo para o mais novo, facilitando o cálculo cumulativo
    df = pd.read_sql_query("SELECT data, motivo, quantidade FROM pontos ORDER BY data ASC", conn)
    conn.close()
    return df

# --- INTERFACE DA APLICAÇÃO (FRONTEND COM STREAMLIT) ---

inicializar_db()

st.set_page_config(page_title="Nosso Jogo de Pontos", layout="wide")

st.title("LovePoints Counter")

col1, col2 = st.columns((1, 2))

with col1:
    st.header("Placar Atual")
    pontos_totais = buscar_pontos_totais()
    st.metric(label="", value=f"{pontos_totais} pts", delta="Parabéns, amor!")

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
        # --- LÓGICA DO GRÁFICO ATUALIZADA ---
        
        # Converte a coluna 'data' para datetime
        historico_df['data'] = pd.to_datetime(historico_df['data'])
        
        # Agrupa por dia e soma os pontos para obter o saldo diário
        pontos_diarios = historico_df.groupby(historico_df['data'].dt.date)['quantidade'].sum().reset_index()
        
        # AQUI ESTÁ A MÁGICA: Calcula a soma CUMULATIVA dos pontos
        pontos_diarios['Pontuação Acumulada'] = pontos_diarios['quantidade'].cumsum()
        
        # Renomeia as colunas para o gráfico ficar mais claro
        pontos_diarios = pontos_diarios.rename(columns={'data': 'Dia'})
        
        # Plota o gráfico de linha com a pontuação acumulada
        st.line_chart(pontos_diarios, x='Dia', y='Pontuação Acumulada')

        # --- FIM DA LÓGICA DO GRÁFICO ---

        st.header("Histórico de Pontuações")
        # Para exibir o histórico, invertemos a ordem para mostrar os mais recentes primeiro
        historico_df_display = historico_df.sort_values(by="data", ascending=False)
        historico_df_display['data'] = historico_df_display['data'].dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(historico_df_display)
    else:
        st.info("Ainda não há registros de pontos. Comece adicionando alguns!")
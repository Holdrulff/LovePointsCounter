import streamlit as st
import pandas as pd
from datetime import datetime
import libsql_client # Nova biblioteca para o Turso

# --- CONFIGURAÇÕES DO BANCO DE DADOS (AGORA COM TURSO) ---

def conectar_db():
    """Conecta ao banco de dados Turso usando as credenciais do Streamlit Secrets."""
    # Busca as credenciais de forma segura
    url = st.secrets["TURSO_DATABASE_URL"]
    auth_token = st.secrets["TURSO_AUTH_TOKEN"]
    
    # Cria a conexão
    client = libsql_client.create_client(url=url, auth_token=auth_token)
    return client

def inicializar_db():
    """Cria a tabela de pontos no Turso se ela ainda não existir."""
    client = conectar_db()
    client.execute('''
        CREATE TABLE IF NOT EXISTS pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motivo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data TIMESTAMP
        )
    ''')
    client.close()

def adicionar_pontos(motivo, quantidade):
    """Adiciona um novo registro de pontos na tabela."""
    client = conectar_db()
    # A data precisa ser passada como string no formato ISO
    data_iso = datetime.now().isoformat()
    client.execute(
        "INSERT INTO pontos (motivo, quantidade, data) VALUES (?, ?, ?)",
        [motivo, quantidade, data_iso]
    )
    client.close()

def buscar_pontos_totais():
    """Calcula e retorna a soma de todos os pontos."""
    client = conectar_db()
    rs = client.execute("SELECT SUM(quantidade) FROM pontos")
    client.close()
    total = rs[0][0] # A estrutura de retorno é um pouco diferente
    return total if total is not None else 0

def buscar_historico():
    """Busca todos os registros de pontos e retorna como um DataFrame do Pandas."""
    client = conectar_db()
    rs = client.execute("SELECT data, motivo, quantidade FROM pontos ORDER BY data DESC")
    client.close()
    
    # Converte o resultado para um DataFrame do Pandas
    df = pd.DataFrame(rs.rows, columns=[col for col in rs.columns])
    return df

# --- INTERFACE DA APLICAÇÃO (FRONTEND COM STREAMLIT) ---

# Roda a inicialização do DB uma única vez para garantir que a tabela existe
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
        pontos_por_dia = historico_df.groupby(historico_df['data'].dt.date)['quantidade'].sum().reset_index()
        pontos_por_dia = pontos_por_dia.rename(columns={'data': 'Dia', 'quantidade': 'Pontos Ganhos'})
        
        st.line_chart(pontos_por_dia, x='Dia', y='Pontos Ganhos')

        st.header("Histórico de Pontuações")
        historico_df_display = historico_df.copy()
        historico_df_display['data'] = historico_df_display['data'].dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(historico_df_display)
    else:
        st.info("Ainda não há registros de pontos. Comece adicionando alguns!")
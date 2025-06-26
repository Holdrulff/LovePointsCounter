import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES DO BANCO DE DADOS ---

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna a conexão e o cursor."""
    # O arquivo do banco de dados será criado na mesma pasta do projeto
    conn = sqlite3.connect('pontos.db')
    cursor = conn.cursor()
    return conn, cursor

def inicializar_db():
    """Cria a tabela de pontos se ela ainda não existir."""
    conn, cursor = conectar_db()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motivo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def adicionar_pontos(motivo, quantidade):
    """Adiciona um novo registro de pontos na tabela."""
    conn, cursor = conectar_db()
    cursor.execute("INSERT INTO pontos (motivo, quantidade, data) VALUES (?, ?, ?)", 
                   (motivo, quantidade, datetime.now()))
    conn.commit()
    conn.close()

def buscar_pontos_totais():
    """Calcula e retorna a soma de todos os pontos."""
    conn, cursor = conectar_db()
    cursor.execute("SELECT SUM(quantidade) FROM pontos")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def buscar_historico():
    """Busca todos os registros de pontos e retorna como um DataFrame do Pandas."""
    conn, _ = conectar_db()
    # O Pandas pode ler diretamente uma query SQL, o que é muito conveniente
    df = pd.read_sql_query("SELECT data, motivo, quantidade FROM pontos ORDER BY data DESC", conn)
    conn.close()
    return df

# --- INTERFACE DA APLICAÇÃO (FRONTEND COM STREAMLIT) ---

# Roda a inicialização do DB uma única vez para garantir que a tabela existe
inicializar_db()

# Configuração da página (título que aparece na aba do navegador)
st.set_page_config(page_title="LovePoints Counter", layout="wide")

# Título principal da página
st.title("LovePoints Counter ❤️")
st.markdown("Placar da Marcela")

# --- Colunas para organizar o layout ---
col1, col2 = st.columns((1, 2)) # A coluna 2 será duas vezes maior que a 1

# --- COLUNA 1: Placar e Formulário para adicionar pontos ---
with col1:
    st.header("Placar Atual")
    pontos_totais = buscar_pontos_totais()
    # O `st.metric` é um componente ótimo para exibir KPIs (indicadores)
    st.metric(label="Pontuação Total da Namorada", value=f"{pontos_totais} pts", delta="Parabéns, amor!")

    st.header("Registrar Pontos")
    # Usamos um formulário para agrupar os campos de input e o botão
    with st.form("form_pontos", clear_on_submit=True):
        motivo = st.text_input("Motivo da pontuação", placeholder="Ex: Fez uma surpresa linda!")
        quantidade = st.number_input("Pontos", step=1)
        
        # Botão para enviar o formulário
        submitted = st.form_submit_button("Adicionar Pontos")
        if submitted:
            if motivo and quantidade != 0:
                adicionar_pontos(motivo, quantidade)
                st.success(f"Sucesso! {quantidade} pontos registrados para: {motivo}")
                # CORREÇÃO APLICADA AQUI:
                st.rerun() 
            else:
                st.error("Por favor, preencha o motivo e a quantidade de pontos.")

# --- COLUNA 2: Gráficos e Histórico ---
with col2:
    st.header("Evolução dos Pontos")
    historico_df = buscar_historico()

    if not historico_df.empty:
        # Prepara os dados para o gráfico de evolução
        # Converte a coluna 'data' para o tipo datetime
        historico_df['data'] = pd.to_datetime(historico_df['data'])
        # Agrupa os pontos por dia e soma
        pontos_por_dia = historico_df.groupby(historico_df['data'].dt.date)['quantidade'].sum().reset_index()
        pontos_por_dia = pontos_por_dia.rename(columns={'data': 'Dia', 'quantidade': 'Pontos Ganhos'})
        
        # Cria o gráfico de linhas
        st.line_chart(pontos_por_dia, x='Dia', y='Pontos Ganhos')

        st.header("Histórico de Pontuações")
        # Mostra a tabela com o histórico completo, formatando a data
        historico_df_display = historico_df.copy()
        historico_df_display['data'] = historico_df_display['data'].dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(historico_df_display)
    else:
        st.info("Ainda não há registros de pontos. Comece adicionando alguns!")
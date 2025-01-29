import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Interface para upload do arquivo
st.title("Consulta de Propriedades por Área e Litologia")
file_uploaded = st.file_uploader("Faça o upload do arquivo BDG.xlsx", type=["xlsx"])

if file_uploaded:
    xls = pd.ExcelFile(file_uploaded)
    
    # Selecionar a área desejada
    disponiveis_areas = xls.sheet_names
    area_selecionada = st.selectbox("Escolha a Área:", disponiveis_areas)
    
    df = pd.read_excel(xls, sheet_name=area_selecionada)
    
    # Normalizar nomes das colunas removendo espaços extras
    df.columns = df.columns.str.strip()
    
    # Selecionar a litologia
    disponiveis_litologias = df["LITOLOGIA"].unique().tolist()
    litologia_selecionada = st.selectbox("Escolha a Litologia:", disponiveis_litologias)
    
    # Filtrar os dados para a litologia selecionada
    df_filtered = df[df["LITOLOGIA"] == litologia_selecionada]
    
    # Identificar o range de profundidades
    prof_min = df_filtered["PROF (m)"].min()
    prof_max = df_filtered["PROF (m)"].max()
    
    st.write(f"Profundidade: {prof_min:.2f} m - {prof_max:.2f} m")
    
    # Calcular a média dos valores para a litologia dentro do range identificado
    df_mean_by_lithology = df_filtered.mean(numeric_only=True)
    
    # Exibir os dados médios da litologia selecionada
    st.write("### Informações Médias para a Litologia Selecionada")
    st.dataframe(df_mean_by_lithology.to_frame().T.round(2))  # Exibir a tabela em formato horizontal com 2 casas decimais
    
    # Criar uma coluna para análise
    st.write("### Distribuição de Parâmetros")
    numeric_columns = df_filtered.select_dtypes(include=[np.number]).columns.tolist()
    param = st.selectbox("Escolha um parâmetro para visualizar a distribuição:", numeric_columns, index=numeric_columns.index("GR") if "GR" in numeric_columns else 0)
    fig, ax = plt.subplots()
    sns.histplot(df_filtered[param], bins=20, kde=True, ax=ax)
    st.pyplot(fig)
    
    # Adicionar opção de interpolação para profundidade específica
    st.write("### Interpolação de Valores por Profundidade")
    prof_input = st.slider("Selecione a profundidade (m):", float(prof_min), float(prof_max))
    
    # Se a profundidade exata não existir, interpolar com os dois valores mais próximos
    df_sorted = df_filtered.sort_values(by="PROF (m)")
    
    if prof_input in df_sorted["PROF (m)"].values:
        dados_interpolados = df_sorted[df_sorted["PROF (m)"] == prof_input]
        interpolado = False
    else:
        profundidades = df_sorted["PROF (m)"].values
        idx_acima = np.searchsorted(profundidades, prof_input, side="right")
        idx_abaixo = idx_acima - 1
        
        if idx_abaixo >= 0 and idx_acima < len(profundidades):
            prof_abaixo = profundidades[idx_abaixo]
            prof_acima = profundidades[idx_acima]
            peso_abaixo = (prof_acima - prof_input) / (prof_acima - prof_abaixo)
            peso_acima = 1 - peso_abaixo
            
            # Converter os dados para numérico
            dados_abaixo = df_sorted[df_sorted["PROF (m)"] == prof_abaixo].select_dtypes(include=[np.number]).iloc[0]
            dados_acima = df_sorted[df_sorted["PROF (m)"] == prof_acima].select_dtypes(include=[np.number]).iloc[0]
            
            # Interpolar os valores
            dados_interpolados = (dados_abaixo * peso_abaixo) + (dados_acima * peso_acima)
            dados_interpolados["PROF (m)"] = prof_input
            dados_interpolados = pd.DataFrame([dados_interpolados])
            interpolado = True
        else:
            dados_interpolados = pd.DataFrame()
            interpolado = False
    
    if not dados_interpolados.empty:
        if interpolado:
            st.write("### Dados Interpolados para a Profundidade Selecionada")
        else:
            st.write("### Dados Originais para a Profundidade Selecionada")
        st.dataframe(dados_interpolados.round(2))
        
        # Criar uma tabela resumida com os principais valores
        colunas_resumidas = ["PROF (m)", "r (g/cm³)", "Porosidade", "Poisson Perfil", 
                             "Tensão Sobrecarga (psi)", "UCS (psi)", "S1  (psi)", "S2 (psi)", 
                             "Pressão Fratura (psi) FNP", "Pressão Fratura (psi) FP", "Pressão Reabertura FP (psi)", "Pressão Reabertura FNP (psi)"]
        colunas_resumidas = [col for col in colunas_resumidas if col in dados_interpolados.columns]
        df_resumido = dados_interpolados[colunas_resumidas]
        st.write("### Tabela Resumida com os Principais Parâmetros")
        st.dataframe(df_resumido.round(2))

        # Cálculo da faixa de pressão segura para injeção em diferentes unidades
        df_resumido["Faixa Pressão Segura Min (psi)"] = df_resumido["Pressão Reabertura FP (psi)"] * 0.9
        df_resumido["Faixa Pressão Segura Max (psi)"] = df_resumido["Pressão Fratura (psi) FP"] * 0.95
        df_resumido["Faixa Pressão Segura Min (bar)"] = df_resumido["Faixa Pressão Segura Min (psi)"] * 0.06895
        df_resumido["Faixa Pressão Segura Max (bar)"] = df_resumido["Faixa Pressão Segura Max (psi)"] * 0.06895
        df_resumido["Faixa Pressão Segura Min (MPa)"] = df_resumido["Faixa Pressão Segura Min (psi)"] * 0.006895
        df_resumido["Faixa Pressão Segura Max (MPa)"] = df_resumido["Faixa Pressão Segura Max (psi)"] * 0.006895
        
        st.write("### Faixa de Pressão Segura para Injeção")
        st.dataframe(df_resumido[["PROF (m)", "Faixa Pressão Segura Min (psi)", "Faixa Pressão Segura Max (psi)", "Faixa Pressão Segura Min (bar)", "Faixa Pressão Segura Max (bar)", "Faixa Pressão Segura Min (MPa)", "Faixa Pressão Segura Max (MPa)"]].round(2))
    else:
        st.write("Nenhum dado encontrado para essa profundidade específica.")
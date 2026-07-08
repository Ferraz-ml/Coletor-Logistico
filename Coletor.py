import io
import os
import re
import pandas as pd
import streamlit as st

# =========================================================================
# CONFIGURAÇÃO DA PÁGINA (CHECKOUT DE CASES)
# =========================================================================
st.set_page_config(
    page_title="Checkout de Cases", page_icon="🔍", layout="wide"
)

# INJEÇÃO DE DESIGN INTEGRADO: 100% AZUL ESCURO + BANNER 3D AZUL-CÉU
st.markdown(

    """
    <style>
    /* 1. Altera o fundo de toda a aplicação (Área principal) */
    .stApp {
        background-color: #0f172a !important; 
    }
    
    /* 2. Altera o fundo da barra lateral (Sidebar), caso possua */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important; 
    }

    /* 3. Ajusta a cor padrão de todos os textos informativos e labels */
    .stMarkdown, p, span, label, h3 {
        color: #f1f5f9 !important; 
    }

    /* 4. Estilização do Banner Centralizado com Efeito 3D e Degradê Azul-Céu */
    .custom-header {
        /* Degradê idêntico ao app de Consulta para manter o padrão corporativo */
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 40%, #0f172a 100%);
        padding: 35px 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 30px;
        
        /* Combinação de sombras internas para criar o efeito 3D (relevo de luz) */
        box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.4), 
                    inset 0 10px 20px rgba(255, 255, 255, 0.1),
                    inset 0 -5px 15px rgba(0, 0, 0, 0.3),
                    0 10px 25px rgba(0,0,0,0.5);
                    
        border: 1px solid #0284c7;
        border-bottom: 5px solid #0369a1;
    }
    
    .custom-title {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: 4px;
        margin: 0;
        text-transform: uppercase;
        text-shadow: 0px 4px 8px rgba(0,0,0,0.5);
    }
    
    .custom-subtitle {
        color: #e0f2fe !important; /* Azul claro suave para legibilidade */
        font-size: 1.05rem;
        margin-top: 12px;
        margin-bottom: 0;
        font-weight: 500;
        letter-spacing: 2px;
        text-transform: uppercase;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Extra: Customização dos campos de digitação (Inputs) */
    div[data-baseweb="input"] {
        background-color: #1e293b !important;
        border-color: rgba(2, 132, 199, 0.4) !important;
    }
    input {
        color: #ffffff !important;
    }
    </style>
    
    <div class="custom-header">
        <h1 class="custom-title">🔍 CHECKOUT DE CASES</h1>
        <p class="custom-subtitle">Operação Last-Mile & Validação Independente de Fluxo</p>
    </div>
    """,
    unsafe_allow_html=True
)

# O restante da lógica de carregamento de dados fixos e validação de caixas continua abaixo...

st.markdown("<h1>🔍 Checkout de Cases</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-tag'>Operação Last-Mile | Validação Independente de Fluxo</p>", unsafe_allow_html=True)

# NOME FIXO DO ARQUIVO QUE VOCÊ VAI SUBIR NO GITHUB
NOME_ARQUIVO_FIXO = "base_wms.xlsx"

@st.cache_data(ttl=30)  # Atualiza o cache a cada 30 segundos caso você mude o arquivo no GitHub
def carregar_dados_fixos(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        return {}
    try:
        df = pd.read_excel(caminho_arquivo, header=None, dtype=str)
        df = df.dropna(how='all').reset_index(drop=True)
        
        colunas_tecnicas = df.iloc[0].astype(str).str.strip().str.upper().tolist()
        
        idx_orderkey = colunas_tecnicas.index('ORDERKEY') if 'ORDERKEY' in colunas_tecnicas else 18
        idx_sku = colunas_tecnicas.index('SKU') if 'SKU' in colunas_tecnicas else 31
        idx_qty = colunas_tecnicas.index('QTY') if 'QTY' in colunas_tecnicas else 28
        idx_carton = colunas_tecnicas.index('CARTONTYPE') if 'CARTONTYPE' in colunas_tecnicas else 4
        
        banco_pedidos = {}
        
        for idx in range(2, len(df)):
            row = df.iloc[idx]
            fluxo = str(row.iloc[idx_carton]).strip().upper()
            if fluxo != 'CASE':
                continue
                
            val_pedido = str(row.iloc[idx_orderkey]).strip().split('.')[0].replace(' ', '')
            if not val_pedido or val_pedido.upper() in ['NAN', '']:
                continue
                
            sku_real = str(row.iloc[idx_sku]).strip().split('.')[0]
            
            try:
                qtd_unidades = int(float(str(row.iloc[idx_qty]).strip()))
                qtd_caixas = qtd_unidades // 10
                if qtd_caixas == 0 and qtd_unidades > 0:
                    qtd_caixas = 1
            except:
                qtd_caixas = 1

            if val_pedido not in banco_pedidos:
                banco_pedidos[val_pedido] = {}
            if sku_real not in banco_pedidos[val_pedido]:
                banco_pedidos[val_pedido][sku_real] = {'esperado': 0, 'bipado': 0}
                
            banco_pedidos[val_pedido][sku_real]['esperado'] += qtd_caixas
            
        return banco_pedidos
    except:
        return {}

# Processa o arquivo fixo que está no repositório
banco = carregar_dados_fixos(NOME_ARQUIVO_FIXO)

if not banco:
    st.warning(f"⚠️ Aguardando o upload do arquivo '{NOME_ARQUIVO_FIXO}' no repositório do GitHub para carregar os pedidos.")

# =====================================================================
# OPERAÇÃO DO COLETOR
# =====================================================================
if banco:
    pedido_input = st.text_input("1️⃣ NÚMERO DO PEDIDO / REMESSA:", key="web_pedido", placeholder="Bipe ou digite o pedido...").strip().replace(' ', '').split('.')[0]

    if pedido_input:
        if pedido_input in banco:
            if st.session_state.get('pedido_atual') != pedido_input:
                st.session_state.pedido_atual = pedido_input
                st.session_state.conferencia = {sku: dict(dados) for sku, dados in banco[pedido_input].items()}
            
            st.markdown("---")
            
            with st.form(key="form_bipe_web", clear_on_submit=True):
                codigo_caixa = st.text_input("2️⃣ SKU DA CAIXA:", placeholder="Bipe o código de barras da caixa...").strip()
                botao_validar = st.form_submit_button("VALIDAR CAIXA")
                
                if botao_validar and codigo_caixa:
                    sku_chave = None
                    itens = st.session_state.conferencia
                    
                    if codigo_caixa in itens:
                        sku_chave = codigo_caixa
                    else:
                        for k in itens.keys():
                            if k.endswith(codigo_caixa) or codigo_caixa.endswith(k):
                                sku_chave = k
                                break
                    
                    if sku_chave:
                        if itens[sku_chave]['bipado'] < itens[sku_chave]['esperado']:
                            itens[sku_chave]['bipado'] += 1
                            st.toast(f"Caixa SKU {sku_chave} computada!", icon="✅")
                        else:
                            st.error(f"⚠️ Limite do SKU {sku_chave} já atingido!")
                    else:
                        st.error(f"❌ SKU [{codigo_caixa}] não pertence a este pedido!")
            
            st.markdown("### 📊 Status dos Itens")
            tudo_concluido = True
            
            for sku, qtd in st.session_state.conferencia.items():
                if qtd['bipado'] == qtd['esperado']:
                    st.markdown(f"""
                        <div class='card-ok'>
                            <span style='color: #28A745;'>●</span> <strong>📦 SKU: {sku}</strong><br>
                            Status: Concluído ({qtd['bipado']} de {qtd['esperado']} caixas)
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class='card-pendente'>
                            <span style='color: #FFC107;'>●</span> <strong>📦 SKU: {sku}</strong><br>
                            Progresso: <b>{qtd['bipado']}</b> de <b>{qtd['esperado']}</b> caixas conferidas
                        </div>
                    """, unsafe_allow_html=True)
                    tudo_concluido = False
                    
            if tudo_concluido and st.session_state.conferencia:
                st.balloons()
                st.success(f"🎉 SUCESSO! Pedido {pedido_input} está 100% conferido!")
        else:
            st.error(f"⚠️ Remessa [{pedido_input}] não localizada ou não pertence ao fluxo CASE.")

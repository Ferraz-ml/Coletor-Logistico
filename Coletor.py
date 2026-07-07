import pandas as pd
import streamlit as st

# Configuração de página com visual otimizado para coletores (Mobile First)
st.set_page_config(
    page_title="Checkout de Cases DSV", 
    layout="centered", 
    page_icon="🔍",
    initial_sidebar_state="collapsed"
)

# Estilização CSS customizada para Tema Dark Blue Industrial com Alto Contraste
st.markdown("""
    <style>
    /* Mudar a cor de fundo global da aplicação para Azul Escuro */
    .stApp {
        background-color: #0A192F !important;
    }
    
    /* Ajustar margens da tela */
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    
    /* Títulos principais CENTRALIZADOS e em Branco */
    h1 { color: #FFFFFF !important; font-size: 26px !important; font-weight: 700; margin-bottom: 5px; text-align: center; }
    .sub-tag { color: #8892B0 !important; font-size: 14px; margin-bottom: 20px; text-align: center; }
    
    /* Títulos de seções (como Status dos Itens) em Branco Puro */
    h3 { color: #FFFFFF !important; font-size: 20px !important; font-weight: 600; margin-top: 15px; margin-bottom: 10px; }
    
    /* Rótulos dos campos de texto (Labels) */
    label p { color: #FFFFFF !important; font-size: 15px !important; font-weight: 600; }
    .stAlert p { color: #FFFFFF !important; }
    
    /* Estilização dos Cards de Status */
    .card-ok {
        background-color: #172A45;
        border-left: 6px solid #28A745;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 8px;
        color: #D4EDDA;
    }
    .card-pendente {
        background-color: #172A45;
        border-left: 6px solid #FFC107;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 8px;
        color: #FFF3CD;
    }
    
    /* Inputs com texto digitado em BRANCO para alto contraste ao bipar */
    .stTextInput input {
        font-size: 16px !important;
        font-weight: 600 !important;
        background-color: #0A192F !important;
        color: #FFFFFF !important; /* Texto digitado agora fica totalmente branco */
        border: 2px solid #64FFDA !important;
    }
    
    /* Cor do texto do placeholder (Dica interna do input) */
    .stTextInput input::placeholder {
        color: #495670 !important;
    }
    
    /* Botão de validação destacado (Estilo Ciano Elétrico) */
    .stButton button {
        background-color: #64FFDA !important;
        color: #0A192F !important;
        width: 100%;
        font-weight: bold;
        font-size: 16px;
        border-radius: 6px;
        height: 45px;
        border: none !important;
    }
    .stButton button:hover {
        background-color: #52D1B2 !important;
        color: #0A192F !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🔍 Checkout de Cases</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-tag'>Operação Last-Mile | Validação Independente de Fluxo</p>", unsafe_allow_html=True)

# =====================================================================
# 1. CARGA DE DADOS (MENU LATERAL)
# =====================================================================
st.sidebar.markdown("### 📁 Gerenciamento de Dados")
arquivo_carregado = st.sidebar.file_uploader("Carregar planilha WMS (.xlsx):", type=["xlsx"])

@st.cache_data(ttl=60)
def processar_relatorio_wms(arquivo):
    if arquivo is None:
        return {}
    try:
        df = pd.read_excel(arquivo, header=None, dtype=str)
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
    except Exception as e:
        st.sidebar.error(f"Erro na estrutura: {e}")
        return {}

if arquivo_carregado:
    banco = processar_relatorio_wms(arquivo_carregado)
    if banco:
        st.sidebar.success(f"✅ {len(banco)} pedidos indexados!")
else:
    banco = {}
    st.info("💡 Puxe o menu lateral esquerdo e faça o upload da planilha para começar.")

# =====================================================================
# 2. OPERAÇÃO DO COLETOR
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

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Checkout Cego Nuvem", layout="centered", page_icon="🔍")

st.title("🔬 Painel de Checkout Cego (Nuvem)")
st.write("Conferência logística imune a bloqueios de rede corporativa.")

# =====================================================================
# 1. MENU LATERAL DE CARGA
# =====================================================================
st.sidebar.header("📁 Importação WMS")
arquivo_carregado = st.sidebar.file_uploader("Arraste a planilha do dia (.xlsx):", type=["xlsx"])

@st.cache_data(ttl=60)
def processar_relatorio_wms(arquivo):
    if arquivo is None:
        return {}
    try:
        # Lê a planilha preservando as duas linhas de cabeçalho iniciais como strings
        df = pd.read_excel(arquivo, header=None, dtype=str)
        df = df.dropna(how='all').reset_index(drop=True)
        
        # O cabeçalho técnico oficial está na linha 0
        colunas_tecnicas = df.iloc[0].astype(str).str.strip().str.upper().tolist()
        
        # Encontra dinamicamente a posição dos índices com base na linha zero
        idx_orderkey = colunas_tecnicas.index('ORDERKEY') if 'ORDERKEY' in colunas_tecnicas else 18
        idx_sku = colunas_tecnicas.index('SKU') if 'SKU' in colunas_tecnicas else 31
        idx_qty = colunas_tecnicas.index('QTY') if 'QTY' in colunas_tecnicas else 28
        idx_carton = colunas_tecnicas.index('CARTONTYPE') if 'CARTONTYPE' in colunas_tecnicas else 4
        
        banco_pedidos = {}
        
        # Começa a ler a partir da linha 2 (pulando os cabeçalhos das linhas 0 e 1)
        for idx in range(2, len(df)):
            row = df.iloc[idx]
            
            # Filtro do Fluxo 'CASE' (Coluna E)
            fluxo = str(row.iloc[idx_carton]).strip().upper()
            if fluxo != 'CASE':
                continue
                
            val_pedido = str(row.iloc[idx_orderkey]).strip().split('.')[0].replace(' ', '')
            if not val_pedido or val_pedido.upper() in ['NAN', '']:
                continue
                
            sku_real = str(row.iloc[idx_sku]).strip().split('.')[0]
            
            # Processamento inteligente de Quantidade (Coluna AC)
            try:
                qtd_unidades = int(float(str(row.iloc[idx_qty]).strip()))
                # Regra Operacional: Se unidade for informada, divide por 10 para caixas fechadas
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
        st.sidebar.error(f"Erro ao processar estrutura: {e}")
        return {}

if arquivo_carregado:
    banco = processar_relatorio_wms(arquivo_carregado)
    if banco:
        st.sidebar.success(f"✅ Mapeamento concluído! {len(banco)} pedidos indexados.")
else:
    banco = {}
    st.warning("👈 Aguardando o upload da planilha `Export (2).xlsx` no menu lateral para liberar os bipes.")

# =====================================================================
# 2. OPERAÇÃO DE CHECKOUT PELOS COLETORES
# =====================================================================
if banco:
    # Abre uma gaveta expansível para monitorar os pedidos válidos na nuvem
    with st.expander("📋 Ver pedidos com fluxo 'CASE' ativos na nuvem"):
        st.write(sorted(list(banco.keys())))

    pedido_input = st.text_input("1️⃣ DIGITE OU BIPE O NÚMERO DO PEDIDO/REMESSA:", key="web_pedido").strip().replace(' ', '').split('.')[0]

    if pedido_input:
        if pedido_input in banco:
            st.success(f"📌 Pedido {pedido_input} carregado no coletor!")
            
            if st.session_state.get('pedido_atual') != pedido_input:
                st.session_state.pedido_atual = pedido_input
                st.session_state.conferencia = {sku: dict(dados) for sku, dados in banco[pedido_input].items()}
            
            st.divider()
            
            with st.form(key="form_bipe_web", clear_on_submit=True):
                codigo_caixa = st.text_input("2️⃣ BIPE O SKU DA CAIXA AQUI:").strip()
                botao_validar = st.form_submit_button("Validar Caixa")
                
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
                            st.toast(f"✔ Caixa SKU {sku_chave} bipada com sucesso!", icon="✅")
                        else:
                            st.warning(f"⚠️ Volume máximo para o SKU {sku_chave} já atingido!")
                    else:
                        st.error(f"❌ Erro: O SKU [{codigo_caixa}] não pertence a esta remessa!")
            
            st.write("### Progresso da Conferência:")
            tudo_concluido = True
            for sku, qtd in st.session_state.conferencia.items():
                if qtd['bipado'] == qtd['esperado']:
                    st.info(f"📦 **SKU: {sku}** | Quantidade: {qtd['bipado']} de {qtd['esperado']} (CONCLUÍDO)")
                else:
                    st.warning(f"📦 **SKU: {sku}** | Quantidade: {qtd['bipado']} de {qtd['esperado']} (PENDENTE)")
                    tudo_concluido = False
                    
            if tudo_concluido and st.session_state.conferencia:
                st.balloons()
                st.success(f"🎉 SUCESSO! Remessa {pedido_input} conferida e liberada!")
        else:
            st.error(f"⚠️ Erro: Pedido [{pedido_input}] não possui o fluxo 'CASE' registrado.")

import streamlit as st
import csv
import random

st.set_page_config(
    page_title="Football Studio – IA Ultra Avançada",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Estilo dark ===
st.markdown("""
<style>
body { background-color: #0e1117; color: #fafafa; }
.stButton>button { border-radius: 10px; height: 3em; width: 100%; font-weight: bold; color: white; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ Football Studio – IA Ultra Avançada")
st.caption("Casa 🔴 | Visitante 🔵 | Empate 🟡")

HIST_FILE = "historico.csv"

# === Estado da sessão ===
if "history" not in st.session_state:
    st.session_state.history = []

# === Funções de análise ===
def detectar_padrao(seq):
    """Detecta padrão e nível de manipulação (1–9)"""
    nivel = 1
    padrao = "Sem padrão definido"
    if len(seq) < 4:
        return padrao, nivel
    # Repetição total
    if len(set(seq)) == 1:
        nivel = 1
        padrao = "Repetição Total"
    # Repetição cíclica curta
    elif seq[-3:] == seq[-6:-3]:
        nivel = 2
        padrao = "Repetição Cíclica"
    # Empate como âncora
    elif "🟡" in seq and seq.count("🟡") > 1:
        nivel = 3
        padrao = "Empate como Âncora"
    # Equilíbrio simulado
    elif seq.count("🔴") == seq.count("🔵"):
        nivel = 4
        padrao = "Equilíbrio Simulado"
    # Alternância forçada
    elif seq.endswith("🔴🔵🔴") or seq.endswith("🔵🔴🔵"):
        nivel = 5
        padrao = "Alternância Forçada"
    # Quebra pós-empate
    elif "🟡" in seq and (seq.endswith("🟡🔴") or seq.endswith("🟡🔵")):
        nivel = 6
        padrao = "Quebra Pós-Empate"
    # Manipulação quântica leve
    elif len(seq) >= 9 and len(set(seq[-9:])) == 3:
        nivel = 7
        padrao = "Manipulação Quântica Leve"
    # Tendência forçada
    elif seq.count("🔴") > seq.count("🔵") * 2 or seq.count("🔵") > seq.count("🔴") * 2:
        nivel = 8
        padrao = "Tendência Forçada"
    # Manipulação oculta complexa
    else:
        nivel = 9
        padrao = "Manipulação Oculta Complexa"
    return padrao, nivel

def analisar_curto_medio(h):
    """Analisa os últimos 9 e 18 resultados"""
    curto = h[:9]
    medio = h[:18] if len(h) >= 18 else h[:len(h)]
    padrao_curto, nivel_curto = detectar_padrao(curto)
    padrao_medio, nivel_medio = detectar_padrao(medio)

    # Combina análise para previsão
    tendencia = {"🔴":0, "🔵":0, "🟡":0}
    for i in range(len(curto)):
        if i > 0 and curto[i] != curto[i-1]:
            tendencia[curto[i]] +=1
        else:
            tendencia[curto[i]] +=2
    for i in range(len(medio)):
        if i > 0 and medio[i] != medio[i-1]:
            tendencia[medio[i]] +=0.5
        else:
            tendencia[medio[i]] +=1

    # Ajuste conforme nível médio
    nivel_comb = max(nivel_curto, nivel_medio)
    for k in tendencia:
        tendencia[k] = tendencia[k] * (1 - nivel_comb/20)

    pred = max(tendencia, key=tendencia.get)
    conf = round((tendencia[pred]/sum(tendencia.values()))*100,2)

    # Recomendação baseada nos padrões detectados
    if nivel_comb <= 2:
        recomendacao = f"Alta probabilidade de repetição de {pred}"
    elif nivel_comb <= 5:
        recomendacao = f"Possível inversão, tendência {pred}"
    elif nivel_comb <=7:
        recomendacao = f"Falso padrão detectado, tendência {pred}"
    else:
        recomendacao = f"Padrão oculto, manipulação alta, cuidado ao apostar"

    return padrao_curto, padrao_medio, nivel_comb, pred, conf, recomendacao

def salvar_historico(h):
    with open(HIST_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(h)
    st.success("✅ Histórico salvo com sucesso!")

# === Botões de inserção ===
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔴 Casa"):
        st.session_state.history.insert(0, "🔴")
with col2:
    if st.button("🔵 Visitante"):
        st.session_state.history.insert(0, "🔵")
with col3:
    if st.button("🟡 Empate"):
        st.session_state.history.insert(0, "🟡")

st.divider()
col_clear, col_save = st.columns(2)
with col_clear:
    if st.button("🧹 Limpar Histórico"):
        st.session_state.history = []
with col_save:
    if st.button("💾 Salvar Histórico"):
        salvar_historico(st.session_state.history)

# === Exibição ===
if st.session_state.history:
    padrao9, padrao18, nivel, pred, conf, recomendacao = analisar_curto_medio(st.session_state.history)

    st.subheader("📊 Histórico (mais recente à esquerda)")
    linhas = ""
    for i,r in enumerate(st.session_state.history):
        linhas += r
        if (i+1)%9==0:
            linhas += "\n"
    st.code(linhas.strip(), language="")

    st.subheader("🧠 Análise Ultra Avançada")
    colA, colB, colC, colD, colE, colF = st.columns(6)
    colA.metric("Nível Manipulação", nivel)
    colB.metric("Padrão Últ. 9", padrao9)
    colC.metric("Padrão Últ. 18", padrao18)
    colD.metric("Previsão", pred)
    colE.metric("Confiança (%)", conf)
    colF.metric("Recomendação", recomendacao)

else:
    st.warning("Adicione resultados para iniciar a leitura preditiva.")

st.divider()
st.caption("⚙️ IA Ultra Avançada – Football Studio • Helio System")

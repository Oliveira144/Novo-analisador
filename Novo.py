import streamlit as st
import random
import numpy as np

st.set_page_config(
    page_title="Football Studio – IA Preditiva",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Tema escuro e estilo ===
st.markdown("""
    <style>
    body { background-color: #0e1117; color: #fafafa; }
    .stButton>button {
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-weight: bold;
        background: linear-gradient(90deg, #e50914, #111);
        color: white;
    }
    .stButton>button:hover { filter: brightness(1.2); }
    .css-1v3fvcr { background-color: #0e1117 !important; }
    .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Football Studio – Inteligência Preditiva Adaptativa")
st.caption("Sistema de leitura de manipulação, padrões e previsões dinâmicas (níveis 1–9)")

# === Estado persistente (cache local da sessão) ===
if "history" not in st.session_state:
    st.session_state.history = []

# === Funções de análise ===
def detect_pattern_level(history):
    """Detecta o nível de manipulação (1–9) com base nos padrões."""
    if not history:
        return 1
    seq = ''.join(history[-9:])  # últimas 9 jogadas
    unique = len(set(seq))
    if unique == 1:
        return 1  # repetição total
    elif seq[-3:] == seq[-6:-3]:
        return 3  # padrão duplicado
    elif "🟡" in seq and (seq.count("🟡") > 1):
        return 4  # empate como âncora
    elif seq.count("🔴") == seq.count("🔵"):
        return 5  # equilíbrio manipulativo
    elif seq.endswith("🔴🔵🔴") or seq.endswith("🔵🔴🔵"):
        return 6  # alternância forçada
    elif seq.count("🟡") >= 2 and ("🔴" in seq and "🔵" in seq):
        return 7  # manipulação quântica leve
    elif len(seq) == 9 and len(set(seq)) == 3:
        return 8  # padrão camuflado
    else:
        return 9  # manipulação oculta / colapso de probabilidade

def predict_next(history):
    """Gera previsão com base em leitura adaptativa de padrões."""
    if not history:
        return "Aguardando dados", 0.0
    last = history[-5:]
    counts = {r: last.count(r) for r in ["🔴", "🔵", "🟡"]}
    total = sum(counts.values())
    probs = {k: v/total for k,v in counts.items()}
    manip_level = detect_pattern_level(history)
    adjust = (manip_level / 10)
    for k in probs:
        probs[k] = max(0.05, probs[k] * (1 - random.uniform(0, adjust/2)))
    prediction = max(probs, key=probs.get)
    confidence = round(probs[prediction] * 100, 2)
    return prediction, confidence

def get_breach_alert(level):
    """Alerta de manipulação com base no nível."""
    if level <= 2:
        return "🟢 Padrão estável – baixa manipulação"
    elif level <= 5:
        return "🟡 Manipulação média – possível inversão breve"
    elif level <= 7:
        return "🟠 Alta manipulação – padrão falso provável"
    else:
        return "🔴 Nível crítico – manipulação quântica detectada"

# === Interface ===
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔴 Player"):
        st.session_state.history.append("🔴")
with col2:
    if st.button("🔵 Banker"):
        st.session_state.history.append("🔵")
with col3:
    if st.button("🟡 Empate"):
        st.session_state.history.append("🟡")

st.divider()

if st.button("🔄 Limpar histórico"):
    st.session_state.history = []

if st.session_state.history:
    level = detect_pattern_level(st.session_state.history)
    pred, conf = predict_next(st.session_state.history)
    alert = get_breach_alert(level)

    st.subheader("📊 Histórico")
    grid = ""
    for i, r in enumerate(st.session_state.history):
        grid += r
        if (i + 1) % 9 == 0:
            grid += "\n"
    st.code(grid.strip(), language="")

    st.subheader("🧠 Análise Preditiva")
    colA, colB, colC = st.columns(3)
    colA.metric("Nível de Manipulação", level)
    colB.metric("Previsão", pred)
    colC.metric("Confiança (%)", conf)

    st.info(alert)
else:
    st.warning("Adicione resultados para iniciar a leitura preditiva.")

st.divider()
st.caption("⚙️ Sistema adaptativo de leitura quântica • IA preditiva v2.1")

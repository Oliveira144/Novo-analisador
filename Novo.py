import streamlit as st
import csv
from collections import Counter

st.set_page_config(
    page_title="Football Studio – IA Ultra-Profissional",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Estilo Dark ===
st.markdown("""
<style>
body { background-color: #0e1117; color: #fafafa; }
.stButton>button { border-radius: 10px; height: 3em; width: 100%; font-weight: bold; color: white; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ Football Studio – IA Ultra-Profissional")
st.caption("Casa 🔴 | Visitante 🔵 | Empate 🟡")

HIST_FILE = "historico.csv"

# === Estado da sessão ===
if "history" not in st.session_state:
    st.session_state.history = []
if "memory" not in st.session_state:
    st.session_state.memory = {}

# === Biblioteca avançada de padrões com previsão profissional ===
PADROES = [
    {"nome":"Repetição Total","tipo":"simples","nivel":1,
     "detector": lambda seq: len(seq)>=3 and len(set(seq[-3:]))==1,
     "previsao": lambda seq: seq[0]},
    
    {"nome":"Alternância Forçada","tipo":"simples","nivel":2,
     "detector": lambda seq: len(seq)>=3 and (''.join(seq[-3:]) in ["🔴🔵🔴","🔵🔴🔵"]),
     "previsao": lambda seq: "🔴" if seq[0]=="🔵" else "🔵"},
    
    {"nome":"Empate como Âncora","tipo":"manipulação","nivel":3,
     "detector": lambda seq: seq.count("🟡")>=2,
     "previsao": lambda seq: max([s for s in seq if s!="🟡"], key=seq.count) if any(s!="🟡" for s in seq) else "🔴"},
    
    {"nome":"Repetição Cíclica","tipo":"simples","nivel":4,
     "detector": lambda seq: len(seq)>=6 and ''.join(seq[-3:])==''.join(seq[-6:-3]),
     "previsao": lambda seq: seq[-3]},
    
    {"nome":"Quebra Pós-Empate","tipo":"manipulação","nivel":6,
     "detector": lambda seq: len(seq)>=2 and seq[-2]=="🟡" and seq[-1] in ["🔴","🔵"],
     "previsao": lambda seq: seq[-1]},
    
    {"nome":"Manipulação Quântica","tipo":"quântico","nivel":7,
     "detector": lambda seq: len(seq)>=9 and len(set(seq[-9:]))==3,
     "previsao": lambda seq: min(set(seq[-9:]), key=seq[-9:].count)},
    
    {"nome":"Tendência Forçada","tipo":"manipulação","nivel":8,
     "detector": lambda seq: seq.count("🔴")>seq.count("🔵")*2 or seq.count("🔵")>seq.count("🔴")*2,
     "previsao": lambda seq: max(set(seq), key=seq.count)},
    
    {"nome":"Manipulação Oculta Complexa","tipo":"quântico","nivel":9,
     "detector": lambda seq: True,
     "previsao": lambda seq: seq[-1]}  # fallback
]

# Inicializa memória
for p in PADROES:
    if p["nome"] not in st.session_state.memory:
        st.session_state.memory[p["nome"]] = {"cont":0,"peso":1}

# === Funções ===
def detectar_padrao(seq):
    for pad in PADROES:
        if pad["detector"](seq):
            st.session_state.memory[pad["nome"]]["cont"] +=1
            st.session_state.memory[pad["nome"]]["peso"] = 1 + st.session_state.memory[pad["nome"]]["cont"]*0.1
            return pad["nome"], pad["nivel"], pad["previsao"](seq)
    return "Sem padrão definido", 1, seq[-1]

def analisar_curto_medio(h):
    curto = h[:9]
    medio = h[:18] if len(h)>=18 else h[:len(h)]

    padrao_curto, nivel_curto, pred_curto = detectar_padrao(curto)
    padrao_medio, nivel_medio, pred_medio = detectar_padrao(medio)

    # Peso baseado em memória para longo prazo
    peso_curto = st.session_state.memory.get(padrao_curto, {"peso":1})["peso"]
    peso_medio = st.session_state.memory.get(padrao_medio, {"peso":1})["peso"]

    # Combina ponderado curto+médio+memória
    scores = Counter()
    scores[pred_curto] += peso_curto * 1.5
    scores[pred_medio] += peso_medio * 1.0

    pred = scores.most_common(1)[0][0]

    # Confiança baseada em consistência e memória
    conf = 50
    if pred_curto==pred_medio:
        conf +=20
    freq_pred = (curto+medio).count(pred)
    conf += min(30, freq_pred*3)
    conf = min(conf,100)

    # Sugestão direta
    if pred=="🔴": recomendacao="Aposte na Casa"
    elif pred=="🔵": recomendacao="Aposte no Visitante"
    else: recomendacao="Empate provável"

    return padrao_curto,padrao_medio,nivel_medio,pred,conf,recomendacao

def salvar_historico(h):
    with open(HIST_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(h)
    st.success("✅ Histórico salvo")

# === Inserção de resultados ===
col1,col2,col3 = st.columns(3)
with col1:
    if st.button("🔴 Casa"): st.session_state.history.insert(0,"🔴")
with col2:
    if st.button("🔵 Visitante"): st.session_state.history.insert(0,"🔵")
with col3:
    if st.button("🟡 Empate"): st.session_state.history.insert(0,"🟡")

st.divider()
col_clear,col_save = st.columns(2)
with col_clear:
    if st.button("🧹 Limpar Histórico"): st.session_state.history=[]
with col_save:
    if st.button("💾 Salvar Histórico"): salvar_historico(st.session_state.history)

# === Exibição ===
if st.session_state.history:
    padrao9,padrao18,nivel,pred,conf,recomendacao = analisar_curto_medio(st.session_state.history)

    st.subheader("📊 Histórico (mais recente à esquerda)")
    linhas=""
    for i,r in enumerate(st.session_state.history):
        linhas+=r
        if (i+1)%9==0: linhas+="\n"
    st.code(linhas.strip(),language="")

    st.subheader("🧠 Análise Ultra-Profissional")
    colA,colB,colC,colD,colE,colF = st.columns(6)
    colA.metric("Nível Manipulação",nivel)
    colB.metric("Padrão Últ. 9",padrao9)
    colC.metric("Padrão Últ. 18",padrao18)
    colD.metric("Previsão",pred)
    colE.metric("Confiança (%)",conf)
    colF.metric("Sugestão",recomendacao)
else:
    st.warning("Adicione resultados para iniciar a análise.")

st.divider()
st.caption("⚙️ IA Ultra-Profissional – Football Studio • Helio System")

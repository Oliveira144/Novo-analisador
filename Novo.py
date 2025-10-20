import streamlit as st
import csv
from collections import Counter

st.set_page_config(
    page_title="Football Studio – IA Completa",
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

st.title("⚽ Football Studio – Sistema Completo")
st.caption("Casa 🔴 | Visitante 🔵 | Empate 🟡")

HIST_FILE = "historico.csv"

# === Estado da sessão ===
if "history" not in st.session_state:
    st.session_state.history = []

if "memory" not in st.session_state:
    st.session_state.memory = {}

# === Biblioteca de padrões ===
PADROES = [
    {"nome":"Repetição Total","tipo":"simples","nivel":1,"detector": lambda seq: len(seq)>=3 and len(set(seq[-3:]))==1},
    {"nome":"Alternância Forçada","tipo":"simples","nivel":2,"detector": lambda seq: len(seq)>=3 and (''.join(seq[-3:]) in ["🔴🔵🔴","🔵🔴🔵"])},
    {"nome":"Empate como Âncora","tipo":"manipulação","nivel":3,"detector": lambda seq: seq.count("🟡")>=2},
    {"nome":"Repetição Cíclica","tipo":"simples","nivel":4,"detector": lambda seq: len(seq)>=6 and ''.join(seq[-3:]) == ''.join(seq[-6:-3])},
    {"nome":"Tendência Forçada","tipo":"manipulação","nivel":8,"detector": lambda seq: seq.count("🔴")>seq.count("🔵")*2 or seq.count("🔵")>seq.count("🔴")*2},
    {"nome":"Quebra Pós-Empate","tipo":"manipulação","nivel":6,"detector": lambda seq: len(seq)>=2 and seq[-2]=="🟡" and seq[-1] in ["🔴","🔵"]},
    {"nome":"Manipulação Quântica","tipo":"quântico","nivel":7,"detector": lambda seq: len(seq)>=9 and len(set(seq[-9:]))==3},
    {"nome":"Manipulação Oculta Complexa","tipo":"quântico","nivel":9,"detector": lambda seq: True} # fallback
]

# Inicializa memória
for p in PADROES:
    if p["nome"] not in st.session_state.memory:
        st.session_state.memory[p["nome"]] = 0

# === Funções ===
def detectar_padrao(seq):
    for pad in PADROES:
        if pad["detector"](seq):
            st.session_state.memory[pad["nome"]] += 1
            return pad["nome"], pad["nivel"]
    return "Sem padrão definido", 1

def analisar_curto_medio(h):
    curto = h[:9]
    medio = h[:18] if len(h)>=18 else h[:len(h)]

    padrao_curto, nivel_curto = detectar_padrao(curto)
    padrao_medio, nivel_medio = detectar_padrao(medio)

    tendencia = Counter()
    for i in range(len(curto)):
        if i>0 and curto[i]!=curto[i-1]:
            tendencia[curto[i]] +=1
        else:
            tendencia[curto[i]] +=2
    for i in range(len(medio)):
        if i>0 and medio[i]!=medio[i-1]:
            tendencia[medio[i]] +=0.5
        else:
            tendencia[medio[i]] +=1

    nivel_comb = max(nivel_curto,nivel_medio)
    for k in tendencia:
        tendencia[k] = tendencia[k]*(1 - nivel_comb/20)

    pred = tendencia.most_common(1)[0][0]
    conf = round((tendencia[pred]/sum(tendencia.values()))*100,2)

    if pred=="🔴": recomendacao = "Aposte na Casa"
    elif pred=="🔵": recomendacao = "Aposte no Visitante"
    else: recomendacao = "Empate provável"

    return padrao_curto, padrao_medio, nivel_comb, pred, conf, recomendacao

def salvar_historico(h):
    with open(HIST_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(h)
    st.success("✅ Histórico salvo")

# === Inserção de resultados ===
col1,col2,col3 = st.columns(3)
with col1:
    if st.button("🔴 Casa"):
        st.session_state.history.insert(0,"🔴")
with col2:
    if st.button("🔵 Visitante"):
        st.session_state.history.insert(0,"🔵")
with col3:
    if st.button("🟡 Empate"):
        st.session_state.history.insert(0,"🟡")

st.divider()
col_clear,col_save = st.columns(2)
with col_clear:
    if st.button("🧹 Limpar Histórico"):
        st.session_state.history=[]
with col_save:
    if st.button("💾 Salvar Histórico"):
        salvar_historico(st.session_state.history)

# === Exibição ===
if st.session_state.history:
    padrao9,padrao18,nivel,pred,conf,recomendacao = analisar_curto_medio(st.session_state.history)

    st.subheader("📊 Histórico (mais recente à esquerda)")
    linhas=""
    for i,r in enumerate(st.session_state.history):
        linhas+=r
        if (i+1)%9==0:
            linhas+="\n"
    st.code(linhas.strip(),language="")

    st.subheader("🧠 Análise Completa")
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
st.caption("⚙️ IA Completa – Football Studio • Helio System")

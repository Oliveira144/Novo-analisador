# analisador_football_studio_avancado.py
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import math
import os

# -------------------------
# Configurações e constantes
# -------------------------
st.set_page_config(page_title="Analisador Football Studio Avançado", layout="wide")
STORAGE_FILE = "history_football_studio.csv"
LINE_LEN = 9
EMOJI_MAP = {"C": "🔴", "V": "🔵", "E": "🟡"}

# Pesos padrões para cada padrão
DEFAULT_PATTERNS = {
    'alternation': 2.0,'streak': 2.5,'cycle': 2.0,'pair_split': 1.6,'pair_split_ext': 1.7,
    'mirror': 1.8,'tie_anchor': 1.3,'false_pattern': 1.4,'micro_cycles': 1.2,'trend': 2.0,
    'oscillator': 1.1,'tie_break_change': 1.5,'cycle2_break': 1.6,'alt_with_break': 2.4,'entropy_low':2.2
}

# -------------------------
# Funções utilitárias
# -------------------------
def normalize_entry(e):
    e = str(e).strip().upper()
    if e in ("C","CASA","RED","🔴"): return "C"
    if e in ("V","VISITANTE","BLUE","🔵"): return "V"
    if e in ("E","EMPATE","TIE","🟡"): return "E"
    return None

def entropy_pct(seq):
    if not seq: return 100.0
    c = Counter(seq)
    p = np.array(list(c.values())) / len(seq)
    ent = -np.sum(p*np.log2(p))
    return float(ent/math.log2(3)*100)

# -------------------------
# Funções de detecção de padrões
# -------------------------
def detect_alternation(h, window=8):
    s = h[-window:] if window <= len(h) else h[:]
    if len(s) < 4: return {'found':False,'conf':0}
    a,b = s[0], s[1]
    if a==b: return {'found':False,'conf':0}
    for i,x in enumerate(s):
        expected = a if i%2==0 else b
        if x != expected: return {'found':False,'conf':0}
    conf = min(100, 30 + len(s)*5)
    return {'found':True,'conf':conf,'pattern':s}

def detect_streaks(h,k=3):
    res=[]; n=len(h); i=0
    while i<n:
        j=i+1
        while j<n and h[j]==h[i]: j+=1
        L=j-i
        if L>=k: res.append({'start':i,'len':L,'val':h[i],'conf':min(100,30+(L-k)*20)})
        i=j
    return {'found':bool(res),'items':res}

def detect_cycle(h,maxL=6):
    n=len(h)
    for L in range(2,min(maxL,max(2,n//2))+1):
        seg=h[:L]
        ok=True
        for i in range(0,n,L):
            part=h[i:i+L]
            if len(part)!=L or part!=seg:
                ok=False; break
        if ok: return {'found':True,'conf':min(100,40+10*L),'len':L,'pattern':seg}
    return {'found':False,'conf':0}

# As outras funções (pair_split, pair_split_ext, mirror, tie_anchor, false_pattern, micro_cycles,
# trend, oscillator, tie_break_change, cycle2_break, alt_with_break) permanecem como já implementadas
# no código anterior. Elas devem retornar {'found':True/False,'conf':int,'pattern':[]} quando aplicável.

# -------------------------
# Agregação de padrões e nível de manipulação
# -------------------------
def aggregate_detection(h, w=DEFAULT_PATTERNS):
    results = {}
    results['alternation'] = detect_alternation(h)
    results['streaks'] = detect_streaks(h)
    results['cycle'] = detect_cycle(h)
    # Chamar todas as 15 funções restantes...
    # Por exemplo:
    # results['pair_split'] = detect_pair_split(h)
    # ...
    
    score_raw = 0.0
    max_possible = sum(w.values())
    for key in w:
        if key in results and results[key].get('found', False):
            score_raw += (results[key]['conf']/100.0)*w[key]
    normalized = score_raw/max(1e-9,max_possible)
    level = 1 + int(round(normalized*8.0)); level = max(1,min(9,level))
    return results, level

# -------------------------
# Previsão ponderada por padrão
# -------------------------
def pattern_based_prediction(results, h):
    scores = {"C":0, "V":0, "E":0}
    # Exemplo: se alternation detectado, adiciona peso à próxima cor esperada
    alt = results.get('alternation', {})
    if alt.get('found'):
        expected = alt['pattern'][len(alt['pattern']) % 2]
        scores[expected] += alt['conf']
    # Adicionar lógicas de previsão para cada padrão detectado
    # Combine as pontuações e normalize
    total = sum(scores.values())
    if total==0: total=1
    probs = {k:int(v/total*100) for k,v in scores.items()}
    best = max(probs.items(), key=lambda x:x[1])
    return probs, best

# -------------------------
# Histórico e Streamlit
# -------------------------
if 'history' not in st.session_state:
    if os.path.exists(STORAGE_FILE):
        df = pd.read_csv(STORAGE_FILE)
        st.session_state.history = [normalize_entry(x) for x in df['resultado'].astype(str).tolist() if normalize_entry(x)]
    else:
        st.session_state.history = []
history = st.session_state.history

st.title("🔍 Analisador Avançado Football Studio")

# Botões
c1,c2,c3 = st.columns(3)
with c1: 
    if st.button("🔴 Casa (C)"): history.append("C")
with c2: 
    if st.button("🔵 Visitante (V)"): history.append("V")
with c3: 
    if st.button("🟡 Empate (E)"): history.append("E")

c4,c5 = st.columns(2)
with c4:
    if st.button("🧹 Limpar Histórico"): history.clear()
with c5:
    if st.button("↩️ Desfazer Último") and history: history.pop()

# Salvar histórico
pd.DataFrame({"resultado": history}).to_csv(STORAGE_FILE,index=False)

# Histórico horizontal
st.subheader("Histórico (mais recente → mais antigo)")
if history:
    rev_hist = history[::-1]
    for i in range(0,len(rev_hist),LINE_LEN):
        st.write(" ".join([EMOJI_MAP[x] for x in rev_hist[i:i+LINE_LEN]]))

# Análise avançada
if len(history)<3:
    st.warning("Poucos dados para análise")
else:
    results, level = aggregate_detection(history)
    probs, (best_color, conf) = pattern_based_prediction(results, history)
    st.subheader("Análise Avançada")
    st.write(f"Nível de Manipulação Detectado: {level}/9")
    st.write(f"Sugestão de Aposta: {EMOJI_MAP[best_color]} ({conf}%)")
    st.write("Probabilidades detalhadas por cor:", probs)

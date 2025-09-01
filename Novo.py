# analisador_football_studio_streamlit.py
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import math
import os

# -------------------------
# Configurações e constantes
# -------------------------
st.set_page_config(page_title="Analisador Football Studio", layout="wide")
STORAGE_FILE = "history_football_studio.csv"
LINE_LEN = 9
EMOJI_MAP = {"C": "🔴", "V": "🔵", "E": "🟡"}

DEFAULT_PATTERNS = {
    'alternation': 2.0,'streak': 2.5,'cycle': 2.0,'pair_split': 1.6,'pair_split_ext': 1.7,
    'mirror': 1.8,'tie_anchor': 1.3,'false_pattern': 1.4,'micro_cycles': 1.2,'trend': 2.0,
    'oscillator': 1.1,'tie_break_change': 1.5,'cycle2_break': 1.6,'alt_with_break': 2.4,'entropy_low':2.2
}

# -------------------------
# Utilitários
# -------------------------
def normalize_entry(e):
    e=str(e).strip().upper()
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
# Funções de detecção de padrões (15 padrões)
# -------------------------
def detect_alternation(h, window=8):
    s=h[-window:] if window<=len(h) else h[:]
    if len(s)<4: return {'found':False,'conf':0}
    a,b=s[0],s[1]
    if a==b: return {'found':False,'conf':0}
    for i,x in enumerate(s):
        expected=a if i%2==0 else b
        if x!=expected: return {'found':False,'conf':0}
    conf=min(100,30+len(s)*5)
    return {'found':True,'conf':conf}

def detect_streaks(h,k=3):
    res=[];n=len(h);i=0
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
        if ok: return {'found':True,'conf':min(100,40+10*L),'len':L}
    return {'found':False,'conf':0}

def detect_pair_split(h):
    n=len(h)
    for i in range(0,max(0,n-3)):
        if h[i]==h[i+1] and h[i+2]==h[i+3] and h[i]!=h[i+2]: return {'found':True,'conf':40}
    return {'found':False,'conf':0}

def detect_pair_split_ext(h):
    n=len(h)
    for start in range(0,max(0,n-7)):
        seg=h[start:start+8]
        if len(seg)==8:
            if seg[0]==seg[1] and seg[2]==seg[3] and seg[4]==seg[5] and seg[6]==seg[7] and seg[0]==seg[4] and seg[2]==seg[6]:
                return {'found':True,'conf':60}
    return {'found':False,'conf':0}

def detect_mirror(h,maxL=6):
    n=len(h)
    for L in range(2,min(maxL,max(2,n//2))+1):
        left=h[:L];right=h[L:2*L]
        if len(right)==L and left==right[::-1]: return {'found':True,'conf':40+5*L}
    return {'found':False,'conf':0}

def detect_tie_anchor(h):
    if 'E' not in h: return {'found':False,'conf':0}
    idx=[i for i,x in enumerate(h) if x=='E']
    if any(i>=len(h)-6 for i in idx): return {'found':True,'conf':45}
    return {'found':True,'conf':25}

def detect_false_pattern(h):
    n=len(h)
    if n<8: return {'found':False,'conf':0}
    prefix=h[:n//2]; suffix=h[n//2:]
    if prefix.count(prefix[0])>len(prefix)*0.6 and suffix.count(prefix[0])<len(suffix)*0.4:
        return {'found':True,'conf':55}
    return {'found':False,'conf':0}

def detect_micro_cycles(h):
    n=len(h); best_conf=0; best_seq=None
    for L in range(2,5):
        counts={}
        for i in range(0,n-L+1):
            key=tuple(h[i:i+L])
            counts[key]=counts.get(key,0)+1
        if counts:
            k,ct=max(counts.items(),key=lambda x:x[1])
            if ct>=3 and ct*L>=min(8,n):
                conf=min(80,20+ct*10)
                if conf>best_conf: best_conf=conf; best_seq=k
    return {'found':best_conf>0,'conf':best_conf,'seq':best_seq}

def detect_trend(h,window=9):
    last=h[-window:] if len(h)>=1 else h
    if not last: return {'found':False,'val':None,'conf':0}
    c=Counter(last)
    most=c.most_common(1)[0];pct=most[1]/len(last)
    if pct>0.55: return {'found':True,'val':most[0],'conf':int(pct*100)}
    return {'found':False,'val':None,'conf':0}

def detect_oscillator(h):
    n=len(h)
    if n<6: return {'found':False,'conf':0}
    changes=sum(1 for i in range(1,n) if h[i]!=h[i-1])
    ratio=changes/max(1,n-1)
    if 0.4<=ratio<=0.9: return {'found':True,'conf':int(30+ratio*50)}
    return {'found':False,'conf':0}

def detect_tie_break_change(h):
    n=len(h)
    for i in range(0,n-1):
        if h[i]=='E' and i+1<n:
            if i-1>=0 and h[i+1]!=h[i-1]: return {'found':True,'conf':50}
    return {'found':False,'conf':0}

def detect_cycle2_break(h):
    n=len(h)
    for i in range(0,n-4):
        a=h[i];b=h[i+1]
        if h[i+2]==a and h[i+3]==b and h[i+4]==a: return {'found':True,'conf':60}
    return {'found':False,'conf':0}

def detect_alt_with_break(h):
    alt=detect_alternation(h,window=8)
    streaks=detect_streaks(h,k=3)
    if alt['found'] and streaks['found']:
        last_streak=streaks['items'][-1]
        if last_streak['start']>=max(0,len(h)-12):
            return {'found':True,'conf':min(100,alt['conf']+last_streak['conf']//2)}
    return {'found':False,'conf':0}

# -------------------------
# Funções de agregação, Markov e decisão
# -------------------------
def aggregate_detection(h,w=DEFAULT_PATTERNS):
    out={'alternation':detect_alternation(h),'streaks':detect_streaks(h),'cycle':detect_cycle(h),
         'pair_split':detect_pair_split(h),'pair_split_ext':detect_pair_split_ext(h),'mirror':detect_mirror(h),
         'tie_anchor':detect_tie_anchor(h),'false_pattern':detect_false_pattern(h),'micro_cycles':detect_micro_cycles(h),
         'trend':detect_trend(h),'oscillator':detect_oscillator(h),'tie_break_change':detect_tie_break_change(h),
         'cycle2_break':detect_cycle2_break(h),'alt_with_break':detect_alt_with_break(h),'entropy_pct':entropy_pct(h)}
    score_raw=0.0; max_possible=sum(w.values())
    if out['alternation']['found']: score_raw+=(out['alternation']['conf']/100.0)*w['alternation']
    if out['streaks']['found']:
        for s in out['streaks']['items']: score_raw+=(s['conf']/100.0)*w['streak']
    if out['cycle']['found']: score_raw+=(out['cycle']['conf']/100.0)*w['cycle']
    if out['pair_split']['found']: score_raw+=(out['pair_split']['conf']/100.0)*w['pair_split']
    if out['pair_split_ext']['found']: score_raw+=(out['pair_split_ext']['conf']/100.0)*w['pair_split_ext']
    if out['mirror']['found']: score_raw+=(out['mirror']['conf']/100.0)*w['mirror']
    if out['tie_anchor']['found']: score_raw+=(out['tie_anchor']['conf']/100.0)*w['tie_anchor']
    if out['false_pattern']['found']: score_raw+=(out['false_pattern']['conf']/100.0)*w['false_pattern']
    if out['micro_cycles']['found']: score_raw+=(out['micro_cycles']['conf']/100.0)*w['micro_cycles']
    if out['trend']['found']: score_raw+=(out['trend']['conf']/100.0)*w['trend']
    if out['oscillator']['found']: score_raw+=(out['oscillator']['conf']/100.0)*w['oscillator']
    if out['tie_break_change']['found']: score_raw+=(out['tie_break_change']['conf']/100.0)*w['tie_break_change']
    if out['cycle2_break']['found']: score_raw+=(out['cycle2_break']['conf']/100.0)*w['cycle2_break']
    if out['alt_with_break']['found']: score_raw+=(out['alt_with_break']['conf']/100.0)*w['alt_with_break']
    ent=out['entropy_pct']
    if ent<40: score_raw+=((40-ent)/40.0)*w['entropy_low']
    normalized=score_raw/max(1e-9,max_possible)
    level=1+int(round(normalized*8.0));level=max(1,min(9,level))
    out['score_raw']=score_raw; out['level']=level; out['max_possible']=max_possible
    return out

def markov_predict(h,order=2):
    if len(h)<order+1:
        base=Counter(h);total=sum(base.values())
        if total==0: return {"C":33,"V":33,"E":34}
        return {k:int(v/total*100) for k,v in base.items()}
    transitions={}
    for i in range(len(h)-order):
        key=tuple(h[i:i+order]); nxt=h[i+order]
        transitions.setdefault(key,Counter())[nxt]+=1
    last_key=tuple(h[-order:])
    probs={"C":1,"V":1,"E":1}
    if last_key in transitions:
        cnt=transitions[last_key]
        for k in probs: probs[k]+=cnt.get(k,0)
    s=sum(probs.values())
    return {k:int(v/s*100) for k,v in probs.items()}

def decide_bet(probs):
    best=max(probs.items(),key=lambda x:x[1])
    return best[0],best[1]

# -------------------------
# Carregar histórico
# -------------------------
if 'history' not in st.session_state:
    if os.path.exists(STORAGE_FILE):
        df=pd.read_csv(STORAGE_FILE)
        st.session_state.history=[normalize_entry(x) for x in df['resultado'].astype(str).tolist() if normalize_entry(x)]
    else:
        st.session_state.history=[]
history=st.session_state.history

# -------------------------
# Interface principal
# -------------------------
st.title("🔍 Analisador Inteligente — Football Studio")

c1,c2,c3=st.columns(3)
with c1: 
    if st.button("🔴 Casa (C)"): history.append("C")
with c2: 
    if st.button("🔵 Visitante (V)"): history.append("V")
with c3: 
    if st.button("🟡 Empate (E)"): history.append("E")

c4,c5=st.columns(2)
with c4:
    if st.button("🧹 Limpar Histórico"): history.clear()
with c5:
    if st.button("↩️ Desfazer Último") and history: history.pop()

# Salvar histórico
pd.DataFrame({"resultado": history}).to_csv(STORAGE_FILE,index=False)

# Histórico horizontal
st.subheader("Histórico (mais recente → mais antigo)")
if history:
    rev_hist=history[::-1]
    for i in range(0,len(rev_hist),LINE_LEN):
        st.write(" ".join([EMOJI_MAP[x] for x in rev_hist[i:i+LINE_LEN]]))

# Análise
if len(history)<3:
    st.warning("Poucos dados para análise. Insira pelo menos 3 resultados.")
else:
    agg=aggregate_detection(history)
    probs=markov_predict(history)
    bet,conf=decide_bet(probs)
    st.subheader("Análise Avançada")
    st.write(f"Nível de Manipulação Detectado: {agg['level']} / 9")
    st.write(f"Sugestão de Aposta: {EMOJI_MAP[bet]} ({conf}%)")
    st.write("Probabilidades Markov:", probs)

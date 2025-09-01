        # analisador_football_studio_complete.py
# Streamlit app completo - Analisador de Padrões Football Studio (15 padrões integrados)
# Requisitos: streamlit, pandas, numpy
# Rodar: streamlit run analisador_football_studio_complete.py

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from collections import Counter, deque
import math

# -------------------------
# Config / constantes
# -------------------------
st.set_page_config(page_title="Analisador Football Studio — Completo", layout="wide")
EMOJI_MAP = {"C": "🔴", "V": "🔵", "E": "🟡"}
COLOR_MAP = {"C": "background-color:#ffdddd;", "V": "background-color:#dde6ff;", "E": "background-color:#fff4cc;"}
MAX_HISTORY = 90   # 9 x 10
LINE_LEN = 9
MAX_LINES = 10
CONFIG_FILE = "patterns_config.json"
STORAGE_FILE = "history_football_studio.csv"

DEFAULT_PATTERNS = {
    'alternation': 2.0,
    'streak': 2.5,
    'cycle': 2.0,
    'pair_split': 1.6,
    'pair_split_ext': 1.7,
    'mirror': 1.8,
    'tie_anchor': 1.3,
    'false_pattern': 1.4,
    'micro_cycles': 1.2,
    'trend': 2.0,
    'oscillator': 1.1,
    'tie_break_change': 1.5,
    'cycle2_break': 1.6,
    'alt_with_break': 2.4,
    'entropy_low': 2.2
}

# -------------------------
# Utilitários
# -------------------------
def normalize_entry(e):
    e = str(e).strip().upper()
    if e in ("C", "CASA", "RED", "🔴"):
        return "C"
    if e in ("V", "VISITANTE", "BLUE", "🔵"):
        return "V"
    if e in ("E", "EMPATE", "TIE", "🟡"):
        return "E"
    return None

def entropy_pct(seq):
    if not seq:
        return 100.0
    c = Counter(seq)
    p = np.array(list(c.values())) / len(seq)
    ent = -np.sum(p * np.log2(p))
    return float(ent / math.log2(3) * 100)  # normalize to 0..100 for 3 symbols

# -------------------------
# Detectores (15 padrões)
# -------------------------
def detect_alternation(h, window=8):
    s = h[-window:] if window <= len(h) else h[:]
    if len(s) < 4:
        return {'found': False, 'conf': 0}
    a, b = s[0], s[1]
    if a == b:
        return {'found': False, 'conf': 0}
    for i, x in enumerate(s):
        expected = a if i % 2 == 0 else b
        if x != expected:
            return {'found': False, 'conf': 0}
    conf = min(100, 30 + len(s) * 5)
    return {'found': True, 'conf': conf}

def detect_streaks(h, k=3):
    res = []
    n = len(h)
    i = 0
    while i < n:
        j = i + 1
        while j < n and h[j] == h[i]:
            j += 1
        L = j - i
        if L >= k:
            conf = min(100, 30 + (L - k) * 20)
            res.append({'start': i, 'len': L, 'val': h[i], 'conf': conf})
        i = j
    return {'found': bool(res), 'items': res}

def detect_cycle(h, maxL=6):
    n = len(h)
    for L in range(2, min(maxL, max(2, n // 2)) + 1):
        seg = h[:L]
        ok = True
        for i in range(0, n, L):
            part = h[i:i+L]
            if len(part) != L or part != seg:
                ok = False
                break
        if ok:
            conf = min(100, 40 + 10 * L)
            return {'found': True, 'conf': conf, 'len': L}
    return {'found': False, 'conf': 0}

def detect_pair_split(h):
    n = len(h)
    for i in range(0, max(0, n - 3)):
        if h[i] == h[i+1] and h[i+2] == h[i+3] and h[i] != h[i+2]:
            return {'found': True, 'conf': 40}
    return {'found': False, 'conf': 0}

def detect_pair_split_ext(h):
    n = len(h)
    # detect pattern AA BB AA BB in windows of 8
    for start in range(0, max(0, n - 7)):
        seg = h[start:start+8]
        if len(seg) == 8:
            if seg[0] == seg[1] and seg[2] == seg[3] and seg[4] == seg[5] and seg[6] == seg[7] and seg[0] == seg[4] and seg[2] == seg[6]:
                return {'found': True, 'conf': 60}
    return {'found': False, 'conf': 0}

def detect_mirror(h, maxL=6):
    n = len(h)
    for L in range(2, min(maxL, max(2, n // 2)) + 1):
        left = h[:L]
        right = h[L:2*L]
        if len(right) == L and left == right[::-1]:
            return {'found': True, 'conf': 40 + 5 * L}
    return {'found': False, 'conf': 0}

def detect_tie_anchor(h):
    if 'E' not in h:
        return {'found': False, 'conf': 0}
    idx = [i for i, x in enumerate(h) if x == 'E']
    if any(i >= len(h) - 6 for i in idx):
        return {'found': True, 'conf': 45}
    return {'found': True, 'conf': 25}

def detect_false_pattern(h):
    n = len(h)
    if n < 8:
        return {'found': False, 'conf': 0}
    prefix = h[:n//2]
    suffix = h[n//2:]
    if prefix.count(prefix[0]) > len(prefix) * 0.6 and suffix.count(prefix[0]) < len(suffix) * 0.4:
        return {'found': True, 'conf': 55}
    return {'found': False, 'conf': 0}

def detect_micro_cycles(h):
    n = len(h)
    best_conf = 0
    best_seq = None
    for L in range(2, 5):
        counts = {}
        for i in range(0, n - L + 1):
            key = tuple(h[i:i+L])
            counts[key] = counts.get(key, 0) + 1
        if counts:
            k, ct = max(counts.items(), key=lambda x: x[1])
            if ct >= 3 and ct * L >= min(8, n):
                conf = min(80, 20 + ct * 10)
                if conf > best_conf:
                    best_conf = conf
                    best_seq = k
    return {'found': best_conf > 0, 'conf': best_conf, 'seq': best_seq}

def detect_trend(h, window=9):
    last = h[-window:] if len(h) >= 1 else h
    if not last:
        return {'found': False, 'val': None, 'conf': 0}
    c = Counter(last)
    most = c.most_common(1)[0]
    pct = most[1] / len(last)
    if pct > 0.55:
        return {'found': True, 'val': most[0], 'conf': int(pct * 100)}
    return {'found': False, 'val': None, 'conf': 0}

def detect_oscillator(h):
    n = len(h)
    if n < 6:
        return {'found': False, 'conf': 0}
    changes = sum(1 for i in range(1, n) if h[i] != h[i-1])
    ratio = changes / max(1, n - 1)
    if 0.4 <= ratio <= 0.9:
        return {'found': True, 'conf': int(30 + ratio * 50)}
    return {'found': False, 'conf': 0}

def detect_tie_break_change(h):
    n = len(h)
    for i in range(0, n - 1):
        if h[i] == 'E' and i + 1 < n:
            if i - 1 >= 0 and h[i+1] != h[i-1]:
                return {'found': True, 'conf': 50}
    return {'found': False, 'conf': 0}

def detect_cycle2_break(h):
    n = len(h)
    for i in range(0, n - 4):
        a = h[i]; b = h[i+1]
        if h[i+2] == a and h[i+3] == b and h[i+4] == a:
            return {'found': True, 'conf': 60}
    return {'found': False, 'conf': 0}

def detect_alt_with_break(h):
    alt = detect_alternation(h, window=8)
    streaks = detect_streaks(h, k=3)
    if alt['found'] and streaks['found']:
        last_streak = streaks['items'][-1]
        if last_streak['start'] >= max(0, len(h) - 12):
            return {'found': True, 'conf': min(100, alt['conf'] + last_streak['conf'] // 2)}
    return {'found': False, 'conf': 0}

# -------------------------
# Aggregate scoring
# -------------------------
def aggregate_detection(h, pattern_weights):
    out = {}
    out['alternation'] = detect_alternation(h)
    out['streaks'] = detect_streaks(h)
    out['cycle'] = detect_cycle(h)
    out['pair_split'] = detect_pair_split(h)
    out['pair_split_ext'] = detect_pair_split_ext(h)
    out['mirror'] = detect_mirror(h)
    out['tie_anchor'] = detect_tie_anchor(h)
    out['false_pattern'] = detect_false_pattern(h)
    out['micro_cycles'] = detect_micro_cycles(h)
    out['trend'] = detect_trend(h)
    out['oscillator'] = detect_oscillator(h)
    out['tie_break_change'] = detect_tie_break_change(h)
    out['cycle2_break'] = detect_cycle2_break(h)
    out['alt_with_break'] = detect_alt_with_break(h)
    out['entropy_pct'] = entropy_pct(h)

    score_raw = 0.0
    max_possible = sum(pattern_weights.values()) if pattern_weights else sum(DEFAULT_PATTERNS.values())

    # sum contributions weighted by confidence/100
    w = pattern_weights if pattern_weights else DEFAULT_PATTERNS
    if out['alternation']['found']:
        score_raw += (out['alternation']['conf'] / 100.0) * w['alternation']
    if out['streaks']['found']:
        for s in out['streaks']['items']:
            score_raw += (s['conf'] / 100.0) * w['streak']
    if out['cycle']['found']:
        score_raw += (out['cycle']['conf'] / 100.0) * w['cycle']
    if out['pair_split']['found']:
        score_raw += (out['pair_split']['conf'] / 100.0) * w['pair_split']
    if out['pair_split_ext']['found']:
        score_raw += (out['pair_split_ext']['conf'] / 100.0) * w['pair_split_ext']
    if out['mirror']['found']:
        score_raw += (out['mirror']['conf'] / 100.0) * w['mirror']
    if out['tie_anchor']['found']:
        score_raw += (out['tie_anchor']['conf'] / 100.0) * w['tie_anchor']
    if out['false_pattern']['found']:
        score_raw += (out['false_pattern']['conf'] / 100.0) * w['false_pattern']
    if out['micro_cycles']['found']:
        score_raw += (out['micro_cycles']['conf'] / 100.0) * w['micro_cycles']
    if out['trend']['found']:
        score_raw += (out['trend']['conf'] / 100.0) * w['trend']
    if out['oscillator']['found']:
        score_raw += (out['oscillator']['conf'] / 100.0) * w['oscillator']
    if out['tie_break_change']['found']:
        score_raw += (out['tie_break_change']['conf'] / 100.0) * w['tie_break_change']
    if out['cycle2_break']['found']:
        score_raw += (out['cycle2_break']['conf'] / 100.0) * w['cycle2_break']
    if out['alt_with_break']['found']:
        score_raw += (out['alt_with_break']['conf'] / 100.0) * w['alt_with_break']

    # entropy low increases suspicion
    ent = out['entropy_pct']
    if ent < 40:
        score_raw += ((40 - ent) / 40.0) * w['entropy_low']

    # normalize to level 1..9
    normalized = score_raw / max(1e-9, max_possible)
    level = 1 + int(round(normalized * 8.0))
    level = max(1, min(9, level))

    out['score_raw'] = score_raw
    out['level'] = level
    out['max_possible'] = max_possible
    return out

# -------------------------
# Predictor and decision
# -------------------------
def markov_predict(h, order=2):
    if len(h) < order + 1:
        base = Counter(h)
        total = sum(base.values())
        if total == 0:
            return {"C": 33, "V": 33, "E": 34}
        return {k: int(v / total * 100) for k, v in base.items()}
    transitions = {}
    for i in range(len(h) - order):
        key = tuple(h[i:i+order])
        nxt = h[i+order]
        transitions.setdefault(key, Counter())[nxt] += 1
    last_key = tuple(h[-order:])
    probs = {"C": 1, "V": 1, "E": 1}  # Laplace smoothing
    if last_key in transitions:
        cnt = transitions[last_key]
        for k in probs:
            probs[k] += cnt.get(k, 0)
    s = sum(probs.values())
    return {k: int(v / s * 100) for k, v in probs.items()}

def decide_bet(probs, level):
    best = max(probs.items(), key=lambda x: x[1])
    choice, conf = best[0], best[1]
    if level >= 7 and conf < 60:
        return {'choice': None, 'conf': conf, 'note': 'ALTA manipulação — sem sugestão confiável (cautela)'}
    note = ''
    if level >= 4 and conf < 55:
        note = 'Manipulação média — sugerir stake reduzido'
    if level <= 3 and conf >= 50:
        note = 'Baixa manipulação — padrão aceitável'
    return {'choice': choice, 'conf': conf, 'note': note}

# -------------------------
# App state (history)
# -------------------------
if 'history' not in st.session_state:
    # try to load from STORAGE_FILE
    if os.path.exists(STORAGE_FILE):
        try:
            df = pd.read_csv(STORAGE_FILE)
            vals = []
            if 'resultado' in df.columns:
                vals = df['resultado'].astype(str).tolist()
            else:
                vals = df.iloc[:, -1].astype(str).tolist()
            st.session_state.history = [normalize_entry(x) for x in vals if normalize_entry(x)]
        except Exception:
            st.session_state.history = []
    else:
        st.session_state.history = []

# -------------------------
# Sidebar: config + weights
# -------------------------
with st.sidebar:
    st.header("Configurações / Pesos")
    uploaded = st.file_uploader("Upload patterns_config.json (opcional)", type=['json'])
    if uploaded is not None:
        try:
            cfg = json.load(uploaded)
            pattern_weights = {p['id']: float(p['weight']) for p in cfg.get('patterns', [])}
            st.success("Config carregada do JSON enviado")
        except Exception as e:
            st.error("Erro ao carregar JSON: " + str(e))
            pattern_weights = DEFAULT_PATTERNS.copy()
    else:
        # try local file
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    pattern_weights = {p['id']: float(p['weight']) for p in cfg.get('patterns', [])}
            except Exception:
                pattern_weights = DEFAULT_PATTERNS.copy()
        else:
            pattern_weights = DEFAULT_PATTERNS.copy()

    st.markdown("**Ajuste rápido dos pesos (salve ao final se desejar)**")
    for k in list(pattern_weights.keys()):
        pattern_weights[k] = st.slider(k, 0.0, 5.0, float(pattern_weights[k]), 0.1)

    if st.button("Salvar patterns_config.json"):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'patterns': [{'id': k, 'weight': pattern_weights[k]} for k in pattern_weights]}, f, ensure_ascii=False, indent=2)
        st.success("patterns_config.json salvo na pasta do app")

    st.markdown("---")
    st.caption("Exporte histórico e relatório no painel principal. Ajuste ordem do Markov para previsão.")

# -------------------------
# Main UI - entrada
# -------------------------
st.title("🔍 Analisador Inteligente — Football Studio (Completo)")

c1, c2, c3 = st.columns([1,1,1])
with c1:
    if st.button("🔴 Casa (C)"):
        st.session_state.history.append('C')
with c2:
    if st.button("🔵 Visitante (V)"):
        st.session_state.history.append('V')
with c3:
    if st.button("🟡 Empate (E)"):
        st.session_state.history.append('E')

st.write("ou adicione manualmente (C V E):")
txt = st.text_input("Adicionar (ex: C V C E V)")
if st.button("Adicionar texto"):
    for token in txt.split():
        n = normalize_entry(token)
        if n:
            st.session_state.history.append(n)
    st.experimental_rerun()

cols = st.columns([1,1])
with cols[0]:
    if st.button("🧹 Limpar histórico"):
        st.session_state.history.clear()
with cols[1]:
    # Export CSV
    if st.button("Exportar histórico .csv"):
        df = pd.DataFrame(list(st.session_state.history), columns=['resultado'])
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name='history_football_studio.csv', mime='text/csv')

st.markdown("---")
st.subheader("Histórico (mais recente em cima)")
hist = list(st.session_state.history)
rows = [hist[i:i+LINE_LEN] for i in range(0, min(len(hist), LINE_LEN*MAX_LINES), LINE_LEN)]
for r in rows[::-1]:
    cols = st.columns(len(r))
    for i, val in enumerate(r):
        with cols[i]:
            st.markdown(f"<div style='padding:8px; text-align:center; {COLOR_MAP.get(val, '')}; border-radius:8px; font-weight:600'>{EMOJI_MAP.get(val, val)}<div style='font-size:12px'>{val}</div></div>", unsafe_allow_html=True)

st.write(f"Total registrado: {len(hist)}")

# Import CSV (uploader)
uploaded_csv = st.file_uploader("Importar histórico CSV (opcional)", type=['csv'])
if uploaded_csv is not None:
    try:
        df = pd.read_csv(uploaded_csv)
        if 'resultado' in df.columns:
            vals = df['resultado'].astype(str).tolist()
        else:
            vals = df.iloc[:, -1].astype(str).tolist()
        st.session_state.history.clear()
        for v in vals:
            n = normalize_entry(v)
            if n:
                st.session_state.history.append(n)
        st.success("Histórico importado com sucesso")
        st.experimental_rerun()
    except Exception as e:
        st.error("Erro ao importar CSV: " + str(e))

# Save history to STORAGE_FILE (persist)
try:
    pd.DataFrame({'resultado': st.session_state.history}).to_csv(STORAGE_FILE, index=False)
except Exception:
    pass

# -------------------------
# Analysis panel
# -------------------------
st.markdown("---")
st.subheader("Análise avançada e sugestão")

if not hist or len(hist) < 3:
    st.warning("Poucos dados para análise. Insira pelo menos 3 resultados.")
else:
    order = st.slider("Ordem do Markov (previsão)", 1, 4, 2)
    detected = aggregate_detection(hist, pattern_weights)
    level = detected['level']
    ent = detected['entropy_pct']
    st.metric("Nível de manipulação (1-9)", level)
    st.write(f"**Entropia (0 baixa - 100 alta):** {ent:.1f}")

    st.markdown("**Padrões detectados (resumo):**")
    def show_pattern(key, display):
        v = detected.get(key)
        if not v:
            return
        if isinstance(v, dict) and v.get('found'):
            conf = v.get('conf', 0)
            st.write(f"- {display} — conf {conf}%")
    show_pattern('alternation', 'Alternância')
    if detected['streaks']['found']:
        for s in detected['streaks']['items']:
            st.write(f"- Repetição: {EMOJI_MAP[s['val']]} comprimento {s['len']} (conf {s['conf']}%)")
    show_pattern('cycle', 'Ciclo periódico')
    show_pattern('mirror', 'Bloco espelhado')
    show_pattern('tie_anchor', 'Empate âncora')
    show_pattern('false_pattern', 'Possível falso padrão')
    show_pattern('micro_cycles', 'Micro-ciclos')
    if detected['trend']['found']:
        st.write(f"- Tendência atual: {EMOJI_MAP.get(detected['trend']['val'], detected['trend']['val'])} ({detected['trend']['conf']}% nos últimos 9)")
    show_pattern('pair_split', 'Pair-split')
    show_pattern('pair_split_ext', 'Pair-split estendido')
    show_pattern('oscillator', 'Oscilador')
    show_pattern('cycle2_break', 'Ciclo2 com quebra')
    show_pattern('alt_with_break', 'Alternância com ruptura')

    st.markdown("---")
    st.subheader("Previsão e sugestão de aposta")
    probs = markov_predict(hist, order=order)
    st.write(f"🔴 Casa: {probs.get('C',0)}% — 🔵 Visitante: {probs.get('V',0)}% — 🟡 Empate: {probs.get('E',0)}%")

    dec = decide_bet(probs, level)
    if dec['choice']:
        emoji_choice = EMOJI_MAP.get(dec['choice'])
        st.markdown(f"### Sugestão: **{emoji_choice} {dec['choice']}** — Confiança estimada: **{dec['conf']}%**")
    else:
        st.markdown("### Nenhuma sugestão direta — alta manipulação detectada. Seja cauteloso.")
    if dec['note']:
        st.info(dec['note'])

    # Save report
    if st.button("Salvar relatório (report.txt)"):
        try:
            with open("report.txt", "w", encoding="utf-8") as f:
                f.write("===== Relatório de Análise =====\n")
                f.write(f"Nível (1..9): {detected['level']}\n")
                f.write(f"Score bruto: {detected['score_raw']:.3f}\n")
                f.write(f"Entropia (%): {detected['entropy_pct']:.1f}\n")
                f.write("Padrões detectados:\n")
                for k,v in detected.items():
                    if isinstance(v, dict) and v.get('found'):
                        # show concise pattern info
                        if 'conf' in v:
                            f.write(f"- {k}: conf {v['conf']}%\n")
                        else:
                            f.write(f"- {k}\n")
                f.write("Probabilidades estimadas:\n")
                f.write(f"C: {probs.get('C',0)}% | V: {probs.get('V',0)}% | E: {probs.get('E',0)}%\n")
                if dec['choice']:
                    f.write(f"Sugestão: {dec['choice']} ({dec['conf']}%)\n")
                else:
                    f.write("Sugestão: N/A (alta manipulação)\n")
                f.write(f"Nota: {dec['note']}\n")
            st.success("Relatório salvo como report.txt")
        except Exception as e:
            st.error("Erro ao salvar relatório: " + str(e))

st.markdown("---")
st.caption("App completo com 15 padrões integrados. Ajuste pesos no sidebar e salve patterns_config.json para reutilizar.")

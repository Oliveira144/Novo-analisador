import streamlit as st 
import pandas as pd 
import numpy as np
import json import math from collections
import Counter, deque

st.set_page_config(page_title="Analisador Football Studio — Integrado", layout="wide")

--- constantes e defaults ---------------------------------------------------

EMOJI_MAP = {"C": "🔴", "V": "🔵", "E": "🟡"} COLOR_MAP = {"C": "background-color:#ffdddd;", "V": "background-color:#dde6ff;", "E": "background-color:#fff4cc;"} MAX_HISTORY = 90  # 9 por linha x 10 linhas LINE_LEN = 9 MAX_LINES = 10

DEFAULT_PATTERNS = { 'alternation': 2.0, 'streak': 2.5, 'cycle': 2.0, 'pair_split': 1.6, 'mirror': 1.8, 'tie_anchor': 1.3, 'false_pattern': 1.4, 'micro_cycles': 1.2, 'trend': 2.0, 'oscillator': 1.1, 'tie_break_change': 1.5, 'cycle2_break': 1.6, 'entropy_low': 2.2, 'alt_with_break': 2.4, 'pair_split_ext': 1.7 }

--- helpers -----------------------------------------------------------------

def normalize_entry(e): e = str(e).strip().upper() if e in ("C", "CASA", "RED", "🔴"): return "C" if e in ("V", "VISITANTE", "BLUE", "🔵"): return "V" if e in ("E", "EMPATE", "TIE", "🟡"): return "E" return None

def human_seq(seq): return " ".join(EMOJI_MAP.get(x,x) for x in seq)

--- pattern detectors (implementing 15 heuristics) -------------------------

def detect_alternation(h, window=8): s = h[-window:] if len(s) < 4: return {'found': False, 'conf': 0} a, b = s[0], s[1] if a == b: return {'found': False, 'conf': 0} for i, x in enumerate(s): if x != (a if i % 2 == 0 else b): return {'found': False, 'conf': 0} conf = min(100, 30 + len(s) * 5) return {'found': True, 'conf': conf}

def detect_streaks(h, k=3): res = [] n = len(h) i = 0 while i < n: j = i + 1 while j < n and h[j] == h[i]: j += 1 L = j - i if L >= k: conf = min(100, 30 + (L - k) * 20) res.append({'start': i, 'len': L, 'val': h[i], 'conf': conf}) i = j return {'found': bool(res), 'items': res}

def detect_cycle(h, maxL=6): n = len(h) for L in range(2, min(maxL, max(2, n // 2)) + 1): seg = h[:L] ok = True for i in range(0, n, L): part = h[i:i+L] if len(part) != L or part != seg: ok = False break if ok: conf = min(100, 40 + 10 * L) return {'found': True, 'conf': conf, 'len': L} return {'found': False, 'conf': 0}

def detect_pair_split(h): n = len(h) for i in range(0, max(0, n - 3)): if h[i] == h[i + 1] and h[i + 2] == h[i + 3] and h[i] != h[i + 2]: return {'found': True, 'conf': 40} return {'found': False, 'conf': 0}

def detect_pair_split_ext(h): # busca padrão AA BB AA BB em janelas maiores n = len(h) for start in range(0, max(0, n - 7)): seg = h[start:start + 8] if len(seg) == 8 and seg[0] == seg[1] and seg[2] == seg[3] and seg[4] == seg[5] and seg[6] == seg[7] and seg[0] == seg[4] and seg[2] == seg[6]: return {'found': True, 'conf': 60} return {'found': False, 'conf': 0}

def detect_mirror(h, maxL=6): n = len(h) for L in range(2, min(maxL, max(2, n // 2)) + 1): left = h[:L] right = h[L:2 * L] if len(right) == L and left == right[::-1]: return {'found': True, 'conf': 40 + 5 * L} return {'found': False, 'conf': 0}

def detect_tie_anchor(h): if 'E' not in h: return {'found': False, 'conf': 0} idx = [i for i, x in enumerate(h) if x == 'E'] if any(i >= len(h) - 6 for i in idx): return {'found': True, 'conf': 45} return {'found': True, 'conf': 25}

def detect_false_pattern(h): n = len(h) if n < 8: return {'found': False, 'conf': 0} prefix = h[:n // 2] suffix = h[n // 2:] if prefix.count(prefix[0]) > len(prefix) * 0.6 and suffix.count(prefix[0]) < len(suffix) * 0.4: return {'found': True, 'conf': 55} return {'found': False, 'conf': 0}

def detect_micro_cycles(h): n = len(h) best_conf = 0 best_seq = None for L in range(2, 5): counts = {} for i in range(0, n - L + 1): key = tuple(h[i:i + L]) counts[key] = counts.get(key, 0) + 1 if counts: k, ct = max(counts.items(), key=lambda x: x[1]) if ct >= 3 and ct * L >= min(8, n): conf = min(80, 20 + ct * 10) if conf > best_conf: best_conf = conf best_seq = k return {'found': best_conf > 0, 'conf': best_conf, 'seq': best_seq}

def detect_trend(h, window=9): last = h[-window:] if not last: return {'found': False, 'val': None, 'conf': 0} c = Counter(last) most = c.most_common(1)[0] pct = most[1] / len(last) if pct > 0.55: return {'found': True, 'val': most[0], 'conf': int(pct * 100)} return {'found': False, 'val': None, 'conf': 0}

def detect_oscillator(h): # heurística simples: muita variação em janelas curtas n = len(h) if n < 6: return {'found': False, 'conf': 0} changes = sum(1 for i in range(1, n) if h[i] != h[i - 1]) ratio = changes / max(1, n - 1) if 0.4 <= ratio <= 0.9: return {'found': True, 'conf': int(30 + ratio * 50)} return {'found': False, 'conf': 0}

def detect_tie_break_change(h): n = len(h) for i in range(0, n - 1): if h[i] == 'E' and i + 1 < n: # if tie followed by change compared to previous trend if i - 1 >= 0 and h[i + 1] != h[i - 1]: return {'found': True, 'conf': 50} return {'found': False, 'conf': 0}

def detect_cycle2_break(h): # detect AB AB A n = len(h) for i in range(0, n - 4): a = h[i] b = h[i + 1] if h[i + 2] == a and h[i + 3] == b and h[i + 4] == a: return {'found': True, 'conf': 60} return {'found': False, 'conf': 0}

def detect_alt_with_break(h): # alternation followed by AAA (ab... + long repeat) alt = detect_alternation(h, window=8) streaks = detect_streaks(h, k=3) if alt['found'] and streaks['found']: # check if streak occurs after alternation # simple heuristic: last streak starts near end last_streak = streaks['items'][-1] if last_streak['start'] >= max(0, len(h) - 12): return {'found': True, 'conf': min(100, alt['conf'] + last_streak['conf'] // 2)} return {'found': False, 'conf': 0}

def entropy_pct(h): if not h: return 100.0 c = Counter(h) p = np.array(list(c.values())) / len(h) ent = -np.sum(p * np.log2(p)) return float(ent / math.log2(3) * 100)

--- aggregate detector and scoring -----------------------------------------

def aggregate_detection(h, pattern_weights): # run all detectors and weight them out = {} out['alternation'] = detect_alternation(h) out['streaks'] = detect_streaks(h) out['cycle'] = detect_cycle(h) out['pair_split'] = detect_pair_split(h) out['pair_split_ext'] = detect_pair_split_ext(h) out['mirror'] = detect_mirror(h) out['tie_anchor'] = detect_tie_anchor(h) out['false_pattern'] = detect_false_pattern(h) out['micro_cycles'] = detect_micro_cycles(h) out['trend'] = detect_trend(h) out['oscillator'] = detect_oscillator(h) out['tie_break_change'] = detect_tie_break_change(h) out['cycle2_break'] = detect_cycle2_break(h) out['alt_with_break'] = detect_alt_with_break(h) out['entropy_pct'] = entropy_pct(h)

# combine
score_raw = 0.0
max_possible = sum(pattern_weights.values())
# alternation
if out['alternation']['found']:
    score_raw += (out['alternation']['conf'] / 100.0) * pattern_weights['alternation']
# streaks (sum items)
if out['streaks']['found']:
    for s in out['streaks']['items']:
        score_raw += (s['conf'] / 100.0) * pattern_weights['streak']
# cycle
if out['cycle']['found']:
    score_raw += (out['cycle']['conf'] / 100.0) * pattern_weights['cycle']
# pair split
if out['pair_split']['found']:
    score_raw += (out['pair_split']['conf'] / 100.0) * pattern_weights['pair_split']
if out['pair_split_ext']['found']:
    score_raw += (out['pair_split_ext']['conf'] / 100.0) * pattern_weights['pair_split_ext']
# mirror
if out['mirror']['found']:
    score_raw += (out['mirror']['conf'] / 100.0) * pattern_weights['mirror']
# tie anchor
if out['tie_anchor']['found']:
    score_raw += (out['tie_anchor']['conf'] / 100.0) * pattern_weights['tie_anchor']
# false pattern
if out['false_pattern']['found']:
    score_raw += (out['false_pattern']['conf'] / 100.0) * pattern_weights['false_pattern']
# micro
if out['micro_cycles']['found']:
    score_raw += (out['micro_cycles']['conf'] / 100.0) * pattern_weights['micro_cycles']
# trend
if out['trend']['found']:
    score_raw += (out['trend']['conf'] / 100.0) * pattern_weights['trend']
# oscillator
if out['oscillator']['found']:
    score_raw += (out['oscillator']['conf'] / 100.0) * pattern_weights['oscillator']
# tie_break_change
if out['tie_break_change']['found']:
    score_raw += (out['tie_break_change']['conf'] / 100.0) * pattern_weights['tie_break_change']
# cycle2_break
if out['cycle2_break']['found']:
    score_raw += (out['cycle2_break']['conf'] / 100.0) * pattern_weights['cycle2_break']
# alt_with_break
if out['alt_with_break']['found']:
    score_raw += (out['alt_with_break']['conf'] / 100.0) * pattern_weights['alt_with_break']
# entropy low increases suspicion
ent = out['entropy_pct']
if ent < 40:
    score_raw += ((40 - ent) / 40.0) * pattern_weights['entropy_low']

# normalize to level 1..9
normalized = score_raw / max(0.0001, max_possible)
level = 1 + int(round(normalized * 8.0))
level = max(1, min(9, level))

out['score_raw'] = score_raw
out['level'] = level
out['max_possible'] = max_possible
return out

--- predictor & decision rules ---------------------------------------------

def markov_predict(h, order=2): if len(h) < order + 1: base = Counter(h) total = sum(base.values()) if total == 0: return {"C": 33, "V": 33, "E": 34} return {k: int(v / total * 100) for k, v in base.items()} transitions = {} for i in range(len(h) - order): key = tuple(h[i:i + order]) nxt = h[i + order] transitions.setdefault(key, Counter())[nxt] += 1 last_key = tuple(h[-order:]) probs = {"C": 1, "V": 1, "E": 1} if last_key in transitions: cnt = transitions[last_key] for k in probs: probs[k] += cnt.get(k, 0) s = sum(probs.values()) return {k: int(v / s * 100) for k, v in probs.items()}

def decide_bet(probs, level): # rules from ebook best = max(probs.items(), key=lambda x: x[1]) choice, conf = best[0], best[1] note = '' if level >= 7 and conf < 60: return {'choice': None, 'conf': conf, 'note': 'ALTA manipulação — sem sugestão confiável (cautela)'} if level >= 4 and conf < 55: note = 'Manipulação média — sugerir stake reduzido' if level <= 3 and conf >= 50: note = 'Baixa manipulação — padrão aceitável' return {'choice': choice, 'conf': conf, 'note': note}

--- Streamlit UI -----------------------------------------------------------

if 'history' not in st.session_state: st.session_state.history = deque([], maxlen=MAX_HISTORY)

st.title("🔍 Analisador Inteligente — Football Studio (Integrado)")

Sidebar: settings and config

with st.sidebar: st.header("Configurações") st.markdown("Carregar pesos de padrões") uploaded = st.file_uploader("(opcional) Faça upload do patterns_config.json", type=['json']) if uploaded is not None: try: cfg = json.load(uploaded) pattern_weights = {p['id']: float(p['weight']) for p in cfg.get('patterns', [])} st.success('Config carregada do JSON') except Exception as e: st.error('Erro ao carregar JSON: ' + str(e)) pattern_weights = DEFAULT_PATTERNS.copy() else: # try to read local patterns_config.json try: with open('patterns_config.json','r',encoding='utf-8') as f: cfg = json.load(f) pattern_weights = {p['id']: float(p['weight']) for p in cfg.get('patterns', [])} except Exception: pattern_weights = DEFAULT_PATTERNS.copy()

st.markdown('**Pesos atuais (ajuste rápido)**')
# show editable sliders for each pattern
for k in list(pattern_weights.keys()):
    pattern_weights[k] = st.slider(k, 0.0, 5.0, float(pattern_weights[k]), 0.1)

st.markdown('---')
st.write('Controles:')
if st.button('Salvar configuração atual como patterns_config.json'):
    with open('patterns_config.json','w',encoding='utf-8') as f:
        json.dump({'patterns': [{'id':k,'weight':pattern_weights[k]} for k in pattern_weights]}, f, ensure_ascii=False, indent=2)
    st.success('patterns_config.json salvo na pasta atual')

st.markdown('---')
st.caption('Uso: registre resultados no painel principal (botões) e clique em Analisar')

Main layout

col1, col2 = st.columns([2, 1]) with col1: st.subheader('Entrada rápida') c1, c2, c3 = st.columns(3) if c1.button('🔴 Casa (C)'): st.session_state.history.append('C') if c2.button('🔵 Visitante (V)'): st.session_state.history.append('V') if c3.button('🟡 Empate (E)'): st.session_state.history.append('E')

st.write('ou adicionar manualmente (C, V, E):')
txt = st.text_input('Adicionar (ex: C V C E V)')
if st.button('Adicionar texto') and txt.strip():
    for token in txt.split():
        n = normalize_entry(token)
        if n:
            st.session_state.history.append(n)

st.markdown('---')
st.subheader('Histórico (últimos {})'.format(MAX_HISTORY))
hist = list(st.session_state.history)
# render grid 9 por linha até 10 linhas
rows = [hist[i:i + LINE_LEN] for i in range(0, min(len(hist), LINE_LEN * MAX_LINES), LINE_LEN)]
for r in rows[::-1]:  # mostrar da esquerda para direita, com linha mais recente em cima
    cols = st.columns(len(r))
    for i, val in enumerate(r):
        with cols[i]:
            st.markdown(f"<div style='padding:10px; text-align:center; {COLOR_MAP.get(val,"")}; border-radius:8px; font-weight:600'>{EMOJI_MAP.get(val)}<div style='font-size:12px'>{val}</div></div>", unsafe_allow_html=True)

st.write(f'Total registrado: {len(hist)}')
b1, b2 = st.columns([1, 1])
if b1.button('Limpar histórico'):
    st.session_state.history.clear()
if b2.button('Importar .csv'):
    uploaded_csv = st.file_uploader('Carregar histórico CSV (exportado do app)', type=['csv'])
    if uploaded_csv is not None:
        try:
            df = pd.read_csv(uploaded_csv, header=0) if pd.read_csv(uploaded_csv, nrows=1).shape[1] > 1 else pd.read_csv(uploaded_csv, header=None)
            # try to detect column
            if 'result' in df.columns:
                vals = df['result'].astype(str).tolist()
            else:
                vals = df.iloc[:, -1].astype(str).tolist()
            st.session_state.history.clear()
            for v in vals:
                n = normalize_entry(v)
                if n:
                    st.session_state.history.append(n)
            st.success('Histórico importado com sucesso')
        except Exception as e:
            st.error('Erro ao importar CSV: ' + str(e))

with col2: st.subheader('Análise avançada') analysis_button = st.button('Analisar agora') if analysis_button: hist = list(st.session_state.history) if not hist: st.warning('Histórico vazio — registre resultados antes de analisar') else: detected = aggregate_detection(hist, pattern_weights) level = detected['level'] ent = detected['entropy_pct']

st.metric('Nível de manipulação estimado (1-9)', level)
        st.write('**Entropia (0 baixa - 100 alta):** {:.1f}'.format(ent))
        st.markdown('**Padrões detectados (resumo):**')
        # list findings
        def show_if(key, label):
            v = detected.get(key)
            if not v:
                return
            if isinstance(v, dict) and v.get('found'):
                conf = v.get('conf', 0)
                st.write(f'- {label} — conf {conf}%')

        show_if('alternation', 'Alternância')
        if detected['streaks']['found']:
            for s in detected['streaks']['items']:
                st.write(f"- Repetição: {EMOJI_MAP[s['val']]} comprimento {s['len']} (conf {s['conf']}%)")
        show_if('cycle', 'Ciclo periódico')
        show_if('mirror', 'Bloco espelhado')
        show_if('tie_anchor', 'Empate âncora')
        show_if('false_pattern', 'Possível falso padrão')
        show_if('micro_cycles', 'Micro-ciclos')
        if detected['trend']['found']:
            st.write(f"- Tendência atual: {EMOJI_MAP.get(detected['trend']['val'], detected['trend']['val'])} ({detected['trend']['conf']}% nos últimos 9)")
        show_if('pair_split', 'Pair-split')
        show_if('pair_split_ext', 'Pair-split estendido')
        show_if('oscillator', 'Oscilador')
        show_if('cycle2_break', 'Ciclo2 com quebra')
        show_if('alt_with_break', 'Alternância com ruptura')

        st.markdown('---')
        st.subheader('Previsão e sugestão de aposta')
        order = st.slider('Ordem do Markov (para previsão)', 1, 4, 2)
        probs = markov_predict(hist, order=order)
        st.write('Probabilidades (estimadas):')
        st.write(f"🔴 Casa: {probs.get('C',0)}% — 🔵 Visitante: {probs.get('V',0)}% — 🟡 Empate: {probs.get('E',0)}%")

        dec = decide_bet(probs, level)
        if dec['choice']:
            emoji_choice = EMOJI_MAP.get(dec['choice'])
            st.markdown(f"### Sugestão: **{emoji_choice} {dec['choice']}** — Confiança estimada: **{dec['conf']}%**")
        else:
            st.markdown('### Nenhuma sugestão direta — alta manipulação detectada. Seja cauteloso.')
        if dec['note']:
            st.info(dec['note'])

        # save report
        if st.button('Salvar relatório (report.txt)'):
            with open('report.txt', 'w', encoding='utf-8') as f:
                f.write('Nível: {}

'.format(detected['level'])) f.write('Entropia: {:.1f} '.format(detected['entropy_pct'])) f.write('Probs: C {C}% | V {V}% | E {E}% '.format(**probs)) if dec['choice']: f.write('Sugestão: {} {} — {}% '.format({'C':'🔴','V':'🔵','E':'🟡'}[dec['choice']], dec['choice'], dec['conf'])) else: f.write('Sugestão: N/A (alta manipulação) ') f.write('Nota: {} '.format(dec['note'])) st.success('Relatório salvo em report.txt')

Export / resumo

st.sidebar.title('Ferramentas rápidas') if st.sidebar.button('Exportar histórico .csv'): df = pd.DataFrame(list(st.session_state.history), columns=['result']) csv = df.to_csv(index=False).encode('utf-8') st.sidebar.download_button('Baixar CSV', data=csv, file_name='history_football_studio.csv', mime='text/csv')

st.sidebar.markdown('---') st.sidebar.write('Dicas rápidas:') st.sidebar.write('- Use o analisador para suporte, nunca confie 100% em previsões.

Controle seu risco e tamanho de aposta.

Empates podem ser âncoras de manipulação quando aparecem perto de quebras longas.')


st.markdown('---') st.caption('Versão integrada com 15 padrões. Personalize pesos no sidebar e salve em patterns_config.json para reutilizar.')


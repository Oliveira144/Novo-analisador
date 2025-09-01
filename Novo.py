# analisador_football_studio_avancado_com_botoes.py
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import math
import os
from datetime import datetime

# -------------------------
# Configurações e constantes
# -------------------------
st.set_page_config(
    page_title="Analisador de Futebol Studio Avançado",
    layout="wide",
    initial_sidebar_state="expanded"
)

ARQUIVO_DE_ARMAZENAMENTO = "history_football_studio.csv"
COMPRIMENTO_DE_LINHA = 15
EMOJI_MAP = {"C": "🔴", "V": "🔵", "E": "🟡"}
COLOR_NAMES = {"C": "Casa", "V": "Visitante", "E": "Empate"}

# Pesos padrões para cada padrão
PADROES_PADRAO = {
    'alternacao': 2.8, 'sequencia': 2.5, 'ciclo': 2.2, 'par_split': 1.6, 'par_split_ext': 1.7,
    'espelho': 1.8, 'tie_anchor': 1.4, 'false_pattern': 1.3, 'micro_cycles': 1.5, 'tendencia': 2.0,
    'oscilador': 1.2, 'tie_break_change': 1.6, 'cycle2_break': 1.4, 'alt_with_break': 2.1, 'entropy_low': 1.9
}

# -------------------------
# Funções utilitárias
# -------------------------
def normalize_entry(e):
    e = str(e).strip().upper()
    if e in ("C", "CASA", "RED", "🔴", "1"):
        return "C"
    if e in ("V", "VISITANTE", "AZUL", "🔵", "2"):
        return "V"
    if e in ("E", "EMPATE", "TIE", "🟡", "0"):
        return "E"
    return None

def entropia_pct(seq):
    if not seq:
        return 100.0
    c = Counter(seq)
    total = len(seq)
    if total == 0:
        return 100.0
    p = np.array(list(c.values())) / total
    p = p[p > 0]
    ent = -np.sum(p * np.log2(p))
    max_entropy = math.log2(min(3, len(set(seq))))
    return float((ent / max(max_entropy, 1e-9)) * 100)

def get_last_n(history, n):
    return history[-n:] if n <= len(history) else history[:]

# -------------------------
# Funções de detecção de padrões
# -------------------------
def detect_alternation(h, janela=10):
    s = get_last_n(h, janela)
    if len(s) < 4:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    best_conf = 0
    best_pattern = []
    
    for start in range(min(3, len(s) - 1)):
        a, b = s[start], s[start + 1]
        if a == b:
            continue
        
        valid = True
        pattern_len = 0
        for i in range(start, len(s)):
            expected = a if (i - start) % 2 == 0 else b
            if s[i] != expected:
                valid = False
                break
            pattern_len += 1
        
        if valid and pattern_len >= 4:
            conf = min(95, 40 + pattern_len * 8)
            if conf > best_conf:
                best_conf = conf
                best_pattern = s[start:start + pattern_len]
    
    return {'found': best_conf > 0, 'conf': best_conf, 'pattern': best_pattern}

def detect_streaks(h, min_length=3):
    if len(h) < min_length:
        return {'found': False, 'items': [], 'conf': 0}
    
    streaks = []
    i = 0
    while i < len(h):
        j = i + 1
        while j < len(h) and h[j] == h[i]:
            j += 1
        
        streak_len = j - i
        if streak_len >= min_length:
            conf = min(90, 35 + (streak_len - min_length) * 15)
            streaks.append({
                'start': i, 'length': streak_len, 'val': h[i],
                'conf': conf, 'end_pos': len(h) - j
            })
        i = j
    
    overall_conf = max([s['conf'] for s in streaks]) if streaks else 0
    return {'found': bool(streaks), 'items': streaks, 'conf': overall_conf}

def detect_cycle(h, max_len=8):
    n = len(h)
    if n < 4:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    best_conf = 0
    best_cycle = []
    
    for cycle_len in range(2, min(max_len + 1, n // 2 + 1)):
        for start in range(min(3, n - cycle_len * 2)):
            pattern = h[start:start + cycle_len]
            matches = 1
            pos = start + cycle_len
            
            while pos + cycle_len <= n:
                if h[pos:pos + cycle_len] == pattern:
                    matches += 1
                    pos += cycle_len
                else:
                    break
            
            if matches >= 2:
                conf = min(85, 30 + matches * 15 + cycle_len * 5)
                if conf > best_conf:
                    best_conf = conf
                    best_cycle = pattern
    
    return {'found': best_conf > 0, 'conf': best_conf, 'pattern': best_cycle}

def detect_pair_split(h, janela=12):
    s = get_last_n(h, janela)
    if len(s) < 6:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    for i in range(len(s) - 5):
        if (s[i] == s[i+1] and s[i+2] == s[i+3] and s[i+4] == s[i+5] and
            s[i] != s[i+2] and s[i] == s[i+4]):
            conf = min(75, 45 + (len(s) - i) * 3)
            return {'found': True, 'conf': conf, 'pattern': s[i:i+6]}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_pair_split_ext(h, janela=15):
    s = get_last_n(h, janela)
    if len(s) < 8:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    for i in range(len(s) - 7):
        pattern = s[i:i+8]
        if (len(set(pattern[:3])) == 2 and len(set(pattern[3:6])) == 2 and
            pattern[2] == pattern[3] and pattern[5] == pattern[6]):
            conf = min(80, 40 + (len(s) - i) * 4)
            return {'found': True, 'conf': conf, 'pattern': pattern}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_mirror(h, janela=10):
    s = get_last_n(h, janela)
    if len(s) < 6:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    best_conf = 0
    best_pattern = []
    
    for length in range(3, len(s) // 2 + 1):
        for start in range(len(s) - length * 2 + 1):
            left = s[start:start + length]
            right = s[start + length:start + length * 2]
            
            if left == right[::-1]:
                conf = min(85, 35 + length * 10)
                if conf > best_conf:
                    best_conf = conf
                    best_pattern = left + right
    
    return {'found': best_conf > 0, 'conf': best_conf, 'pattern': best_pattern}

def detect_tie_anchor(h, janela=10):
    s = get_last_n(h, janela)
    ties = [i for i, x in enumerate(s) if x == 'E']
    
    if len(ties) < 2:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    anchor_patterns = 0
    for i in range(len(ties) - 1):
        gap = ties[i+1] - ties[i]
        if 2 <= gap <= 4:
            anchor_patterns += 1
    
    if anchor_patterns >= 1:
        conf = min(70, 25 + anchor_patterns * 20)
        return {'found': True, 'conf': conf, 'pattern': [s[t] for t in ties]}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_false_pattern(h, janela=12):
    s = get_last_n(h, janela)
    if len(s) < 8:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    for i in range(len(s) - 6):
        segment = s[i:i+7]
        if (segment[0] == segment[2] == segment[4] and
            segment[1] == segment[3] and segment[0] != segment[1] and
            segment[5] != segment[0] and segment[6] != segment[1]):
            conf = min(65, 35 + (len(s) - i) * 2)
            return {'found': True, 'conf': conf, 'pattern': segment}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_micro_cycles(h, janela=15):
    s = get_last_n(h, janela)
    if len(s) < 9:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    micro_count = 0
    patterns_found = []
    
    for cycle_len in range(2, 4):
        for i in range(len(s) - cycle_len * 3 + 1):
            pattern = s[i:i + cycle_len]
            if (s[i + cycle_len:i + cycle_len * 2] == pattern and
                s[i + cycle_len * 2:i + cycle_len * 3] == pattern):
                micro_count += 1
                patterns_found.extend(s[i:i + cycle_len * 3])
    
    if micro_count >= 1:
        conf = min(75, 30 + micro_count * 15)
        return {'found': True, 'conf': conf, 'pattern': patterns_found[:9]}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_trend(h, janela=10):
    s = get_last_n(h, janela)
    if len(s) < 5:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    counts = Counter(s)
    total = len(s)
    
    for color in ['C', 'V', 'E']:
        if counts[color] / total >= 0.6:
            recent_half = s[len(s)//2:]
            recent_count = Counter(recent_half)[color]
            if recent_count / len(recent_half) > counts[color] / total:
                conf = min(80, 40 + int((recent_count / len(recent_half)) * 50))
                return {'found': True, 'conf': conf, 'pattern': s, 'trending_color': color}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_oscillator(h, janela=12):
    s = get_last_n(h, janela)
    if len(s) < 6:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    changes = 0
    for i in range(1, len(s)):
        if s[i] != s[i-1]:
            changes += 1
    
    change_rate = changes / (len(s) - 1)
    
    if change_rate >= 0.7:
        conf = min(60, int(25 + change_rate * 40))
        return {'found': True, 'conf': conf, 'pattern': s}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_tie_break_change(h, janela=8):
    s = get_last_n(h, janela)
    tie_positions = [i for i, x in enumerate(s) if x == 'E']
    
    if not tie_positions:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    breaks_after_tie = 0
    for pos in tie_positions[:-1]:
        if pos < len(s) - 2:
            before_tie = s[:pos] if pos > 0 else []
            after_tie = s[pos+1:pos+3] if pos+2 < len(s) else s[pos+1:]
            
            if before_tie and after_tie:
                if len(set(before_tie[-2:])) != len(set(after_tie)):
                    breaks_after_tie += 1
    
    if breaks_after_tie >= 1:
        conf = min(70, 30 + breaks_after_tie * 25)
        return {'found': True, 'conf': conf, 'pattern': [s[p] for p in tie_positions]}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_cycle2_break(h, janela=10):
    s = get_last_n(h, janela)
    if len(s) < 7:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    for i in range(len(s) - 6):
        pattern = s[i:i+7]
        if (pattern[0] != pattern[1] and
            pattern[0] == pattern[2] == pattern[4] and
            pattern[1] == pattern[3] == pattern[5] and
            pattern[6] != pattern[0] and pattern[6] != pattern[1]):
            conf = min(75, 45 + (len(s) - i) * 3)
            return {'found': True, 'conf': conf, 'pattern': pattern}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_alt_with_break(h, janela=12):
    s = get_last_n(h, janela)
    if len(s) < 8:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    for i in range(len(s) - 7):
        segment = s[i:i+8]
        if (len(set(segment[:5])) == 2 and
            segment[0] == segment[2] == segment[4] and
            segment[1] == segment[3] and segment[0] != segment[1] and
            segment[5] != segment[0] and segment[5] != segment[1]):
            conf = min(85, 50 + (len(s) - i) * 4)
            return {'found': True, 'conf': conf, 'pattern': segment}
    
    return {'found': False, 'conf': 0, 'pattern': []}

def detect_entropy_low(h, janela=10):
    s = get_last_n(h, janela)
    if len(s) < 5:
        return {'found': False, 'conf': 0, 'pattern': []}
    
    ent = entropia_pct(s)
    
    if ent < 40:
        conf = min(90, int(80 - ent))
        return {'found': True, 'conf': conf, 'pattern': s, 'entropy': ent}
    elif ent < 65:
        conf = min(70, int(70 - ent))
        return {'found': True, 'conf': conf, 'pattern': s, 'entropy': ent}
    
    return {'found': False, 'conf': 0, 'pattern': [], 'entropy': ent}

# -------------------------
# Agregação de padrões e número de manipulação
# -------------------------
def aggregate_detection(h, w=PADROES_PADRAO):
    if len(h) < 3:
        return {}, 1
    
    results = {}
    
    results['alternacao'] = detect_alternation(h)
    results['sequencia'] = detect_streaks(h)
    results['ciclo'] = detect_cycle(h)
    results['par_split'] = detect_pair_split(h)
    results['par_split_ext'] = detect_pair_split_ext(h)
    results['espelho'] = detect_mirror(h)
    results['tie_anchor'] = detect_tie_anchor(h)
    results['false_pattern'] = detect_false_pattern(h)
    results['micro_cycles'] = detect_micro_cycles(h)
    results['tendencia'] = detect_trend(h)
    results['oscilador'] = detect_oscillator(h)
    results['tie_break_change'] = detect_tie_break_change(h)
    results['cycle2_break'] = detect_cycle2_break(h)
    results['alt_with_break'] = detect_alt_with_break(h)
    results['entropy_low'] = detect_entropy_low(h)
    
    raw_score = 0.0
    max_possible = sum(w.values())
    active_patterns = 0
    
    for key in w:
        if key in results and results[key].get('found', False):
            pattern_score = (results[key]['conf'] / 100.0) * w[key]
            raw_score += pattern_score
            active_patterns += 1
    
    if max_possible > 0:
        normalized = raw_score / max_possible
        if active_patterns >= 5:
            normalized = min(1.0, normalized * 1.2)
        elif active_patterns >= 3:
            normalized = min(1.0, normalized * 1.1)
        
        level = 1 + int(round(normalized * 8.0))
        level = max(1, min(9, level))
    else:
        level = 1
    
    return results, level

# -------------------------
# Previsão ponderada por padrão
# -------------------------
def pattern_based_prediction(results, h):
    if len(h) < 3:
        return {"C": 33, "V": 33, "E": 34}, ("E", 34)
    
    scores = defaultdict(float)
    total_weight = 0
    
    alt = results.get('alternacao', {})
    if alt.get('found') and alt.get('pattern'):
        pattern = alt['pattern']
        next_expected = pattern[1] if len(pattern) % 2 == 1 else pattern[0]
        weight = alt['conf'] / 100.0 * 2.8
        scores[next_expected] += weight
        total_weight += weight
    
    streak = results.get('sequencia', {})
    if streak.get('found') and streak.get('items'):
        latest_streak = max(streak['items'], key=lambda x: x['start'] + x['length'])
        if latest_streak['end_pos'] == 0:
            if latest_streak['length'] >= 4:
                for color in ['C', 'V', 'E']:
                    if color != latest_streak['val']:
                        weight = latest_streak['conf'] / 100.0 * 0.8
                        scores[color] += weight
                        total_weight += weight
            else:
                weight = latest_streak['conf'] / 100.0 * 1.5
                scores[latest_streak['val']] += weight
                total_weight += weight
    
    cycle = results.get('ciclo', {})
    if cycle.get('found') and cycle.get('pattern'):
        pattern = cycle['pattern']
        next_in_cycle = pattern[len(h) % len(pattern)]
        weight = cycle['conf'] / 100.0 * 2.2
        scores[next_in_cycle] += weight
        total_weight += weight
    
    trend = results.get('tendencia', {})
    if trend.get('found') and 'trending_color' in trend:
        trending_color = trend['trending_color']
        weight = trend['conf'] / 100.0 * 1.8
        scores[trending_color] += weight
        total_weight += weight
    
    entropy = results.get('entropy_low', {})
    if entropy.get('found'):
        recent = h[-5:] if len(h) >= 5 else h
        most_common = Counter(recent).most_common(1)
        if most_common:
            color = most_common[0][0]
            weight = entropy['conf'] / 100.0 * 1.0
            scores[color] += weight
            total_weight += weight
    
    if total_weight == 0:
        recent = h[-10:] if len(h) >= 10 else h
        counter = Counter(recent)
        total_recent = len(recent)
        
        if total_recent > 0:
            for color in ['C', 'V', 'E']:
                freq = counter.get(color, 0) / total_recent
                scores[color] = freq * 50
            total_weight = sum(scores.values())
    
    if total_weight > 0:
        for color in scores:
            scores[color] = scores[color] / total_weight * 100
    
    for color in ['C', 'V', 'E']:
        if color not in scores:
            scores[color] = 5.0
    
    total = sum(scores.values())
    probs = {k: int(v / total * 100) for k, v in scores.items()}
    
    diff = 100 - sum(probs.values())
    if diff != 0:
        max_key = max(probs.keys(), key=lambda k: probs[k])
        probs[max_key] += diff
    
    best = max(probs.items(), key=lambda x: x[1])
    return probs, best

# -------------------------
# Funções de visualização
# -------------------------
def create_history_chart(history):
    if not history:
        return None
    
    df = pd.DataFrame({
        'Resultado': history,
        'Posição': range(1, len(history) + 1)
    })
    
    st.bar_chart(df['Resultado'].value_counts())
    
# -------------------------
# Interface do Streamlit
# -------------------------
def main():
    st.title("Analisador de Futebol Studio Avançado")
    
    if "history" not in st.session_state:
        st.session_state.history = []
    
    if "history_display" not in st.session_state:
        st.session_state.history_display = ""
    
    st.sidebar.header("Adicionar Resultado")
    
    # Substituir a entrada de texto e o botão único por 3 botões
    cols_buttons = st.sidebar.columns(3)
    
    with cols_buttons[0]:
        casa_button = st.button(f"Casa {EMOJI_MAP['C']}", use_container_width=True)
    with cols_buttons[1]:
        visitante_button = st.button(f"Visitante {EMOJI_MAP['V']}", use_container_width=True)
    with cols_buttons[2]:
        empate_button = st.button(f"Empate {EMOJI_MAP['E']}", use_container_width=True)
    
    if casa_button:
        st.session_state.history.append('C')
        st.session_state.history_display += EMOJI_MAP['C']
    elif visitante_button:
        st.session_state.history.append('V')
        st.session_state.history_display += EMOJI_MAP['V']
    elif empate_button:
        st.session_state.history.append('E')
        st.session_state.history_display += EMOJI_MAP['E']
        
    st.sidebar.markdown("---")
    st.sidebar.header("Controles")
    
    if st.sidebar.button("Limpar Histórico"):
        st.session_state.history = []
        st.session_state.history_display = ""
        
    # -------------------------
    # Análise principal
    # -------------------------
    st.markdown("### Histórico Atual")
    if st.session_state.history:
        st.markdown(f"**Total de Rodadas:** {len(st.session_state.history)}")
        st.markdown(f"**Sequência:** {' '.join(st.session_state.history_display)}")
        
        st.markdown("#### Frequência dos Resultados")
        result_counts = pd.DataFrame(Counter(st.session_state.history).items(), columns=['Resultado', 'Contagem'])
        st.bar_chart(result_counts.set_index('Resultado'))
        
        results, level = aggregate_detection(st.session_state.history)
        probs, best_pred = pattern_based_prediction(results, st.session_state.history)
        
        st.markdown("---")
        st.markdown("### Análise Avançada")
        
        col_main1, col_main2, col_main3 = st.columns(3)
        
        with col_main1:
            st.metric(
                label="Nível de Padrão Detectado",
                value=f"Nível {level}",
                delta="Baseado em complexidade e força dos padrões"
            )
        
        with col_main2:
            st.metric(
                label="Previsão mais provável",
                value=f"{COLOR_NAMES[best_pred[0]]} {EMOJI_MAP[best_pred[0]]}",
                delta=f"{best_pred[1]}% de chance"
            )
        
        with col_main3:
            st.markdown("#### Probabilidades")
            probs_df = pd.DataFrame(probs.items(), columns=['Resultado', 'Probabilidade'])
            st.dataframe(probs_df.set_index('Resultado'))
        
        st.markdown("---")
        st.markdown("### Padrões Detectados")
        
        detected_patterns = {k: v for k, v in results.items() if v.get('found')}
        if detected_patterns:
            for pattern_name, details in detected_patterns.items():
                st.markdown(f"**- {pattern_name.replace('_', ' ').title()}**: Confiança {details.get('conf')}%")
                if details.get('pattern'):
                    pattern_emojis = [EMOJI_MAP.get(p, '?') for p in details['pattern']]
                    st.markdown(f"  Padrão: `{' '.join(details['pattern'])}` -> {' '.join(pattern_emojis)}")
        else:
            st.info("Nenhum padrão forte detectado na sequência atual.")
    else:
        st.info("Adicione alguns resultados para iniciar a análise.")

if __name__ == "__main__":
    main()

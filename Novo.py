import streamlit as st
from collections import deque, Counter
import math

# -------------------------
# Config e inicialização
# -------------------------
MAX_HISTORY = 1000          # Limite de entradas em memória
ANALYSIS_WINDOW = 27        # Janela usada para análises

st.set_page_config(page_title="Football Studio – Análise Avançada", layout="wide")

# Inicializa histórico como deque para limite automático
if "historico" not in st.session_state:
    st.session_state.historico = deque(maxlen=MAX_HISTORY)

# -------------------------
# Utilitárias
# -------------------------
def bolha_cor(r):
    return {"C": "🟥", "V": "🟦", "E": "🟨"}.get(r, "⬜")

def get_valores(h):
    vals = [x for x in h if x in ("C", "V", "E")]
    return vals[-ANALYSIS_WINDOW:]

# -------------------------
# Métricas e análises
# -------------------------
def maior_sequencia(h):
    v = get_valores(h)
    if not v:
        return 0
    max_seq = atual = 1
    for i in range(1, len(v)):
        if v[i] == v[i-1]:
            atual += 1
            if atual > max_seq:
                max_seq = atual
        else:
            atual = 1
    return max_seq

def sequencia_final(h):
    v = get_valores(h)
    if not v:
        return 0
    atual = v[-1]
    cont = 1
    for i in range(len(v)-2, -1, -1):
        if v[i] == atual:
            cont += 1
        else:
            break
    return cont

def alternancia(h):
    v = get_valores(h)
    if len(v) <= 1:
        return 0
    return sum(1 for i in range(1, len(v)) if v[i] != v[i-1])

def eco_visual(h):
    v = get_valores(h)
    if len(v) < 12:
        return {"status": "Poucos dados", "detected": False}
    detected = v[-6:] == v[-12:-6]
    return {"status": "Detectado" if detected else "Não houve", "detected": detected}

def eco_parcial(h):
    v = get_valores(h)
    if len(v) < 12:
        return {"status": "Poucos dados", "match_count": 0}
    anterior = v[-12:-6]
    atual = v[-6:]
    semelhantes = sum(1 for a, b in zip(anterior, atual) if a == b or (a in ['C','V'] and b in ['C','V']))
    return {"status": f"{semelhantes}/6 semelhantes", "match_count": semelhantes}

def dist_empates(h):
    v = get_valores(h)
    empates = [i for i, r in enumerate(v) if r == 'E']
    if len(empates) < 2:
        return None
    return empates[-1] - empates[-2]

def blocos_espelhados(h):
    v = get_valores(h)
    cont = 0
    for i in range(len(v) - 5):
        if v[i:i+3] == v[i+3:i+6][::-1]:
            cont += 1
    return cont

def alternancia_por_linha(h, cols=9):
    v = get_valores(h)
    linhas = [v[i:i+cols] for i in range(0, len(v), cols)]
    return [sum(1 for j in range(1, len(l)) if l[j] != l[j-1]) for l in linhas]

def tendencia_final(h, window=5):
    v = get_valores(h)
    if not v:
        return {"C":0, "V":0, "E":0}
    ult = v[-window:]
    return {"C": ult.count("C"), "V": ult.count("V"), "E": ult.count("E")}

def analise_por_terco(h):
    v = get_valores(h)
    if len(v) < ANALYSIS_WINDOW:
        return {}
    t1, t2, t3 = v[:9], v[9:18], v[18:27]
    return {
        "t1": {"C": t1.count("C"), "V": t1.count("V"), "E": t1.count("E")},
        "t2": {"C": t2.count("C"), "V": t2.count("V"), "E": t2.count("E")},
        "t3": {"C": t3.count("C"), "V": t3.count("V"), "E": t3.count("E")}
    }

def contagem_sequencias(h):
    v = get_valores(h)
    if len(v) < 2:
        return {"seq_2":0, "seq_3":0, "seq_4+":0}
    sequencias = {"seq_2":0, "seq_3":0, "seq_4+":0}
    atual = 1
    for i in range(1, len(v)):
        if v[i] == v[i-1]:
            atual += 1
        else:
            if atual == 2:
                sequencias["seq_2"] += 1
            elif atual == 3:
                sequencias["seq_3"] += 1
            elif atual >= 4:
                sequencias["seq_4+"] += 1
            atual = 1
    if atual == 2:
        sequencias["seq_2"] += 1
    elif atual == 3:
        sequencias["seq_3"] += 1
    elif atual >= 4:
        sequencias["seq_4+"] += 1
    return sequencias

def entropia(h):
    v = get_valores(h)
    if not v:
        return 0.0
    freq = Counter(v)
    total = len(v)
    H = 0.0
    for _, c in freq.items():
        p = c/total
        H -= p * math.log2(p)
    maxH = math.log2(3)
    return (H / maxH) * 100

def quebra_padrao(h):
    v = get_valores(h)
    if len(v) < 6:
        return {"status": "Poucos dados", "break": False}
    if all(v[-6+i] != v[-6+i-1] for i in range(1,6)) and sequencia_final(h) > 1:
        return {"status": "Quebra de alternância detectada", "break": True}
    return {"status": "Sem quebra", "break": False}

# -------------------------
# Sistema preditivo — sugestão
# -------------------------
def sugestao(h):
    v = get_valores(h)
    if not v:
        return {"texto":"Insira resultados para gerar previsão.", "tipo":"info", "bet": None, "confianca": 0.0}
    ult = v[-1]
    seq = sequencia_final(h)
    eco = eco_visual(h)
    parcial = eco_parcial(h)
    quebra = quebra_padrao(h)
    contagens = Counter(v)
    score = {"C":0.0, "V":0.0, "E":0.0}

    if seq >= 5 and ult in ("C","V"):
        inv = "V" if ult == "C" else "C"
        score[inv] += 3.0
    elif seq >= 3 and ult in ("C","V"):
        inv = "V" if ult == "C" else "C"
        score[inv] += 1.5

    if ult == "E":
        score["C"] += 1.0
        score["V"] += 1.0

    if eco["detected"]:
        score[ult] += 2.5
    elif parcial["match_count"] >= 4:
        score[ult] += 1.5

    if len(v) >= 9:
        maior = contagens.most_common(1)[0][0]
        score[maior] += 1.0

    if quebra["break"]:
        score[ult] += 1.5

    ent = entropia(h)
    if ent < 45:
        maior = contagens.most_common(1)[0][0]
        score[maior] += 0.8

    score["E"] *= 0.6

    ordem = sorted(score.items(), key=lambda x: x[1], reverse=True)
    melhor, melhor_val = ordem[0]
    soma = sum(score.values()) if sum(score.values()) != 0 else 1.0
    confianca = (melhor_val / soma) * 100
    reasons = []
    if seq >= 3:
        reasons.append(f"Sequência final: {seq}")
    if eco["detected"]:
        reasons.append("Eco visual detectado")
    if parcial["match_count"] >= 4:
        reasons.append(f"Eco parcial: {parcial['match_count']}/6")
    if quebra["break"]:
        reasons.append("Quebra de alternância")
    reasons.append(f"Entropia: {ent:.1f}%")
    razoes = " | ".join(reasons)

    texto = f"🎯 Sugestão: {bolha_cor(melhor)} ({melhor}) — confiança {confianca:.1f}% | ⚙️ Razões: {razoes}"
    tipo = "success" if confianca >= 60 else ("warning" if confianca >= 40 else "info")
    return {"texto": texto, "tipo": tipo, "bet": melhor, "confianca": confianca, "score": score}

# -------------------------
# Interface
# -------------------------
st.title("🎲 Football Studio Live — Leitura Estratégica")

# Entrada de resultados
col1, col2, col3, col4 = st.columns(4)
if col1.button("➕ Casa (C)"): st.session_state.historico.append("C")
if col2.button("➕ Visitante (V)"): st.session_state.historico.append("V")
if col3.button("➕ Empate (E)"): st.session_state.historico.append("E")
if col4.button("🧹 Limpar histórico"):
    st.session_state.historico.clear()
    st.rerun()

h = st.session_state.historico

# Sugestão
st.subheader("🎯 Sugestão de entrada")
sug = sugestao(h)
if sug["tipo"] == "success":
    st.success(sug["texto"])
elif sug["tipo"] == "warning":
    st.warning(sug["texto"])
else:
    st.info(sug["texto"])

# Histórico visual
st.subheader("🧾 Histórico visual (últimas linhas)")
bolhas = [bolha_cor(r) for r in reversed(h)]
for i in range(0, len(bolhas), 9):
    linha = bolhas[i:i+9]
    st.markdown(" ".join(linha))

# Métricas principais
st.subheader("📊 Análises recentes")
valores = get_valores(h)
col1, col2, col3 = st.columns(3)
col1.metric("Total Casa", valores.count("C"))
col2.metric("Total Visitante", valores.count("V"))
col3.metric("Total Empates", valores.count("E"))

st.write("---")
col1, col2, col3 = st.columns(3)
col1.metric("Maior sequência", maior_sequencia(h))
col2.metric("Alternância total", alternancia(h))
col3.metric("Distância entre empates", dist_empates(h) or "-")

st.write("---")
col1, col2 = st.columns(2)
col1.metric("Eco visual", eco_visual(h)["status"])
col2.metric("Eco parcial", eco_parcial(h)["status"])
st.write(f"Blocos espelhados: **{blocos_espelhados(h)}**")
st.write(f"Tendência final: **{tendencia_final(h)}**")
st.write(f"Alternância por linha: **{alternancia_por_linha(h)}**")

# Novas métricas
st.subheader("🔎 Análise Avançada de Padrões")
analise_tercos = analise_por_terco(h)
if analise_tercos:
    col1, col2, col3 = st.columns(3)
    col1.metric("Terço 1", f"C:{analise_tercos['t1']['C']} V:{analise_tercos['t1']['V']} E:{analise_tercos['t1']['E']}")
    col2.metric("Terço 2", f"C:{analise_tercos['t2']['C']} V:{analise_tercos['t2']['V']} E:{analise_tercos['t2']['E']}")
    col3.metric("Terço 3", f"C:{analise_tercos['t3']['C']} V:{analise_tercos['t3']['V']} E:{analise_tercos['t3']['E']}")

st.write(f"Contagem de Sequências: **{contagem_sequencias(h)}**")
st.write(f"Quebra de Padrão: **{quebra_padrao(h)['status']}**")
st.write(f"Entropia: **{entropia(h):.1f}%**")

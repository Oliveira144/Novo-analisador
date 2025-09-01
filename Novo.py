import streamlit as st
from collections import deque, Counter
import math
import csv
import io
import datetime

# -------------------------
# Config e inicialização
# -------------------------
MAX_HISTORY = 1000          # Limite de entradas em memória
ANALYSIS_WINDOW = 27        # Janela usada para análises
SIDEBAR_WIDTH = 300

st.set_page_config(page_title="Football Studio – Análise Avançada", layout="wide")

# Inicializa histórico como deque para limite automático
if "historico" not in st.session_state:
    st.session_state.historico = deque(maxlen=MAX_HISTORY)

# -------------------------
# Utilitárias
# -------------------------

def bolha_cor(r):
    """Retorna emoji/bolha para um valor 'C','V' ou 'E'."""
    return {"C": "🟥", "V": "🟦", "E": "🟨"}.get(r, "⬜")


def get_valores(h):
    """Filtra apenas valores válidos e retorna os últimos ANALYSIS_WINDOW."""
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
    return {"t1": {"C": t1.count("C"), "V": t1.count("V"), "E": t1.count("E")},
            "t2": {"C": t2.count("C"), "V": t2.count("V"), "E": t2.count("E")},
            "t3": {"C": t3.count("C"), "V": t3.count("V"), "E": t3.count("E")}}


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
    # última sequência
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


def detectar_ciclos(h, min_len=2, max_len=6):
    v = get_valores(h)
    found = []
    seq = v[-ANALYSIS_WINDOW:]
    L = len(seq)
    for l in range(min_len, max_len+1):
        if L < l*2:
            continue
        bloco = seq[-l:]
        anterior = seq[-2*l:-l]
        if bloco == anterior:
            found.append({"len": l, "pattern": bloco})
    return found


def padrao_alternancia_strito(h, window=6):
    v = get_valores(h)
    if len(v) < window:
        return False
    w = v[-window:]
    return all(w[i] != w[i-1] for i in range(1, len(w)))


def quebra_padrao(h):
    v = get_valores(h)
    if len(v) < 6:
        return {"status": "Poucos dados", "break": False}
    if padrao_alternancia_strito(h, window=6) and sequencia_final(h) > 1:
        return {"status": "Quebra de alternância detectada", "break": True}
    return {"status": "Sem quebra", "break": False}

# -------------------------
# Nível de manipulação (1 a 9)
# -------------------------

def nivel_manipulacao(h):
    v = get_valores(h)
    if len(v) < 9:
        return 1
    score = 0
    seq = sequencia_final(h)
    if seq >= 3:
        score += 2
    if seq >= 5:
        score += 2
    if eco_visual(h)["detected"]:
        score += 2
    if eco_parcial(h)["match_count"] >= 4:
        score += 1
    if blocos_espelhados(h) >= 1:
        score += 1
    d_emp = dist_empates(h)
    if isinstance(d_emp, int) and d_emp <= 2:
        score += 1
    if entropia(h) < 40:
        score += 1
    if quebra_padrao(h)["break"]:
        score += 1
    return max(1, min(1 + score, 9))

# -------------------------
# Sistema preditivo — sugestão com pontuação
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

    # Regras ponderadas
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

    # Penaliza empates para que não venham primeiro em score empate
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
    texto = f"🎯 Sugestão: {bolha_cor(melhor)} ({melhor}) — confiança {confianca:.1f}%

⚙️ Razões: {razoes}"
    tipo = "success" if confianca >= 60 else ("warning" if confianca >= 40 else "info")
    return {"texto": texto, "tipo": tipo, "bet": melhor, "confianca": confianca, "score": score}

# -------------------------
# Alertas graduados
# -------------------------

def gerar_alertas(h):
    alerts = []
    v = get_valores(h)
    if not v:
        return alerts
    seq = sequencia_final(h)
    if seq >= 7:
        alerts.append({"nivel": "crítico", "msg": f"🔴 Sequência muito longa ({seq}) — alto risco de reversão/manipulação."})
    elif seq >= 5:
        alerts.append({"nivel": "médio", "msg": f"🟠 Sequência ativa ({seq}) — possível inversão."})
    elif seq >= 3:
        alerts.append({"nivel": "leve", "msg": f"🟡 Sequência de {seq} — monitorar."})
    if eco_visual(h)["detected"]:
        alerts.append({"nivel": "médio", "msg": "🔁 Eco visual detectado — padrão repetido."})
    if eco_parcial(h)["match_count"] >= 5:
        alerts.append({"nivel": "médio", "msg": "🔁 Eco parcial forte — alta semelhança entre blocos."})
    d_emp = dist_empates(h)
    if isinstance(d_emp, int) and d_emp == 1:
        alerts.append({"nivel": "crítico", "msg": "🟨 Empates consecutivos — instabilidade imediata."})
    if blocos_espelhados(h) >= 1:
        alerts.append({"nivel": "leve", "msg": "🧩 Blocos espelhados detectados."})
    if quebra_padrao(h)["break"]:
        alerts.append({"nivel": "médio", "msg": "💥 Quebra de alternância — nova tendência possível."})
    nivel_ordem = {"crítico":3, "médio":2, "leve":1}
    return sorted(alerts, key=lambda a: nivel_ordem.get(a["nivel"], 0), reverse=True)

# -------------------------
# Visual do histórico
# -------------------------

def exibir_historico_visual(h, cols=9, active_rows=3):
    v = [x for x in h if x in ("C","V","E")]
    if not v:
        st.info("Sem resultados ainda.")
        return
    rev = v[::-1]
    rows = [rev[i:i+cols] for i in range(0, len(rev), cols)]
    for idx, row in enumerate(rows):
        is_active = idx < active_rows
        size = "26px" if is_active else "20px"
        opacity = "1" if is_active else "0.45"
        row_html = "".join(f"<span style='font-size:{size}; opacity:{opacity}; margin-right:6px;'>{bolha_cor(c)}</span>" for c in row)
        st.markdown(f"<div style='display:flex; align-items:center; margin-bottom:6px;'>{row_html}</div>", unsafe_allow_html=True)

# -------------------------
# Export / Import helpers
# -------------------------

def export_csv(h):
    v = [x for x in h]
    if not v:
        return None
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "result"])
    ts = datetime.datetime.now().isoformat()
    for r in v:
        writer.writerow([ts, r])
    return output.getvalue()

# -------------------------
# Interface / Layout
# -------------------------

st.title("🎲 Football Studio Live — Leitura Estratégica (Refinado)")

# Input buttons
col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    if st.button("➕ Casa (🟥)"):
        st.session_state.historico.append("C")
        st.rerun()
with col2:
    if st.button("➕ Visitante (🟦)"):
        st.session_state.historico.append("V")
        st.rerun()
with col3:
    if st.button("➕ Empate (🟨)"):
        st.session_state.historico.append("E")
        st.rerun()
with col4:
    if st.button("🔄 Reiniciar Baralho"):
        st.session_state.historico.clear()
        st.success("Histórico reiniciado.")
        st.rerun()

h_full = list(st.session_state.historico)

# Suggestion
st.subheader("🎯 Sugestão de Entrada")
res = sugestao(h_full)
if res["tipo"] == "success":
    st.success(res["texto"])
elif res["tipo"] == "warning":
    st.warning(res["texto"])
else:
    st.info(res["texto"])

# Histórico visual
st.subheader("🧾 Histórico visual (zona ativa: 3 linhas)")
exibir_historico_visual(h_full)

st.write("---")
st.subheader("📊 Análise dos últimos 27 jogadas")
valores = get_valores(h_full)

colA, colB, colC = st.columns(3)
colA.metric("Total Casa (últ 27)", valores.count("C"))
colB.metric("Total Visitante (últ 27)", valores.count("V"))
colC.metric("Total Empates (últ 27)", valores.count("E"))

st.write("---")
cm1, cm2, cm3 = st.columns(3)
cm1.metric("Maior sequência", maior_sequencia(h_full))
cm2.metric("Alternância total", alternancia(h_full))
emp_dist = dist_empates(h_full)
cm3.metric("Distância entre empates", emp_dist if emp_dist is not None else "N/A")

st.write("---")
cm4, cm5, cm6 = st.columns(3)
eco = eco_visual(h_full)
cm4.metric("Eco visual", eco["status"])
par = eco_parcial(h_full)
cm5.metric("Eco parcial", par["status"])
cm6.metric("Entropia (%)", f"{entropia(h_full):.1f}%")

st.write(f"Blocos espelhados: **{blocos_espelhados(h_full)}**")
st.write(f"Tendência final (últ 5): **{tendencia_final(h_full, window=5)['C']}C / {tendencia_final(h_full, window=5)['V']}V / {tendencia_final(h_full, window=5)['E']}E**")
st.write(f"Alternância por linha (cada 9): **{alternancia_por_linha(h_full)}**")

# Análise avançada
st.subheader("🔎 Análise Avançada de Padrões")
tercos = analise_por_terco(h_full)
if tercos:
    t1, t2, t3 = tercos['t1'], tercos['t2'], tercos['t3']
    tcol1, tcol2, tcol3 = st.columns(3)
    tcol1.metric("Terço 1 (1-9)", f"{t1['C']}C / {t1['V']}V / {t1['E']}E")
    tcol2.metric("Terço 2 (10-18)", f"{t2['C']}C / {t2['V']}V / {t2['E']}E")
    tcol3.metric("Terço 3 (19-27)", f"{t3['C']}C / {t3['V']}V / {t3['E']}E")
else:
    st.info("Dados insuficientes para análise por terços (necessita >= 27 jogadas válidas).")

st.write("---")
st.write(f"Contagem de Sequências: **{contagem_sequencias(h_full)}**")
st.write(f"Quebra de Padrão (Breakout): **{quebra_padrao(h_full)['status']}**")
st.write(f"Detecção de ciclos/repete: **{detectar_ciclos(h_full)}**")

# Nível de manipulação
nivel = nivel_manipulacao(h_full)
st.subheader("🧠 Nível estimado de manipulação")
st.metric("Nível (1 a 9)", nivel)

# Alertas
st.subheader("🚨 Alertas estratégicos")
alerts = gerar_alertas(h_full)
if not alerts:
    st.info("Nenhum padrão crítico identificado.")
else:
    for a in alerts:
        if a['nivel'] == 'crítico':
            st.error(a['msg'])
        elif a['nivel'] == 'médio':
            st.warning(a['msg'])
        else:
            st.info(a['msg'])

st.write("---")
# Export / Import
st.subheader("💾 Exportar / Importar histórico")
col_e1, col_e2 = st.columns([1,1])
with col_e1:
    csv_data = export_csv(h_full)
    if csv_data:
        st.download_button("⬇️ Baixar CSV", data=csv_data, file_name="historico_football.csv", mime='text/csv')
    else:
        st.button("⬇️ Baixar CSV (sem dados)", disabled=True)
with col_e2:
    uploaded = st.file_uploader("📤 Importar CSV (coluna 'result')", type=['csv'])
    if uploaded is not None:
        try:
            s = io.StringIO(uploaded.getvalue().decode('utf-8'))
            reader = csv.DictReader(s)
            imported = 0
            for row in reader:
                val = row.get('result') or row.get('result'.upper())
                if val and val.strip() in ('C','V','E'):
                    st.session_state.historico.append(val.strip())
                    imported += 1
            st.success(f"Importados: {imported} resultados")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {e}")

st.write("---")
st.subheader("📌 Detalhes / debug rápido")
st.write(f"Janela de análise: {ANALYSIS_WINDOW} últimas jogadas válidas")
st.write(f"Histórico total (últimos {len(h_full)} entradas): {h_full}")
res_score = res.get('score') if isinstance(res, dict) else None
st.write(f"Score interno (exemplo): {res_score}")

# Limpar histórico
if st.button("🧹 Limpar histórico"):
    st.session_state.historico.clear()
    st.rerun()

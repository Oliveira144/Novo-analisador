import streamlit as st
from collections import Counter, deque
import math

# -------------------------
# Config e inicialização
# -------------------------
MAX_HISTORY = 200  # limite total de entradas na sessão (mantém memória)
ANALYSIS_WINDOW = 27  # janela usada para a maioria das análises

st.set_page_config(page_title="Football Studio – Análise Avançada", layout="wide")
st.title("🎲 Football Studio Live — Leitura Estratégica (refinado)")

if "historico" not in st.session_state:
    st.session_state.historico = deque(maxlen=MAX_HISTORY)  # mantemos como deque para limite automático

# -------------------------
# Utilitárias básicas
# -------------------------
def adicionar_resultado(valor):
    # Valor pode ser "C", "V", "E" ou "🔽" (reiniciar)
    if valor == "🔽":
        # Reiniciar: limpa histórico
        st.session_state.historico.clear()
    else:
        st.session_state.historico.append(valor)

def lista_historico():
    # retorna lista simples a partir do deque (ordem cronológica)
    return list(st.session_state.historico)

def filtrar_validos(h):
    # Remove qualquer símbolo não relacionado e pega os últimos ANALYSIS_WINDOW válidos
    valid = [r for r in h if r in ("C", "V", "E")]
    return valid[-ANALYSIS_WINDOW:]

# Bubbles/bolha emoji
def bolha_cor(r):
    return {"C": "🟥", "V": "🟦", "E": "🟨"}.get(r, "⬜")

# -------------------------
# Métricas e análises
# -------------------------
def maior_sequencia(h):
    valores = filtrar_validos(h)
    if not valores:
        return 0
    max_seq = atual = 1
    for i in range(1, len(valores)):
        if valores[i] == valores[i - 1]:
            atual += 1
            if atual > max_seq:
                max_seq = atual
        else:
            atual = 1
    return max_seq

def sequencia_final(h):
    valores = filtrar_validos(h)
    if not valores:
        return 0
    atual = valores[-1]
    count = 1
    for i in range(len(valores) - 2, -1, -1):
        if valores[i] == atual:
            count += 1
        else:
            break
    return count

def alternancia(h):
    valores = filtrar_validos(h)
    if len(valores) <= 1:
        return 0
    return sum(1 for i in range(1, len(valores)) if valores[i] != valores[i - 1])

def eco_visual(h):
    valores = filtrar_validos(h)
    if len(valores) < 12:
        return {"status": "Poucos dados", "detected": False}
    # compara últimos 6 com os 6 anteriores
    detected = valores[-6:] == valores[-12:-6]
    return {"status": "Detectado" if detected else "Não houve", "detected": detected}

def eco_parcial(h):
    valores = filtrar_validos(h)
    if len(valores) < 12:
        return {"status": "Poucos dados", "match_count": 0}
    anterior = valores[-12:-6]
    atual = valores[-6:]
    semelhantes = sum(1 for a, b in zip(anterior, atual) if a == b or (a in ["C","V"] and b in ["C","V"]))
    return {"status": f"{semelhantes}/6 semelhantes", "match_count": semelhantes}

def dist_empates(h):
    valores = filtrar_validos(h)
    empates = [i for i, r in enumerate(valores) if r == "E"]
    if len(empates) < 2:
        return None
    return empates[-1] - empates[-2]

def blocos_espelhados(h):
    valores = filtrar_validos(h)
    cont = 0
    # procura blocos 3 que sejam espelhados (abc == cba)
    for i in range(len(valores) - 5):
        if valores[i:i+3] == valores[i+3:i+6][::-1]:
            cont += 1
    return cont

def alternancia_por_linha(h, cols=9):
    valores = filtrar_validos(h)
    linhas = [valores[i:i+cols] for i in range(0, len(valores), cols)]
    return [sum(1 for j in range(1, len(l)) if l[j] != l[j-1]) for l in linhas]

def tendencia_final(h, window=5):
    valores = filtrar_validos(h)
    if not valores:
        return {"C":0,"V":0,"E":0}
    ult = valores[-window:]
    return {"C": ult.count("C"), "V": ult.count("V"), "E": ult.count("E")}

def analise_por_terco(h):
    valores = filtrar_validos(h)
    if len(valores) < ANALYSIS_WINDOW:
        return {}
    t1 = valores[:9]
    t2 = valores[9:18]
    t3 = valores[18:27]
    return {
        "t1": {"C": t1.count("C"), "V": t1.count("V"), "E": t1.count("E")},
        "t2": {"C": t2.count("C"), "V": t2.count("V"), "E": t2.count("E")},
        "t3": {"C": t3.count("C"), "V": t3.count("V"), "E": t3.count("E")}
    }

def contagem_sequencias(h):
    valores = filtrar_validos(h)
    if len(valores) < 2:
        return {"seq_2":0,"seq_3":0,"seq_4+":0}
    sequencias = {"seq_2": 0, "seq_3": 0, "seq_4+": 0}
    atual_seq = 1
    for i in range(1, len(valores)):
        if valores[i] == valores[i-1]:
            atual_seq += 1
        else:
            if atual_seq == 2: sequencias["seq_2"] += 1
            elif atual_seq == 3: sequencias["seq_3"] += 1
            elif atual_seq >= 4: sequencias["seq_4+"] += 1
            atual_seq = 1
    # última sequência
    if atual_seq == 2: sequencias["seq_2"] += 1
    elif atual_seq == 3: sequencias["seq_3"] += 1
    elif atual_seq >= 4: sequencias["seq_4+"] += 1
    return sequencias

# Entropia de Shannon (normalizada)
def entropia(h):
    valores = filtrar_validos(h)
    if not valores:
        return 0.0
    freq = Counter(valores)
    total = len(valores)
    H = 0.0
    for _, c in freq.items():
        p = c/total
        H -= p * math.log2(p)
    # normalizar por log2(k) onde k = número possível de símbolos (3)
    maxH = math.log2(3)
    return (H / maxH) * 100  # retorna porcentagem de entropia (0-100)

# Detecta ciclos / padrões repetidos nos últimos ANALYSIS_WINDOW
def detectar_ciclos(h, min_len=2, max_len=6):
    valores = filtrar_validos(h)
    found = []
    seq = valores[-ANALYSIS_WINDOW:]
    L = len(seq)
    for l in range(min_len, max_len+1):
        # checar se há repetição de um bloco final
        if L < l*2:
            continue
        bloco = seq[-l:]
        anterior = seq[-2*l:-l]
        if bloco == anterior:
            found.append({"len": l, "pattern": bloco})
    return found

# Detecta padrões como C V C V C (alternância estrita)
def padrao_alternancia_strito(h, window=6):
    valores = filtrar_validos(h)
    if len(valores) < window:
        return False
    w = valores[-window:]
    return all(w[i] != w[i-1] for i in range(1, len(w)))

def quebra_padrao(h):
    valores = filtrar_validos(h)
    if len(valores) < 6:
        return {"status": "Poucos dados", "break": False}
    # se houve alternância estrita e uma sequência no final indica quebra
    if padrao_alternancia_strito(h, window=6) and sequencia_final(h) > 1:
        return {"status": "Quebra de alternância detectada", "break": True}
    return {"status": "Sem quebra", "break": False}

# -------------------------
# Nível de Manipulação (1 a 9)
# -------------------------
def nivel_manipulacao(h):
    score = 0
    valores = filtrar_validos(h)
    if len(valores) < 9:
        return 1
    # pesos/critérios
    # sequencia longa
    seq_final = sequencia_final(h)
    if seq_final >= 3:
        score += 2
    if seq_final >= 5:
        score += 2
    # eco visual
    if eco_visual(h)["detected"]:
        score += 2
    # eco parcial forte
    if eco_parcial(h)["match_count"] >= 4:
        score += 1
    # blocos espelhados
    if blocos_espelhados(h) >= 1:
        score += 1
    # dist empates pequenos
    d_emp = dist_empates(h)
    if isinstance(d_emp, int) and d_emp <= 2:
        score += 1
    # entropia baixa (muito previsível) aumenta suspeita
    ent = entropia(h)
    if ent < 40:
        score += 1
    # quebra de padrão recente
    if quebra_padrao(h)["break"]:
        score += 1
    nivel = 1 + score  # base 1
    return max(1, min(nivel, 9))

# -------------------------
# Sistema preditivo — sugestão com pontuação ponderada
# -------------------------
def sugestao(h):
    valores = filtrar_validos(h)
    if not valores:
        return {"texto":"Insira resultados para gerar previsão.", "tipo":"info", "bet": None, "confianca": 0.0}

    ult = valores[-1]
    seq = sequencia_final(h)
    eco = eco_visual(h)
    parcial = eco_parcial(h)
    quebra = quebra_padrao(h)
    contagens = Counter(valores)

    # Inicializa score
    score = {"C": 0.0, "V": 0.0, "E": 0.0}

    # Regras ponderadas (valores empíricos, podem ser afinados)
    # 1) Sequência longa => favorece reversão (peso alto se seq >=5)
    if seq >= 5 and ult in ("C","V"):
        inv = "V" if ult == "C" else "C"
        score[inv] += 3.0
        reason_seq = f"Sequência final de {seq} {bolha_cor(ult)} detectada (favor reversão)"
    elif seq >= 3 and ult in ("C","V"):
        inv = "V" if ult == "C" else "C"
        score[inv] += 1.5
        reason_seq = f"Sequência curta ({seq}) favorece reversão"
    else:
        reason_seq = ""

    # 2) Empate recente — aumenta incerteza (distribui pontos para ambas cores)
    if ult == "E":
        score["C"] += 1.0
        score["V"] += 1.0
        reason_emp = "Empate recente — instabilidade"
    else:
        reason_emp = ""

    # 3) Eco detectado — reforça repetição da última cor
    if eco["detected"]:
        score[ult] += 2.5
        reason_eco = "Eco visual detectado — repetir padrão"
    elif parcial["match_count"] >= 4:
        score[ult] += 1.5
        reason_eco = f"Eco parcial {parcial['match_count']}/6 — similaridade"
    else:
        reason_eco = ""

    # 4) Frequência histórica (maior frequência ganha 1 ponto)
    if len(valores) >= 9:
        maior = contagens.most_common(1)[0][0]
        score[maior] += 1.0
        reason_freq = f"Tendência histórica favorece {maior}"
    else:
        reason_freq = ""

    # 5) Quebra de padrão sugere continuidade inesperada — reforça último
    if quebra["break"]:
        score[ult] += 1.5
        reason_quebra = "Quebra de alternância detectada — atenção à nova tendência"
    else:
        reason_quebra = ""

    # 6) Entropia baixa => sistema previsível, favorece maior frequência
    ent = entropia(h)
    if ent < 45:
        maior = contagens.most_common(1)[0][0]
        score[maior] += 0.8
        reason_ent = f"Entropia baixa ({ent:.1f}%) — padrão previsível"
    else:
        reason_ent = f"Entropia {ent:.1f}%"

    # Normaliza e escolhe melhor opção
    # Evita que empate leve a escolher "E" sem necessidade: tratamos E com menos prioridade
    score["E"] *= 0.6

    # Convert to sorted list
    ordem = sorted(score.items(), key=lambda x: x[1], reverse=True)
    melhor, melhor_val = ordem[0]
    soma = sum(score.values()) if sum(score.values()) != 0 else 1.0
    confianca = (melhor_val / soma) * 100

    # Geração de texto com razões
    reasons = [r for r in [reason_seq, reason_emp, reason_eco, reason_freq, reason_quebra, reason_ent] if r]
    razoes = " | ".join(reasons) if reasons else "Baseado em métricas padrão"

    texto = f"🎯 Sugestão: {bolha_cor(melhor)} ({melhor}) — confiança {confianca:.1f}%\n\n⚙️ Razões: {razoes}"
    tipo = "success" if confianca >= 60 else ("warning" if confianca >= 40 else "info")
    return {"texto": texto, "tipo": tipo, "bet": melhor, "confianca": confianca, "score": score}

# -------------------------
# Alerta graduado (leve, médio, crítico)
# -------------------------
def gerar_alertas(h):
    alerts = []
    valores = filtrar_validos(h)
    if not valores:
        return alerts

    seq = sequencia_final(h)
    if seq >= 7:
        alerts.append({"nivel":"crítico", "msg": f"🔴 Sequência muito longa ({seq}) — alto risco de manipulação/reversão."})
    elif seq >= 5:
        alerts.append({"nivel":"médio", "msg": f"🟠 Sequência ativa ({seq}) — possível inversão em breve."})
    elif seq >= 3:
        alerts.append({"nivel":"leve", "msg": f"🟡 Sequência de {seq} — monitorar."})

    eco = eco_visual(h)
    if eco["detected"]:
        alerts.append({"nivel":"médio", "msg":"🔁 Eco visual detectado — padrão repetido."})
    elif eco_parcial(h)["match_count"] >= 5:
        alerts.append({"nivel":"médio", "msg":"🔁 Eco parcial forte — semelhante entre blocos."})

    d_emp = dist_empates(h)
    if isinstance(d_emp, int) and d_emp == 1:
        alerts.append({"nivel":"crítico", "msg":"🟨 Empates consecutivos — alta instabilidade."})

    if blocos_espelhados(h) >= 1:
        alerts.append({"nivel":"leve", "msg":"🧩 Blocos espelhados detectados — reflexo estratégico."})

    if quebra_padrao(h)["break"]:
        alerts.append({"nivel":"médio", "msg":"💥 Quebra de alternância — nova tendência pode estar surgindo."})

    # Ordena por nível de severidade
    nivel_ordem = {"crítico": 3, "médio": 2, "leve": 1}
    alerts_sorted = sorted(alerts, key=lambda a: nivel_ordem.get(a["nivel"], 0), reverse=True)
    return alerts_sorted

# -------------------------
# Visual do histórico
# -------------------------
def exibir_historico_visual(h, cols=9, active_rows=3):
    valores = [v for v in h if v in ("C","V","E")]
    # Reverter para exibir do mais recente para o topo
    rev = valores[::-1]
    rows = [rev[i:i+cols] for i in range(0, len(rev), cols)]
    # zone active: primeiras active_rows linhas (mais recentes)
    html = ""
    for idx, row in enumerate(rows):
        is_active = idx < active_rows
        style_size = "26px" if is_active else "20px"
        opacity = "1" if is_active else "0.45"
        # constrói linha
        row_html = "".join(f"<span style='font-size:{style_size}; opacity:{opacity}; margin-right:6px;'>{bolha_cor(c)}</span>" for c in row)
        html += f"<div style='display:flex; align-items:center; margin-bottom:6px;'>{row_html}</div>"
    if not html:
        html = "<div>Sem resultados ainda.</div>"
    st.markdown(html, unsafe_allow_html=True)

# -------------------------
# Layout / Interface
# -------------------------
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
with col_btn1:
    if st.button("➕ Casa (C)"):
        adicionar_resultado("C")
with col_btn2:
    if st.button("➕ Visitante (V)"):
        adicionar_resultado("V")
with col_btn3:
    if st.button("➕ Empate (E)"):
        adicionar_resultado("E")
with col_btn4:
    if st.button("🔄 Reiniciar Baralho"):
        adicionar_resultado("🔽")
        st.success("Histórico reiniciado.")

h_full = lista_historico()
h_valid = filtrar_validos(h_full)

# Sugestão preditiva
st.subheader("🎯 Sugestão de Entrada")
s = sugestao(h_full)
if s["tipo"] == "success":
    st.success(s["texto"])
elif s["tipo"] == "warning":
    st.warning(s["texto"])
else:
    st.info(s["texto"])

# Painel principal com histórico visual e métricas
st.subheader("🧾 Histórico visual (zona ativa: 3 linhas)")
exibir_historico_visual(h_full)

st.write("---")
st.subheader("📊 Análise dos últimos 27 jogadas")
valores = h_valid  # já está limitado por filtrar_validos

col1, col2, col3 = st.columns(3)
col1.metric("Total Casa (últ 27)", valores.count("C"))
col2.metric("Total Visitante (últ 27)", valores.count("V"))
col3.metric("Total Empates (últ 27)", valores.count("E"))

st.write("---")
c1, c2, c3 = st.columns(3)
c1.metric("Maior sequência (janela)", maior_sequencia(h_full))
c2.metric("Alternância total", alternancia(h_full))
d_emp = dist_empates(h_full)
c3.metric("Distância entre empates", d_emp if d_emp is not None else "N/A")

st.write("---")
c4, c5, c6 = st.columns(3)
eco = eco_visual(h_full)
c4.metric("Eco visual", eco["status"])
par = eco_parcial(h_full)
c5.metric("Eco parcial", par["status"])
c6.metric("Entropia (%)", f"{entropia(h_full):.1f}%")

st.write(f"Blocos espelhados: **{blocos_espelhados(h_full)}**")
st.write(f"Tendência final (últ 5): **{tendencia_final(h_full, window=5)['C']}C / {tendencia_final(h_full, window=5)['V']}V / {tendencia_final(h_full, window=5)['E']}E**")
st.write(f"Alternância por linha (cada 9): **{alternancia_por_linha(h_full)}**")

# Novas métricas
st.subheader("🔎 Análise Avançada de Padrões")
tercos = analise_por_terco(h_full)
if tercos:
    t1, t2, t3 = tercos["t1"], tercos["t2"], tercos["t3"]
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Terço 1 (1-9)", f"{t1['C']}C / {t1['V']}V / {t1['E']}E")
    col_t2.metric("Terço 2 (10-18)", f"{t2['C']}C / {t2['V']}V / {t2['E']}E")
    col_t3.metric("Terço 3 (19-27)", f"{t3['C']}C / {t3['V']}V / {t3['E']}E")
else:
    st.info("Dados insuficientes para análise por terços (necessário >= 27 jogadas válidas).")

st.write("---")
st.write(f"Contagem de Sequências: **{contagem_sequencias(h_full)}**")
break_info = quebra_padrao(h_full)
st.write(f"Quebra de Padrão (Breakout): **{break_info['status']}**")
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
        if a["nivel"] == "crítico":
            st.error(a["msg"])
        elif a["nivel"] == "médio":
            st.warning(a["msg"])
        else:
            st.info(a["msg"])

st.write("---")
st.subheader("📌 Detalhes técnicos / debug rápido")
st.write(f"Janela de análise: {ANALYSIS_WINDOW} últimas jogadas válidas")
st.write(f"Histórico total (últimos {len(h_full)} entradas): {h_full}")
st.write(f"Score interno (exemplo): {s.get('score')}")

# Botão limpar (com confirmação simples)
if st.button("🧹 Limpar histórico"):
    st.session_state.historico.clear()
    st.experimental_rerun()

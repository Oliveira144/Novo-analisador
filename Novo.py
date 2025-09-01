import streamlit as st

# ----------------- Inicialização -----------------
if "historico" not in st.session_state:
    st.session_state.historico = []

def adicionar_resultado(valor):
    st.session_state.historico.append(valor)

# ----------------- Helpers -----------------
def get_valores(h, limite=36):
    """Retorna últimos valores válidos (C, V, E) com limite."""
    return [r for r in h if r in ["C", "V", "E"]][-limite:]

def bolha_cor(r):
    return {"C":"🟥","V":"🟦","E":"🟨","🔽":"⬇️"}.get(r,"⬜")

# ----------------- Padrões / Métricas -----------------
def maior_sequencia(h):
    h = get_valores(h)
    if not h: return 0
    max_seq = atual = 1
    for i in range(1, len(h)):
        if h[i] == h[i - 1]:
            atual += 1
            max_seq = max(max_seq, atual)
        else:
            atual = 1
    return max_seq

def sequencia_final(h):
    h = get_valores(h)
    if not h: return 0
    atual = h[-1]
    count = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == atual:
            count += 1
        else:
            break
    return count

def alternancia(h):
    h = get_valores(h)
    if not h: return 0
    return sum(1 for i in range(1, len(h)) if h[i] != h[i-1])

def alternancia_por_linha(h):
    h = get_valores(h)
    if not h: return []
    linhas = [h[i:i+9] for i in range(0, len(h), 9)]
    return [sum(1 for j in range(1, len(linha)) if linha[j] != linha[j-1]) for linha in linhas]

def eco_visual(h):
    h = get_valores(h)
    if len(h) < 12:
        return 0
    # retorna número de posições iguais entre os dois blocos de 6 (0..6)
    return sum(1 for i in range(6) if h[-6+i] == h[-12+i])

def eco_parcial(h):
    # manter compatibilidade (retorna 0..6)
    return eco_visual(h)

def dist_empates(h):
    h = get_valores(h)
    empates = [i for i,r in enumerate(h) if r == 'E']
    return empates[-1] - empates[-2] if len(empates) >= 2 else "N/A"

def blocos_espelhados(h):
    h = get_valores(h)
    if len(h) < 6: return 0
    cont = 0
    for i in range(len(h) - 5):
        if h[i:i+3] == h[i+3:i+6][::-1]:
            cont += 1
    return cont

def tendencia_final(h):
    h = get_valores(h)
    if not h: return "0C / 0V / 0E"
    ult = h[-5:]
    return f"{ult.count('C')}C / {ult.count('V')}V / {ult.count('E')}E"

def sequencias_intercaladas(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h) - 3):
        bloco = h[i:i+4]
        if bloco[0] != bloco[1] and bloco[0] == bloco[2] and bloco[1] == bloco[3]:
            cont += 1
    return cont

def ciclos_curtos(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h) - 1):
        if len(set(h[i:i+2])) == 2:
            cont += 1
    return cont

def ciclos_largos(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h) - 3):
        if len(set(h[i:i+4])) >= 3:
            cont += 1
    return cont

def falsos_padroes(h):
    h = get_valores(h)
    cont = 0
    for i in range(2, len(h)):
        # quebra súbita após repetição: X X Y  (Y != X)
        if h[i] != h[i-1] and h[i-1] == h[i-2]:
            cont += 1
    return cont

def empates_ancora(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h) - 2):
        if h[i] == 'E' and h[i+1] == h[i+2]:
            cont += 1
    return cont

def peso_frequencia(h):
    h = get_valores(h)
    if not h: return None, 0
    contagens = {"C":h.count("C"), "V":h.count("V"), "E":h.count("E")}
    maior = max(contagens, key=contagens.get)
    return maior, contagens[maior]

# ----------------- Análise por PADRÕES (inteligente) -----------------
def analise_por_padrao(h):
    valores = get_valores(h)
    # se não há valores suficientes, entregar resultado neutro
    if not valores:
        return {"C":0,"V":0,"E":0}, "N/A", 50

    padrao_score = {"C":0,"V":0,"E":0}

    # Coletar métricas
    seq_final = sequencia_final(h)
    seq_maior = maior_sequencia(h)
    alt = alternancia(h)
    eco = eco_visual(h)
    esp = blocos_espelhados(h)
    anc_emp = empates_ancora(h)
    seq_inter = sequencias_intercaladas(h)
    ciclos_s = ciclos_curtos(h)
    ciclos_l = ciclos_largos(h)
    falsos = falsos_padroes(h)

    ultimo = valores[-1]

    # Pontuação por padrão: regra baseada em interação com histórico (ajustável)
    for r in ["C","V","E"]:
        # 1) Base: frequência simples
        padrao_score[r] += valores.count(r)

        # 2) Sequência final favorece repetição (aumenta impacto da cor que está em sequência)
        if seq_final >= 2 and ultimo == r:
            padrao_score[r] += seq_final * 2

        # 3) Grande sequência histórica favorece a cor dominante
        if seq_maior >= 4 and valores.count(r) >= 3:
            padrao_score[r] += 2

        # 4) Eco visual/parcial: reforça cor presente no final do bloco repetido
        if eco >= 4 and ultimo == r:
            padrao_score[r] += 3
        elif eco >= 3 and r in valores[-6:]:
            padrao_score[r] += 1

        # 5) Blocos espelhados: adiciona pontos às cores que aparecem no bloco
        if esp >= 1 and r in valores[-6:]:
            padrao_score[r] += 2

        # 6) Empates como âncora: empates próximos reforçam cores não-E (heurística)
        if anc_emp >= 1 and r != 'E':
            padrao_score[r] += 2

        # 7) Sequências intercaladas favorecem as duas cores que alternam
        if seq_inter >= 1 and r in valores[-4:]:
            padrao_score[r] += 1

        # 8) Ciclos curtos e longos (reforçam participação recente)
        if ciclos_s >= 2 and r in valores[-2:]:
            padrao_score[r] += 1
        if ciclos_l >= 1 and r in valores[-4:]:
            padrao_score[r] += 1

        # 9) Falsos padrões reduzem pontos (reduz confiança da cor interrompida)
        if falsos >= 1 and r == ultimo:
            padrao_score[r] -= 1

    # Normalizar scores para evitar valores negativos extremos
    for k in padrao_score:
        if padrao_score[k] < 0:
            padrao_score[k] = 0

    # Escolher padrão (cor) sugerido — com base em maior pontuação de padrão
    cor_sugerida = max(padrao_score, key=padrao_score.get)

    # Calcular confiança: relação entre diferença dos scores e magnitude total
    total_positivos = sum(padrao_score.values())
    if total_positivos <= 0:
        confiança = 50
    else:
        dominante = padrao_score[cor_sugerida]
        # Score relativo (0..1)
        rel = dominante / total_positivos
        # Base 50% + escala até 45% dependendo da dominância e magnitude
        confiança = int(50 + min(45, rel * 100 * 0.45 + (dominante * 2)))
        confiança = max(10, min(95, confiança))

    return padrao_score, cor_sugerida, confiança

# ----------------- Nível de manipulação -----------------
def nivel_manipulacao(h):
    nivel = 1
    seq_final_val = sequencia_final(h)
    seq_maior_val = maior_sequencia(h)
    alt_val = alternancia(h)
    eco_val = eco_visual(h)
    esp_val = blocos_espelhados(h)
    anc_emp = empates_ancora(h)
    falsos = falsos_padroes(h)

    if seq_final_val >= 5: nivel += 2
    if seq_maior_val >= 5: nivel += 1
    if alt_val < 10: nivel += 1
    if eco_val >= 4: nivel += 2
    if esp_val >= 1: nivel += 1
    if anc_emp >= 1: nivel += 1
    if falsos >= 2: nivel += 1

    return min(nivel, 9)

# ----------------- Sugestão final (BASEADA EM PADRÕES) -----------------
def sugestao(h):
    padrao_score, cor, conf = analise_por_padrao(h)
    nivel = nivel_manipulacao(h)
    # Mensagem detalhada e interpretativa
    descricao = f"🎯 Sugestão baseada em padrão: {bolha_cor(cor)} ({cor}) | Nível {nivel} | Confiança {conf}%"
    return descricao

# ----------------- Interface Streamlit -----------------
st.set_page_config(page_title="Football Studio – Análise por Padrões (Inteligente)", layout="wide")
st.title("🎲 Football Studio Live — Análise Inteligente por Padrões")

# Entrada de resultados (botões)
col1, col2, col3, col4 = st.columns(4)
if col1.button("➕ Casa (C)"):
    adicionar_resultado("C")
if col2.button("➕ Visitante (V)"):
    adicionar_resultado("V")
if col3.button("➕ Empate (E)"):
    adicionar_resultado("E")
if col4.button("🗂️ Novo baralho"):
    adicionar_resultado("🔽")

h = st.session_state.historico

# Sugestão (apenas quando houver algum dado)
st.subheader("🎯 Sugestão de entrada")
st.success(sugestao(h))

# Histórico visual (exibe de trás pra frente, linhas de 9)
st.subheader("🧾 Histórico visual")
h_rev = h[::-1]
bolhas = [bolha_cor(r) for r in h_rev]
for i in range(0, len(bolhas), 9):
    linha = bolhas[i:i+9]
    estilo = 'font-size:24px;' if i < 27 else 'font-size:20px; opacity:0.5;'
    bolha_html = "".join(f"<span style='{estilo} margin-right:4px;'>{b}</span>" for b in linha)
    st.markdown(f"<div style='display:flex; gap:4px;'>{bolha_html}</div>", unsafe_allow_html=True)

# Painel de análise detalhada (todas as métricas)
st.subheader("📊 Análise detalhada (últimos valores válidos)")
valores = get_valores(h)
col1, col2, col3 = st.columns(3)
col1.metric("Total Casa", valores.count("C") if valores else 0)
col2.metric("Total Visitante", valores.count("V") if valores else 0)
col3.metric("Total Empates", valores.count("E") if valores else 0)

st.write(f"Maior sequência: **{maior_sequencia(h)}**")
st.write(f"Sequência final: **{sequencia_final(h)}**")
st.write(f"Alternância total: **{alternancia(h)}**")
st.write(f"Alternância por linha: **{alternancia_por_linha(h)}**")
st.write(f"Eco visual (posições iguais entre blocos de 6): **{eco_visual(h)} / 6**")
st.write(f"Distância entre empates: **{dist_empates(h)}**")
st.write(f"Blocos espelhados: **{blocos_espelhados(h)}**")
st.write(f"Tendência final (últimos 5): **{tendencia_final(h)}**")
st.write(f"Sequências intercaladas (padrão X Y X Y): **{sequencias_intercaladas(h)}**")
st.write(f"Ciclos curtos: **{ciclos_curtos(h)}**")
st.write(f"Ciclos longos: **{ciclos_largos(h)}**")
st.write(f"Falsos padrões: **{falsos_padroes(h)}**")
st.write(f"Empates como âncora: **{empates_ancora(h)}**")
pf, pf_count = peso_frequencia(h)
st.write(f"Cor mais frequente (peso): **{pf if pf else 'N/A'} ({pf_count})**")

# Mostrar scores por padrão (transparência)
st.subheader("🔎 Scores por padrão (transparência)")
padrao_score, cor_sug, conf_sug = analise_por_padrao(h)
st.write(padrao_score)
st.write(f"Cor sugerida (padrão): **{cor_sug}** — Confiança: **{conf_sug}%**")

# Alertas estratégicos integrados
st.subheader("🚨 Alertas estratégicos")
alertas = []
nivel = nivel_manipulacao(h)
if sequencia_final(h) >= 5:
    alertas.append(f"🟥 Sequência final ativa — possível inversão | Nível {nivel}")
if eco_visual(h) >= 4:
    alertas.append(f"🔁 Eco visual detectado (>=4) | Nível {nivel}")
if eco_parcial(h) >= 4:
    alertas.append(f"🧠 Eco parcial significativo | Nível {nivel}")
if dist_empates(h) == 1:
    alertas.append("🟨 Empates consecutivos — instabilidade")
if blocos_espelhados(h) >= 1:
    alertas.append("🧩 Bloco espelhado detectado")
if sequencias_intercaladas(h) >= 1:
    alertas.append("🔀 Sequência intercalada detectada")
if falsos_padroes(h) >= 1:
    alertas.append("⚠️ Falso padrão detectado")
if empates_ancora(h) >= 1:
    alertas.append("🟨 Empate como âncora detectado")

if not alertas:
    st.info("Nenhum padrão crítico identificado.")
else:
    for a in alertas:
        st.warning(a)

# Botão limpar histórico
if st.button("🧹 Limpar histórico"):
    st.session_state.historico = []
    st.rerun()

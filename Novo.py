import streamlit as st

# ============================================
# Utilitários
# ============================================
def bolha_cor(valor):
    cores = {"C": "🔴", "V": "🔵", "E": "🟡"}
    return cores.get(valor, valor)

def get_valores(h):
    return [x for x in h if x in ["C", "V", "E"]]

# ============================================
# Funções de análise
# ============================================
def sequencia_final(h):
    v = get_valores(h)
    if not v: return 0
    ult = v[-1]
    cont = 0
    for x in reversed(v):
        if x == ult:
            cont += 1
        else:
            break
    return cont

def eco_visual(h):
    v = get_valores(h)
    if len(v) < 6:
        return "Insuficiente"
    if v[-1] == v[-3] == v[-5]:
        return "Detectado"
    return "Não"

def eco_parcial(h):
    v = get_valores(h)
    if len(v) < 6:
        return "Insuficiente"
    bloco1 = v[-6:-3]
    bloco2 = v[-3:]
    iguais = sum([1 for i in range(3) if bloco1[i] == bloco2[i]])
    return f"{iguais}/3"

def quebra_padrao(h):
    v = get_valores(h)
    if len(v) < 4:
        return "Poucos dados"
    ultimos = v[-4:]
    alterna = all(ultimos[i] != ultimos[i+1] for i in range(3))
    if not alterna:
        return "Quebra de alternância detectada"
    return "Sem quebra"

def dist_empates(h):
    v = get_valores(h)
    if "E" not in v:
        return "Nunca ocorreu"
    pos = [i for i, x in enumerate(v) if x == "E"]
    if len(pos) < 2:
        return "Apenas um empate"
    return pos[-1] - pos[-2]

# ============================================
# Sugestão inteligente
# ============================================
def sugestao(h):
    valores = get_valores(h)
    if not valores:
        return "Insira resultados para gerar previsão.", "info"

    ult = valores[-1]
    seq = sequencia_final(h)
    eco = eco_visual(h)
    parcial = eco_parcial(h)
    quebra = quebra_padrao(h)
    contagens = {x: valores.count(x) for x in ["C", "V", "E"]}

    score = {"C": 0, "V": 0, "E": 0}

    # Sequência longa sugere reversão
    if seq >= 5 and ult in ["C", "V"]:
        cor_inv = "V" if ult == "C" else "C"
        score[cor_inv] += 3

    # Empate recente gera instabilidade
    if ult == "E":
        score["C"] += 1
        score["V"] += 1

    # Eco detectado reforça última jogada
    if eco == "Detectado" or str(parcial).startswith(("5", "6")):
        score[ult] += 2

    # Frequência histórica
    if len(valores) >= 9:
        mais_freq = max(contagens, key=contagens.get)
        score[mais_freq] += 1

    # Quebra de padrão favorece continuidade
    if quebra == "Quebra de alternância detectada":
        score[ult] += 2

    cor_final = max(score, key=score.get)
    total = sum(score.values()) or 1
    confianca = (score[cor_final] / total) * 100

    return f"🎯 Sugestão: {bolha_cor(cor_final)} ({cor_final}) — confiança {confianca:.1f}%", "success"

# ============================================
# Nível de manipulação
# ============================================
def nivel_manipulacao(h):
    valores = get_valores(h)
    if len(valores) < 9:
        return 1
    
    nivel = 1
    if sequencia_final(h) >= 5: nivel += 2
    if eco_visual(h) == "Detectado": nivel += 2
    if quebra_padrao(h) == "Quebra de alternância detectada": nivel += 2
    if isinstance(eco_parcial(h), str) and eco_parcial(h).startswith(("5", "6")):
        nivel += 1
    if dist_empates(h) == 1: nivel += 1

    return min(nivel, 9)

# ============================================
# Interface Streamlit
# ============================================
st.set_page_config(page_title="Analisador Football Studio", layout="wide")

if "historico" not in st.session_state:
    st.session_state.historico = []

st.title("📊 Analisador Football Studio — Inteligência Avançada")

# Botões de entrada
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🔴 Casa"):
        st.session_state.historico.append("C")
        st.rerun()
with col2:
    if st.button("🔵 Visitante"):
        st.session_state.historico.append("V")
        st.rerun()
with col3:
    if st.button("🟡 Empate"):
        st.session_state.historico.append("E")
        st.rerun()
with col4:
    if st.button("↩️ Reset"):
        st.session_state.historico = []
        st.rerun()

h = st.session_state.historico[-90:]  # manter últimos 90

# Histórico visual
st.subheader("Histórico")
if h:
    linhas = [h[i:i+9] for i in range(0, len(h), 9)]
    for linha in linhas:
        st.write(" ".join([bolha_cor(x) for x in linha]))
else:
    st.info("Nenhum resultado inserido ainda.")

# Análises
st.subheader("🔍 Análises do Padrão")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Sequência final", sequencia_final(h))
    st.metric("Eco visual", eco_visual(h))
with col2:
    st.metric("Eco parcial", eco_parcial(h))
    st.metric("Quebra padrão", quebra_padrao(h))
with col3:
    st.metric("Distância entre empates", dist_empates(h))
    st.metric("Nível de Manipulação", nivel_manipulacao(h))

# Sugestão
st.subheader("🎯 Sugestão Inteligente")
sug, status = sugestao(h)
st.success(sug) if status == "success" else st.info(sug)

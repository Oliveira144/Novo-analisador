import streamlit as st

# Inicialização do histórico
if "historico" not in st.session_state:
    st.session_state.historico = []

def adicionar_resultado(valor):
    st.session_state.historico.append(valor)

# 🔍 Funções analíticas usando os últimos 27 válidos
def get_valores(h):
    return [r for r in h if r in ["C", "V", "E"]][-27:]

def maior_sequencia(h):
    h = get_valores(h)
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
    if not h:
        return 0
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
    return sum(1 for i in range(1, len(h)) if h[i] != h[i - 1])

def eco_visual(h):
    h = get_valores(h)
    if len(h) < 12:
        return "Poucos dados"
    return "Detectado" if h[-6:] == h[-12:-6] else "Não houve"

def eco_parcial(h):
    h = get_valores(h)
    if len(h) < 12:
        return "Poucos dados"
    anterior = h[-12:-6]
    atual = h[-6:]
    semelhantes = sum(1 for a, b in zip(anterior, atual) if a == b or (a in ['C', 'V'] and b in ['C', 'V']))
    return semelhantes

def dist_empates(h):
    h = get_valores(h)
    empates = [i for i, r in enumerate(h) if r == 'E']
    return empates[-1] - empates[-2] if len(empates) >= 2 else "N/A"

def blocos_espelhados(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h) - 5):
        if h[i:i + 3] == h[i + 3:i + 6][::-1]:
            cont += 1
    return cont

def alternancia_por_linha(h):
    h = get_valores(h)
    linhas = [h[i:i + 9] for i in range(0, len(h), 9)]
    return [sum(1 for j in range(1, len(linha)) if linha[j] != linha[j - 1]) for linha in linhas]

def tendencia_final(h):
    h = get_valores(h)
    ult = h[-5:]
    return f"{ult.count('C')}C / {ult.count('V')}V / {ult.count('E')}E"

def bolha_cor(r):
    return {
        "C": "🟥",
        "V": "🟦",
        "E": "🟨",
        "🔽": "⬇️"
    }.get(r, "⬜")

# 🔹 Função para calcular nível de manipulação e confiança
def analisar_nivel(h):
    seq = sequencia_final(h)
    eco = eco_visual(h)
    parcial = eco_parcial(h)
    altern = alternancia(h)
    espelhados = blocos_espelhados(h)

    nivel = 1  # nível mínimo
    if seq >= 5: nivel += 2
    if eco == "Detectado": nivel += 2
    if parcial >= 4: nivel += 1
    if altern < 10: nivel += 1
    if espelhados >= 1: nivel += 1
    nivel = min(nivel, 9)
    
    conf = min(95, 50 + nivel*5 + min(seq,6)*5)
    
    return nivel, conf

# 🔹 Sugestão aprimorada com emoji e confiança
def sugestao(h):
    valores = get_valores(h)
    if not valores:
        return "Insira resultados para gerar previsão."
    
    ult = valores[-1]
    seq = sequencia_final(h)
    eco = eco_visual(h)
    parcial = eco_parcial(h)
    contagens = {
        "C": valores.count("C"),
        "V": valores.count("V"),
        "E": valores.count("E")
    }
    
    nivel, conf = analisar_nivel(h)
    
    if seq >= 5 and ult in ["C", "V"]:
        cor_inversa = "V" if ult == "C" else "C"
        return f"🔁 Sequência de {bolha_cor(ult)} — possível reversão para {bolha_cor(cor_inversa)} | Nível {nivel} | Confiança {conf}%"
    
    if ult == "E":
        maior = max(contagens, key=contagens.get)
        return f"🟨 Empate recente — sugerido {bolha_cor(maior)} | Nível {nivel} | Confiança {conf}%"
    
    if eco == "Detectado" or parcial >= 5:
        return f"🔄 Eco visual/parcial — repetir padrão {bolha_cor(ult)} | Nível {nivel} | Confiança {conf}%"
    
    maior = max(contagens, key=contagens.get)
    return f"📊 Tendência favorece entrada em {bolha_cor(maior)} ({maior}) | Nível {nivel} | Confiança {conf}%"

# Interface
st.set_page_config(page_title="Football Studio – Análise Evoluída", layout="wide")
st.title("🎲 Football Studio Live — Leitura Estratégica Evoluída")

# Entrada
col1, col2, col3, col4 = st.columns(4)
if col1.button("➕ Casa (C)"): adicionar_resultado("C")
if col2.button("➕ Visitante (V)"): adicionar_resultado("V")
if col3.button("➕ Empate (E)"): adicionar_resultado("E")
if col4.button("🗂️ Novo baralho"): adicionar_resultado("🔽")

h = st.session_state.historico

# Sugestão preditiva
st.subheader("🎯 Sugestão de entrada")
st.success(sugestao(h))

# Histórico visual
st.subheader("🧾 Histórico visual (zona ativa: 3 linhas)")
h_reverso = h[::-1]
bolhas_visuais = [bolha_cor(r) for r in h_reverso]
for i in range(0, len(bolhas_visuais), 9):
    linha = bolhas_visuais[i:i + 9]
    estilo = 'font-size:24px;' if i < 27 else 'font-size:20px; opacity:0.5;'
    bolha_html = "".join(f"<span style='{estilo} margin-right:4px;'>{b}</span>" for b in linha)
    st.markdown(f"<div style='display:flex; gap:4px;'>{bolha_html}</div>", unsafe_allow_html=True)

# Painel de análise
st.subheader("📊 Análise dos últimos 27 jogadas")
valores = get_valores(h)
col1, col2, col3 = st.columns(3)
col1.metric("Total Casa", valores.count("C"))
col2.metric("Total Visitante", valores.count("V"))
col3.metric("Total Empates", valores.count("E"))

st.write(f"Maior sequência: **{maior_sequencia(h)}**")
st.write(f"Alternância total: **{alternancia(h)}**")
st.write(f"Eco visual: **{eco_visual(h)}**")
st.write(f"Eco parcial: **{eco_parcial(h)}**")
st.write(f"Distância entre empates: **{dist_empates(h)}**")
st.write(f"Blocos espelhados: **{blocos_espelhados(h)}**")
st.write(f"Alternância por linha: **{alternancia_por_linha(h)}**")
st.write(f"Tendência final: **{tendencia_final(h)}**")

# Alertas estratégicos
st.subheader("🚨 Alerta estratégico")
alertas = []
if sequencia_final(h) >= 5 and valores[-1] in ["C", "V"]:
    alertas.append(f"🟥 Sequência final ativa — possível inversão | Nível {analisar_nivel(h)[0]}")
if eco_visual(h) == "Detectado":
    alertas.append(f"🔁 Eco visual detectado — possível repetição | Nível {analisar_nivel(h)[0]}")
if eco_parcial(h) >= 4:
    alertas.append(f"🧠 Eco parcial — padrão reescrito | Nível {analisar_nivel(h)[0]}")
if dist_empates(h) == 1:
    alertas.append("🟨 Empates consecutivos — instabilidade")
if blocos_espelhados(h) >= 1:
    alertas.append("🧩 Bloco espelhado — reflexo estratégico")

if not alertas:
    st.info("Nenhum padrão crítico identificado.")
else:
    for alerta in alertas:
        st.warning(alerta)

# Limpar histórico
if st.button("🧹 Limpar histórico"):
    st.session_state.historico = []
    st.rerun()

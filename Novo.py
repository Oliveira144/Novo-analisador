import streamlit as st

# =========================
# Histórico com limite geral
# =========================
if "historico" not in st.session_state:
    st.session_state.historico = []

def adicionar_resultado(valor):
    st.session_state.historico.append(valor)

# =========================
# Funções auxiliares
# =========================
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

def eco_visual(h):
    h = get_valores(h)
    if len(h) < 12: return False
    return h[-6:] == h[-12:-6]

def eco_parcial(h):
    h = get_valores(h)
    if len(h) < 12: return 0
    anterior = h[-12:-6]
    atual = h[-6:]
    return sum(1 for a,b in zip(anterior,atual) if a==b)

def blocos_espelhados(h):
    h = get_valores(h)
    cont=0
    for i in range(len(h)-5):
        if h[i:i+3] == h[i+3:i+6][::-1]:
            cont+=1
    return cont

def alternancia(h):
    h = get_valores(h)
    return sum(1 for i in range(1,len(h)) if h[i]!=h[i-1])

def tendencia_final(h):
    h=get_valores(h)
    ult=h[-5:]
    return {"C":ult.count("C"),"V":ult.count("V"),"E":ult.count("E")}

def bolha_cor(r):
    return {"C":"🟥","V":"🟦","E":"🟨","🔽":"⬇️"}.get(r,"⬜")

# =========================
# 🔮 Inteligência de padrões
# =========================
def analise_por_padrao(h):
    valores=get_valores(h)
    if not valores: return None

    scores={"C":0,"V":0,"E":0}
    ult=valores[-1]
    seq_final=sequencia_final(h)

    # 1) Sequência longa → sugere reversão
    if seq_final>=3 and ult in ["C","V"]:
        cor_inversa="V" if ult=="C" else "C"
        scores[cor_inversa]+=seq_final*3

    # 2) Eco visual → repetir padrão
    if eco_visual(h):
        scores[ult]+=4

    # 3) Eco parcial → reforça último
    parc=eco_parcial(h)
    if parc>=4:
        scores[ult]+=parc

    # 4) Blocos espelhados → favorece inversão
    if blocos_espelhados(h)>0:
        cor_inv="V" if ult=="C" else "C"
        scores[cor_inv]+=2

    # 5) Frequência recente (tendência)
    tendencia=tendencia_final(h)
    max_cor=max(tendencia,key=tendencia.get)
    scores[max_cor]+=tendencia[max_cor]

    # 6) Empate instável
    if ult=="E":
        scores["C"]+=1
        scores["V"]+=1

    # Normalização da confiança
    total=sum(scores.values()) or 1
    cor_sugerida=max(scores,key=scores.get)
    confianca=int((scores[cor_sugerida]/total)*100)

    # Nível de manipulação (1 a 9)
    nivel=1
    if seq_final>=5: nivel=7
    if eco_visual(h): nivel=8
    if parc>=5: nivel=9

    return cor_sugerida, confianca, nivel, scores

def sugestao(h):
    resultado=analise_por_padrao(h)
    if not resultado:
        return "Insira resultados para gerar previsão."
    cor,conf,nivel,scores=resultado
    return f"📊 Sugestão: {bolha_cor(cor)} | Nível {nivel} | Confiança {conf}%\n\n🔎 Scores por padrão (transparência)\n{scores}"

# =========================
# Interface
# =========================
st.set_page_config(page_title="Football Studio – Análise", layout="wide")
st.title("🎲 Football Studio Live — Leitura Estratégica")

# Entrada
col1,col2,col3,col4=st.columns(4)
if col1.button("➕ Casa (C)"): adicionar_resultado("C")
if col2.button("➕ Visitante (V)"): adicionar_resultado("V")
if col3.button("➕ Empate (E)"): adicionar_resultado("E")
if col4.button("🗂️ Novo baralho"): adicionar_resultado("🔽")

h=st.session_state.historico

# Sugestão preditiva
st.subheader("🎯 Sugestão de entrada")
st.success(sugestao(h))

# Histórico visual
st.subheader("🧾 Histórico visual (zona ativa: 3 linhas)")
h_reverso=h[::-1]
bolhas_visuais=[bolha_cor(r) for r in h_reverso]
for i in range(0,len(bolhas_visuais),9):
    linha=bolhas_visuais[i:i+9]
    estilo='font-size:24px;' if i<27 else 'font-size:20px; opacity:0.5;'
    bolha_html="".join(f"<span style='{estilo} margin-right:4px;'>{b}</span>" for b in linha)
    st.markdown(f"<div style='display:flex; gap:4px;'>{bolha_html}</div>",unsafe_allow_html=True)

# Painel de análise
st.subheader("📊 Análise dos últimos 27 jogadas")
valores=get_valores(h)
col1,col2,col3=st.columns(3)
col1.metric("Total Casa",valores.count("C"))
col2.metric("Total Visitante",valores.count("V"))
col3.metric("Total Empates",valores.count("E"))

st.write(f"Maior sequência: **{maior_sequencia(h)}**")
st.write(f"Alternância total: **{alternancia(h)}**")
st.write(f"Eco visual: **{eco_visual(h)}**")
st.write(f"Eco parcial: **{eco_parcial(h)}**")
st.write(f"Blocos espelhados: **{blocos_espelhados(h)}**")
st.write(f"Tendência final: **{tendencia_final(h)}**")

# Alertas
st.subheader("🚨 Alerta estratégico")
alertas=[]
if sequencia_final(h)>=5 and valores and valores[-1] in ["C","V"]:
    alertas.append("🟥 Sequência longa ativa — possível inversão")
if eco_visual(h):
    alertas.append("🔁 Eco visual detectado — possível repetição")
if eco_parcial(h)>=4:
    alertas.append("🧠 Eco parcial — padrão reescrito com alta semelhança")
if blocos_espelhados(h)>=1:
    alertas.append("🧩 Bloco espelhado — reflexo estratégico")
if not alertas:
    st.info("Nenhum padrão crítico identificado.")
else:
    for alerta in alertas:
        st.warning(alerta)

# Limpar
if st.button("🧹 Limpar histórico"):
    st.session_state.historico=[]
    st.rerun()

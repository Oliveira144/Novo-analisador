import streamlit as st

# Inicialização do histórico
if "historico" not in st.session_state:
    st.session_state.historico = []

def adicionar_resultado(valor):
    st.session_state.historico.append(valor)

# 🔹 Obter últimos valores válidos
def get_valores(h, limite=36):
    return [r for r in h if r in ["C", "V", "E"]][-limite:]

# 🔹 Funções de análise de padrões
def maior_sequencia(h):
    h = get_valores(h)
    max_seq = atual = 1
    for i in range(1,len(h)):
        if h[i]==h[i-1]:
            atual+=1
            max_seq=max(max_seq,atual)
        else:
            atual=1
    return max_seq

def sequencia_final(h):
    h = get_valores(h)
    if not h: return 0
    atual = h[-1]
    count=1
    for i in range(len(h)-2,-1,-1):
        if h[i]==atual: count+=1
        else: break
    return count

def alternancia(h):
    h = get_valores(h)
    return sum(1 for i in range(1,len(h)) if h[i]!=h[i-1])

def eco_visual(h):
    h = get_valores(h)
    if len(h)<12: return 0
    return sum(1 for i in range(6) if h[-6+i]==h[-12+i])

def blocos_espelhados(h):
    h = get_valores(h)
    cont=0
    for i in range(len(h)-5):
        if h[i:i+3]==h[i+3:i+6][::-1]: cont+=1
    return cont

def empates_ancora(h):
    h = get_valores(h)
    cont=0
    for i in range(len(h)-2):
        if h[i]=='E' and h[i+1]==h[i+2]: cont+=1
    return cont

def sequencias_intercaladas(h):
    h = get_valores(h)
    cont=0
    for i in range(len(h)-3):
        bloco = h[i:i+4]
        if bloco[0]!=bloco[1] and bloco[0]==bloco[2] and bloco[1]==bloco[3]:
            cont+=1
    return cont

def ciclos_curtos(h):
    h = get_valores(h)
    cont=0
    for i in range(len(h)-1):
        if len(set(h[i:i+2]))==2: cont+=1
    return cont

def ciclos_largos(h):
    h = get_valores(h)
    cont=0
    for i in range(len(h)-3):
        if len(set(h[i:i+4]))>=3: cont+=1
    return cont

def falsos_padroes(h):
    h = get_valores(h)
    cont=0
    for i in range(2,len(h)):
        if h[i]!=h[i-1] and h[i-1]==h[i-2]: cont+=1
    return cont

# 🔹 Bolha de cor
def bolha_cor(r):
    return {"C":"🟥","V":"🟦","E":"🟨","🔽":"⬇️"}.get(r,"⬜")

# 🔹 Análise de padrões com pontuação
def analise_por_padrao(h):
    valores = get_valores(h)
    padrao_score = {"C":0,"V":0,"E":0}
    
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
    
    for r in ["C","V","E"]:
        # Sequência final favorece repetição
        if valores[-1]==r and seq_final>=3: padrao_score[r]+=seq_final*2
        # Maior sequência reforça cor dominante no histórico
        padrao_score[r]+=valores.count(r)
        # Eco visual
        if eco>=4 and valores[-1]==r: padrao_score[r]+=3
        # Blocos espelhados
        if esp>=1: padrao_score[r]+=2
        # Empates como âncora reforçam cores não E
        if anc_emp>=1 and r!='E': padrao_score[r]+=2
        # Sequências intercaladas reforçam cores alternadas
        if seq_inter>=1 and r in valores[-4:]: padrao_score[r]+=1
        # Ciclos curtos e longos
        if ciclos_s>=2 and r in valores[-2:]: padrao_score[r]+=1
        if ciclos_l>=1 and r in valores[-4:]: padrao_score[r]+=1
        # Falsos padrões reduzem pontos
        if falsos>=1: padrao_score[r]-=1
    
    # Determinar cor/padrão sugerido
    cor_sugerida = max(padrao_score,key=padrao_score.get)
    
    # Calcular confiança
    total_pontos = sum(max(0,v) for v in padrao_score.values())
    conf = int(50 + (total_pontos/len(valores)*50)) if valores else 50
    
    return cor_sugerida, conf

# 🔹 Nível de manipulação baseado em padrões
def nivel_manipulacao(h):
    nivel=1
    seq_final_val = sequencia_final(h)
    seq_maior_val = maior_sequencia(h)
    alt_val = alternancia(h)
    eco_val = eco_visual(h)
    esp_val = blocos_espelhados(h)
    anc_emp = empates_ancora(h)
    
    if seq_final_val>=5: nivel+=2
    if seq_maior_val>=5: nivel+=1
    if alt_val<10: nivel+=1
    if eco_val>=4: nivel+=2
    if esp_val>=1: nivel+=1
    if anc_emp>=1: nivel+=1
    return min(nivel,9)

# 🔹 Sugestão final baseada em padrões
def sugestao(h):
    cor, conf = analise_por_padrao(h)
    nivel = nivel_manipulacao(h)
    return f"🎯 Sugestão baseada em padrão: {bolha_cor(cor)} ({cor}) | Nível {nivel} | Confiança {conf}%"

# ----------------- Interface -----------------
st.set_page_config(page_title="Football Studio – Análise Inteligente por Padrão", layout="wide")
st.title("🎲 Football Studio Live — Análise Inteligente por Padrão")

# Entrada de resultados
col1,col2,col3,col4=st.columns(4)
if col1.button("➕ Casa (C)"): adicionar_resultado("C")
if col2.button("➕ Visitante (V)"): adicionar_resultado("V")
if col3.button("➕ Empate (E)"): adicionar_resultado("E")
if col4.button("🗂️ Novo baralho"): adicionar_resultado("🔽")

h = st.session_state.historico

# Sugestão
st.subheader("🎯 Sugestão de entrada")
st.success(sugestao(h))

# Histórico visual
st.subheader("🧾 Histórico visual")
h_rev = h[::-1]
bolhas = [bolha_cor(r) for r in h_rev]
for i in range(0,len(bolhas),9):
    linha = bolhas[i:i+9]
    estilo = 'font-size:24px;' if i<27 else 'font-size:20px; opacity:0.5;'
    bolha_html = "".join(f"<span style='{estilo} margin-right:4px;'>{b}</span>" for b in linha)
    st.markdown(f"<div style='display:flex; gap:4px;'>{bolha_html}</div>",unsafe_allow_html=True)

# Limpar histórico
if st.button("🧹 Limpar histórico"):
    st.session_state.historico=[]
    st.rerun()

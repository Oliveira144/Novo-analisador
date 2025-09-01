import streamlit as st

# Inicialização do histórico
if "historico" not in st.session_state:
    st.session_state.historico = []

def adicionar_resultado(valor):
    st.session_state.historico.append(valor)

# 🔍 Funções analíticas usando os últimos 36 válidos para mais robustez
def get_valores(h):
    return [r for r in h if r in ["C", "V", "E"]][-36:]

# Padrão 1: Maior sequência
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

# Padrão 2: Sequência final
def sequencia_final(h):
    h = get_valores(h)
    if not h: return 0
    atual = h[-1]
    count = 1
    for i in range(len(h)-2,-1,-1):
        if h[i]==atual: count+=1
        else: break
    return count

# Padrão 3: Alternância total
def alternancia(h):
    h = get_valores(h)
    return sum(1 for i in range(1,len(h)) if h[i]!=h[i-1])

# Padrão 4: Alternância por linha
def alternancia_por_linha(h):
    h = get_valores(h)
    linhas = [h[i:i+9] for i in range(0,len(h),9)]
    return [sum(1 for j in range(1,len(linha)) if linha[j]!=linha[j-1]) for linha in linhas]

# Padrão 5: Eco visual
def eco_visual(h):
    h = get_valores(h)
    if len(h)<12: return "Poucos dados"
    return "Detectado" if h[-6:]==h[-12:-6] else "Não houve"

# Padrão 6: Eco parcial
def eco_parcial(h):
    h = get_valores(h)
    if len(h)<12: return 0
    anterior = h[-12:-6]
    atual = h[-6:]
    return sum(1 for a,b in zip(anterior,atual) if a==b or (a in ['C','V'] and b in ['C','V']))

# Padrão 7: Distância entre empates
def dist_empates(h):
    h = get_valores(h)
    empates = [i for i,r in enumerate(h) if r=='E']
    return empates[-1]-empates[-2] if len(empates)>=2 else "N/A"

# Padrão 8: Blocos espelhados
def blocos_espelhados(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h)-5):
        if h[i:i+3]==h[i+3:i+6][::-1]: cont+=1
    return cont

# Padrão 9: Tendência final
def tendencia_final(h):
    h = get_valores(h)
    ult = h[-5:]
    return f"{ult.count('C')}C / {ult.count('V')}V / {ult.count('E')}E"

# Padrão 10: Sequências intercaladas (C V C V)
def sequencias_intercaladas(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h)-3):
        bloco = h[i:i+4]
        if bloco[0]!=bloco[1] and bloco[0]==bloco[2] and bloco[1]==bloco[3]:
            cont+=1
    return cont

# Padrão 11: Ciclos curtos (2 ou 3 cores)
def ciclos_curtos(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h)-1):
        if len(set(h[i:i+2]))==2: cont+=1
    return cont

# Padrão 12: Ciclos longos (4 a 6 cores)
def ciclos_largos(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h)-3):
        if len(set(h[i:i+4]))>=3: cont+=1
    return cont

# Padrão 13: Falsos padrões (quebra súbita)
def falsos_padroes(h):
    h = get_valores(h)
    cont = 0
    for i in range(1,len(h)):
        if h[i]!=h[i-1] and h[i-1]==h[i-2:i-1][0] if i>1 else False:
            cont+=1
    return cont

# Padrão 14: Empate como âncora
def empates_ancora(h):
    h = get_valores(h)
    cont = 0
    for i in range(len(h)-2):
        if h[i]=='E' and h[i+1]==h[i+2]: cont+=1
    return cont

# Padrão 15: Peso por frequência (mais recorrente)
def peso_frequencia(h):
    h = get_valores(h)
    contagens = {"C":h.count("C"),"V":h.count("V"),"E":h.count("E")}
    maior = max(contagens,key=contagens.get)
    return maior, contagens[maior]

# Bolha de cor
def bolha_cor(r):
    return {"C":"🟥","V":"🟦","E":"🟨","🔽":"⬇️"}.get(r,"⬜")

# 🔹 Nível de manipulação e confiança com todos os padrões
def analisar_nivel(h):
    seq_final = sequencia_final(h)
    seq_maior = maior_sequencia(h)
    alt_total = alternancia(h)
    eco = eco_visual(h)
    eco_par = eco_parcial(h)
    esp = blocos_espelhados(h)
    seq_inter = sequencias_intercaladas(h)
    ciclos_s = ciclos_curtos(h)
    ciclos_l = ciclos_largos(h)
    falsos = falsos_padroes(h)
    anc_empates = empates_ancora(h)
    
    nivel = 1
    if seq_final>=5: nivel+=2
    if seq_maior>=5: nivel+=1
    if alt_total<10: nivel+=1
    if eco=="Detectado": nivel+=2
    if eco_par>=4: nivel+=1
    if esp>=1: nivel+=1
    if seq_inter>=1: nivel+=1
    if ciclos_s>=2: nivel+=1
    if ciclos_l>=1: nivel+=1
    if falsos>=1: nivel+=1
    if anc_empates>=1: nivel+=1
    nivel = min(nivel,9)
    
    conf = min(95, 50 + nivel*5 + min(seq_final,6)*5)
    
    return nivel, conf

# Sugestão inteligente com emoji e confiança
def sugestao(h):
    valores = get_valores(h)
    if not valores: return "Insira resultados para gerar previsão."
    
    ult = valores[-1]
    contagens = {"C":valores.count("C"),"V":valores.count("V"),"E":valores.count("E")}
    maior = max(contagens,key=contagens.get)
    
    nivel, conf = analisar_nivel(h)
    
    seq_final_val = sequencia_final(h)
    
    if seq_final_val>=5 and ult in ["C","V"]:
        cor_inv = "V" if ult=="C" else "C"
        return f"🔁 Sequência de {bolha_cor(ult)} — possível reversão para {bolha_cor(cor_inv)} | Nível {nivel} | Confiança {conf}%"
    if ult=="E":
        return f"🟨 Empate recente — sugerido {bolha_cor(maior)} | Nível {nivel} | Confiança {conf}%"
    return f"📊 Tendência favorece {bolha_cor(maior)} ({maior}) | Nível {nivel} | Confiança {conf}%"

# Interface
st.set_page_config(page_title="Football Studio – Análise Inteligente", layout="wide")
st.title("🎲 Football Studio Live — Análise Inteligente")

# Botões de entrada
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

# Painel de análise
st.subheader("📊 Análise detalhada")
valores = get_valores(h)
col1,col2,col3=st.columns(3)
col1.metric("Total Casa",valores.count("C"))
col2.metric("Total Visitante",valores.count("V"))
col3.metric("Total Empates",valores.count("E"))

st.write(f"Maior sequência: **{maior_sequencia(h)}**")
st.write(f"Sequência final: **{sequencia_final(h)}**")
st.write(f"Alternância total: **{alternancia(h)}**")
st.write(f"Alternância por linha: **{alternancia_por_linha(h)}**")
st.write(f"Eco visual: **{eco_visual(h)}**")
st.write(f"Eco parcial: **{eco_parcial(h)}**")
st.write(f"Distância entre empates: **{dist_empates(h)}**")
st.write(f"Blocos espelhados: **{blocos_espelhados(h)}**")
st.write(f"Tendência final: **{tendencia_final(h)}**")
st.write(f"Sequências intercaladas: **{sequencias_intercaladas(h)}**")
st.write(f"Ciclos curtos: **{ciclos_curtos(h)}**")
st.write(f"Ciclos longos: **{ciclos_largos(h)}**")
st.write(f"Falsos padrões: **{falsos_padroes(h)}**")
st.write(f"Empates como âncora: **{empates_ancora(h)}**")
st.write(f"Cor mais frequente: **{peso_frequencia(h)[0]} ({peso_frequencia(h)[1]})**")

# Alertas estratégicos
st.subheader("🚨 Alertas estratégicos")
alertas=[]
nivel,_ = analisar_nivel(h)
if sequencia_final(h)>=5: alertas.append(f"🟥 Sequência final ativa — possível inversão | Nível {nivel}")
if eco_visual(h)=="Detectado": alertas.append(f"🔁 Eco visual detectado | Nível {nivel}")
if eco_parcial(h)>=4: alertas.append(f"🧠 Eco parcial significativo | Nível {nivel}")
if dist_empates(h)==1: alertas.append("🟨 Empates consecutivos — instabilidade")
if blocos_espelhados(h)>=1: alertas.append("🧩 Bloco espelhado detectado")
if sequencias_intercaladas(h)>=1: alertas.append("🔀 Sequência intercalada detectada")
if falsos_padroes(h)>=1: alertas.append("⚠️ Falso padrão detectado")
if empates_ancora(h)>=1: alertas.append("🟨 Empate como âncora detectado")

if not alertas: st.info("Nenhum padrão crítico identificado.")
else:
    for a in alertas: st.warning(a)

# Limpar histórico
if st.button("🧹 Limpar histórico"):
    st.session_state.historico=[]
    st.rerun()

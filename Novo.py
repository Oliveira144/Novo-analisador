import streamlit as st

# Histórico com limite geral
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
    if not h:
        return 0
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
    return f"{semelhantes}/6 semelhantes"

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

# Novos algoritmos de análise
def analise_por_terco(h):
    valores = get_valores(h)
    if len(valores) < 27:
        return {}
    terco1 = valores[:9]
    terco2 = valores[9:18]
    terco3 = valores[18:27]
    
    return {
        "Terço 1 (1-9)": f"{terco1.count('C')}C/{terco1.count('V')}V/{terco1.count('E')}E",
        "Terço 2 (10-18)": f"{terco2.count('C')}C/{terco2.count('V')}V/{terco2.count('E')}E",
        "Terço 3 (19-27)": f"{terco3.count('C')}C/{terco3.count('V')}V/{terco3.count('E')}E"
    }

def contagem_sequencias(h):
    valores = get_valores(h)
    if len(valores) < 9:
        return {}
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
    
    # Adicionar a última sequência
    if atual_seq == 2: sequencias["seq_2"] += 1
    elif atual_seq == 3: sequencias["seq_3"] += 1
    elif atual_seq >= 4: sequencias["seq_4+"] += 1
    
    return sequencias

def quebra_padrao(h):
    valores = get_valores(h)
    if len(valores) < 3:
        return "Poucos dados"
    
    padrao_alternancia = all(valores[i] != valores[i-1] for i in range(1, len(valores[-6:])))
    
    if padrao_alternancia and sequencia_final(h) > 1:
        return "Quebra de alternância detectada"
    return "Não houve quebra de padrão"

def variacao_alternancia(h):
    valores = get_valores(h)
    if len(valores) < 5:
        return "Poucos dados"
    
    total_alternancias = alternancia(valores)
    total_jogadas_validas = len(valores) - 1
    
    # Alternância esperada seria em torno de 50%
    esperado = total_jogadas_validas / 2
    variacao_percentual = ((total_alternancias - esperado) / esperado) * 100
    
    return f"{variacao_percentual:.2f}%"

def sugestao(h):
    valores = get_valores(h)
    if not valores:
        return "Insira resultados para gerar previsão.", "info"
    
    ult = valores[-1]
    seq = sequencia_final(h)
    eco = eco_visual(h)
    parcial = eco_parcial(h)
    contagens = {
        "C": valores.count("C"),
        "V": valores.count("V"),
        "E": valores.count("E")
    }

    if seq >= 5 and ult in ["C", "V"]:
        cor_inversa = "V" if ult == "C" else "C"
        return f"🔁 Sequência atual de {bolha_cor(ult)} — possível reversão para {bolha_cor(cor_inversa)}", "warning"
    if ult == "E":
        return "🟨 Empate recente — instável, possível 🟥 ou 🟦", "warning"
    if eco == "Detectado" or parcial.startswith(("5", "6")):
        return f"🔄 Reescrita visual — repetir padrão com {bolha_cor(ult)}", "success"
    
    # Ajuste: Apenas sugere a cor mais frequente se houver dados suficientes.
    if len(valores) >= 9:
        maior = max(contagens, key=contagens.get)
        return f"📊 Tendência favorece entrada em {bolha_cor(maior)} ({maior})", "info"
    else:
        return "Continue inserindo dados para análises mais precisas.", "info"


def exibir_historico(h):
    h_reverso = h[::-1]
    bolhas_visuais = [bolha_cor(r) for r in h_reverso]
    for i in range(0, len(bolhas_visuais), 9):
        linha = bolhas_visuais[i:i + 9]
        estilo = 'font-size:24px;' if i < 27 else 'font-size:20px; opacity:0.5;'
        bolha_html = "".join(
            f"<span style='{estilo} margin-right:4px;'>{b}</span>" for b in linha
        )
        st.markdown(f"<div style='display:flex; gap:4px;'>{bolha_html}</div>", unsafe_allow_html=True)


# ---
# Interface
st.set_page_config(page_title="Football Studio – Análise", layout="wide")
st.title("🎲 Football Studio Live — Leitura Estratégica")

# Entrada
col1, col2, col3, col4 = st.columns(4)
if col1.button("➕ Casa (C)"): adicionar_resultado("C")
if col2.button("➕ Visitante (V)"): adicionar_resultado("V")
if col3.button("➕ Empate (E)"): adicionar_resultado("E")
if col4.button("🔄 Reiniciar Baralho"): adicionar_resultado("🔽")

h = st.session_state.historico

# ---
# Sugestão preditiva
st.subheader("🎯 Sugestão de entrada")
sugestao_texto, tipo_alerta = sugestao(h)
if tipo_alerta == "success":
    st.success(sugestao_texto)
elif tipo_alerta == "warning":
    st.warning(sugestao_texto)
else:
    st.info(sugestao_texto)

# ---
# Histórico visual
st.subheader("🧾 Histórico visual (zona ativa: 3 linhas)")
exibir_historico(h)

# ---
# Painel de análise
st.subheader("📊 Análise dos últimos 27 jogadas")
valores = get_valores(h)
col1, col2, col3 = st.columns(3)
col1.metric("Total Casa", valores.count("C"))
col2.metric("Total Visitante", valores.count("V"))
col3.metric("Total Empates", valores.count("E"))

# Usando st.metric para as métricas principais
st.write("---")
col_metrica1, col_metrica2, col_metrica3 = st.columns(3)
col_metrica1.metric("Maior sequência", maior_sequencia(h))
col_metrica2.metric("Alternância total", alternancia(h))
col_metrica3.metric("Distância entre empates", dist_empates(h))

st.write("---")
col_metrica4, col_metrica5 = st.columns(2)
col_metrica4.metric("Eco visual", eco_visual(h))
col_metrica5.metric("Eco parcial", eco_parcial(h))
st.write(f"Blocos espelhados: **{blocos_espelhados(h)}**")
st.write(f"Tendência final: **{tendencia_final(h)}**")
st.write(f"Alternância por linha: **{alternancia_por_linha(h)}**")

# Novas métricas de análise
st.subheader("🔎 Análise Avançada de Padrões")
analise_tercos = analise_por_terco(h)
if analise_tercos:
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Tendência Terço 1", analise_tercos["Terço 1 (1-9)"])
    col_t2.metric("Tendência Terço 2", analise_tercos["Terço 2 (10-18)"])
    col_t3.metric("Tendência Terço 3", analise_tercos["Terço 3 (19-27)"])

st.write("---")
st.write(f"Contagem de Sequências: **{contagem_sequencias(h)}**")
st.write(f"Quebra de Padrão (Breakout): **{quebra_padrao(h)}**")
st.write(f"Variação de Alternância: **{variacao_alternancia(h)}**")

# ---
# Alertas
st.subheader("🚨 Alerta estratégico")
alertas = []
if len(valores) > 0 and sequencia_final(h) >= 5 and valores[-1] in ["C", "V"]:
    alertas.append(("🟥 Sequência final ativa — possível inversão", "error"))
if eco_visual(h) == "Detectado":
    alertas.append(("🔁 Eco visual detectado — possível repetição", "warning"))
if isinstance(eco_parcial(h), str) and eco_parcial(h).startswith(("4", "5", "6")):
    alertas.append(("🧠 Eco parcial — padrão reescrito com semelhança", "info"))
if isinstance(dist_empates(h), int) and dist_empates(h) == 1:
    alertas.append(("🟨 Empates consecutivos — instabilidade", "error"))
if blocos_espelhados(h) >= 1:
    alertas.append(("🧩 Bloco espelhado — reflexo estratégico", "info"))
if quebra_padrao(h) == "Quebra de alternância detectada":
    alertas.append(("💥 Padrão de alternância quebrado - nova tendência pode estar surgindo", "warning"))

if not alertas:
    st.info("Nenhum padrão crítico identificado.")
else:
    for alerta, tipo in alertas:
        if tipo == "error":
            st.error(alerta)
        elif tipo == "warning":
            st.warning(alerta)
        else:
            st.info(alerta)

# ---
# Limpar
if st.button("🧹 Limpar histórico"):
    st.session_state.historico = []
    st.rerun()

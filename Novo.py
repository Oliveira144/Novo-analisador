import streamlit as st
from collections import deque, Counter
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -------------------------
# Configuração
# -------------------------
MAX_HISTORY = 1000
ANALYSIS_WINDOW = 27
SHORT_WINDOW = 9
PREDICTION_CONFIDENCE_THRESHOLD = 65

st.set_page_config(
    page_title="Football Studio – Dashboard Estratégico", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhor aparência
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007BFF;
        margin: 0.5rem 0;
    }
    .pattern-alert {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .prediction-high {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .prediction-medium {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .prediction-low {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializa estado
if "historico" not in st.session_state:
    st.session_state.historico = deque(maxlen=MAX_HISTORY)
if "timestamps" not in st.session_state:
    st.session_state.timestamps = deque(maxlen=MAX_HISTORY)

# -------------------------
# Funções utilitárias aprimoradas
# -------------------------
def bolha_cor(r):
    return {"C": "🏠", "V": "✈️", "E": "⚖️"}.get(r, "⬜")

def get_valores(h, window=None):
    valores = [x for x in h if x in ("C","V","E")]
    return valores[-window:] if window else valores

def add_result(result):
    st.session_state.historico.append(result)
    st.session_state.timestamps.append(datetime.now())

# -------------------------
# Análises aprimoradas
# -------------------------
def analise_ciclos(h):
    """Detecta ciclos e padrões repetitivos"""
    v = get_valores(h)
    if len(v) < 6: return {"ciclos": [], "periodo_dominante": None}
    
    ciclos_detectados = []
    
    # Busca por ciclos de tamanho 2 a 9
    for tam_ciclo in range(2, min(10, len(v)//3)):
        for start in range(len(v) - tam_ciclo*3):
            padrao = v[start:start+tam_ciclo]
            repeticoes = 1
            
            for i in range(start+tam_ciclo, len(v)-tam_ciclo+1, tam_ciclo):
                if v[i:i+tam_ciclo] == padrao:
                    repeticoes += 1
                else:
                    break
            
            if repeticoes >= 2:
                ciclos_detectados.append({
                    'padrao': padrao,
                    'tamanho': tam_ciclo,
                    'repeticoes': repeticoes,
                    'posicao': start
                })
    
    return {
        'ciclos': sorted(ciclos_detectados, key=lambda x: x['repeticoes'], reverse=True)[:3],
        'periodo_dominante': ciclos_detectados[0]['tamanho'] if ciclos_detectados else None
    }

def analise_momentum(h):
    """Analisa o momentum atual baseado em múltiplos fatores"""
    v = get_valores(h)
    if len(v) < 5: return {"score": 0, "direcao": "neutro", "intensidade": "baixa"}
    
    ult_5 = v[-5:]
    ult_3 = v[-3:]
    
    scores = {"C": 0, "V": 0, "E": 0}
    
    # Peso por recência
    pesos = [0.5, 0.7, 1.0, 1.3, 1.6]  # Mais recente = maior peso
    for i, resultado in enumerate(ult_5):
        scores[resultado] += pesos[i]
    
    # Bonus por sequência
    seq_atual = sequencia_final(h)
    if seq_atual >= 2:
        scores[v[-1]] += seq_atual * 0.8
    
    # Analise tendência
    max_score = max(scores.values())
    direcao = [k for k, v in scores.items() if v == max_score][0]
    
    intensidade = "alta" if max_score >= 4 else ("média" if max_score >= 2.5 else "baixa")
    
    return {
        "scores": scores,
        "direcao": direcao,
        "intensidade": intensidade,
        "confianca": min(100, (max_score / sum(scores.values())) * 100) if sum(scores.values()) > 0 else 0
    }

def detectar_reversoes(h):
    """Detecta padrões de reversão de tendência"""
    v = get_valores(h)
    if len(v) < 7: return {"reversoes": [], "probabilidade_reversao": 0}
    
    reversoes = []
    
    # Padrão: 3+ mesmo resultado seguido de mudança
    for i in range(3, len(v)):
        if all(v[j] == v[i-3] for j in range(i-2, i)) and v[i] != v[i-1]:
            reversoes.append({
                'posicao': i,
                'de': v[i-1],
                'para': v[i],
                'tamanho_seq': 3
            })
    
    # Calcula probabilidade de reversão atual
    seq_atual = sequencia_final(h)
    prob_reversao = 0
    
    if seq_atual >= 3:
        # Histórico de reversões após sequências similares
        reversoes_similares = [r for r in reversoes if r['de'] == v[-1]]
        if reversoes_similares:
            prob_reversao = min(85, seq_atual * 15 + len(reversoes_similares) * 5)
    
    return {
        "reversoes": reversoes[-5:],  # Últimas 5 reversões
        "probabilidade_reversao": prob_reversao,
        "seq_atual": seq_atual
    }

def analise_distribuicao_avancada(h):
    """Análise estatística avançada da distribuição"""
    v = get_valores(h)
    if not v: return {}
    
    total = len(v)
    contagem = Counter(v)
    
    # Frequências esperadas vs observadas
    freq_esperada = total / 3
    desvios = {k: abs(contagem[k] - freq_esperada) for k in ['C', 'V', 'E']}
    
    # Chi-square test approximation
    chi_square = sum((contagem.get(k, 0) - freq_esperada)**2 / freq_esperada for k in ['C', 'V', 'E'])
    
    # Coeficiente de variação
    valores_freq = list(contagem.values())
    media_freq = sum(valores_freq) / len(valores_freq)
    cv = (math.sqrt(sum((f - media_freq)**2 for f in valores_freq) / len(valores_freq)) / media_freq) * 100
    
    return {
        "distribuicao": dict(contagem),
        "desvios": desvios,
        "chi_square": chi_square,
        "coef_variacao": cv,
        "mais_defasado": min(desvios.keys(), key=lambda k: contagem[k]),
        "mais_frequente": contagem.most_common(1)[0][0] if contagem else None
    }

# Funções existentes otimizadas
def maior_sequencia(h):
    v = get_valores(h)
    if not v: return {"tamanho": 0, "tipo": None}
    
    max_seq = atual = 1
    tipo_max = tipo_atual = v[0]
    
    for i in range(1, len(v)):
        if v[i] == v[i-1]:
            atual += 1
            if atual > max_seq:
                max_seq = atual
                tipo_max = v[i]
        else:
            atual = 1
            tipo_atual = v[i]
    
    return {"tamanho": max_seq, "tipo": tipo_max}

def sequencia_final(h):
    v = get_valores(h)
    if not v: return {"tamanho": 0, "tipo": None}
    
    atual = v[-1]
    cont = 1
    for i in range(len(v)-2, -1, -1):
        if v[i] == atual:
            cont += 1
        else:
            break
    
    return {"tamanho": cont, "tipo": atual}

def entropia(h):
    v = get_valores(h)
    if not v: return 0.0
    
    freq = Counter(v)
    total = len(v)
    H = -sum((c/total) * math.log2(c/total) for c in freq.values() if c > 0)
    maxH = math.log2(3)
    return (H / maxH) * 100

# -------------------------
# Sistema de predição aprimorado
# -------------------------
def sistema_predicao_avancado(h):
    """Sistema de predição com múltiplos algoritmos"""
    v = get_valores(h)
    if len(v) < 5:
        return {
            "predicao": None,
            "confianca": 0,
            "explicacao": "Histórico insuficiente",
            "algoritmos": {}
        }
    
    # Diferentes algoritmos de predição
    algoritmos = {}
    
    # 1. Análise de Momentum
    momentum = analise_momentum(h)
    peso_momentum = momentum["confianca"] / 100
    algoritmos["momentum"] = {
        "predicao": momentum["direcao"],
        "peso": peso_momentum,
        "confianca": momentum["confianca"]
    }
    
    # 2. Análise de Reversão
    reversao = detectar_reversoes(h)
    if reversao["probabilidade_reversao"] > 30:
        atual = v[-1]
        predicao_reversao = "V" if atual == "C" else ("C" if atual == "V" else "C")
        algoritmos["reversao"] = {
            "predicao": predicao_reversao,
            "peso": reversao["probabilidade_reversao"] / 100,
            "confianca": reversao["probabilidade_reversao"]
        }
    
    # 3. Análise de Distribuição
    dist = analise_distribuicao_avancada(h)
    if dist and dist["mais_defasado"]:
        algoritmos["distribuicao"] = {
            "predicao": dist["mais_defasado"],
            "peso": 0.3,
            "confianca": 40
        }
    
    # 4. Análise de Ciclos
    ciclos = analise_ciclos(h)
    if ciclos["ciclos"]:
        melhor_ciclo = ciclos["ciclos"][0]
        padrao = melhor_ciclo["padrao"]
        pos_atual = len(v) % len(padrao)
        if pos_atual < len(padrao):
            algoritmos["ciclos"] = {
                "predicao": padrao[pos_atual],
                "peso": melhor_ciclo["repeticoes"] * 0.2,
                "confianca": min(70, melhor_ciclo["repeticoes"] * 25)
            }
    
    # Combina predições
    if not algoritmos:
        return {
            "predicao": None,
            "confianca": 0,
            "explicacao": "Nenhum padrão detectado",
            "algoritmos": {}
        }
    
    # Sistema de votação ponderada
    votos = {"C": 0, "V": 0, "E": 0}
    peso_total = 0
    
    for nome, alg in algoritmos.items():
        votos[alg["predicao"]] += alg["peso"] * alg["confianca"]
        peso_total += alg["peso"] * alg["confianca"]
    
    predicao_final = max(votos.keys(), key=lambda k: votos[k])
    confianca_final = (votos[predicao_final] / peso_total) if peso_total > 0 else 0
    
    # Gera explicação
    explicacao_parts = []
    for nome, alg in algoritmos.items():
        if alg["predicao"] == predicao_final:
            explicacao_parts.append(f"{nome.title()}: {alg['confianca']:.1f}%")
    
    explicacao = f"Baseado em: {', '.join(explicacao_parts)}"
    
    return {
        "predicao": predicao_final,
        "confianca": confianca_final,
        "explicacao": explicacao,
        "algoritmos": algoritmos,
        "distribuicao_votos": votos
    }

# -------------------------
# Interface Principal
# -------------------------

# Header principal
st.markdown("""
<div class="main-header">
    <h1>⚽ Football Studio - Dashboard Estratégico</h1>
    <p>Análise inteligente de padrões e predições avançadas</p>
</div>
""", unsafe_allow_html=True)

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    show_advanced = st.checkbox("Mostrar análises avançadas", True)
    auto_predict = st.checkbox("Predição automática", True)
    confidence_threshold = st.slider("Limite de confiança (%)", 30, 90, PREDICTION_CONFIDENCE_THRESHOLD)
    
    st.header("📊 Estatísticas Rápidas")
    if st.session_state.historico:
        h = st.session_state.historico
        total_jogos = len([x for x in h if x in ["C","V","E"]])
        st.metric("Total de jogos", total_jogos)
        
        if total_jogos > 0:
            contagem = Counter(get_valores(h))
            for resultado, emoji in [("C", "🏠"), ("V", "✈️"), ("E", "⚖️")]:
                pct = (contagem.get(resultado, 0) / total_jogos) * 100
                st.metric(f"{emoji} {resultado}", f"{contagem.get(resultado, 0)} ({pct:.1f}%)")

# Entrada de resultados
st.subheader("🎮 Entrada de Resultados")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🏠 Casa (C)", use_container_width=True):
        add_result("C")
        st.rerun()

with col2:
    if st.button("✈️ Visitante (V)", use_container_width=True):
        add_result("V")
        st.rerun()

with col3:
    if st.button("⚖️ Empate (E)", use_container_width=True):
        add_result("E")
        st.rerun()

with col4:
    if st.button("↶ Desfazer", use_container_width=True):
        if st.session_state.historico:
            st.session_state.historico.pop()
            if st.session_state.timestamps:
                st.session_state.timestamps.pop()
            st.rerun()

with col5:
    if st.button("🧹 Limpar", use_container_width=True):
        st.session_state.historico.clear()
        st.session_state.timestamps.clear()
        st.rerun()

h = st.session_state.historico

# Sistema de predição principal
if len(get_valores(h)) >= 5 and auto_predict:
    st.subheader("🎯 Predição Inteligente")
    
    predicao = sistema_predicao_avancado(h)
    
    if predicao["predicao"]:
        confianca = predicao["confianca"]
        
        # Determina o estilo baseado na confiança
        if confianca >= confidence_threshold:
            css_class = "prediction-high"
            icon = "🟢"
        elif confianca >= 40:
            css_class = "prediction-medium" 
            icon = "🟡"
        else:
            css_class = "prediction-low"
            icon = "🔴"
        
        st.markdown(f"""
        <div class="{css_class}">
            <h3>{icon} Predição: {bolha_cor(predicao["predicao"])} {predicao["predicao"]}</h3>
            <p><strong>Confiança:</strong> {confianca:.1f}%</p>
            <p><strong>Explicação:</strong> {predicao["explicacao"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar da confiança
        st.progress(confianca / 100)
        
        if show_advanced and predicao["algoritmos"]:
            with st.expander("📊 Detalhes dos Algoritmos"):
                for nome, alg in predicao["algoritmos"].items():
                    st.write(f"**{nome.title()}**: {alg['predicao']} ({alg['confianca']:.1f}%)")

# Histórico visual
if get_valores(h):
    st.subheader("📈 Histórico Visual")
    
    # Cria gráfico de linha temporal
    valores = get_valores(h)
    if len(valores) >= 3:
        df_hist = pd.DataFrame({
            'Jogo': range(1, len(valores) + 1),
            'Resultado': valores
        })
        
        # Converte para numérico para o gráfico
        resultado_num = {'C': 1, 'V': 2, 'E': 3}
        df_hist['Resultado_Num'] = df_hist['Resultado'].map(resultado_num)
        
        fig = px.line(df_hist, x='Jogo', y='Resultado_Num',
                     title="Sequência de Resultados",
                     labels={'Resultado_Num': 'Resultado'})
        
        fig.update_yaxis(
            tickvals=[1, 2, 3],
            ticktext=['Casa', 'Visitante', 'Empate']
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display das últimas jogadas
    st.write("**Últimas 18 jogadas:**")
    ultimas = list(reversed(get_valores(h, 18)))
    
    # Organiza em 3 linhas de 6
    for linha in range(3):
        cols = st.columns(6)
        for col_idx in range(6):
            idx = linha * 6 + col_idx
            if idx < len(ultimas):
                resultado = ultimas[idx]
                emoji = bolha_cor(resultado)
                cols[col_idx].markdown(f"<div style='text-align: center; font-size: 2rem;'>{emoji}</div>", unsafe_allow_html=True)

# Métricas principais
if get_valores(h):
    st.subheader("📊 Análise Principal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    maior_seq = maior_sequencia(h)
    seq_final = sequencia_final(h)
    ent = entropia(h)
    
    with col1:
        st.metric(
            "Maior Sequência", 
            f"{maior_seq['tamanho']} ({maior_seq['tipo']})" if maior_seq['tipo'] else "0"
        )
    
    with col2:
        st.metric(
            "Sequência Atual",
            f"{seq_final['tamanho']} ({seq_final['tipo']})" if seq_final['tipo'] else "0"
        )
    
    with col3:
        st.metric("Entropia", f"{ent:.1f}%")
    
    with col4:
        momentum = analise_momentum(h)
        st.metric("Momentum", f"{momentum['direcao']} ({momentum['intensidade']})")

# Análises avançadas
if show_advanced and len(get_valores(h)) >= 10:
    st.subheader("🧠 Análises Avançadas")
    
    # Análise de ciclos
    ciclos = analise_ciclos(h)
    if ciclos["ciclos"]:
        st.write("**Padrões Cíclicos Detectados:**")
        for i, ciclo in enumerate(ciclos["ciclos"][:3], 1):
            padrao_str = "".join([bolha_cor(x) for x in ciclo["padrao"]])
            st.write(f"{i}. {padrao_str} (repetido {ciclo['repeticoes']}x)")
    
    # Análise de reversões
    reversao = detectar_reversoes(h)
    if reversao["probabilidade_reversao"] > 20:
        st.markdown(f"""
        <div class="pattern-alert">
            <strong>⚠️ Alerta de Reversão</strong><br>
            Probabilidade de mudança: {reversao["probabilidade_reversao"]:.1f}%<br>
            Sequência atual: {reversao["seq_atual"]} {seq_final["tipo"] if seq_final["tipo"] else ""}
        </div>
        """, unsafe_allow_html=True)
    
    # Distribuição estatística
    dist = analise_distribuicao_avancada(h)
    if dist:
        st.write("**Análise Estatística:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Distribuição atual:")
            for resultado in ["C", "V", "E"]:
                count = dist["distribuicao"].get(resultado, 0)
                total = sum(dist["distribuicao"].values())
                pct = (count / total * 100) if total > 0 else 0
                st.write(f"• {bolha_cor(resultado)} {resultado}: {count} ({pct:.1f}%)")
        
        with col2:
            st.write("Métricas:")
            st.write(f"• Mais defasado: {bolha_cor(dist['mais_defasado'])} {dist['mais_defasado']}")
            st.write(f"• Coef. variação: {dist['coef_variacao']:.1f}%")
            st.write(f"• Chi-square: {dist['chi_square']:.2f}")

# Footer
st.markdown("---")
st.markdown("**💡 Dica:** Use as análises como apoio à decisão, nunca como garantia de resultado.")

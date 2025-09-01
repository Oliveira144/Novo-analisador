import streamlit as st
from collections import deque, Counter
import math
import pandas as pd
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
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #007BFF;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .pattern-alert {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffeaa7;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .prediction-high {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 2px solid #28a745;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(40,167,69,0.2);
    }
    .prediction-medium {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(255,193,7,0.2);
    }
    .prediction-low {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border: 2px solid #dc3545;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(220,53,69,0.2);
    }
    .game-bubble {
        display: inline-block;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        text-align: center;
        line-height: 50px;
        margin: 5px;
        font-size: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .bubble-casa { background: linear-gradient(135deg, #ff6b6b, #ee5a52); color: white; }
    .bubble-visitante { background: linear-gradient(135deg, #4ecdc4, #45b7b8); color: white; }
    .bubble-empate { background: linear-gradient(135deg, #ffe66d, #ff6b6b); color: white; }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .trend-arrow {
        font-size: 1.5rem;
        margin: 0 10px;
    }
    .sequence-display {
        font-size: 2rem;
        text-align: center;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
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

def get_css_class(r):
    return {"C": "bubble-casa", "V": "bubble-visitante", "E": "bubble-empate"}.get(r, "")

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
    if len(v) < 5: return {"score": 0, "direcao": "neutro", "intensidade": "baixa", "confianca": 0}
    
    ult_5 = v[-5:]
    
    scores = {"C": 0, "V": 0, "E": 0}
    
    # Peso por recência
    pesos = [0.5, 0.7, 1.0, 1.3, 1.6]  # Mais recente = maior peso
    for i, resultado in enumerate(ult_5):
        scores[resultado] += pesos[i]
    
    # Bonus por sequência
    seq_atual = sequencia_final(h)
    if seq_atual["tamanho"] >= 2:
        scores[v[-1]] += seq_atual["tamanho"] * 0.8
    
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
    if len(v) < 7: return {"reversoes": [], "probabilidade_reversao": 0, "seq_atual": 0}
    
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
    seq_atual = sequencia_final(h)["tamanho"]
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
    desvios = {k: abs(contagem.get(k, 0) - freq_esperada) for k in ['C', 'V', 'E']}
    
    # Chi-square test approximation
    chi_square = sum((contagem.get(k, 0) - freq_esperada)**2 / freq_esperada for k in ['C', 'V', 'E'])
    
    # Coeficiente de variação
    valores_freq = [contagem.get(k, 0) for k in ['C', 'V', 'E']]
    media_freq = sum(valores_freq) / len(valores_freq)
    cv = 0
    if media_freq > 0:
        cv = (math.sqrt(sum((f - media_freq)**2 for f in valores_freq) / len(valores_freq)) / media_freq) * 100
    
    return {
        "distribuicao": dict(contagem),
        "desvios": desvios,
        "chi_square": chi_square,
        "coef_variacao": cv,
        "mais_defasado": min(desvios.keys(), key=lambda k: contagem.get(k, 0)),
        "mais_frequente": contagem.most_common(1)[0][0] if contagem else None
    }

def analise_padroes_especiais(h):
    """Detecta padrões especiais como alternância, zigzag, etc."""
    v = get_valores(h)
    if len(v) < 6: return {}
    
    padroes = {}
    
    # Alternância perfeita
    alternancia_perfeita = all(v[i] != v[i+1] for i in range(len(v)-1))
    padroes["alternancia_perfeita"] = alternancia_perfeita
    
    # Padrão ABC (C-V-E repetindo)
    if len(v) >= 6:
        abc_pattern = all(v[i] == v[i-3] for i in range(3, min(9, len(v))))
        padroes["padrao_abc"] = abc_pattern
    
    # Dominância recente (70%+ nos últimos 9)
    if len(v) >= 9:
        ult_9 = v[-9:]
        contagem_9 = Counter(ult_9)
        max_freq = max(contagem_9.values())
        dominancia = (max_freq / 9) >= 0.7
        resultado_dominante = contagem_9.most_common(1)[0][0] if contagem_9 else None
        padroes["dominancia_recente"] = {
            "ativo": dominancia,
            "resultado": resultado_dominante,
            "frequencia": max_freq
        }
    
    return padroes

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

def calcular_tendencias(h):
    """Calcula tendências de curto e longo prazo"""
    v = get_valores(h)
    if len(v) < 6: return {}
    
    # Tendência curto prazo (últimas 6)
    curto = v[-6:]
    contagem_curto = Counter(curto)
    
    # Tendência longo prazo (últimas 18 ou todas se menor)
    longo = v[-18:] if len(v) >= 18 else v
    contagem_longo = Counter(longo)
    
    return {
        "curto_prazo": {
            "periodo": 6,
            "distribuicao": dict(contagem_curto),
            "dominante": contagem_curto.most_common(1)[0] if contagem_curto else None
        },
        "longo_prazo": {
            "periodo": len(longo),
            "distribuicao": dict(contagem_longo),
            "dominante": contagem_longo.most_common(1)[0] if contagem_longo else None
        }
    }

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
            "explicacao": "Histórico insuficiente (mín. 5 jogos)",
            "algoritmos": {}
        }
    
    # Diferentes algoritmos de predição
    algoritmos = {}
    
    # 1. Análise de Momentum
    momentum = analise_momentum(h)
    if momentum["confianca"] > 30:
        peso_momentum = momentum["confianca"] / 100
        algoritmos["momentum"] = {
            "predicao": momentum["direcao"],
            "peso": peso_momentum,
            "confianca": momentum["confianca"],
            "descricao": f"Momentum {momentum['intensidade']} para {momentum['direcao']}"
        }
    
    # 2. Análise de Reversão
    reversao = detectar_reversoes(h)
    if reversao["probabilidade_reversao"] > 30:
        atual = v[-1]
        predicao_reversao = "V" if atual == "C" else ("C" if atual == "V" else "C")
        algoritmos["reversao"] = {
            "predicao": predicao_reversao,
            "peso": reversao["probabilidade_reversao"] / 100,
            "confianca": reversao["probabilidade_reversao"],
            "descricao": f"Reversão após {reversao['seq_atual']} jogos consecutivos"
        }
    
    # 3. Análise de Distribuição
    dist = analise_distribuicao_avancada(h)
    if dist and dist["mais_defasado"]:
        algoritmos["distribuicao"] = {
            "predicao": dist["mais_defasado"],
            "peso": 0.4,
            "confianca": 45,
            "descricao": f"Compensação estatística - {dist['mais_defasado']} está defasado"
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
                "confianca": min(75, melhor_ciclo["repeticoes"] * 25),
                "descricao": f"Ciclo detectado: {'-'.join(padrao)} (repetido {melhor_ciclo['repeticoes']}x)"
            }
    
    # 5. Análise de Padrões Especiais
    padroes = analise_padroes_especiais(h)
    if padroes.get("dominancia_recente", {}).get("ativo"):
        dom = padroes["dominancia_recente"]
        # Se há dominância, apostar no contrário
        contrario = "V" if dom["resultado"] == "C" else ("C" if dom["resultado"] == "V" else "C")
        algoritmos["anti_dominancia"] = {
            "predicao": contrario,
            "peso": 0.6,
            "confianca": 55,
            "descricao": f"Anti-dominância - {dom['resultado']} dominou {dom['frequencia']}/9 recentes"
        }
    
    # Combina predições
    if not algoritmos:
        return {
            "predicao": None,
            "confianca": 0,
            "explicacao": "Nenhum padrão claro detectado",
            "algoritmos": {}
        }
    
    # Sistema de votação ponderada
    votos = {"C": 0, "V": 0, "E": 0}
    peso_total = 0
    
    for nome, alg in algoritmos.items():
        peso_real = alg["peso"] * (alg["confianca"] / 100)
        votos[alg["predicao"]] += peso_real
        peso_total += peso_real
    
    if peso_total == 0:
        return {
            "predicao": None,
            "confianca": 0,
            "explicacao": "Algoritmos sem peso suficiente",
            "algoritmos": algoritmos
        }
    
    predicao_final = max(votos.keys(), key=lambda k: votos[k])
    confianca_final = (votos[predicao_final] / peso_total) * 100
    
    # Gera explicação
    algoritmos_relevantes = [
        alg for alg in algoritmos.values() 
        if alg["predicao"] == predicao_final and alg["confianca"] > 30
    ]
    
    if algoritmos_relevantes:
        explicacao = f"Baseado em {len(algoritmos_relevantes)} algoritmo(s): "
        explicacao += "; ".join([alg["descricao"] for alg in algoritmos_relevantes[:2]])
    else:
        explicacao = "Predição baseada em análise combinada"
    
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
        total_jogos = len(get_valores(h))
        st.metric("Total de jogos", total_jogos)
        
        if total_jogos > 0:
            contagem = Counter(get_valores(h))
            for resultado, emoji in [("C", "🏠"), ("V", "✈️"), ("E", "⚖️")]:
                count = contagem.get(resultado, 0)
                pct = (count / total_jogos) * 100 if total_jogos > 0 else 0
                st.metric(f"{emoji} {resultado}", f"{count} ({pct:.1f}%)")
        
        # Últimos resultados na sidebar
        if total_jogos > 0:
            st.subheader("🎯 Últimos 10")
            ultimos_10 = list(reversed(get_valores(h, 10)))
            emoji_sequence = " ".join([bolha_cor(r) for r in ultimos_10])
            st.write(emoji_sequence)

# Entrada de resultados
st.subheader("🎮 Entrada de Resultados")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🏠 Casa (C)", use_container_width=True, type="primary"):
        add_result("C")
        st.rerun()

with col2:
    if st.button("✈️ Visitante (V)", use_container_width=True, type="primary"):
        add_result("V")
        st.rerun()

with col3:
    if st.button("⚖️ Empate (E)", use_container_width=True, type="primary"):
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
            nivel = "ALTA"
        elif confianca >= 40:
            css_class = "prediction-medium" 
            icon = "🟡"
            nivel = "MÉDIA"
        else:
            css_class = "prediction-low"
            icon = "🔴"
            nivel = "BAIXA"
        
        st.markdown(f"""
        <div class="{css_class}">
            <h3>{icon} PREDIÇÃO: {bolha_cor(predicao["predicao"])} {predicao["predicao"]}</h3>
            <p><strong>Confiança {nivel}:</strong> {confianca:.1f}%</p>
            <p><strong>Explicação:</strong> {predicao["explicacao"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar da confiança
        st.progress(confianca / 100)
        
        if show_advanced and predicao["algoritmos"]:
            with st.expander("🔍 Detalhes dos Algoritmos de Análise"):
                for nome, alg in predicao["algoritmos"].items():
                    st.write(f"**{nome.title()}**: {alg['predicao']} - {alg['confianca']:.1f}% confiança")
                    st.write(f"   ↳ {alg['descricao']}")
                    st.write("")

# Histórico visual
if get_valores(h):
    st.subheader("📈 Histórico Visual")
    
    # Display das jogadas com CSS customizado
    valores = get_valores(h)
    
    # Últimas 21 jogadas (3 linhas de 7)
    st.write("**Últimas 21 jogadas (mais recente à direita):**")
    ultimas_21 = list(reversed(valores[-21:]))
    
    # Organiza em linhas
    linhas = []
    for i in range(0, len(ultimas_21), 7):
        linha = ultimas_21[i:i+7]
        linhas.append(linha)
    
    for linha in linhas:
        cols = st.columns(7)
        for i, resultado in enumerate(linha):
            if i < len(cols):
                emoji = bolha_cor(resultado)
                css_class = get_css_class(resultado)
                cols[i].markdown(f"""
                <div class="game-bubble {css_class}">
                    {emoji}
                </div>
                """, unsafe_allow_html=True)
    
    # Sequência simples dos últimos 12
    st.write("**Sequência dos últimos 12:**")
    ultimos_12 = list(reversed(valores[-12:]))
    sequencia_str = " → ".join([f"{bolha_cor(r)}" for r in ultimos_12])
    st.markdown(f"""
    <div class="sequence-display">
        {sequencia_str}
    </div>
    """, unsafe_allow_html=True)

# Métricas principais
if get_valores(h):
    st.subheader("📊 Análise Principal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    maior_seq = maior_sequencia(h)
    seq_final = sequencia_final(h)
    ent = entropia(h)
    momentum = analise_momentum(h)
    
    with col1:
        valor = f"{maior_seq['tamanho']}" if maior_seq['tipo'] else "0"
        if maior_seq['tipo']:
            valor += f" ({bolha_cor(maior_seq['tipo'])} {maior_seq['tipo']})"
        st.metric("Maior Sequência", valor)
    
    with col2:
        valor = f"{seq_final['tamanho']}" if seq_final['tipo'] else "0"
        if seq_final['tipo']:
            valor += f" ({bolha_cor(seq_final['tipo'])} {seq_final['tipo']})"
        st.metric("Sequência Atual", valor)
    
    with col3:
        cor_entropia = "🟢" if ent > 80 else ("🟡" if ent > 60 else "🔴")
        st.metric("Entropia", f"{cor_entropia} {ent:.1f}%")
    
    with col4:
        momentum_display = f"{bolha_cor(momentum['direcao'])} {momentum['direcao']}"
        if momentum['intensidade'] != 'baixa':
            momentum_display += f" ({momentum['intensidade']})"
        st.metric("Momentum", momentum_display)

# Tendências
if len(get_valores(h)) >= 6:
    st.subheader("📈 Análise de Tendências")
    
    tendencias = calcular_tendencias(h)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 Curto Prazo (últimas 6)**")
        if tendencias.get("curto_prazo"):
            cp = tendencias["curto_prazo"]
            for resultado in ["C", "V", "E"]:
                count = cp["distribuicao"].get(resultado, 0)
                pct = (count / 6) * 100
                barra = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                st.write(f"{bolha_cor(resultado)} {resultado}: {count} ({pct:.0f}%) {barra}")
    
    with col2:
        st.write("**📈 Longo Prazo (últimas 18)**")
        if tendencias.get("longo_prazo"):
            lp = tendencias["longo_prazo"]
            total_lp = lp["periodo"]
            for resultado in ["C", "V", "E"]:
                count = lp["distribuicao"].get(resultado, 0)
                pct = (count / total_lp) * 100 if total_lp > 0 else 0
                barra = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                st.write(f"{bolha_cor(resultado)} {resultado}: {count} ({pct:.0f}%) {barra}")

# Análises avançadas
if show_advanced and len(get_valores(h)) >= 10:
    st.subheader("🧠 Análises Avançadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Análise de ciclos
        ciclos = analise_ciclos(h)
        if ciclos["ciclos"]:
            st.write("**🔄 Padrões Cíclicos Detectados:**")
            for i, ciclo in enumerate(ciclos["ciclos"][:3], 1):
                padrao_str = " → ".join([f"{bolha_cor(x)} {x}" for x in ciclo["padrao"]])
                st.write(f"{i}. {padrao_str}")
                st.write(f"   ↳ Repetido **{ciclo['repeticoes']}x** (tamanho: {ciclo['tamanho']})")
        
        # Padrões especiais
        padroes = analise_padroes_especiais(h)
        if padroes:
            st.write("**🎯 Padrões Especiais:**")
            
            if padroes.get("alternancia_perfeita"):
                st.write("✅ **Alternância Perfeita** detectada")
            
            if padroes.get("padrao_abc"):
                st.write("✅ **Padrão ABC** (C-V-E) detectado")
            
            if padroes.get("dominancia_recente", {}).get("ativo"):
                dom = padroes["dominancia_recente"]
                st.write(f"⚠️ **Dominância**: {bolha_cor(dom['resultado'])} {dom['resultado']} dominou {dom['frequencia']}/9 jogos recentes")
    
    with col2:
        # Análise de reversões
        reversao = detectar_reversoes(h)
        if reversao["probabilidade_reversao"] > 20:
            st.markdown(f"""
            <div class="pattern-alert">
                <strong>⚠️ Alerta de Reversão</strong><br>
                Probabilidade de mudança: <strong>{reversao["probabilidade_reversao"]:.1f}%</strong><br>
                Sequência atual: {reversao["seq_atual"]} {bolha_cor(sequencia_final(h)["tipo"]) if sequencia_final(h)["tipo"] else ""} {sequencia_final(h)["tipo"] or ""}
            </div>
            """, unsafe_allow_html=True)
        
        # Distribuição estatística
        dist = analise_distribuicao_avancada(h)
        if dist:
            st.write("**📊 Análise Estatística:**")
            
            st.write("*Distribuição vs Expectativa:*")
            total = sum(dist["distribuicao"].values())
            expectativa = total / 3
            
            for resultado in ["C", "V", "E"]:
                atual = dist["distribuicao"].get(resultado, 0)
                diff = atual - expectativa
                seta = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
                st.write(f"• {bolha_cor(resultado)} {resultado}: {atual} {seta} ({diff:+.1f})")
            
            st.write(f"**Mais defasado:** {bolha_cor(dist['mais_defasado'])} {dist['mais_defasado']}")
            st.write(f"**Coef. variação:** {dist['coef_variacao']:.1f}%")
            st.write(f"**Chi-square:** {dist['chi_square']:.2f}")

# Seção de insights e dicas
if len(get_valores(h)) >= 15:
    st.subheader("💡 Insights e Recomendações")
    
    insights = []
    v = get_valores(h)
    
    # Insight sobre entropia
    ent = entropia(h)
    if ent > 85:
        insights.append("🎲 **Alta randomização** - Resultados muito equilibrados, difícil prever padrões")
    elif ent < 50:
        insights.append("📊 **Baixa entropia** - Padrões mais previsíveis, alguns resultados dominando")
    
    # Insight sobre sequências
    maior_seq = maior_sequencia(h)
    if maior_seq["tamanho"] >= 5:
        insights.append(f"🔥 **Sequência longa detectada** - {maior_seq['tamanho']} {maior_seq['tipo']} consecutivos. Probabilidade de mudança aumenta!")
    
    # Insight sobre momentum
    momentum = analise_momentum(h)
    if momentum["confianca"] > 70:
        insights.append(f"📈 **Momentum forte** - Tendência {momentum['intensidade']} para {bolha_cor(momentum['direcao'])} {momentum['direcao']}")
    
    # Insight sobre distribuição
    contagem = Counter(v)
    mais_freq = contagem.most_common(1)[0]
    menos_freq = contagem.most_common()[-1]
    
    if mais_freq[1] - menos_freq[1] >= len(v) * 0.3:
        insights.append(f"⚖️ **Desbalanceamento significativo** - {bolha_cor(mais_freq[0])} {mais_freq[0]} muito mais frequente que {bolha_cor(menos_freq[0])} {menos_freq[0]}")
    
    # Insight sobre padrões especiais
    padroes = analise_padroes_especiais(h)
    if padroes.get("alternancia_perfeita"):
        insights.append("🔄 **Alternância perfeita** - Padrão raro detectado, probabilidade de quebra aumenta")
    
    if insights:
        for insight in insights:
            st.write(insight)
    else:
        st.write("📝 Acumule mais dados para insights mais precisos")

# Seção de estatísticas detalhadas
if show_advanced and len(get_valores(h)) >= 20:
    with st.expander("📈 Estatísticas Detalhadas"):
        v = get_valores(h)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Análise por Período:**")
            
            # Primeiros vs Últimos 10
            if len(v) >= 20:
                primeiros_10 = Counter(v[:10])
                ultimos_10 = Counter(v[-10:])
                
                st.write("*Primeiros 10:*")
                for resultado in ["C", "V", "E"]:
                    st.write(f"• {resultado}: {primeiros_10.get(resultado, 0)}")
                
                st.write("*Últimos 10:*")
                for resultado in ["C", "V", "E"]:
                    st.write(f"• {resultado}: {ultimos_10.get(resultado, 0)}")
        
        with col2:
            st.write("**Análise de Sequências:**")
            
            # Contagem de todas as sequências
            sequencias = {"1": 0, "2": 0, "3": 0, "4": 0, "5+": 0}
            atual_seq = 1
            
            for i in range(1, len(v)):
                if v[i] == v[i-1]:
                    atual_seq += 1
                else:
                    seq_key = str(min(atual_seq, 5)) if atual_seq < 5 else "5+"
                    if atual_seq > 1:  # Só conta sequências > 1
                        sequencias[seq_key] += 1
                    atual_seq = 1
            
            # Conta a última sequência se > 1
            if atual_seq > 1:
                seq_key = str(min(atual_seq, 5)) if atual_seq < 5 else "5+"
                sequencias[seq_key] += 1
            
            for tam, count in sequencias.items():
                if tam != "1":  # Não mostra sequências de 1
                    st.write(f"• Sequências de {tam}: {count}")
        
        with col3:
            st.write("**Métricas Avançadas:**")
            
            # Taxa de alternância
            alternacoes = sum(1 for i in range(1, len(v)) if v[i] != v[i-1])
            taxa_alternancia = (alternacoes / (len(v) - 1)) * 100 if len(v) > 1 else 0
            
            st.write(f"• Taxa alternância: {taxa_alternancia:.1f}%")
            st.write(f"• Entropia: {entropia(h):.1f}%")
            
            # Distância média entre empates
            empates_pos = [i for i, r in enumerate(v) if r == 'E']
            if len(empates_pos) >= 2:
                distancias = [empates_pos[i] - empates_pos[i-1] for i in range(1, len(empates_pos))]
                dist_media = sum(distancias) / len(distancias)
                st.write(f"• Dist. média empates: {dist_media:.1f}")

# Footer com informações
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🎯 Como usar:**")
    st.markdown("• Registre os resultados dos jogos")
    st.markdown("• Acompanhe as predições inteligentes")
    st.markdown("• Use as análises como apoio à decisão")

with col2:
    st.markdown("**📊 Algoritmos:**")
    st.markdown("• Análise de momentum")
    st.markdown("• Detecção de ciclos")
    st.markdown("• Probabilidade de reversão")
    st.markdown("• Compensação estatística")

with col3:
    st.markdown("**⚠️ Avisos:**")
    st.markdown("• Resultados passados ≠ futuros")
    st.markdown("• Use com responsabilidade")
    st.markdown("• Ferramenta de análise, não garantia")

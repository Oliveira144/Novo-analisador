import streamlit as st
import numpy as np
import pandas as pd
from collections import deque, Counter
import math
from datetime import datetime

# =====================================
# CONFIGURAÇÕES PROFISSIONAIS
# =====================================

st.set_page_config(
    page_title="Football Studio Pro Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profissional
st.markdown("""
<style>
    .main-container {
        padding: 0;
    }
    .header-section {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 0 0 20px 20px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-professional {
        background: white;
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .statistical-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    .alert-professional {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .alert-high { background: #d1ecf1; border-left: 4px solid #0c5460; }
    .alert-medium { background: #fff3cd; border-left: 4px solid #856404; }
    .alert-low { background: #f8d7da; border-left: 4px solid #721c24; }
    .data-table {
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    .confidence-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 8px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# =====================================
# CLASSE PRINCIPAL DE ANÁLISE
# =====================================

class FootballStudioAnalyzer:
    def __init__(self):
        self.outcomes = {'C': 0, 'V': 1, 'E': 2}  # Casa, Visitante, Empate
        self.outcome_names = {0: 'Casa', 1: 'Visitante', 2: 'Empate'}
        self.min_sample_size = 30  # Mínimo para análises estatísticas confiáveis
        
    def encode_sequence(self, sequence):
        """Converte sequência de strings para números"""
        return [self.outcomes[x] for x in sequence if x in self.outcomes]
    
    def calculate_transition_matrix(self, sequence):
        """Calcula matriz de transição de estados"""
        if len(sequence) < 10:
            return None, 0
            
        encoded = self.encode_sequence(sequence)
        if len(encoded) < 10:
            return None, 0
            
        # Matriz 3x3 para as transições
        matrix = np.zeros((3, 3))
        
        for i in range(len(encoded) - 1):
            current_state = encoded[i]
            next_state = encoded[i + 1]
            matrix[current_state][next_state] += 1
        
        # Normaliza para probabilidades
        row_sums = matrix.sum(axis=1)
        transition_matrix = np.divide(matrix, row_sums[:, np.newaxis], 
                                    out=np.zeros_like(matrix), where=row_sums[:, np.newaxis]!=0)
        
        # Calcula confiabilidade baseada no tamanho da amostra
        reliability = min(1.0, len(encoded) / 100)  # 100+ observações = confiabilidade máxima
        
        return transition_matrix, reliability
    
    def chi_square_independence_test(self, sequence):
        """Teste Chi-quadrado para independência (implementação própria)"""
        if len(sequence) < 20:
            return None, None, 0
            
        encoded = self.encode_sequence(sequence)
        if len(encoded) < 20:
            return None, None, 0
            
        # Cria tabela de contingência para pares consecutivos
        contingency = np.zeros((3, 3))
        for i in range(len(encoded) - 1):
            contingency[encoded[i]][encoded[i + 1]] += 1
        
        if contingency.sum() == 0:
            return None, None, 0
            
        try:
            # Calcula valores esperados
            row_totals = contingency.sum(axis=1)
            col_totals = contingency.sum(axis=0)
            total = contingency.sum()
            
            expected = np.outer(row_totals, col_totals) / total
            
            # Calcula chi-quadrado
            chi2 = np.sum((contingency - expected)**2 / (expected + 1e-10))
            
            # Graus de liberdade
            dof = (contingency.shape[0] - 1) * (contingency.shape[1] - 1)
            
            # Aproximação do p-valor usando distribuição normal
            # Para grandes amostras, chi2 aproxima normal
            if dof > 0:
                p_value = 1 - self._normal_cdf((chi2 - dof) / math.sqrt(2 * dof))
            else:
                p_value = 0.5
                
            return chi2, max(0, min(1, p_value)), min(1.0, len(encoded) / 50)
        except:
            return None, None, 0
    
    def _normal_cdf(self, x):
        """Função de distribuição cumulativa normal padrão (aproximação)"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def runs_test(self, sequence):
        """Teste de corridas para aleatoriedade (implementação própria)"""
        if len(sequence) < 15:
            return None, None, 0
            
        encoded = self.encode_sequence(sequence)
        if len(encoded) < 15:
            return None, None, 0
            
        # Converte para binário (Casa vs Não-Casa)
        binary = [1 if x == 0 else 0 for x in encoded]
        
        n1 = sum(binary)  # Número de Casas
        n2 = len(binary) - n1  # Número de Não-Casas
        
        if n1 == 0 or n2 == 0:
            return None, None, 0
            
        # Conta o número de corridas
        runs = 1
        for i in range(1, len(binary)):
            if binary[i] != binary[i-1]:
                runs += 1
        
        # Estatística do teste
        expected_runs = ((2 * n1 * n2) / (n1 + n2)) + 1
        variance = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / ((n1 + n2) ** 2 * (n1 + n2 - 1))
        
        if variance <= 0:
            return None, None, 0
            
        z_score = (runs - expected_runs) / math.sqrt(variance)
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
        
        return z_score, max(0, min(1, p_value)), min(1.0, len(encoded) / 40)
    
    def autocorrelation_analysis(self, sequence, max_lag=10):
        """Análise de autocorrelação para detectar padrões temporais"""
        if len(sequence) < 25:
            return None, 0
            
        encoded = self.encode_sequence(sequence)
        if len(encoded) < 25:
            return None, 0
            
        autocorrs = []
        for lag in range(1, min(max_lag + 1, len(encoded) // 3)):
            if len(encoded) - lag < 5:
                break
                
            x1 = np.array(encoded[:-lag])
            x2 = np.array(encoded[lag:])
            
            if len(x1) == 0 or len(x2) == 0:
                continue
                
            # Calcula correlação de Pearson manualmente
            try:
                mean_x1 = np.mean(x1)
                mean_x2 = np.mean(x2)
                
                numerator = np.sum((x1 - mean_x1) * (x2 - mean_x2))
                denominator = math.sqrt(np.sum((x1 - mean_x1)**2) * np.sum((x2 - mean_x2)**2))
                
                if denominator > 0:
                    corr = numerator / denominator
                    if not math.isnan(corr):
                        autocorrs.append((lag, corr))
            except:
                continue
        
        reliability = min(1.0, len(encoded) / 60)
        return autocorrs, reliability
    
    def frequency_domain_analysis(self, sequence):
        """Análise no domínio da frequência usando FFT"""
        if len(sequence) < 32:
            return None, 0
            
        encoded = self.encode_sequence(sequence)
        if len(encoded) < 32:
            return None, 0
            
        # Remove a tendência (detrend)
        detrended = np.array(encoded) - np.mean(encoded)
        
        # FFT
        fft_result = np.fft.fft(detrended)
        freqs = np.fft.fftfreq(len(detrended))
        
        # Pega apenas frequências positivas
        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft_result[:len(fft_result)//2])
        
        # Encontra picos significativos
        if len(magnitude) > 3:
            threshold = np.mean(magnitude) + 2 * np.std(magnitude)
            peaks = [(positive_freqs[i], magnitude[i]) for i in range(1, len(magnitude)) 
                    if magnitude[i] > threshold]
            
            # Converte frequência para período
            periods = [(1/freq if freq > 0 else 0, mag) for freq, mag in peaks]
            periods = [(p, m) for p, m in periods if 2 <= p <= len(encoded)//3]
            
            reliability = min(1.0, len(encoded) / 80)
            return sorted(periods, key=lambda x: x[1], reverse=True)[:5], reliability
        
        return [], 0
    
    def entropy_analysis(self, sequence):
        """Análise de entropia de Shannon"""
        if len(sequence) < 10:
            return 0, 0
            
        encoded = self.encode_sequence(sequence)
        if len(encoded) < 10:
            return 0, 0
            
        # Entropia de Shannon
        counter = Counter(encoded)
        total = len(encoded)
        
        entropy = 0
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normaliza (máximo para 3 estados é log2(3))
        max_entropy = math.log2(3)
        normalized_entropy = entropy / max_entropy
        
        reliability = min(1.0, len(encoded) / 30)
        return normalized_entropy, reliability
    
    def markov_chain_prediction(self, sequence):
        """Predição baseada em cadeia de Markov"""
        if len(sequence) < 20:
            return None, 0
            
        transition_matrix, reliability = self.calculate_transition_matrix(sequence)
        if transition_matrix is None:
            return None, 0
            
        # Estado atual
        current_state = self.outcomes.get(sequence[-1])
        if current_state is None:
            return None, 0
            
        # Probabilidades do próximo estado
        next_probs = transition_matrix[current_state]
        
        # Verifica se há diferença significativa
        if np.max(next_probs) - np.min(next_probs) < 0.1:  # Diferença < 10%
            return None, reliability * 0.5
            
        predicted_state = np.argmax(next_probs)
        confidence = next_probs[predicted_state]
        
        # Converte de volta para string
        prediction = [k for k, v in self.outcomes.items() if v == predicted_state][0]
        
        return {
            'prediction': prediction,
            'confidence': confidence * 100,
            'probabilities': {
                'C': next_probs[0] * 100,
                'V': next_probs[1] * 100,
                'E': next_probs[2] * 100
            }
        }, reliability

    def pattern_detection(self, sequence):
        """Detecta padrões repetitivos na sequência"""
        if len(sequence) < 6:
            return []
            
        patterns = []
        
        # Procura por padrões de tamanho 2 a 6
        for pattern_length in range(2, min(7, len(sequence) // 3)):
            pattern_counts = Counter()
            
            for i in range(len(sequence) - pattern_length + 1):
                pattern = tuple(sequence[i:i + pattern_length])
                pattern_counts[pattern] += 1
            
            # Considera apenas padrões que aparecem mais de 1 vez
            for pattern, count in pattern_counts.items():
                if count > 1:
                    significance = count / (len(sequence) - pattern_length + 1)
                    if significance > 0.1:  # Pelo menos 10% de ocorrência
                        patterns.append({
                            'pattern': list(pattern),
                            'count': count,
                            'length': pattern_length,
                            'significance': significance
                        })
        
        return sorted(patterns, key=lambda x: x['significance'], reverse=True)[:5]

# =====================================
# INICIALIZAÇÃO
# =====================================

if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=1000)
if "timestamps" not in st.session_state:
    st.session_state.timestamps = deque(maxlen=1000)

analyzer = FootballStudioAnalyzer()

# =====================================
# INTERFACE PRINCIPAL
# =====================================

# Header
st.markdown("""
<div class="header-section">
    <h1>🏈 Football Studio Pro Analytics</h1>
    <p>Análise estatística profissional baseada em métodos matemáticos rigorosos</p>
</div>
""", unsafe_allow_html=True)

# Sidebar de configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    confidence_threshold = st.slider("Limiar de confiança (%)", 50, 95, 70)
    show_statistical_tests = st.checkbox("Mostrar testes estatísticos", True)
    show_advanced_metrics = st.checkbox("Métricas avançadas", True)
    min_predictions = st.number_input("Mín. jogos para predição", 10, 100, 20)
    
    st.header("📊 Resumo da Sessão")
    if st.session_state.history:
        total = len([x for x in st.session_state.history if x in ['C','V','E']])
        if total > 0:
            counter = Counter([x for x in st.session_state.history if x in ['C','V','E']])
            st.metric("Total de jogos", total)
            for outcome, name in [('C', 'Casa'), ('V', 'Visitante'), ('E', 'Empate')]:
                count = counter.get(outcome, 0)
                pct = (count / total) * 100
                st.write(f"{name}: {count} ({pct:.1f}%)")

# Controles de entrada
st.subheader("📥 Registro de Resultados")
col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])

with col1:
    if st.button("🏠 CASA", use_container_width=True, type="primary"):
        st.session_state.history.append('C')
        st.session_state.timestamps.append(datetime.now())
        st.rerun()

with col2:
    if st.button("✈️ VISITANTE", use_container_width=True, type="primary"):
        st.session_state.history.append('V')
        st.session_state.timestamps.append(datetime.now())
        st.rerun()

with col3:
    if st.button("⚖️ EMPATE", use_container_width=True, type="primary"):
        st.session_state.history.append('E')
        st.session_state.timestamps.append(datetime.now())
        st.rerun()

with col4:
    if st.button("↶", help="Desfazer"):
        if st.session_state.history:
            st.session_state.history.pop()
            if st.session_state.timestamps:
                st.session_state.timestamps.pop()
            st.rerun()

with col5:
    if st.button("🗑️", help="Limpar"):
        st.session_state.history.clear()
        st.session_state.timestamps.clear()
        st.rerun()

# =====================================
# ANÁLISES ESTATÍSTICAS PRINCIPAIS
# =====================================

sequence = [x for x in st.session_state.history if x in ['C','V','E']]

if len(sequence) >= 10:
    
    # Predição Markoviana
    st.subheader("🎯 Predição Estatística (Cadeia de Markov)")
    
    if len(sequence) >= min_predictions:
        prediction_result, reliability = analyzer.markov_chain_prediction(sequence)
        
        if prediction_result and reliability > 0.3:
            pred = prediction_result['prediction']
            conf = prediction_result['confidence']
            probs = prediction_result['probabilities']
            
            # Determina o nível de confiança
            if conf >= confidence_threshold:
                alert_class = "alert-high"
                icon = "🟢"
                status = "ALTA CONFIANÇA"
            elif conf >= confidence_threshold * 0.7:
                alert_class = "alert-medium"
                icon = "🟡"
                status = "CONFIANÇA MODERADA"
            else:
                alert_class = "alert-low"
                icon = "🔴"
                status = "BAIXA CONFIANÇA"
            
            outcome_names = {'C': 'CASA 🏠', 'V': 'VISITANTE ✈️', 'E': 'EMPATE ⚖️'}
            
            st.markdown(f"""
            <div class="alert-professional {alert_class}">
                <h3>{icon} PREDIÇÃO: {outcome_names[pred]}</h3>
                <p><strong>Confiança:</strong> {conf:.1f}% | <strong>Status:</strong> {status}</p>
                <p><strong>Confiabilidade do modelo:</strong> {reliability*100:.1f}%</p>
                <p><strong>Base estatística:</strong> {len(sequence)} observações</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostra todas as probabilidades
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏠 Casa", f"{probs['C']:.1f}%")
            with col2:
                st.metric("✈️ Visitante", f"{probs['V']:.1f}%")
            with col3:
                st.metric("⚖️ Empate", f"{probs['E']:.1f}%")
        else:
            st.info("📊 Dados insuficientes ou padrão não detectado para predição confiável")
    else:
        st.info(f"📊 Aguardando mais dados... ({len(sequence)}/{min_predictions} jogos mínimos)")

    # Matriz de Transição
    if show_advanced_metrics and len(sequence) >= 15:
        st.subheader("📊 Matriz de Transição de Estados")
        
        transition_matrix, reliability = analyzer.calculate_transition_matrix(sequence)
        if transition_matrix is not None:
            
            # Cria DataFrame para exibição
            df_matrix = pd.DataFrame(
                transition_matrix * 100,  # Converte para percentual
                columns=['Casa', 'Visitante', 'Empate'],
                index=['Casa →', 'Visitante →', 'Empate →']
            )
            
            st.write("**Probabilidades de transição (%):**")
            st.dataframe(df_matrix.round(1), use_container_width=True)
            
            st.write(f"**Confiabilidade:** {reliability*100:.1f}% (baseada em {len(sequence)} observações)")
            
            # Interpretação
            max_prob = np.max(transition_matrix)
            if max_prob > 0.6:
                st.warning("⚠️ Padrão determinístico detectado - sequência pode não ser aleatória")
            elif max_prob < 0.4:
                st.success("✅ Distribuição equilibrada - comportamento próximo ao aleatório")

    # Testes Estatísticos
    if show_statistical_tests and len(sequence) >= 20:
        st.subheader("🔬 Testes de Hipótese Estatística")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="statistical-section">
                <h4>Teste Chi-quadrado (Independência)</h4>
            """, unsafe_allow_html=True)
            
            chi2, p_value, reliability = analyzer.chi_square_independence_test(sequence)
            if chi2 is not None:
                alpha = 0.05
                is_independent = p_value > alpha
                
                st.write(f"**Chi² = {chi2:.3f}**")
                st.write(f"**p-valor = {p_value:.4f}**")
                st.write(f"**Confiabilidade: {reliability*100:.1f}%**")
                
                if is_independent:
                    st.success("✅ Não há evidência de dependência (sequência aleatória)")
                else:
                    st.error("❌ Evidência de dependência detectada (padrão presente)")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="statistical-section">
                <h4>Teste de Corridas (Aleatoriedade)</h4>
            """, unsafe_allow_html=True)
            
            z_score, p_value, reliability = analyzer.runs_test(sequence)
            if z_score is not None:
                alpha = 0.05
                is_random = p_value > alpha
                
                st.write(f"**Z-score = {z_score:.3f}**")
                st.write(f"**p-valor = {p_value:.4f}**")
                st.write(f"**Confiabilidade: {reliability*100:.1f}%**")
                
                if is_random:
                    st.success("✅ Sequência compatível com aleatoriedade")
                else:
                    st.error("❌ Sequência não-aleatória detectada")
            
            st.markdown("</div>", unsafe_allow_html=True)

    # Análise de Autocorrelação
    if show_advanced_metrics and len(sequence) >= 25:
        st.subheader("📈 Análise de Autocorrelação Temporal")
        
        autocorrs, reliability = analyzer.autocorrelation_analysis(sequence)
        if autocorrs and reliability > 0.2:
            
            # Cria DataFrame para visualização
            df_autocorr = pd.DataFrame(autocorrs, columns=['Lag', 'Correlação'])
            df_autocorr['Correlação_Abs'] = df_autocorr['Correlação'].abs()
            df_autocorr = df_autocorr.sort_values('Correlação_Abs', ascending=False)
            
            st.write(f"**Correlações mais significativas (confiabilidade: {reliability*100:.1f}%):**")
            
            for _, row in df_autocorr.head(5).iterrows():
                lag = int(row['Lag'])
                corr = row['Correlação']
                
                if abs(corr) > 0.3:
                    significance = "🔴 FORTE"
                elif abs(corr) > 0.15:
                    significance = "🟡 MODERADA"
                else:
                    significance = "🟢 FRACA"
                    
                st.write(f"• **Lag {lag}:** {corr:.3f} ({significance})")
                
                if abs(corr) > 0.25:
                    st.write(f"  ↳ Padrão cíclico de período {lag} detectado")

    # Análise de Entropia
    if show_advanced_metrics and len(sequence) >= 15:
        st.subheader("🧮 Análise de Entropia Informacional")
        
        entropy, reliability = analyzer.entropy_analysis(sequence)
        if reliability > 0.3:
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Entropia Normalizada", f"{entropy:.3f}")
            
            with col2:
                predictability = (1 - entropy) * 100
                st.metric("Predictibilidade", f"{predictability:.1f}%")
            
            with col3:
                st.metric("Confiabilidade", f"{reliability*100:.1f}%")
            
            # Interpretação
            if entropy > 0.95:
                st.success("✅ Alta aleatoriedade - distribuição muito equilibrada")
            elif entropy > 0.85:
                st.info("ℹ️ Aleatoriedade moderada - leve desvio da uniformidade")
            elif entropy > 0.70:
                st.warning("⚠️ Baixa aleatoriedade - padrões evidentes")
            else:
                st.error("❌ Muito baixa aleatoriedade - forte presença de padrões")

    # Detecção de Padrões
    if show_advanced_metrics and len(sequence) >= 12:
        st.subheader("🔍 Detecção de Padrões Repetitivos")
        
        patterns = analyzer.pattern_detection(sequence)
        if patterns:
            st.write("**Padrões significativos detectados:**")
            
            for i, pattern in enumerate(patterns[:5], 1):
                pattern_str = " → ".join(pattern['pattern'])
                significance_pct = pattern['significance'] * 100
                
                if pattern['significance'] > 0.3:
                    strength = "🔴 MUITO FORTE"
                elif pattern['significance'] > 0.2:
                    strength = "🟡 FORTE"
                else:
                    strength = "🟢 MODERADO"
                
                st.write(f"**{i}. {pattern_str}**")
                st.write(f"   ↳ Ocorrências: {pattern['count']} | Significância: {significance_pct:.1f}% ({strength})")

# =====================================
# HISTÓRICO E MÉTRICAS BÁSICAS
# =====================================

if sequence:
    st.subheader("📋 Dados Históricos")
    
    # Últimas 30 jogadas
    recent = sequence[-30:] if len(sequence) > 30 else sequence
    
    # Organiza em tabela
    rows = []
    for i in range(0, len(recent), 10):
        row = recent[i:i+10]
        # Preenche com espaços se necessário
        while len(row) < 10:
            row.append("")
        rows.append(row)
    
    if rows:
        df_history = pd.DataFrame(rows, columns=[f"Pos {i+1}" for i in range(10)])
        
        # Substitui símbolos para melhor visualização
        df_display = df_history.replace({'C': '🏠', 'V': '✈️', 'E': '⚖️', '': ''})
        
        st.write("**Últimas 30 jogadas (mais recentes à direita):**")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Estatísticas descritivas
    st.subheader("📈 Estatísticas Descritivas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    counter = Counter(sequence)
    total = len(sequence)
    
    with col1:
        casa_pct = (counter.get('C', 0) / total) * 100
        st.metric("🏠 Casa", f"{counter.get('C', 0)} ({casa_pct:.1f}%)")
    
    with col2:
        visit_pct = (counter.get('V', 0) / total) * 100
        st.metric("✈️ Visitante", f"{counter.get('V', 0)} ({visit_pct:.1f}%)")
    
    with col3:
        empate_pct = (counter.get('E', 0) / total) * 100
        st.metric("⚖️ Empate", f"{counter.get('E', 0)} ({empate_pct:.1f}%)")
    
    with col4:
        st.metric("📊 Total", f"{total} jogos")

else:
    st.info("👆 Comece registrando alguns resultados para ver as análises estatísticas")

# =====================================
# RODAPÉ INFORMATIVO
# =====================================

st.markdown("---")

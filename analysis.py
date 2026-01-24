import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os

# Configurações globais
sns.set_theme(style="whitegrid")
custom_palette = ["#3d1152", "#6a2c70", "#b83b5e", "#f08a5d", "#f9ed69"]
sns.set_palette(sns.color_palette(custom_palette))
plt.rcParams['figure.figsize'] = (14, 7)
warnings.filterwarnings('ignore')

# Criar diretório para salvar plots
OUTPUT_DIR = "output/plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Diretório de saída configurado: {OUTPUT_DIR}")

def load_data(filepath):
    """Carrega e realiza a limpeza inicial dos dados."""
    print("\n--- 1. Ingestão dos Dados ---")
    print(f"Lendo arquivo: {filepath}")

    # Leitura com separador ';' e decimal ','
    df = pd.read_csv(filepath, sep=';', decimal=',')

    # Limpeza dos nomes das colunas
    clean_columns = {}
    for col in df.columns:
        # Remove ' Value <unidade>' mantendo apenas o tag
        if ' Value' in col:
            clean_name = col.split(' Value')[0]
        else:
            clean_name = col
        clean_columns[col] = clean_name.strip()

    df = df.rename(columns=clean_columns)

    # Conversão de timestamp
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        # Ordenar pelo tempo para garantir integridade em séries temporais
        df = df.sort_values('Timestamp').reset_index(drop=True)

    print(f"Shape inicial: {df.shape}")
    return df

def perform_eda(df, target):
    """Realiza a análise exploratória de dados."""
    print("\n--- 2. Análise Exploratória de Dados (EDA) ---")

    cols_pv = [c for c in df.columns if '.PV' in c]
    cols_sp = [c for c in df.columns if '.SP' in c]

    print(f"Variáveis PV: {len(cols_pv)} | Variáveis SP: {len(cols_sp)}")

    # Estatísticas Descritivas
    print("\nTop 5 variáveis com maior desvio padrão:")
    stats_desc = df[cols_pv].describe().T
    print(stats_desc.sort_values('std', ascending=False).head(5)[['mean', 'std', 'min', 'max']])

    # Distribuição do Target
    plt.figure(figsize=(14, 6))
    plt.subplot(1, 2, 1)
    sns.histplot(df[target], kde=True, color="#3d1152", bins=30)
    plt.title(f'Distribuição de {target}')
    plt.xlabel('Densidade de Saída (kg/m3)')

    plt.subplot(1, 2, 2)
    sns.lineplot(x=df['Timestamp'], y=df[target], color="#3d1152")
    plt.title(f'Série Temporal de {target}')
    plt.xlabel('Tempo')
    plt.ylabel('Valor')

    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "distribuicao_target.png")
    plt.savefig(save_path)
    print(f"Gráfico salvo: {save_path}")
    plt.close()

    # Correlação
    print("\nCalculando correlações...")
    corr_matrix = df[cols_pv].corr()

    plt.figure(figsize=(16, 12))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, cmap='magma', vmax=1, vmin=-1, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5})
    plt.title('Matriz de Correlação - Variáveis de Processo (.PV)')

    save_path = os.path.join(OUTPUT_DIR, "matriz_correlacao.png")
    plt.savefig(save_path)
    print(f"Gráfico salvo: {save_path}")
    plt.close()

    target_corr = corr_matrix[target].sort_values(ascending=False)

    # Análise de Outliers (Top features correlacionadas)
    top_corr_vars = target_corr.abs().sort_values(ascending=False).head(7).index.tolist()
    if target in top_corr_vars:
        top_corr_vars.remove(target)

    plt.figure(figsize=(15, 10))
    for i, col in enumerate(top_corr_vars[:6]):
        plt.subplot(2, 3, i+1)
        sns.boxplot(y=df[col], color="#3d1152")
        plt.title(col)
        plt.ylabel('')

    plt.suptitle('Boxplots das Principais Variáveis Correlacionadas', fontsize=16)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "outliers_boxplots.png")
    plt.savefig(save_path)
    print(f"Gráfico salvo: {save_path}")
    plt.close()

def feature_engineering(df, target):
    """Realiza engenharia de atributos e limpeza."""
    print("\n--- 3. Engenharia de Atributos e Limpeza ---")

    # Identificando pares PV e SP
    pv_vars = [c for c in df.columns if '.PV' in c and c != target]
    pv_to_sp = {}
    for pv in pv_vars:
        sp_candidate = pv.replace('.PV', '.SP')
        if sp_candidate in df.columns:
            pv_to_sp[pv] = sp_candidate

    print(f"Pares PV-SP identificados: {len(pv_to_sp)}")

    df_eng = df.copy()

    # Features Temporais
    df_eng['Hour'] = df_eng['Timestamp'].dt.hour
    df_eng['DayOfWeek'] = df_eng['Timestamp'].dt.dayofweek

    window_size = 30

    for pv, sp in pv_to_sp.items():
        # Erro (Flutuação)
        error_col = f"{pv}_Error"
        df_eng[error_col] = df_eng[pv] - df_eng[sp]

        # Tempo fora do ideal
        mu, sigma = df_eng[error_col].mean(), df_eng[error_col].std()

        if sigma == 0:
            continue

        upper_limit = mu + 2 * sigma
        lower_limit = mu - 2 * sigma

        is_out = ((df_eng[error_col] > upper_limit) | (df_eng[error_col] < lower_limit)).astype(int)

        out_time_col = f"{pv}_OutTime_{window_size}m"
        df_eng[out_time_col] = is_out.rolling(window=window_size, min_periods=1).sum()

    # Limpeza
    # Remover SPs
    sp_vars = [c for c in df.columns if '.SP' in c]
    df_clean = df_eng.drop(columns=sp_vars)

    # Remover Constantes
    const_cols = [c for c in df_clean.columns if df_clean[c].std() == 0]
    df_clean = df_clean.drop(columns=const_cols)
    print(f"Colunas constantes removidas: {len(const_cols)}")

    # Remover Multicolinearidade (>0.95)
    corr_abs = df_clean.select_dtypes(include=[np.number]).corr().abs()
    upper = corr_abs.where(np.triu(np.ones(corr_abs.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]

    if target in to_drop:
        to_drop.remove(target)

    df_clean = df_clean.drop(columns=to_drop)
    print(f"Colunas removidas por multicolinearidade (>0.95): {len(to_drop)}")

    print(f"Shape após engenharia: {df_clean.shape}")
    return df_clean

def prepare_for_ml(df, target):
    """Prepara o dataset final para ML."""
    print("\n--- 4. Preparação Final para ML ---")

    # Tratamento de nulos (Forward Fill para séries temporais)
    if df.isnull().sum().sum() > 0:
        print("Preenchendo valores nulos (ffill/bfill)...")
        df = df.ffill().bfill()

    # Separação X e y
    X = df.drop(columns=['Timestamp', target])
    y = df[target]

    print(f"Features (X): {X.shape}")
    print(f"Target (y): {y.shape}")

    return X, y

def propose_ml_paths():
    """Exibe propostas de caminhos de ML."""
    print("\n--- 5. Caminhos de Machine Learning (Proposta) ---")
    print("""
    Caminho 1: Regressão Linear Regularizada (Lasso/ElasticNet)
    - Baseline robusto e interpretável.
    - Útil para seleção de features automática.

    Caminho 2: Modelos Baseados em Árvores (XGBoost / Random Forest)
    - Captura não-linearidades e interações complexas.
    - Robusto a outliers e dados mistos. Recomendado como principal abordagem.

    Caminho 3: Métodos de Ensemble (Voting Regressor)
    - Combina estabilidade linear com flexibilidade de árvores.
    - Maximiza robustez e generalização.
    """)

def main():
    filepath = 'dataset.csv'
    target = 'AT-1100.PV'

    if not os.path.exists(filepath):
        print(f"Erro: Arquivo '{filepath}' não encontrado.")
        return

    # Pipeline de execução
    df = load_data(filepath)
    perform_eda(df, target)
    df_clean = feature_engineering(df, target)
    X, y = prepare_for_ml(df_clean, target)
    propose_ml_paths()

    print("\nProcessamento concluído com sucesso!")
    print(f"Gráficos salvos em: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

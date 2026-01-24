import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

# Configuração de estilo visual
sns.set_theme(style="whitegrid")

def carregar_e_limpar_dados(filepath):
    print("--- Carregando e Limpando Dados ---")
    # Carregar CSV com separador ';' e decimal ','
    df = pd.read_csv(filepath, sep=';', decimal=',')

    # Limpar nomes das colunas: remover " Value" e unidades se houver
    # Ex: "AT-1100.PV Value kg/m3" -> "AT-1100.PV"
    df.columns = [col.split(' Value')[0] for col in df.columns]

    print(f"Dataset original: {df.shape[0]} linhas, {df.shape[1]} colunas.")

    # Filtrar colunas que terminam com ".SP" (Set Points)
    cols_to_drop = [col for col in df.columns if ".SP" in col]
    df = df.drop(columns=cols_to_drop)
    print(f"Removidas {len(cols_to_drop)} colunas de Set Point (.SP).")

    # Remover coluna de Timestamp se existir (não é sensor)
    if 'Timestamp' in df.columns:
        df = df.drop(columns=['Timestamp'])
        print("Coluna 'Timestamp' removida para análise estática.")

    # Remover linhas com valores faltantes (NaN)
    df = df.dropna()
    print(f"Dataset final: {df.shape[0]} linhas, {df.shape[1]} colunas.")

    return df

def analise_1_correlacao_vs_mutual_info(df, target_col):
    print("\n\n=== Análise 1: Matriz de Correlação vs. Mutual Information Score ===")
    print("Objetivo: Verificar se existem relações não-lineares fortes que a correlação linear ignora.")
    print("Interpretação: Se MI é alto mas Correlação é baixa, temos não-linearidade -> Ponto para Árvores (Gradient Boosting).")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Calcular Correlação de Pearson (absoluta)
    correlations = X.corrwith(y).abs()

    # Calcular Mutual Information
    # MI captura qualquer tipo de dependência, não só linear
    mi_scores = mutual_info_regression(X, y, random_state=42)
    mi_series = pd.Series(mi_scores, index=X.columns)

    # Juntar em um DataFrame para comparar
    comparison = pd.DataFrame({
        'Pearson Correlation (Abs)': correlations,
        'Mutual Information': mi_series
    })

    # Ordenar por MI
    comparison = comparison.sort_values('Mutual Information', ascending=False).head(10)

    print("\nTop 10 Features por Mutual Information:")
    print(comparison)

    # Plotar
    plt.figure(figsize=(10, 6))
    comparison.plot(kind='bar', figsize=(12, 6))
    plt.title("Análise 1: Pearson Correlation vs Mutual Information (Top 10 Features)")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig('analise_1_correlacao_vs_mi.png')
    print("Gráfico salvo em 'analise_1_correlacao_vs_mi.png'")

    return comparison.index.tolist() # Retorna top features

def analise_2_visual_scatter(df, target_col, top_features):
    print("\n\n=== Análise 2: Inspeção Visual (Scatter Plots) ===")
    print("Objetivo: Buscar formas não-lineares nos dados (curvas, 'S', clusters).")
    print("Interpretação: Se os pontos não formam uma reta clara, Regressão Linear falhará.")

    top_3 = top_features[:3]

    plt.figure(figsize=(18, 5))
    for i, feature in enumerate(top_3):
        plt.subplot(1, 3, i+1)
        sns.scatterplot(data=df, x=feature, y=target_col, alpha=0.5)
        plt.title(f"{feature} vs {target_col}")
        plt.xlabel(feature)
        plt.ylabel(target_col)

    plt.tight_layout()
    plt.savefig('analise_2_scatter_plots.png')
    print(f"Gráfico salvo em 'analise_2_scatter_plots.png' para as features: {', '.join(top_3)}")

def analise_3_residuos_linear(df, target_col):
    print("\n\n=== Análise 3: Análise de Resíduos de Regressão Linear ===")
    print("Objetivo: Treinar um modelo linear simples e ver onde ele erra.")
    print("Interpretação: Se o gráfico de resíduos mostra um padrão (não é ruído branco aleatório), o modelo linear é insuficiente.")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Escalar dados (boa prática para Linear Reg)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(X_scaled, y)

    y_pred = model.predict(X_scaled)
    residuals = y - y_pred
    r2 = r2_score(y, y_pred)

    print(f"R² do Modelo Linear: {r2:.4f}")

    # Plotar Real vs Predito e Resíduos
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    sns.scatterplot(x=y, y=y_pred, alpha=0.5)
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
    plt.title("Real vs Predito (Linear Regression)")
    plt.xlabel("Real")
    plt.ylabel("Predito")

    plt.subplot(1, 2, 2)
    sns.scatterplot(x=y_pred, y=residuals, alpha=0.5)
    plt.axhline(0, color='r', linestyle='--')
    plt.title("Resíduos vs Predito")
    plt.xlabel("Predito")
    plt.ylabel("Resíduos (Erro)")

    plt.tight_layout()
    plt.savefig('analise_3_residuos.png')
    print("Gráfico salvo em 'analise_3_residuos.png'")

    if r2 < 0.6:
        print("\nCONCLUSÃO PARCIAL: O R² baixo sugere que o modelo linear tem dificuldade em capturar a variância.")
    else:
        print("\nCONCLUSÃO PARCIAL: O R² é razoável, mas verifique se há padrões nos resíduos.")

def main():
    filepath = 'dataset.csv'
    # Identificar nome exato do alvo
    # No readme/head vimos "AT-1100.PV Value kg/m3", que virará "AT-1100.PV" após limpeza
    target_name = "AT-1100.PV"

    try:
        df = carregar_e_limpar_dados(filepath)

        # Verificar se alvo está nas colunas
        if target_name not in df.columns:
            # Tentar achar algo parecido
            candidatos = [c for c in df.columns if "AT-1100" in c]
            if candidatos:
                target_name = candidatos[0]
                print(f"Alvo ajustado para: {target_name}")
            else:
                raise ValueError(f"Coluna alvo {target_name} não encontrada!")

        # Executar análises
        top_features = analise_1_correlacao_vs_mutual_info(df, target_name)
        analise_2_visual_scatter(df, target_name, top_features)
        analise_3_residuos_linear(df, target_name)

        print("\n\n=== CONCLUSÃO GERAL ===")
        print("Revise os gráficos gerados.")
        print("1. Se 'Mutual Information' mostra barras altas onde 'Pearson' é baixo -> Relação não-linear.")
        print("2. Se os Scatter Plots mostram curvas ou nuvens complexas -> Relação não-linear.")
        print("3. Se os Resíduos têm forma (ex: parábola, funil) -> Modelo Linear falhou.")
        print("Se a maioria desses for VERDADEIRO, sua hipótese está confirmada: USE ÁRVORES (XGBoost/LightGBM).")

    except Exception as e:
        print(f"Erro na execução: {e}")

if __name__ == "__main__":
    main()

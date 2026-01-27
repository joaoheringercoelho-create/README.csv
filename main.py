# -*- coding: utf-8 -*-
"""
Script Principal para Análise e Modelagem ElasticNet (Processo Químico Industrial)
Objetivo: Prever a densidade de saída (AT-1100.PV) usando dados de processo.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

from sklearn.model_selection import train_test_split, KFold
from sklearn.linear_model import ElasticNetCV, ElasticNet
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Configuração de estilo dos gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def carregar_e_limpar_dados(caminho_arquivo):
    """
    Carrega o dataset, limpa nomes de colunas e seleciona features.

    Args:
        caminho_arquivo (str): Caminho para o arquivo CSV.

    Returns:
        pd.DataFrame: DataFrame limpo e filtrado.
    """
    print("--- Iniciando Carregamento e Limpeza de Dados ---")

    # Carregar dataset (delimitador ; e decimal ,)
    try:
        df = pd.read_csv(caminho_arquivo, sep=';', decimal=',')
        print(f"Dataset carregado com sucesso: {df.shape[0]} registros, {df.shape[1]} colunas.")
    except Exception as e:
        print(f"Erro ao carregar dataset: {e}")
        return None

    # Limpeza de nomes de colunas (remover unidades e espaços extras)
    # Ex: "AT-1100.PV Value kg/m3" -> "AT-1100.PV"
    df.columns = [col.split(' Value')[0].strip() for col in df.columns]
    print("Nomes de colunas limpos.")

    # Converter Timestamp para datetime
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df.set_index('Timestamp', inplace=True)
        print("Coluna Timestamp convertida e definida como índice.")
    else:
        print("AVISO: Coluna Timestamp não encontrada.")

    # Seleção de Features e Target
    target_col = 'AT-1100.PV'

    # Identificar colunas a serem removidas
    # 1. Remover colunas .SP (Set Points)
    cols_sp = [c for c in df.columns if c.endswith('.SP')]

    # 2. Remover outras tags de análise (AT-) que não sejam o target
    # O target AT-1100.PV deve ser mantido, mas AT-1104.PV, etc. devem sair.
    cols_at_other = [c for c in df.columns if c.startswith('AT-') and c != target_col]

    cols_to_remove = cols_sp + cols_at_other

    # Manter apenas colunas que terminam com .PV (e remover as exceções acima)
    # Primeiro, filtrar apenas .PV e o target (caso o target não terminasse em PV, mas aqui termina)
    cols_pv = [c for c in df.columns if c.endswith('.PV')]

    # Interseção final de colunas a manter
    final_features = [c for c in cols_pv if c not in cols_to_remove]

    # Garantir que o target está na lista
    if target_col not in final_features:
        print(f"ERRO CRÍTICO: Target {target_col} foi removido acidentalmente.")
        return None

    df_final = df[final_features].copy()

    print(f"Features removidas (SP): {len(cols_sp)}")
    print(f"Features removidas (Outros AT-): {len(cols_at_other)}")
    print(f"Features finais selecionadas: {len(final_features)} (incluindo target)")

    return df_final

def analisar_outliers(df, target_col, output_dir='output/plots'):
    """
    Analisa outliers no target e gera visualizações.
    Não remove dados, apenas documenta.
    """
    print("\n--- Analisando Outliers ---")

    if target_col not in df.columns:
        print(f"Target {target_col} não encontrado para análise de outliers.")
        return

    # Estatísticas descritivas
    desc = df[target_col].describe()
    print(f"Estatísticas do Target ({target_col}):")
    print(desc)

    # Visualização: Boxplot
    plt.figure()
    sns.boxplot(x=df[target_col], color='#3d1152') # Cor solicitada na memória
    plt.title(f'Boxplot de {target_col} (Identificação de Outliers)', fontweight='bold')
    plt.xlabel('Valor')
    plt.savefig(f'{output_dir}/boxplot_target.png')
    plt.close()
    print(f"Gráfico salvo: {output_dir}/boxplot_target.png")

    # Visualização: Time Series
    plt.figure()
    df[target_col].plot(color='#3d1152')
    plt.title(f'Série Temporal de {target_col}', fontweight='bold')
    plt.ylabel('Valor')
    plt.xlabel('Tempo')
    plt.savefig(f'{output_dir}/timeseries_target.png')
    plt.close()
    print(f"Gráfico salvo: {output_dir}/timeseries_target.png")

def treinar_modelo(df, target_col):
    """
    Divide os dados, cria o pipeline com RobustScaler e ElasticNetCV, e treina o modelo.

    Args:
        df (pd.DataFrame): DataFrame processado.
        target_col (str): Nome da coluna alvo.

    Returns:
        dict: Dicionário contendo o modelo treinado, métricas e dados de teste.
    """
    print("\n--- Iniciando Treinamento do Modelo ---")

    # Separação X (Features) e y (Target)
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Divisão Treino/Teste (80/20)
    # Importante: shuffle=False para respeitar a ordem temporal dos dados (série temporal)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, shuffle=False)

    print(f"Tamanho do Treino: {X_train.shape[0]} amostras")
    print(f"Tamanho do Teste: {X_test.shape[0]} amostras")

    # Definição do Cross-Validation para o ElasticNetCV
    # O usuário permitiu KFold padrão.
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    # Criação do Pipeline
    # 1. RobustScaler: Escala os dados sendo robusto a outliers (usando quartis),
    #    evitando que outliers distorçam a média e desvio padrão como no StandardScaler.
    # 2. ElasticNetCV: Modelo linear que combina penalidades L1 (Lasso) e L2 (Ridge).
    #    - O CV ajusta automaticamente os hiperparâmetros alpha (força da regularização)
    #      e l1_ratio (mistura entre L1 e L2).
    pipeline = Pipeline([
        ('scaler', RobustScaler()),
        ('elasticnet', ElasticNetCV(
            l1_ratio=[.1, .5, .7, .9, .95, .99, 1], # Lista de l1_ratios para testar
            cv=cv,
            n_jobs=-1, # Usar todos os processadores
            random_state=42,
            verbose=0
        ))
    ])

    # Treinamento
    print("Treinando ElasticNet com validação cruzada para encontrar melhores hiperparâmetros...")
    pipeline.fit(X_train, y_train)

    # Recuperando o modelo ElasticNet treinado dentro do pipeline
    model = pipeline.named_steps['elasticnet']

    print(f"Melhor alpha encontrado: {model.alpha_:.6f}")
    print(f"Melhor l1_ratio encontrado: {model.l1_ratio_:.6f}")

    return {
        'pipeline': pipeline,
        'model': model,
        'X_test': X_test,
        'y_test': y_test,
        'X_train': X_train, # Útil para feature importance names
        'y_train': y_train
    }

def avaliar_e_visualizar(resultados, target_col, output_dir='output/plots'):
    """
    Avalia o modelo, calcula métricas (incluindo esparsidade e dual gap),
    gera gráficos e imprime os resultados.
    """
    print("\n--- Iniciando Avaliação e Visualização ---")

    pipeline = resultados['pipeline']
    model_cv = resultados['model'] # O objeto ElasticNetCV treinado
    X_test = resultados['X_test']
    y_test = resultados['y_test']
    X_train = resultados['X_train']
    y_train = resultados['y_train']

    # Predições
    y_pred = pipeline.predict(X_test)
    y_train_pred = pipeline.predict(X_train)

    # Métricas de Erro
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)

    print(f"R² (Teste): {r2:.4f}")
    print(f"RMSE (Teste): {rmse:.4f}")
    print(f"MAE (Teste): {mae:.4f}")

    # --- Métricas Avançadas ---

    # 1. Esparsidade
    # Coeficientes do modelo
    coefs = model_cv.coef_
    n_features = len(coefs)
    n_zeros = np.sum(coefs == 0)
    sparsity = n_zeros / n_features

    print(f"\nEsparsidade (Sparsity): {sparsity:.2%} ({n_zeros}/{n_features} features zeradas)")

    # 2. Dual Gap
    # O ElasticNetCV não expõe dual_gap_ diretamente para o modelo refitado final de forma simples.
    # Vamos instanciar um ElasticNet padrão com os melhores parâmetros e treinar nos dados transformados
    # para obter o dual_gap_ exato.

    # Extrair os dados transformados pelo Scaler
    scaler = pipeline.named_steps['scaler']
    X_train_scaled = scaler.transform(X_train)

    # Treinar modelo simples para pegar o gap
    enet_refit = ElasticNet(
        alpha=model_cv.alpha_,
        l1_ratio=model_cv.l1_ratio_,
        random_state=42
    )
    enet_refit.fit(X_train_scaled, y_train)
    dual_gap = enet_refit.dual_gap_
    print(f"Dual Gap: {dual_gap:.6f}")

    # --- Visualizações ---

    # 1. Time Series (Real vs Predito)
    plt.figure()
    plt.plot(y_test.index, y_test, label='Real', color='gray', alpha=0.7)
    plt.plot(y_test.index, y_pred, label='Predito', color='#3d1152', linewidth=2)
    plt.title('Série Temporal: Real vs Predito (Teste)', fontweight='bold')
    plt.xlabel('Tempo')
    plt.ylabel(target_col)
    plt.legend()
    plt.savefig(f'{output_dir}/timeseries_prediction.png')
    plt.close()
    print(f"Gráfico salvo: {output_dir}/timeseries_prediction.png")

    # 2. Scatter Plot (Real vs Predito)
    plt.figure()
    plt.scatter(y_test, y_pred, alpha=0.5, color='#3d1152')
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2) # Linha de identidade
    plt.title('Scatter Plot: Real vs Predito', fontweight='bold')
    plt.xlabel('Real')
    plt.ylabel('Predito')
    plt.savefig(f'{output_dir}/scatter_prediction.png')
    plt.close()
    print(f"Gráfico salvo: {output_dir}/scatter_prediction.png")

    # 3. Resíduos
    residuos = y_test - y_pred
    plt.figure()
    plt.scatter(y_pred, residuos, alpha=0.5, color='#3d1152')
    plt.axhline(0, color='r', linestyle='--')
    plt.title('Análise de Resíduos', fontweight='bold')
    plt.xlabel('Predito')
    plt.ylabel('Resíduo (Real - Predito)')
    plt.savefig(f'{output_dir}/residuals.png')
    plt.close()
    print(f"Gráfico salvo: {output_dir}/residuals.png")

    # 4. Importância das Features
    features_names = X_train.columns
    # Criar DataFrame de coeficientes
    coef_df = pd.DataFrame({
        'Feature': features_names,
        'Coeficiente': coefs,
        'Abs_Coef': np.abs(coefs)
    })
    # Ordenar por magnitude
    coef_df = coef_df.sort_values(by='Abs_Coef', ascending=False)

    plt.figure(figsize=(10, 8))
    sns.barplot(x='Coeficiente', y='Feature', data=coef_df.head(20), hue='Feature', palette='viridis', legend=False)
    plt.title('Top 20 Features mais Importantes (Coeficientes ElasticNet)', fontweight='bold')
    plt.xlabel('Valor do Coeficiente')
    plt.savefig(f'{output_dir}/feature_importance.png')
    plt.close()
    print(f"Gráfico salvo: {output_dir}/feature_importance.png")

    print("\nTop 5 Features Importantes:")
    print(coef_df[['Feature', 'Coeficiente']].head(5))

if __name__ == "__main__":
    caminho_dataset = 'dataset.csv'
    df = carregar_e_limpar_dados(caminho_dataset)

    if df is not None:
        target_col = 'AT-1100.PV'
        analisar_outliers(df, target_col)

        # Treinamento
        resultados = treinar_modelo(df, target_col)

        # Avaliação
        avaliar_e_visualizar(resultados, target_col)

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from skl2onnx import to_onnx
from skl2onnx.common.data_types import FloatTensorType

DATASET_PATH = 'dataset.csv'
TARGET_COL_AT = 'AT-1100.PV'  # Target Densidade
TARGET_COL_TT = 'TT-1100.PV'  # Target Temperatura

MODEL_FILENAME_AT = 'Densidade_Model.onnx'
MODEL_FILENAME_TT = 'Temperatura_Model.onnx'

# Lista manual de variáveis de interesse (Sensores Chave)
COLS_TO_KEEP = [
    'AT-1100.PV',
    'FT-1004.PV', 'FT-1005.PV',
    'PT-1100.PV', 'PT-1004.PV', 'TT-1004.PV',
    'TT-1005.PV', 'TT-1006.PV', 'TT-1100.PV',
]

def carregar_e_limpar(caminho_arquivo, colunas_desejadas):
    """
    Carrega o dataset, normaliza nomes, filtra colunas seguras e converte tipos.
    """
    print(f"\n[IO] Carregando: {caminho_arquivo}...")
    try:
        df = pd.read_csv(caminho_arquivo, sep=';', decimal=',')
    except Exception as e:
        raise IOError(f"Falha crítica ao abrir arquivo: {e}")

    # 1. Normalização de Nomes (Remove unidades " Value kg/m3")
    df.columns = [col.split(' Value')[0].strip() for col in df.columns]

    # 2. Timestamp como Índice
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df.set_index('Timestamp', inplace=True)
        df.sort_index(inplace=True) # Garante ordem cronológica para TimeSeries

    # 3. Filtragem Segura
    cols_existentes = [c for c in colunas_desejadas if c in df.columns]
    missing = set(colunas_desejadas) - set(cols_existentes)

    if missing:
        print(f"[AVISO] {len(missing)} colunas não encontradas ignoradas: {missing}")

    df_final = df[cols_existentes].copy()

    # 4. Auditoria de SetPoints (.SP)
    sp_cols = [c for c in df_final.columns if '.SP' in c]
    if sp_cols:
        print(f"[ALERTA] Cuidado! Features do tipo SetPoint (.SP) detectadas: {sp_cols}")

    # 5. Otimização de Memória
    cols_float = df_final.select_dtypes(include=['float64']).columns
    df_final[cols_float] = df_final[cols_float].astype('float32')

    print(f"[OK] Dataset carregado. Shape: {df_final.shape}")
    return df_final.dropna()

def treinar_e_exportar(X, y, model_filename, target_name):
    """
    Função genérica para treinar o modelo e exportar para ONNX.
    """
    print(f"\n" + "="*50)
    print(f"TREINAMENTO DO MODELO: {target_name}")
    print("="*50)

    # Divisão Temporal (Train/Test)
    train_size = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

    # Pipeline e GridSearch
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('elastic', ElasticNet(max_iter=5000))
    ])

    param_grid = {
        'elastic__alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
        'elastic__l1_ratio': [0.5, 0.7, 0.9, 0.95, 1.0]}

    tscv = TimeSeriesSplit(n_splits=3)
    grid = GridSearchCV(pipeline, param_grid, cv=tscv, scoring='neg_mean_squared_error', n_jobs=-1)
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_

    # Métricas
    y_pred = best_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    print(f"Melhores parâmetros ({target_name}): {grid.best_params_}")
    print(f"R² ({target_name}): {r2:.4f}")

    # Exportação ONNX
    feature_list = X_train.columns.tolist()
    initial_type = [('input', FloatTensorType([None, len(feature_list)]))]
    onnx_model = to_onnx(best_model, initial_types=initial_type, target_opset=12)

    with open(model_filename, "wb") as f:
        f.write(onnx_model.SerializeToString())

    print(f"[OK] Modelo ONNX exportado: {model_filename}")

    # Mapa de Integração
    print("\n" + "-"*40)
    print(f"MAPA DE MAPEAMENTO ({target_name})")
    print("-"*40)
    for i, tag in enumerate(feature_list):
        print(f"Entrada {i} -> Tag DCS: {tag}")
    print("-"*40)

# =========================================================
# EXECUÇÃO PRINCIPAL
# =========================================================

# 1. Carregamento Geral
df = carregar_e_limpar(DATASET_PATH, COLS_TO_KEEP)

# ---------------------------------------------------------
# MODELO 1: DENSIDADE (AT-1100.PV)
# ---------------------------------------------------------
# Regra: Features = COLS_TO_KEEP exceto o próprio target (AT-1100.PV)
# A variável 'At' (Features) contém tudo menos o target
target_at = TARGET_COL_AT
cols_features_at = [c for c in df.columns if c != target_at]

X_at = df[cols_features_at] # Matriz de características 'At'
y_at = df[target_at]        # Alvo Densidade

treinar_e_exportar(X_at, y_at, MODEL_FILENAME_AT, "DENSIDADE (AT-1100.PV)")

# ---------------------------------------------------------
# MODELO 2: TEMPERATURA (TT-1100.PV)
# ---------------------------------------------------------
# Regra: Features = COLS_TO_KEEP exceto o próprio target (TT-1100.PV)
# E exceto AT-1100.PV (conforme pedido: "tt não deve ter nenhuma influência ou conexão com a leitura de At")
# Ou seja, removemos TT-1100.PV e AT-1100.PV das features.

target_tt = TARGET_COL_TT
cols_features_tt = [c for c in df.columns if c != target_tt and c != TARGET_COL_AT]

X_tt = df[cols_features_tt] # Matriz de características
y_tt = df[target_tt]        # Alvo Temperatura 'tt'

treinar_e_exportar(X_tt, y_tt, MODEL_FILENAME_TT, "TEMPERATURA (TT-1100.PV)")

print("\n[SUCESSO] Processo concluído para ambos os modelos.")

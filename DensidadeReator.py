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
TARGET_COL = 'AT-1100.PV'
MODEL_FILENAME = 'Testparameters.onnx'

# Lista manual de variáveis de interesse (Sensores Chave)
# Nota: Removemos explicitamente .SP e controladores para evitar ruído
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
    return df_final


# 1. Carregamento e Preparação
df = carregar_e_limpar(DATASET_PATH, COLS_TO_KEEP)
X = df.drop(TARGET_COL, axis=1)
y = df[TARGET_COL]

# 2. Divisão Temporal (Train/Test)
train_size = int(len(X) * 0.8)
X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

# 3. Pipeline e GridSearch com TimeSeriesSplit
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

# ---------------------------------------------------------
# 4. EXPORTAÇÃO ONNX COM QUALIDADE INDUSTRIAL
# ---------------------------------------------------------
best_model = grid.best_estimator_
feature_list = X_train.columns.tolist()



initial_type = [('input', FloatTensorType([None, len(feature_list)]))]

# Conversão garantindo Opset 12 (estabilidade industrial)
onnx_model = to_onnx(best_model, initial_types=initial_type, target_opset=12)

with open(MODEL_FILENAME, "wb") as f:
    f.write(onnx_model.SerializeToString())

print(f"\n[OK] Modelo ONNX exportado: {MODEL_FILENAME}")

# ---------------------------------------------------------
# 5. GERAÇÃO DO MAPA DE INTEGRAÇÃO (DOCUMENTAÇÃO)
# ---------------------------------------------------------
print("\n" + "="*50)
print("MAPA DE MAPEAMENTO PARA AVEVA CORP")
print("="*50)
for i, tag in enumerate(feature_list):
    print(f"Entrada {i} (Index {i}) -> Tag DCS: {tag}")
print("="*50)
print("\n" + "="*40)
print("🧪 INICIANDO TESTE DE INDICADORES (VALIDAÇÃO)")
print("="*40)


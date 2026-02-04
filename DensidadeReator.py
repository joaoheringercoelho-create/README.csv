import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet, LinearRegression
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from skl2onnx import to_onnx
from skl2onnx.common.data_types import FloatTensorType
import warnings

warnings.filterwarnings("ignore")

DATASET_PATH = 'dataset.csv'
MODEL_FILENAME = 'Testparameters.onnx'

# --- Definição de Variáveis ---
TARGET_AT = 'AT-1100.PV'  # Output 1
TARGET_TT = 'TT-1100.PV'  # Output 2 (Soft Sensor) E Input (para AT)

# Inputs Base (Sensores Normais)
INPUTS_BASE = [
    'FT-1004.PV', 'FT-1005.PV',
    'PT-1100.PV', 'PT-1004.PV',
    'TT-1004.PV', 'TT-1005.PV', 'TT-1006.PV'
]

# Input Full para o modelo (Base + Sensor TT)
# Importante: TT deve ser o último para facilitar a manipulação da matriz de pesos
INPUTS_FULL = INPUTS_BASE + [TARGET_TT]

def load_data(path):
    print(f"\n[IO] Carregando: {path}...")
    df = pd.read_csv(path, sep=';', decimal=',')
    df.columns = [c.split(' Value')[0].strip() for c in df.columns]

    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df.set_index('Timestamp', inplace=True)
        df.sort_index(inplace=True)

    return df

def train_elasticnet(X, y, name):
    print(f"[Treino] {name}...")
    # GridSearch sem Pipeline interno (dados já escalados) para obter coeficientes diretos
    model = ElasticNet(max_iter=5000)
    grid = GridSearchCV(model, {'alpha': [0.1, 1.0], 'l1_ratio': [0.5, 0.9]},
                        cv=TimeSeriesSplit(n_splits=3), scoring='neg_mean_squared_error', n_jobs=-1)
    grid.fit(X, y)
    print(f"  -> Params: {grid.best_params_}")
    return grid.best_estimator_

# --- Execução Principal ---

# 1. Carga e Preparação
df = load_data(DATASET_PATH)

# Separar X e y
# X_full inclui o sensor TT-1100.PV
X_full = df[INPUTS_FULL].astype('float32')
y_at = df[TARGET_AT].astype('float32')
y_tt = df[TARGET_TT].astype('float32')

# Split 80/20
split = int(len(X_full) * 0.8)
X_train_full = X_full.iloc[:split]
X_test_full = X_full.iloc[split:]
y_at_train = y_at.iloc[:split]
y_at_test = y_at.iloc[split:]
y_tt_train = y_tt.iloc[:split]
y_tt_test = y_tt.iloc[split:]

# 2. Scaling (Global)
# Treinamos o scaler no dataset completo (Full Inputs)
scaler = StandardScaler()
X_train_full_scaled = scaler.fit_transform(X_train_full)
X_test_full_scaled = scaler.transform(X_test_full)

# Recuperar índices das colunas para treino parcial
# INPUTS_BASE são as primeiras N colunas
n_base = len(INPUTS_BASE)
X_train_base_scaled = X_train_full_scaled[:, :n_base]

# 3. Treinamento dos Modelos Individuais

# Modelo A: TT (Soft Sensor)
# Usa apenas INPUTS_BASE (sem ler o próprio sensor TT)
model_tt = train_elasticnet(X_train_base_scaled, y_tt_train, "Temperatura (TT) [Base Inputs]")

# Modelo B: AT (Densidade)
# Usa INPUTS_FULL (Inputs + Sensor TT)
model_at = train_elasticnet(X_train_full_scaled, y_at_train, "Densidade (AT) [Full Inputs]")

# 4. Construção do Modelo Unificado (Proxy)
# Criamos um LinearRegression dummy para conter os pesos combinados
# Output esperado: [AT, TT]
# Matriz de Coeficientes shape: (2, n_inputs_full)

# Coeficientes AT (Linha 0): Copia direta do model_at
coef_at = model_at.coef_

# Coeficientes TT (Linha 1): Copia do model_tt + 0.0 na posição do input TT
coef_tt = np.append(model_tt.coef_, 0.0)

final_coefs = np.vstack([coef_at, coef_tt])
final_intercepts = np.array([model_at.intercept_, model_tt.intercept_])

# Criar estimator "falso" para exportação
proxy_model = LinearRegression()
proxy_model.coef_ = final_coefs
proxy_model.intercept_ = final_intercepts
proxy_model.n_features_in_ = len(INPUTS_FULL)

# Criar Pipeline Final: Scaler -> ProxyModel
final_pipeline = Pipeline([
    ('scaler', scaler),
    ('model', proxy_model)
])

# 5. Exportação ONNX Padrão
# Isso gera um gráfico simples: Scaler -> LinearRegressor -> Output
# Compatibilidade máxima com AVEVA/DCS
initial_type = [('input', FloatTensorType([None, len(INPUTS_FULL)]))]
onnx_model = to_onnx(final_pipeline, initial_types=initial_type, target_opset=12)

with open(MODEL_FILENAME, "wb") as f:
    f.write(onnx_model.SerializeToString())
print(f"\n[OK] Modelo ONNX Padrão exportado: {MODEL_FILENAME}")

# 6. Documentação
print("\n" + "="*60)
print(f"MAPA DE INPUTS (Total: {len(INPUTS_FULL)})")
print("="*60)
for i, col in enumerate(INPUTS_FULL):
    extra_info = " [SENSOR TT]" if col == TARGET_TT else ""
    print(f"Index {i} -> {col:12s}{extra_info} | Range: [{X_train_full[col].min():.2f}, {X_train_full[col].max():.2f}]")

print("\n" + "="*60)
print("MAPA DE OUTPUTS")
print("="*60)
print("Index 0 -> AT-1100.PV (Densidade)   [Lê X + Sensor TT]")
print("Index 1 -> TT-1100.PV (Soft Sensor) [Lê apenas X, ignora Sensor TT]")

# 7. Validação
print("\n[Validação] R² Score (Test Set):")
# Predição usando o pipeline unificado
y_pred_full = final_pipeline.predict(X_test_full)

# y_pred_full[:, 0] é AT
# y_pred_full[:, 1] é TT
r2_at = r2_score(y_at_test, y_pred_full[:, 0])
r2_tt = r2_score(y_tt_test, y_pred_full[:, 1])

print(f"  - Densidade (AT):   {r2_at:.4f}")
print(f"  - Temperatura (TT): {r2_tt:.4f}")

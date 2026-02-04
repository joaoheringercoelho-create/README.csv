import pandas as pd
import numpy as np
import onnx
from onnx import helper
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from skl2onnx import to_onnx
from skl2onnx.common.data_types import FloatTensorType
import warnings

# Suppress sklearn future warnings regarding feature names
warnings.filterwarnings("ignore")

DATASET_PATH = 'dataset.csv'
MODEL_FILENAME = 'Testparameters.onnx'

# Define Targets explicitly
TARGET_TT = 'TT-1100.PV'  # Independent
TARGET_AT = 'AT-1100.PV'  # Dependent on X + TT

# Features
COLS_TO_KEEP = [
    'AT-1100.PV', 'TT-1100.PV', # Targets
    'FT-1004.PV', 'FT-1005.PV',
    'PT-1100.PV', 'PT-1004.PV', 'TT-1004.PV',
    'TT-1005.PV', 'TT-1006.PV',
]

def carregar_e_limpar(caminho_arquivo, colunas_desejadas):
    print(f"\n[IO] Carregando: {caminho_arquivo}...")
    try:
        df = pd.read_csv(caminho_arquivo, sep=';', decimal=',')
    except Exception as e:
        raise IOError(f"Falha crítica ao abrir arquivo: {e}")

    df.columns = [col.split(' Value')[0].strip() for col in df.columns]

    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df.set_index('Timestamp', inplace=True)
        df.sort_index(inplace=True)

    cols_existentes = [c for c in colunas_desejadas if c in df.columns]
    df_final = df[cols_existentes].copy()

    # Check for setpoints
    sp_cols = [c for c in df_final.columns if '.SP' in c]
    if sp_cols:
        print(f"[ALERTA] SetPoints detectados: {sp_cols}")

    cols_float = df_final.select_dtypes(include=['float64']).columns
    df_final[cols_float] = df_final[cols_float].astype('float32')

    return df_final

def train_optimize(X, y, name="Model"):
    print(f"\n[Treino] Otimizando {name}...")
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('elastic', ElasticNet(max_iter=5000))
    ])

    param_grid = {
        'elastic__alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
        'elastic__l1_ratio': [0.5, 0.7, 0.9, 0.95, 1.0]
    }

    tscv = TimeSeriesSplit(n_splits=3)
    grid = GridSearchCV(pipeline, param_grid, cv=tscv, scoring='neg_mean_squared_error', n_jobs=-1)
    grid.fit(X, y)

    print(f"  - Melhores Params: {grid.best_params_}")
    return grid.best_estimator_

def merge_onnx_models(model1, model2):
    """
    Merges two ONNX models sequentially.
    Model 1: X -> TT
    Model 2: [X, TT] -> AT
    Result: X -> [TT, AT]
    """
    # Prefix to avoid collision
    m1 = onnx.compose.add_prefix(model1, prefix="tt_")
    m2 = onnx.compose.add_prefix(model2, prefix="at_")

    m1_in = m1.graph.input[0].name     # Global Input
    m1_out = m1.graph.output[0].name   # TT Output
    m2_in = m2.graph.input[0].name     # Input for Model 2 (Combined)
    m2_out = m2.graph.output[0].name   # AT Output

    # Create Concat Node: [X, TT] -> Combined Input for Model 2
    concat_node = helper.make_node(
        'Concat',
        inputs=[m1_in, m1_out],
        outputs=[m2_in],
        axis=1,
        name='concat_chain'
    )

    # Build merged graph
    all_nodes = list(m1.graph.node) + [concat_node] + list(m2.graph.node)
    all_inits = list(m1.graph.initializer) + list(m2.graph.initializer)
    all_inputs = list(m1.graph.input)
    # Output both targets
    all_outputs = list(m1.graph.output) + list(m2.graph.output)

    graph = helper.make_graph(
        all_nodes,
        "reactor_chained_model",
        all_inputs,
        all_outputs,
        all_inits
    )

    # Use m1 opsets
    model = helper.make_model(graph, producer_name="aveva_reactor_chain", opset_imports=list(m1.opset_import))
    return model

# 1. Carregamento
df = carregar_e_limpar(DATASET_PATH, COLS_TO_KEEP)
targets_all = [TARGET_TT, TARGET_AT]

# X Base (independent vars only)
X = df.drop(targets_all, axis=1)
y_tt = df[[TARGET_TT]]
y_at = df[[TARGET_AT]] # Use dataframe for consistent indexing

# Split
train_size = int(len(X) * 0.8)
X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
y_tt_train, y_tt_test = y_tt.iloc[:train_size], y_tt.iloc[train_size:]
y_at_train, y_at_test = y_at.iloc[:train_size], y_at.iloc[train_size:]

# ---------------------------------------------------------
# 2. MODELAGEM EM CADEIA (CHAINED)
# ---------------------------------------------------------

# Passo A: Treinar Modelo Temperatura (X -> TT)
best_tt = train_optimize(X_train, y_tt_train, name="Temperature (TT)")

# Passo B: Treinar Modelo Densidade (X + TT_real -> AT)
# Teacher Forcing: Usamos o TT real no treino para estabilidade
X_train_aug = pd.concat([X_train, y_tt_train], axis=1)
best_at = train_optimize(X_train_aug, y_at_train, name="Density (AT)")

# ---------------------------------------------------------
# 3. EXPORTAÇÃO ONNX
# ---------------------------------------------------------
# Converter TT Model
initial_type_tt = [('input', FloatTensorType([None, X_train.shape[1]]))]
onnx_tt = to_onnx(best_tt, initial_types=initial_type_tt, target_opset=12)

# Converter AT Model (Input size + 1)
initial_type_at = [('input_aug', FloatTensorType([None, X_train.shape[1] + 1]))]
onnx_at = to_onnx(best_at, initial_types=initial_type_at, target_opset=12)

# Mesclar
final_onnx = merge_onnx_models(onnx_tt, onnx_at)
onnx.checker.check_model(final_onnx)

with open(MODEL_FILENAME, "wb") as f:
    f.write(final_onnx.SerializeToString())

print(f"\n[OK] Modelo ONNX encadeado exportado: {MODEL_FILENAME}")

# ---------------------------------------------------------
# 4. DOCUMENTAÇÃO E MAPA
# ---------------------------------------------------------
print("\n" + "="*60)
print("MAPA DE INTEGRAÇÃO - ESTRUTURA ENCADEADA (CHAINED)")
print("="*60)
print("LÓGICA: TT-1100 é calculado primeiro. AT-1100 usa (Inputs + TT-1100).")
print("\n--- INPUTS (ENTRADAS DO MODELO) ---")
feature_list = X_train.columns.tolist()
for i, tag in enumerate(feature_list):
    min_val = X_train[tag].min()
    max_val = X_train[tag].max()
    print(f"Entrada {i} (Index {i}) -> Tag: {tag:12s} | Range Treino: [{min_val:.2f}, {max_val:.2f}]")

print("\n--- OUTPUTS (SAÍDAS DO ONNX) ---")
print("Saída 0 -> Tag: TT-1100.PV (Temperatura) [Independente]")
print("Saída 1 -> Tag: AT-1100.PV (Densidade)   [Depende de TT]")
print("="*60)

# ---------------------------------------------------------
# 5. AVALIAÇÃO (Simulação da Cadeia)
# ---------------------------------------------------------
print("\n" + "="*40)
print("🧪 AVALIAÇÃO DO MODELO ENCADEADO (TEST SET)")
print("="*40)

# 1. Prever TT
pred_tt = best_tt.predict(X_test)
# Ajustar shape para concatenação (se necessário)
if pred_tt.ndim == 1: pred_tt = pred_tt.reshape(-1, 1)

# 2. Montar Input para AT (Usando TT predito!)
# Nota: Aqui usamos TT predito, não o real, para simular a produção
pred_tt_df = pd.DataFrame(pred_tt, index=X_test.index, columns=[TARGET_TT])
X_test_aug = pd.concat([X_test, pred_tt_df], axis=1)

# 3. Prever AT
pred_at = best_at.predict(X_test_aug)

# Métricas TT
mae_tt = mean_absolute_error(y_tt_test, pred_tt)
r2_tt = r2_score(y_tt_test, pred_tt)
print(f"\n📈 Target: {TARGET_TT} (Temperatura)")
print(f"   - R² Score: {r2_tt:.4f}")
print(f"   - MAE:      {mae_tt:.4f}")

# Métricas AT
mae_at = mean_absolute_error(y_at_test, pred_at)
r2_at = r2_score(y_at_test, pred_at)
print(f"\n📈 Target: {TARGET_AT} (Densidade)")
print(f"   - R² Score: {r2_at:.4f}")
print(f"   - MAE:      {mae_at:.4f}")
print(f"   (Obs: AT calculada usando TT predito)")

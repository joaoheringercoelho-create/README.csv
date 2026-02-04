import pandas as pd
import numpy as np
import onnx
from onnx import helper
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from skl2onnx import to_onnx
from skl2onnx.common.data_types import FloatTensorType
import warnings

warnings.filterwarnings("ignore")

DATASET_PATH = 'dataset.csv'
MODEL_FILENAME = 'Testparameters.onnx'

# Configuração de Variáveis
TARGET_TT = 'TT-1100.PV'  # Variável independente
TARGET_AT = 'AT-1100.PV'  # Variável dependente (usa X + TT)
COLS = [TARGET_AT, TARGET_TT, 'FT-1004.PV', 'FT-1005.PV', 'PT-1100.PV', 'PT-1004.PV', 'TT-1004.PV', 'TT-1005.PV', 'TT-1006.PV']

def load_data(path, cols):
    """Carrega e limpa o dataset."""
    print(f"\n[IO] Carregando: {path}...")
    df = pd.read_csv(path, sep=';', decimal=',')
    df.columns = [c.split(' Value')[0].strip() for c in df.columns]

    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df.set_index('Timestamp', inplace=True)
        df.sort_index(inplace=True)

    return df[ [c for c in cols if c in df.columns] ].astype('float32')

def train_model(X, y, name):
    """Treina ElasticNet com GridSearchCV."""
    print(f"[Treino] {name}...")
    pipe = Pipeline([('scaler', StandardScaler()), ('elastic', ElasticNet(max_iter=5000))])
    grid = GridSearchCV(pipe, {'elastic__alpha': [0.1, 1.0], 'elastic__l1_ratio': [0.5, 0.9]},
                        cv=TimeSeriesSplit(n_splits=3), scoring='neg_mean_squared_error', n_jobs=-1)
    grid.fit(X, y)
    print(f"  -> Params: {grid.best_params_}")
    return grid.best_estimator_

def merge_onnx(m1, m2):
    """Mescla dois modelos ONNX: M1(X->TT) e M2(X+TT->AT) em um único grafo."""
    m1 = onnx.compose.add_prefix(m1, "tt_")
    m2 = onnx.compose.add_prefix(m2, "at_")

    # Cria nó de concatenação: [Input_Global, Output_M1] -> Input_M2
    concat = helper.make_node('Concat', inputs=[m1.graph.input[0].name, m1.graph.output[0].name],
                              outputs=[m2.graph.input[0].name], axis=1, name='link_tt_to_at')

    # Monta grafo final
    graph = helper.make_graph(
        list(m1.graph.node) + [concat] + list(m2.graph.node),
        "chained_model",
        list(m1.graph.input),
        list(m1.graph.output) + list(m2.graph.output), # Outputs: TT, AT
        list(m1.graph.initializer) + list(m2.graph.initializer)
    )
    return helper.make_model(graph, producer_name="reactor_chain", opset_imports=list(m1.opset_import))

# --- Execução Principal ---

# 1. Preparação dos Dados
df = load_data(DATASET_PATH, COLS)
X = df.drop([TARGET_TT, TARGET_AT], axis=1)
y_tt = df[[TARGET_TT]]
y_at = df[[TARGET_AT]]

# Split Temporal (80/20)
split = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_tt_train, y_tt_test = y_tt.iloc[:split], y_tt.iloc[split:]
y_at_train, y_at_test = y_at.iloc[:split], y_at.iloc[split:]

# 2. Treinamento em Cadeia
# Modelo 1: Preve Temperatura baseado nos sensores
model_tt = train_model(X_train, y_tt_train, "Temperatura (TT)")

# Modelo 2: Preve Densidade baseado nos sensores + Temperatura Real (Teacher Forcing)
X_aug_train = pd.concat([X_train, y_tt_train], axis=1)
model_at = train_model(X_aug_train, y_at_train, "Densidade (AT)")

# 3. Exportação e Fusão ONNX
onnx_tt = to_onnx(model_tt, initial_types=[('in', FloatTensorType([None, X.shape[1]]))], target_opset=12)
onnx_at = to_onnx(model_at, initial_types=[('in_aug', FloatTensorType([None, X.shape[1]+1]))], target_opset=12)
final_onnx = merge_onnx(onnx_tt, onnx_at)

with open(MODEL_FILENAME, "wb") as f:
    f.write(final_onnx.SerializeToString())
print(f"\n[OK] Modelo ONNX salvo: {MODEL_FILENAME}")

# 4. Documentação para Simulador
print("\n" + "="*60)
print(f"MAPA DE INPUTS (Total: {X.shape[1]} inputs)")
print("="*60)
for i, col in enumerate(X_train.columns):
    print(f"Index {i} -> {col:12s} | Range Treino: [{X_train[col].min():.2f}, {X_train[col].max():.2f}]")

print("\n" + "="*60)
print("MAPA DE OUTPUTS (ONNX)")
print("="*60)
print("Index 0 -> TT-1100.PV (Temperatura) [Independente]")
print("Index 1 -> AT-1100.PV (Densidade)   [Depende de TT]")

# 5. Validação Rápida
print("\n[Validação] R² Score no Test Set:")
p_tt = model_tt.predict(X_test)
p_at = model_at.predict(pd.concat([X_test, pd.DataFrame(p_tt, index=X_test.index, columns=[TARGET_TT])], axis=1))

print(f"  - Temperatura: {r2_score(y_tt_test, p_tt):.4f}")
print(f"  - Densidade:   {r2_score(y_at_test, p_at):.4f}")

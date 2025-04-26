from prefect import flow, task
from prefect.settings import PREFECT_API_URL, temporary_settings
import pandas as pd
import numpy as np
import math
import joblib
import mlflow
import matplotlib.pyplot as plt
import seaborn as sns

from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report


@task
def mlflow_init():
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("FinalXGB_vs_SnapshotEnsemble_CV")


# @task
# def load_data():
#     df = pd.read_csv("train_dataset.csv")
#     X = df.drop("label", axis=1)
#     y = df["label"]
#     return X, y

from minio import Minio
from io import BytesIO
import pandas as pd
from prefect import task

@task
def load_data():
    try:
            
        # Connect to MinIO
        client = Minio(
            "http://localhost:9001",  # e.g., "localhost:9000"
            access_key="minio",
            secret_key="minio123",
            secure=False  # set to True if using HTTPS
        )

        # Download the object
        response = client.get_object(
            bucket_name="test",
            object_name="train_dataset.csv"
        )

        # Read into pandas
        df = pd.read_csv(BytesIO(response.read()))
        response.close()
        response.release_conn()

        X = df.drop("label", axis=1)
        y = df["label"]

        return X, y
    except:
        df = pd.read_csv("train_dataset.csv")
        X = df.drop("label", axis=1)
        y = df["label"]
        return X, y


@task
def youden_j_statistic(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    sensitivity = tp / (tp + fn)
    specificity = tn / (tn + fp)
    return sensitivity + specificity - 1

@task
def plot_conf_matrix(y_true, y_pred, title):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots()
    sns.heatmap(cm, annot=True, fmt='d', cmap="Blues", ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    return fig

@task
def evaluate_cv_model(model_func, X, y, name, is_ensemble=False):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    preds_all, true_all = [], []

    for train_idx, test_idx in skf.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = model_func(X_train, y_train)

        if is_ensemble:
            preds = np.array([m.predict(X_test) for m in model])
            y_pred = np.round(np.mean(preds, axis=0)).astype(int)
        else:
            y_pred = model.predict(X_test)

        preds_all.extend(y_pred)
        true_all.extend(y_test)

    # Evaluation
    acc = accuracy_score(true_all, preds_all)
    f1 = f1_score(true_all, preds_all, average='weighted')
    j = youden_j_statistic(true_all, preds_all)

    mlflow.log_metrics({
        f"{name}_acc": acc,
        f"{name}_f1": f1,
        f"{name}_j": j
    })

    print(f"📊 {name.upper()} | Accuracy: {acc:.4f}, F1: {f1:.4f}, Youden's J: {j:.4f}")
    print(classification_report(true_all, preds_all))

    fig = plot_conf_matrix(true_all, preds_all, f"{name} Confusion Matrix")
    fig_path = f"{name}_conf_matrix.png"
    fig.savefig(fig_path)
    mlflow.log_artifact(fig_path)

    return model

@task
def train_xgb_full(X_train, y_train):
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', verbosity=0)
    model.fit(X_train, y_train)
    return model

@task
def train_snapshot_ensemble_full(X_train, y_train, num_snapshots=5, total_estimators=500):
    models = []
    base_lr = 0.1
    estimators_per_snapshot = total_estimators // num_snapshots

    for i in range(num_snapshots):
        lr = base_lr * 0.5 * (1 + math.cos(math.pi * i / num_snapshots))
        model = XGBClassifier(
            n_estimators=estimators_per_snapshot,
            learning_rate=lr,
            max_depth=6,
            use_label_encoder=False,
            eval_metric='logloss',
            verbosity=0
        )
        model.fit(X_train, y_train)
        models.append(model)
    return models


@flow(name="final_xgb_and_snapshot_cv")
def main():
    mlflow_init()
    X, y = load_data()

    with mlflow.start_run(run_name="Final_XGBoost_Eval"):
        model = evaluate_cv_model(train_xgb_full, X, y, "xgboost")
        joblib.dump(model, "xgb_final_model.pkl")
        mlflow.log_artifact("xgb_final_model.pkl")

    with mlflow.start_run(run_name="Final_Snapshot_Ensemble_Eval"):
        ensemble_models = evaluate_cv_model(train_snapshot_ensemble_full, X, y, "snapshot", is_ensemble=True)
        joblib.dump(ensemble_models, "snapshot_final_models.pkl")
        mlflow.log_artifact("snapshot_final_models.pkl")


if __name__ == "__main__":
    with temporary_settings({PREFECT_API_URL: "http://Prefect:4200/api"}):
        main()

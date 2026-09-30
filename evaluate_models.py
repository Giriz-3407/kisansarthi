"""
=============================================================================
KisanSarthi - ML Model Evaluation & Benchmarking Suite
=============================================================================
This script provides comprehensive evaluation metrics and benchmark test runs
for the KisanSarthi backend Machine Learning models:
  1. Crop Suggestion Model (crop_model.pkl)
  2. Fertilizer Recommendation Model (fertilizer.pkl)

Supported Metrics:
  - Accuracy & Balanced Accuracy
  - Precision (Macro, Weighted, Micro, Per-Class)
  - Recall / Sensitivity (Macro, Weighted, Micro, Per-Class)
  - F1-Score & F-beta Score (Macro, Weighted, Micro)
  - Top-1, Top-2, Top-3, and Top-5 Accuracy
  - Matthews Correlation Coefficient (MCC)
  - Cohen's Kappa Coefficient
  - Cross-Entropy / Multi-class Log Loss
  - ROC-AUC Score (One-vs-Rest)
  - Confusion Matrix & Classification Report

Usage:
  py kisansarthi/evaluate_models.py --model all
  py kisansarthi/evaluate_models.py --model crop
  py kisansarthi/evaluate_models.py --model fertilizer
  py kisansarthi/evaluate_models.py --run-sample-inference
=============================================================================
"""

import sys
import os
import argparse
import json
import numpy as np

# Configure console encoding for Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agents.pandas_compat
from agents.pandas_compat import pd
import joblib
import pickle
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    matthews_corrcoef,
    cohen_kappa_score,
    log_loss,
    top_k_accuracy_score
)

# Paths to models
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CROP_MODEL_PATH = os.path.join(BASE_DIR, 'agents', 'model', 'crop_model.pkl')
FERT_MODEL_PATH = os.path.join(BASE_DIR, 'agents', 'model', 'fertilizer.pkl')


def load_crop_model():
    """Loads and returns the trained Crop Suggestion RandomForestClassifier model."""
    if not os.path.exists(CROP_MODEL_PATH):
        raise FileNotFoundError(f"Crop model not found at: {CROP_MODEL_PATH}")
    return joblib.load(CROP_MODEL_PATH)


def load_fertilizer_model():
    """Loads and returns the trained Fertilizer Recommendation RandomForestClassifier model."""
    if not os.path.exists(FERT_MODEL_PATH):
        raise FileNotFoundError(f"Fertilizer model not found at: {FERT_MODEL_PATH}")
    with open(FERT_MODEL_PATH, 'rb') as f:
        return pickle.load(f)


def generate_crop_benchmark_dataset(n_samples_per_class=20, random_seed=42):
    """
    Generates a realistic agronomic evaluation dataset across standard Indian crop profiles
    covering N, P, K, temperature, humidity, pH, and rainfall distributions.
    """
    np.random.seed(random_seed)
    
    # Agronomic profiles for major crops [N_mean, P_mean, K_mean, temp_mean, hum_mean, ph_mean, rain_mean]
    profiles = {
        'rice':        [80, 48, 40, 24.0, 82.0, 6.4, 235.0],
        'maize':       [78, 48, 20, 22.5, 65.0, 6.2, 85.0],
        'chickpea':    [40, 68, 80, 18.8, 17.0, 7.3, 80.0],
        'kidneybeans': [21, 68, 20, 20.1, 21.6, 5.7, 106.0],
        'pigeonpeas':  [21, 68, 20, 27.7, 48.1, 5.8, 149.0],
        'mothbeans':   [21, 48, 20, 28.2, 53.2, 6.8, 51.2],
        'mungbean':    [21, 48, 20, 28.5, 85.5, 6.7, 48.4],
        'blackgram':   [40, 68, 20, 30.0, 65.0, 7.1, 68.0],
        'lentil':      [19, 68, 19, 24.5, 64.8, 6.9, 45.6],
        'pomegranate': [19, 19, 40, 21.8, 90.1, 6.4, 107.5],
        'banana':      [100, 75, 50, 27.4, 80.4, 6.0, 104.6],
        'mango':       [20, 27, 30, 31.2, 50.2, 5.8, 94.7],
        'grapes':      [23, 133, 201, 23.8, 81.9, 6.0, 69.6],
        'watermelon':  [99, 17, 50, 25.6, 85.2, 6.5, 50.8],
        'muskmelon':   [100, 18, 50, 28.6, 92.3, 6.3, 24.7],
        'apple':       [21, 134, 200, 22.6, 92.3, 5.9, 112.7],
        'orange':      [20, 16, 10, 22.8, 92.2, 7.0, 110.4],
        'papaya':      [50, 59, 50, 33.7, 92.4, 6.7, 142.6],
        'coconut':     [22, 17, 31, 27.4, 94.9, 6.0, 175.7],
        'cotton':      [118, 46, 20, 24.0, 79.8, 6.9, 80.4],
        'jute':        [78, 46, 40, 25.0, 79.6, 6.7, 174.8],
        'coffee':      [101, 29, 30, 25.5, 58.9, 6.8, 158.1],
        'wheat':       [90, 50, 40, 19.5, 60.0, 6.5, 60.0],
        'sugarcane':   [120, 60, 60, 28.0, 75.0, 6.8, 120.0],
        'groundnut':   [40, 60, 40, 26.0, 60.0, 6.0, 70.0],
        'tea':         [80, 40, 40, 22.0, 85.0, 5.5, 200.0],
        'tobacco':     [70, 50, 60, 27.0, 70.0, 6.5, 90.0],
        'millet':      [50, 30, 25, 30.0, 45.0, 7.0, 45.0],
        'peas':        [30, 55, 35, 18.0, 55.0, 6.5, 65.0],
        'adzuki':      [25, 50, 20, 23.0, 60.0, 6.2, 75.0],
        'rubber':      [60, 35, 30, 27.0, 82.0, 5.8, 220.0],
    }

    feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    records = []
    labels = []

    for crop, prof in profiles.items():
        for _ in range(n_samples_per_class):
            # Add realistic gaussian noise to features
            noise = np.random.normal(0, [5.0, 5.0, 5.0, 1.2, 3.0, 0.25, 10.0])
            sample = np.maximum([prof[i] + noise[i] for i in range(7)], 0.1)
            records.append({
                'N': sample[0],
                'P': sample[1],
                'K': sample[2],
                'temperature': sample[3],
                'humidity': min(100.0, sample[4]),
                'ph': min(14.0, max(3.0, sample[5])),
                'rainfall': sample[6]
            })
            labels.append(crop)

    df_x = pd.DataFrame(records, columns=feature_cols)
    return df_x, np.array(labels)


def generate_fertilizer_benchmark_dataset(n_samples_per_class=25, random_seed=42):
    """
    Generates an evaluation dataset for the Fertilizer Model covering soil colors,
    nutrient levels, pH, rainfall, temperature, and crop identifiers.
    """
    np.random.seed(random_seed)
    
    # Feature columns: ['Soil_color', 'Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'Rainfall', 'Temperature', 'Crop']
    # 19 target classes for fertilizer recommendations
    feature_cols = ['Soil_color', 'Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'Rainfall', 'Temperature', 'Crop']
    records = []
    labels = []

    for fert_class in range(1, 20):
        for _ in range(n_samples_per_class):
            soil_color = np.random.choice([0, 1, 2, 3, 4])
            crop = np.random.choice(range(1, 17))
            n_val = np.random.randint(10, 140)
            p_val = np.random.randint(10, 140)
            k_val = np.random.randint(10, 140)
            ph_val = round(np.random.uniform(5.0, 8.5), 2)
            rainfall = round(np.random.uniform(40.0, 250.0), 1)
            temp = round(np.random.uniform(15.0, 38.0), 1)

            records.append({
                'Soil_color': soil_color,
                'Nitrogen': n_val,
                'Phosphorus': p_val,
                'Potassium': k_val,
                'pH': ph_val,
                'Rainfall': rainfall,
                'Temperature': temp,
                'Crop': crop
            })
            labels.append(fert_class)

    df_x = pd.DataFrame(records, columns=feature_cols)
    return df_x, np.array(labels)


def evaluate_classification_model(model, X_test, y_true, model_name="Model", top_k=(1, 3, 5)):
    """
    Computes a full suite of classification evaluation metrics for a multi-class model.
    """
    print("\n" + "=" * 80)
    print(f"📊 EVALUATION REPORT: {model_name.upper()}")
    print("=" * 80)
    
    # Predictions & Probabilities
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    classes = list(model.classes_)
    
    # 1. Overall & Balanced Accuracy
    acc = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    
    # 2. Precision (Macro, Weighted, Micro)
    prec_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    prec_weighted = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    prec_micro = precision_score(y_true, y_pred, average='micro', zero_division=0)
    
    # 3. Recall / Sensitivity (Macro, Weighted, Micro)
    rec_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
    rec_weighted = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    rec_micro = recall_score(y_true, y_pred, average='micro', zero_division=0)
    
    # 4. F1-Score (Macro, Weighted, Micro)
    f1_mac = f1_score(y_true, y_pred, average='macro', zero_division=0)
    f1_wt = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    f1_mic = f1_score(y_true, y_pred, average='micro', zero_division=0)
    
    # 5. Matthews Correlation Coefficient (MCC) & Cohen's Kappa
    mcc = matthews_corrcoef(y_true, y_pred)
    kappa = cohen_kappa_score(y_true, y_pred)
    
    # 6. Top-K Accuracies
    top_k_results = {}
    for k in top_k:
        if k <= len(classes):
            top_k_results[f"Top-{k} Accuracy"] = top_k_accuracy_score(
                y_true, y_prob, k=k, labels=classes
            )
            
    # 7. Log Loss (Cross-Entropy)
    try:
        ce_loss = log_loss(y_true, y_prob, labels=classes)
    except Exception:
        ce_loss = None

    # Print Formatted Metric Summary Table
    print("\n--- 1. OVERALL PERFORMANCE METRICS ---")
    print(f"{'Metric':<35} | {'Value':<12} | {'Description / Interpretation':<40}")
    print("-" * 80)
    print(f"{'Accuracy (Overall)':<35} | {acc:.4f} ({acc*100:.2f}%) | Correctly classified instances / Total")
    print(f"{'Balanced Accuracy':<35} | {bal_acc:.4f} ({bal_acc*100:.2f}%) | Macro-average recall across all classes")
    print(f"{'Precision (Macro)':<35} | {prec_macro:.4f}       | Unweighted mean precision across classes")
    print(f"{'Precision (Weighted)':<35} | {prec_weighted:.4f}    | Support-weighted mean precision")
    print(f"{'Recall (Macro)':<35} | {rec_macro:.4f}          | Unweighted mean sensitivity / recall")
    print(f"{'Recall (Weighted)':<35} | {rec_weighted:.4f}       | Support-weighted mean sensitivity / recall")
    print(f"{'F1-Score (Macro)':<35} | {f1_mac:.4f}          | Harmonic mean of macro precision & recall")
    print(f"{'F1-Score (Weighted)':<35} | {f1_wt:.4f}           | Harmonic mean weighted by class support")
    print(f"{'Matthews Correlation (MCC)':<35} | {mcc:.4f}     | Balanced quality metric (-1 to +1)")
    print(f"{'Cohen\'s Kappa (κ)':<35} | {kappa:.4f}           | Inter-rater agreement above chance")
    if ce_loss is not None:
        print(f"{'Multi-class Log Loss':<35} | {ce_loss:.4f}     | Cross-entropy loss of predicted probabilities")
        
    for name, val in top_k_results.items():
        print(f"{name:<35} | {val:.4f} ({val*100:.2f}%) | True label is within the top-{name.split('-')[1].split()[0]} predictions")

    # 8. Detailed Classification Report (Per-Class)
    print("\n--- 2. DETAILED CLASSIFICATION REPORT (PER-CLASS BREAKDOWN) ---")
    report = classification_report(y_true, y_pred, zero_division=0)
    print(report)

    # 9. Confusion Matrix Summary
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    print("--- 3. CONFUSION MATRIX SUMMARY ---")
    print(f"Total Test Instances: {len(y_true)}")
    print(f"Total Classes: {len(classes)}")
    print(f"Matrix Dimensions: {cm.shape[0]}x{cm.shape[1]}")
    diagonal_sum = np.trace(cm)
    print(f"True Positive Classifications (Diagonal): {diagonal_sum} / {len(y_true)} ({diagonal_sum/len(y_true)*100:.2f}%)")

    metrics_dict = {
        "model_name": model_name,
        "accuracy": float(acc),
        "balanced_accuracy": float(bal_acc),
        "precision_macro": float(prec_macro),
        "precision_weighted": float(prec_weighted),
        "recall_macro": float(rec_macro),
        "recall_weighted": float(rec_weighted),
        "f1_macro": float(f1_mac),
        "f1_weighted": float(f1_wt),
        "matthews_corrcoef": float(mcc),
        "cohen_kappa": float(kappa),
        "top_k_accuracies": {k: float(v) for k, v in top_k_results.items()},
        "log_loss": float(ce_loss) if ce_loss is not None else None,
        "total_test_samples": int(len(y_true)),
        "num_classes": int(len(classes))
    }
    return metrics_dict


def run_sample_inference_demo():
    """
    Runs sample test cases against both backend models and displays prediction results.
    """
    print("\n" + "=" * 80)
    print("🚀 RUNNING SAMPLE INFERENCE ON BACKEND MODELS")
    print("=" * 80)
    
    # Crop Model Inference
    print("\n[1] Testing Crop Suggestion Model:")
    crop_model = load_crop_model()
    
    test_cases = [
        {"desc": "High moisture & warm (Paddy/Rice condition)", "input": {'N': 85, 'P': 45, 'K': 40, 'temperature': 24.5, 'humidity': 82.0, 'ph': 6.5, 'rainfall': 220.0}},
        {"desc": "Moderate rainfall & dry (Maize condition)",   "input": {'N': 75, 'P': 45, 'K': 20, 'temperature': 22.0, 'humidity': 65.0, 'ph': 6.2, 'rainfall': 85.0}},
        {"desc": "Cool & low humidity (Chickpea condition)",    "input": {'N': 40, 'P': 65, 'K': 80, 'temperature': 18.5, 'humidity': 18.0, 'ph': 7.2, 'rainfall': 75.0}},
    ]
    
    for idx, case in enumerate(test_cases, 1):
        df_input = pd.DataFrame([case["input"]], columns=['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall'])
        pred = crop_model.predict(df_input)[0]
        probs = crop_model.predict_proba(df_input)[0]
        top3_indices = probs.argsort()[-3:][::-1]
        top3 = [(crop_model.classes_[i], round(float(probs[i]), 4)) for i in top3_indices]
        
        print(f"\n  Test Case {idx}: {case['desc']}")
        print(f"  Input Features : {case['input']}")
        print(f"  Predicted Crop : {pred}")
        print(f"  Top 3 Ranked   : {top3}")

    # Fertilizer Model Inference
    print("\n[2] Testing Fertilizer Recommendation Model:")
    fert_model = load_fertilizer_model()
    
    fert_cases = [
        {"desc": "Black soil, Rice crop with NPK inputs", "input": {'Soil_color': 1, 'Nitrogen': 75, 'Phosphorus': 50, 'Potassium': 50, 'pH': 6.2, 'Rainfall': 140.0, 'Temperature': 28.0, 'Crop': 4}},
        {"desc": "Red soil, Cotton crop with NPK inputs", "input": {'Soil_color': 0, 'Nitrogen': 110, 'Phosphorus': 40, 'Potassium': 25, 'pH': 6.8, 'Rainfall': 80.0, 'Temperature': 26.0, 'Crop': 3}},
    ]
    
    for idx, case in enumerate(fert_cases, 1):
        df_input = pd.DataFrame([case["input"]], columns=['Soil_color', 'Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'Rainfall', 'Temperature', 'Crop'])
        pred = fert_model.predict(df_input)[0]
        probs = fert_model.predict_proba(df_input)[0]
        top3_idx = probs.argsort()[-3:][::-1]
        top3 = [(int(fert_model.classes_[i]), round(float(probs[i]), 4)) for i in top3_idx]
        
        print(f"\n  Fertilizer Case {idx}: {case['desc']}")
        print(f"  Input Features  : {case['input']}")
        print(f"  Predicted Class : Fertilizer #{pred}")
        print(f"  Top 3 Ranked    : {top3}")


def main():
    parser = argparse.ArgumentParser(description="KisanSarthi ML Model Evaluation Suite")
    parser.add_argument(
        "--model",
        type=str,
        default="all",
        choices=["all", "crop", "fertilizer"],
        help="Which model to evaluate (default: all)"
    )
    parser.add_argument(
        "--run-sample-inference",
        action="store_true",
        help="Run interactive test sample inferences"
    )
    parser.add_argument(
        "--save-report",
        type=str,
        default=None,
        help="File path to save JSON metrics report"
    )
    
    args = parser.parse_args()
    
    all_results = {}
    
    if args.run_sample_inference:
        run_sample_inference_demo()
        return

    # Evaluate Crop Model
    if args.model in ["all", "crop"]:
        print("\nLoading Crop Suggestion Model...")
        crop_model = load_crop_model()
        X_crop, y_crop = generate_crop_benchmark_dataset(n_samples_per_class=30)
        crop_results = evaluate_classification_model(
            model=crop_model,
            X_test=X_crop,
            y_true=y_crop,
            model_name="Crop Suggestion Model (RandomForest, 31 Classes)",
            top_k=(1, 2, 3, 5)
        )
        all_results["crop_model"] = crop_results

    # Evaluate Fertilizer Model
    if args.model in ["all", "fertilizer"]:
        print("\nLoading Fertilizer Recommendation Model...")
        fert_model = load_fertilizer_model()
        X_fert, y_fert = generate_fertilizer_benchmark_dataset(n_samples_per_class=30)
        fert_results = evaluate_classification_model(
            model=fert_model,
            X_test=X_fert,
            y_true=y_fert,
            model_name="Fertilizer Recommendation Model (RandomForest, 19 Classes)",
            top_k=(1, 2, 3)
        )
        all_results["fertilizer_model"] = fert_results

    # Run inference demo
    run_sample_inference_demo()

    # Save report if requested
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n✅ Evaluation report saved to: {args.save_report}")


if __name__ == "__main__":
    main()

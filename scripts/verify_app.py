"""Automated test script to verify app/streamlit_app.py logic and safety guards."""

import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.streamlit_app import (
    load_classical_assets,
    load_deep_learning_assets,
    load_sample_gallery,
    preprocess_image_for_cnn,
    evaluate_deep_ood_gate,
    evaluate_classical_ood_gate,
    CLASSES,
)
from src.baseline_ml import extract_features_single


def test_app_pipeline():
    print("=" * 80)
    print("VERIFYING KUKUGUARD STREAMLIT APPLICATION LOGIC & GATES")
    print("=" * 80)

    # 1. Load assets
    print("Loading assets...")
    svm_model, scaler, class_proto, center_indices = load_classical_assets()
    ort_session, pytorch_model, gradcam_engine, temp, cnn_proto, ood_cfg = load_deep_learning_assets()
    gallery = load_sample_gallery()
    print(f"Loaded successfully! Gallery contains {len(gallery)} samples.")

    # 2. Test In-Distribution Sample (Coccidiosis)
    cocci_sample = [s for s in gallery if s["id"] == "cocci_01"][0]
    img_path = PROJECT_ROOT / "app" / "samples" / cocci_sample["filename"]
    img = Image.open(img_path)
    cnn_np, cnn_tensor = preprocess_image_for_cnn(img)

    # OOD check Option A
    out = ort_session.run(["logits", "features"], {"input": cnn_np})
    logits, feats = out[0][0], out[1]
    is_ood_a, score_a = evaluate_deep_ood_gate(feats, cnn_proto, threshold=-0.4585)
    print(f"\n[Test ID Sample] Option A OOD Check: is_ood={is_ood_a}, score={score_a:.4f} (Expected: False)")
    assert not is_ood_a, "Error: Valid Coccidiosis sample was wrongly rejected!"

    # Classical diagnosis
    feat_410 = extract_features_single(str(img_path))
    feat_205 = np.nan_to_num(feat_410[center_indices], nan=0.0).reshape(1, -1)
    feat_205_scaled = scaler.transform(feat_205)
    pred_class = CLASSES[int(svm_model.predict(feat_205_scaled)[0])]
    print(f"[Test ID Sample] Primary SVM Prediction: {pred_class} (Expected: Coccidiosis)")
    assert pred_class == "Coccidiosis", f"Error: Expected Coccidiosis, got {pred_class}"

    # Grad-CAM
    cam = gradcam_engine.generate_heatmap(cnn_tensor, target_class=0)
    assert cam.shape == (224, 224), f"Error: Heatmap shape {cam.shape} != (224, 224)"
    print("[Test ID Sample] Grad-CAM generated successfully (shape 224x224).")

    # 3. Test OOD Sample (Rubber Boot)
    boot_sample = [s for s in gallery if s["id"] == "ood_boot_01"][0]
    boot_path = PROJECT_ROOT / "app" / "samples" / boot_sample["filename"]
    boot_img = Image.open(boot_path)
    boot_cnn_np, _ = preprocess_image_for_cnn(boot_img)

    boot_out = ort_session.run(["logits", "features"], {"input": boot_cnn_np})
    boot_logits, boot_feats = boot_out[0][0], boot_out[1]
    boot_is_ood_a, boot_score_a = evaluate_deep_ood_gate(boot_feats, cnn_proto, threshold=-0.4585)
    print(f"\n[Test OOD Sample] Rubber Boot Option A OOD Check: is_ood={boot_is_ood_a}, score={boot_score_a:.4f} (Expected: True)")
    assert boot_is_ood_a, "Error: Rubber boot failed to be rejected by Option A OOD gate!"

    # Option B OOD check on Boot
    boot_feat_410 = extract_features_single(str(boot_path))
    boot_feat_205 = np.nan_to_num(boot_feat_410[center_indices], nan=0.0).reshape(1, -1)
    boot_scaled = scaler.transform(boot_feat_205)
    boot_is_ood_b, boot_score_b = evaluate_classical_ood_gate(boot_scaled, class_proto, threshold=-10.9736)
    print(f"[Test OOD Sample] Rubber Boot Option B OOD Check: is_ood={boot_is_ood_b}, score={boot_score_b:.4f} (Expected: True)")
    assert boot_is_ood_b, "Error: Rubber boot failed to be rejected by Option B OOD gate!"

    # 4. Test Corrupt File Handling
    corrupt_file = PROJECT_ROOT / "app" / "corrupt_test.jpg"
    corrupt_file.write_text("This is not a real jpeg file.")
    try:
        c_img = Image.open(corrupt_file)
        c_img.verify()
        passed_corrupt = True
    except Exception:
        passed_corrupt = False
    corrupt_file.unlink()
    print(f"\n[Corrupt File Test] Handled gracefully: {not passed_corrupt} (Expected: True)")
    assert not passed_corrupt, "Corrupt file was not caught!"

    print("\n" + "=" * 80)
    print("ALL APP UNIT & PIPELINE TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    test_app_pipeline()

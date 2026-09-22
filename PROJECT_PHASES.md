# Poultry Disease Detection from Faecal Images — Project Phases

**Goal:** A 4-class image classifier (Healthy / Coccidiosis / Newcastle Disease / Salmonella) trained on PCR-verified chicken faecal images, with explainability, calibrated confidence, OOD rejection, and a demo app.

**Stack (locked):** Python 3.10+, **PyTorch + timm**, scikit-learn, OpenCV, imagehash, networkx, XGBoost, SHAP, onnxruntime, Streamlit. Do not introduce TensorFlow/Keras anywhere in this project.

---

## Ground rules for the agent

- Work **one phase at a time**. Do not start the next phase until the user says so.
- At the end of every phase: print a short summary of what was created, the numbers produced, and anything that looked wrong.
- Never fabricate metrics. If a script wasn't run, say so.
- All randomness seeded (`SEED = 42`) and set in one place.
- No notebook-only code. Every phase produces runnable `.py` scripts; notebooks are optional extras.
- Keep config in `config.yaml`, not hardcoded across files.
- Log every training run to `runs/<timestamp>/` with config, metrics JSON, and weights.
- **No MixUp, no CutMix, ever.** Blending a bloody mucoid Coccidiosis stool with a normal one produces an image that cannot exist biologically and corrupts the gradient signal. This is a hard ban, not a preference.

---

## Target repo layout

```
poultry-disease-detection/
├── config.yaml
├── requirements.txt
├── README.md
├── scripts/
│   └── download_data.py
├── data/
│   ├── raw/              # ALL images, flattened, no upstream split folders
│   ├── manifest.csv
│   ├── splits/           # train.csv / val.csv / test.csv (path,label,group_id)
│   └── .gitignore
├── src/
│   ├── config.py
│   ├── dedup.py          # phash → graph → connected components → group_id
│   ├── data.py           # dataset, transforms, loaders, samplers
│   ├── model.py
│   ├── losses.py         # weighted CE + focal loss
│   ├── train.py
│   ├── evaluate.py
│   ├── calibrate.py      # ECE + temperature scaling
│   ├── gradcam.py
│   ├── ood.py            # energy score
│   ├── baseline_ml.py
│   ├── export.py         # ONNX + INT8
│   └── utils.py
├── app/
│   ├── streamlit_app.py
│   └── samples/
├── runs/
└── reports/
    ├── figures/
    └── results.md
```

---

## Phase 0 — Scaffold and environment

**Goal:** A repo that runs a dry-run import check without errors, before any real data exists.

**Do:**
- Create the folder structure above.
- `requirements.txt` with pinned versions (torch, timm, scikit-learn, opencv-python, imagehash, networkx, xgboost, shap, onnx, onnxruntime, streamlit, pyyaml, matplotlib, seaborn, pandas).
- `config.yaml` with: paths, seed, image size (224), batch size, epochs, lr, backbone name, class names, `loss: {type: weighted_ce | focal, gamma: 2.0}`, `sampler: {weighted: false}`, `normalization: {mode: imagenet | dataset}`, `dedup: {hamming_threshold: 4}`.
- `src/utils.py`: seeding, device selection (cuda/mps/cpu), timestamped run dir creation, JSON metric dump.
- `README.md` stub with project description and setup commands.
- `.gitignore` excluding `data/raw/`, `runs/`, `__pycache__`, `*.pth`, `*.onnx`.

**Acceptance:** Repo imports cleanly; `python -c "from src.utils import set_seed, get_device; set_seed(42); print(get_device())"` works.

**Do NOT:** download data, write model code, or install GPU-specific packages yet.

---

## Phase 1 — Data acquisition and EDA

**Goal:** Dataset on disk, flattened, understood, with a written inventory.

**Dataset:** Machuve et al., *Machine Learning Dataset for Poultry Diseases Diagnostics* (Zenodo DOI `10.5281/zenodo.5801834`; also mirrored on Kaggle as "Poultry Diseases Detection"). 4 classes. Approx. counts in the augmented release: Coccidiosis 2476, Healthy 2404, Newcastle 562, Salmonella 2625.

**Do:**
- `scripts/download_data.py` — download and extract. If the source needs a manual login, write clear manual instructions into the README rather than faking the download.
- **Flatten first.** Kaggle mirrors often arrive pre-partitioned into `train/`, `val/`, `test/` folders built by naive random splitting — near-duplicates are already smeared across those splits. Ignore all upstream split folders, pool every image into `data/raw/<class>/`, and rebuild splits from scratch in Phase 2. Log how many images came from each upstream folder so the flattening is auditable.
- Build `data/manifest.csv`: `filepath, label, width, height, filesize, md5`.
- EDA script producing into `reports/figures/`:
  - class distribution bar chart (state the imbalance ratio explicitly)
  - image size distribution
  - a 4×5 grid of sample images per class
  - mean RGB / HSV histogram per class — colour is the main diagnostic signal, so verify it actually separates
- **Substrate confounder check.** Droppings are photographed on wood shavings, wire mesh, soil, concrete. If one farm shot all its Coccidiosis samples on wood shavings, the CNN will happily learn "wood shavings = Coccidiosis". Do a visual audit (sample grid grouped by class, eyeball the backgrounds) plus a cheap quantitative proxy — e.g. cluster background colour statistics from image border crops and cross-tabulate cluster vs class label. Report any strong correlation as a named risk.
- Write findings into `reports/results.md` under "Phase 1 — Data".

**Acceptance:** Manifest CSV has one row per image; upstream split folders confirmed flattened; all figures rendered; substrate/class cross-tab reported; imbalance ratio stated.

**Do NOT:** split, augment, resize, or train.

---

## Phase 2 — Deduplication, grouped splits, data pipeline

**Goal:** Mathematically leak-free splits and a working `DataLoader`.

**Do:**
- `src/dedup.py`, in this exact order:
  1. Exact duplicates via md5.
  2. Perceptual hashes with `imagehash.phash` for every image.
  3. Build an adjacency graph: edge between any pair with **Hamming distance ≤ 4** (config-driven; sweep ≤ 6 and report how group counts change).
  4. Extract **connected components** (`networkx.connected_components` or `scipy.sparse.csgraph.connected_components`).
  5. Assign every image a `group_id` — singletons get their own id. Write back into the manifest.
- Split with **`sklearn.model_selection.StratifiedGroupKFold`** (groups = `group_id`, stratify = label) to carve 70/15/15 into `data/splits/{train,val,test}.csv`. This guarantees no group straddles a split.
- `src/data.py`: Dataset class; train transforms = resize 224, random H+V flip, rotation ±20°, mild brightness/contrast; val/test = resize + normalise only.
  - **Colour caution:** hue/saturation jitter off or near-zero. Colour carries the diagnosis.
  - **No MixUp / CutMix.**
  - Implement `WeightedRandomSampler` behind a config flag for Phase 4 use.
- **Normalization policy:** compute dataset mean/std from the train split and store it in `config.yaml`, but use it *only* for the scratch CNN (Phase 3) and classical features (Phase 6). Pre-trained timm backbones (Phase 4) use **standard ImageNet normalization** — mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]` — because custom stats shift early-filter activations away from what the pre-trained weights expect. `config.normalization.mode` selects between them.
- Sanity script: render one augmented batch to `reports/figures/batch_preview.png`.

**Acceptance:** Assert zero `group_id` overlap across splits and fail loudly if violated; report number of groups vs number of images (the gap is your duplicate burden); class proportions match within ~1%; batch preview looks like chicken droppings.

---

## Phase 3 — Baseline CNN

**Goal:** An honest floor to beat.

**Do:**
- Small CNN from scratch (3–4 conv blocks) in `src/model.py`. Use dataset normalization here.
- `src/train.py`: class-weighted cross-entropy, AdamW, cosine LR, early stopping on **val macro-F1**, per-epoch logging, best-checkpoint saving.
- `src/losses.py`: weighted CE and focal loss (γ=2), selected by config.

**Acceptance:** Training curves saved; val macro-F1 reported. Expect roughly 70–85%. If it hits 97%, stop and re-audit Phase 2 for leakage.

---

## Phase 4 — Transfer learning and fine-tuning

**Goal:** The main model.

**Do:**
- Via timm, train at least three backbones: `mobilenetv2_100`, `efficientnet_b0`, `resnet50` (`densenet121` optional). ImageNet normalization.
- Two-stage per backbone: (a) freeze base, train head ~5 epochs; (b) unfreeze top ~30% of layers, fine-tune at lr 1e-5 with early stopping.
- Identical class weights / seeds / splits across backbones — this must be a fair comparison.
- **Newcastle imbalance (562 vs ~2,500, roughly 1:4.5).** Start with weighted CE. If Newcastle recall lags the other three classes by more than ~10 points, switch to focal loss (γ=2) or `WeightedRandomSampler` via the config flags and re-run. Report both attempts, not just the winner.
- Comparison table in `reports/results.md`: backbone, params, val macro-F1, test macro-F1, per-class Newcastle recall, CPU inference ms/image.

**Acceptance:** Best model ≥ 0.93 test macro-F1. Reference point: the original paper's fine-tuned MobileNetV2 reached ~98% validation accuracy, so falling far below that means something is wrong — but note their splits were not group-aware, so a few points lower here is expected and *more* honest.

---

## Phase 5 — Evaluation, calibration, explainability

**Goal:** The part that earns marks.

**Do:**
- `src/evaluate.py`: per-class precision/recall/F1, macro + weighted F1, confusion matrix (counts and row-normalised), one-vs-rest ROC-AUC.
- Explicitly analyse the **Coccidiosis ↔ Salmonella** confusion (the known hard pair) and Newcastle recall.
- `src/gradcam.py` with a **target-layer lookup dict** so no per-model hacking is needed:
  - `resnet*` → `layer4[-1]`
  - `mobilenetv2*` → `conv_head` (fallback `features[-1]`)
  - `efficientnet_b*` → `conv_head` (fallback `blocks[-1]`)
  - `densenet*` → `features.norm5`
  Assert the resolved layer exists before running; fail with a clear message listing available module names.
- Overlays for 3 correct + 3 incorrect predictions per class into `reports/figures/gradcam/`. Check attention lands on the dropping, not the litter — cross-reference the Phase 1 substrate finding.
- `src/calibrate.py`: reliability diagram, **Expected Calibration Error (ECE)** before and after **temperature scaling** (single scalar T fitted on the validation logits by minimising NLL). Save the fitted T into the run directory; the Streamlit app must use temperature-scaled probabilities so displayed confidence is empirically meaningful.

**Acceptance:** Full classification report in `reports/results.md`; Grad-CAM grid saved; ECE reported pre/post scaling with the fitted T.

---

## Phase 6 — Classical ML baseline (the differentiator)

**Goal:** Show deep learning isn't the only option for a low-resource farm setting.

**Do:**
- `src/baseline_ml.py`: multi-colour-space features — RGB/HSV/LAB histograms, LBP texture, GLCM stats, wavelet energies. Dataset normalization (or raw), not ImageNet.
- Feature selection via PCA and/or XGBoost importance.
- Train SVM (RBF), Random Forest, XGBoost. 5-fold **grouped** CV on train (reuse `group_id`), evaluate on the same held-out test split as the CNNs.
- SHAP global importance for the best classical model.
- Table comparing best CNN vs best classical model: macro-F1, model size, CPU latency.

**Acceptance:** Classical model ≥ 0.85 macro-F1; honest side-by-side table with a one-paragraph interpretation.

---

## Phase 7 — Out-of-distribution rejection

**Goal:** Stop the model confidently diagnosing a photo of a shoe.

**Method — use the Free Energy Score.** `E(x) = -T · log Σᵢ exp(fᵢ(x)/T)` over the logits, with Maximum Logit Score (MLS) as a secondary comparison.

Rejected alternatives, and state why in the report:
- **A 5th "not-a-dropping" class** teaches the model those specific 300 training images, not the concept of "not a dropping". A feeding trough or a glove it has never seen still lands confidently in a disease class.
- **Max-softmax thresholding** is weak because softmax normalisation makes deep nets overconfident even on pure noise.

Energy scoring needs no retraining, is mathematically grounded, and separates in-distribution faecal images from arbitrary objects far more cleanly.

**Do:**
- `src/ood.py`: compute energy scores for the test split (in-distribution) and for a held-out OOD set (~300 images: floor, grass, hands, feed troughs, random objects — deliberately include object types absent from any training data).
- Pick the threshold on the **validation** in-distribution energies (e.g. 95th percentile), never on the OOD set.
- Report AUROC and FPR@95TPR for energy vs MLS vs max-softmax as a three-way comparison — that table is a genuine result.

**Acceptance:** ≥ 90% of OOD images rejected with < 5% of valid test images wrongly rejected; three-way comparison table present.

---

## Phase 8 — Streamlit app and export

**Goal:** A demo someone can click.

**Do:**
- `src/export.py`: `torch.onnx.export` → ONNX, then `onnxruntime.quantization` dynamic **INT8**. Run inference through `onnxruntime`. Report model size and CPU latency before/after quantisation, and verify predictions match the PyTorch model within tolerance.
  - **ONNX Runtime is the export target, not TFLite.** PyTorch → ONNX → TensorFlow → TFLite drags in a whole second framework for no benefit in a pure-PyTorch project.
- `app/streamlit_app.py`:
  - Upload image → temperature-scaled class probabilities → confidence bar chart → Grad-CAM overlay → disease info panel (cause, transmission, typical signs, management) → prominent disclaimer that this is a screening aid, not veterinary diagnosis.
  - **Sample gallery.** Nobody testing this has chicken dropping photos on their laptop. Ship `app/samples/` with 1–2 test images per class plus at least one OOD image, exposed as an "Or pick a sample image" dropdown/carousel, so the demo is interactive with zero setup.
  - Energy-score gate runs first: if the image is OOD, show "Not recognised as a faecal image" and stop — don't show a disease prediction at all.
  - If in-distribution but below the calibrated confidence threshold, show "Uncertain — recommend lab confirmation".

**Acceptance:** App runs locally, handles a corrupt/non-image upload without crashing, sample gallery works, quantised ONNX size and latency reported.

---

## Phase 9 — Documentation and report

**Do:**
- Finish `README.md`: problem, dataset + citation, setup, how to reproduce each phase, results table, screenshots, limitations.
- Consolidate `reports/results.md`: methodology, results, error analysis, limitations, future work.
- **Limitations to state honestly:** dataset is from Tanzanian farms only (lighting/breed/substrate bias); Newcastle class is ~4.5× smaller; any substrate–class correlation found in Phase 1; faecal appearance alone cannot confirm a diagnosis; no external validation set; group-aware splits mean our numbers are not directly comparable to published figures that used random splits.
- Citation: Machuve, D., Nwankwo, E., Mduma, N., Mbelwa, J. (2022). Poultry diseases diagnostics models using deep learning. *Frontiers in Artificial Intelligence*.

---

## Definition of done

- [ ] `python -m src.train` reproduces the best model from config
- [ ] Test-set macro-F1 ≥ 0.93 with asserted zero group leakage
- [ ] Per-class metrics + confusion matrix + Grad-CAM in the report
- [ ] ECE reported before and after temperature scaling
- [ ] Classical ML comparison table
- [ ] Energy-score OOD rejection with three-way method comparison
- [ ] Streamlit app runs with sample gallery
- [ ] Quantised ONNX export verified
- [ ] README lets a stranger reproduce it
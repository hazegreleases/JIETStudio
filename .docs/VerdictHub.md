# ⚖️ VerdictHub: Model Validation Dashboard

VerdictHub is the definitive evaluation suite for JIET Studio. It transforms raw training metrics into actionable insights, allowing you to objectively verify the quality of your models before deployment.

## 🔑 Key Features

- **Metrics Dashboard**:
  - **Automated Visualization**: Direct rendering of `results.png` and `confusion_matrix.png` from training runs.
  - **Historical Comparison**: Easily switch between different training "runs" to compare performance evolution.
- **Visual Verification (GT vs. Pred)**:
  - **Side-by-Side Comparison**: Dual-canvas layout synchronized to show **Ground Truth (GT)** annotations alongside **Model Predictions**.
  - **High-Fidelity Rendering**: Intelligent scaling ensures large validation images are crystal clear and fit the available screen real estate without distortion.
- **Run Discovery**:
  - Automatically scans your project's `runs/` directory to categorize and display the latest training and validation results.

## 📈 Understanding the Verdict

Use VerdictHub to identify "hard" cases where the model fails (False Negatives) or hallucinates detections (False Positives). This feedback loop is essential for refining your dataset using **FlowLabeler** and **ForgeAugment**.

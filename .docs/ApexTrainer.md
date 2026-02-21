# 🚀 ApexTrainer: Professional YOLO Orchestrator

ApexTrainer is the core training module for JIET Studio, providing a high-level interface for the Ultralytics YOLO framework. It simplifies complex training configurations into a streamlined, real-time monitored experience.

## 🔑 Key Features

- **Real-Time Instrumentation**:
  - **Console Streaming**: Live feedback from the training process.
  - **Resource Bar Analytics**: Dedicated progress indicators for Epoch, Percentage Completion, and ETA.
- **Advanced Hyperparameter Control**:
  - **Internal Augmentations**: Tune Mosaic, Mixup, and Blur parameters directly within the UI.
  - **Training Resumption**: One-click "Resume" functionality to pick up exactly where a previous session left off.
- **Intelligent Dataset Preparation**:
  - **BG Ratio Balancing**: Automatically includes verified background images based on a user-defined ratio to reduce false positives.
  - **Memory Sanitization**: Aggressive VRAM and RAM cleanup post-training to ensure system stability.

## 📂 Run Management

All training logs, weights (`best.pt`, `last.pt`), and evaluation plots are automatically organized within the project's `runs/` directory, sorted by timestamp for easy retrieval.

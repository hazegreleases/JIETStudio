# JIET Studio: The Professional Computer Vision Suite

JIET Studio is a high-performance, modular environment designed for professional-grade YOLO training, dataset management, and real-time inference. Engineered for speed and precision, it streamlines the entire computer vision workflow from raw data to production-ready models.

## The Flow Suite

Experience a seamless end-to-end pipeline with our specialized toolset:

### [FlowLabeler](.docs/FlowLabeler.md)
**The Precision Labeling Engine.**
A high-velocity annotation tool supporting Edit, Draw, and Magic Wand (SAM-powered) modes. Designed for rapid, accurate data labeling with zero-friction workflows.

### [ApexTrainer](.docs/ApexTrainer.md)
**Professional Training Orchestrator.**
A robust interface for training YOLO models. Features real-time progress parsing, advanced hyperparameter tuning (Mosaic, Mixup, Blur), and one-click resumption.

### [ForgeAugment](.docs/ForgeAugment.md)
**Modular Data Synthesis.**
A dynamic augmentation pipeline that allows for complex, multi-stage image transformations using a modular filter-loading system.

 How To Make Custom Filters?
 [Custom Filter Documentation](docs\custom_filters.md)

### [InsightEngine](.docs/InsightEngine.md)
**Real-Time Vision Analytics.**
A versatile inference engine for real-time model validation. Supports single images, batch folders, video files, and live webcam streams.

### [LoomSuite](.docs/LoomSuite.md)
**Dataset Utility Fabric.**
Essential tools for dataset hygiene, including specialized Health Checks, class distribution analysis, and intelligent video frame extraction.

### [VerdictHub](.docs/VerdictHub.md)
**Model Validation Dashboard.**
A comprehensive evaluation suite providing deep insights into model performance with side-by-side Ground Truth vs. Prediction visualizations.

---

## Quick Start

1. **Setup Environment**: `pip install -r requirements.txt`
2. **Launch**: `python main.py`
3. **Configure**: Visit the global Settings (JIET > Settings) to configure hardware acceleration and default models.

## License
AGPL-3.0

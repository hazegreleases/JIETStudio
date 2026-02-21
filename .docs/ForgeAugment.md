# ⚒️ ForgeAugment: Modular Synthesis Pipeline

ForgeAugment is a non-destructive image augmentation suite built on top of the Albumentations library. It empowers users to create complex data synthesis pipelines that significantly improve model generalization.

## 🔑 Key Features

- **Modular Plugin System**:
  - **Dynamic Loading**: Hot-load new augmentation filters as independent `.py` scripts.
  - **Pipeline Editor**: Drag-and-drop ordering of effects with granular probability controls.
- **BBox-Safe Transformations**:
  - All augmentations are rigorously tested for bounding box consistency.
  - **Precision Guard**: Automatic coordinate clipping prevents floating-point errors from crashing the pipeline.
- **Infinite Variety**:
  - **Copies per Image**: Configure the number of unique variations generated for every source image.
  - **Live Preview**: Real-time side-by-side visualization of original vs. augmented outputs.

## 🧩 Adding Custom Filters

1. Place your specialized Albumentations-based script in `app/core/augmentation/filters/`.
2. Inherit from `AugmentationEffect`.
3. Use **LoomSuite** to verify filter performance on project subsets.

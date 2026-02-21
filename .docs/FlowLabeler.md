# 🌊 FlowLabeler: Precision Annotation Engine

FlowLabeler is a high-speed, intuitive annotation tool designed to minimize the time between data collection and training readiness. By combining traditional methods with AI-powered assistance, it ensures high-quality datasets with minimal effort.

## 🔑 Key Features

- **Triple-Mode Flexibility**:
  - **Edit Mode**: Refine existing annotations with intuitive click-and-drag resizing.
  - **Draw Mode**: Rapidly create new bounding boxes with optimized mouse tracking.
  - **Magic Wand**: Leverage the power of **SAM (Segment Anything Model)** to auto-generate bounding boxes via single-point or box-prompt clicks.
- **Zero-Friction Workflow**:
  - **Auto-Advance**: Seamlessly move to the next image upon confirmation.
  - **Smart Selection**: Quickly switch between Unlabeled, Verified Background, and Labeled datasets.
  - **Visual Feedback**: Canvas flashes and status indicators provide immediate confirmation of actions without intrusive popups.

## ⌨️ Global Shortcuts

- `Shift + N`: Mark as Verified Background (creates empty label file).
- `Delete`: Remove selected image or bounding box.
- `Mouse Wheel`: Precision Zoom (aspect-preserving).
- `Middle Click/Drag`: Fluid Panning across high-resolution images.

## 🛠️ Configuration

Configure SAM device acceleration and default labeling model paths in the global **JIET > Settings** menu.

# 🏷️ NeuroPilot Labeler Pro: Professional Data Annotation Platform

**NeuroPilot Labeler Pro** is a high-performance, modular platform designed for annotating image data for autonomous driving tasks. Built with a focus on Clean Architecture and Domain-Driven Design (DDD), it provides a robust and scalable foundation for self-driving trajectory prediction and object detection.

---

## 🌟 Key Features

-   **Clean Architecture & DDD**: Backend structured into concentric layers (Domain, Application, Infrastructure) for maximum testability and maintainability.
-   **Dynamic Behavioral Logic**: Define custom behavioral commands (FOLLOW_LANE, TURN_LEFT, etc.) per project directly from the UI.
-   **Intelligent Export**: Export datasets in YOLO format with on-the-fly resizing (640x640, 320x320) and stratified splitting.
-   **Modern Canvas UI**: React & TypeScript interface for precision bounding box and trajectory annotation.
-   **Hybrid Storage**: Seamlessly serves images from both MinIO (S3-compatible) and local data directories with automated discovery.
-   **Docker Ready**: Integrated MinIO storage setup via Docker Compose.

---

## 🏗️ Technical Architecture

-   **Frontend**: React 18 + Vite + Tailwind CSS + Lucide Icons.
-   **Backend**: FastAPI + Python 3.10 (Strictly typed).
-   **Database**: SQLite (Relational metadata).
-   **Storage**: MinIO (Object Storage) + Local Filesystem Fallbacks.
-   **Patterns**: Repository Pattern, Dependency Injection, Factory Pattern, Value Objects.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
-   [uv](https://astral.sh/uv/) (Python package manager)
-   [Docker & Docker Compose](https://www.docker.com/)
-   [Node.js](https://nodejs.org/) (for UI development)

### 2. Backend Setup
```bash
# Sync dependencies and create venv
uv sync

# Start MinIO storage
docker-compose up -d

# Run the backend
uv run run.py
```

### 3. Frontend Setup
```bash
cd ui
npm install
npm run dev
```
The UI will be accessible at `http://localhost:5173`.

---

## 📂 Project Structure

The project follows **Clean Architecture** and **Domain-Driven Design (DDD)** principles to ensure high maintainability and testability.

```text
app/
├── domain/                 # Layer 1: Enterprise Business Rules (Pure Logic)
│   ├── models/             # Rich Entities (Project, Sample, LabelData)
│   ├── interfaces/         # Repository & Storage Abstract Base Classes
│   └── services/           # Application Use Cases (Annotation, Project, Sample Services)
├── core/                   # Layer 2: Infrastructure (Frameworks & Config)
│   ├── config.py           # Global settings and environment variables
│   └── storage/            # MinIO & Hybrid storage implementations
├── repositories/           # Layer 2: Infrastructure (Persistence)
│   ├── base_repository.py  # Base SQLite connection management
│   ├── project_repository.py# Project SQL implementation (Implements IProjectRepo)
│   ├── sample_repository.py # Sample SQL implementation (Implements ISampleRepo)
│   └── version_repository.py# Version SQL implementation
├── routers/                # Layer 3: Presentation (Adapters)
│   ├── label_router.py     # Labeling & Project API Endpoints
│   ├── upload_router.py    # Media upload & processing Endpoints
│   └── version_router.py   # Dataset Export & Versioning Endpoints
├── schemas/                # Data Transfer Objects (DTOs) for API I/O
└── utils/                  # Cross-cutting concerns (YOLO formatters, etc.)

data/                       # Local data storage (SQLite DB, Uploads, Exports)
tests/                      # Automated Test Suite
├── unit/                   # Isolated logic tests (Domain & Services)
└── integration/            # Full-flow API tests
ui/                         # Modern React Frontend (Vite + TS)
```

---

## 🧪 Quality Control

### Testing
We maintain a 100% logic coverage goal using PyTest:
```bash
# Run all tests
uv run pytest tests/

# Run unit tests only
uv run pytest tests/unit/
```

### Linting & Formatting
We use `ruff` for extremely fast linting and formatting:
```bash
# Check for errors
uv run ruff check .

# Fix auto-fixable errors
uv run ruff check --fix .

# Format code
uv run ruff format .
```

---

## 🤝 Integration with NeuroPilot E2E

This tool is optimized for the **NeuroPilot E2E** framework. Exported datasets are ready for training out-of-the-box with standard YOLOv8/v11 configurations.

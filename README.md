# 🏷️ NeuroPilot Labeler: Professional Data Annotation Platform

**NeuroPilot Labeler** is a full-stack, modular platform designed specifically for annotating image data for autonomous driving tasks. It features a modern React UI, a FastAPI backend, and S3-compatible storage (MinIO).

---

## 🌟 Key Features

-   **Seamless Backend**: FastAPI with SQLite for project and version management.
-   **Modern Canvas UI**: Built with React & TypeScript for high-performance bounding box and trajectory annotation.
-   **S3-Compatible Storage**: Integrated **MinIO** for scalable storage of raw images and exported datasets.
-   **Docker Integration**: Spin up your local cloud storage in seconds with Docker Compose.
-   **Flexible Exports**: Support for multiple dataset formats (YOLO, custom task formats).

---

## 🏗️ Architecture

-   **Frontend**: React + Vite + Tailwind CSS (Interactive Canvas).
-   **Backend**: FastAPI + SQLAlchemy (Project, Sample, and Label Management).
-   **Storage**: MinIO (Object Storage) + Local SQLite (Metadata).
-   **Infrastructure**: Docker (MinIO).

---

## 🛠️ Installation & Setup

### 1. Prerequisites
-   [uv](https://astral.sh/uv/) (Python package manager)
-   [Docker & Docker Compose](https://www.docker.com/)
-   [Node.js](https://nodejs.org/) (for UI development)

### 2. Backend Setup
```bash
# Sync dependencies
uv sync

# Start MinIO storage
docker-compose up -d

# Start the application (Backend + Automated MinIO Bucket Init)
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

```text
app/                    # FastAPI Backend
├── core/               # App configuration & Storage provider
├── repositories/       # Database access layer
├── routers/            # API endpoints (Labels, Uploads, Versions)
├── schemas/            # Pydantic models
├── services/           # Business logic
└── utils/              # Helper functions (YOLO utils, etc.)

data/                   # Storage (local DB and MinIO volume)
scripts/                # Audit, Cleanup, and Migration scripts
ui/                     # React Frontend
├── src/                # Component logic, Hooks, and API client
└── tailwind.config.js  # Styling configuration
```

---

## 🧪 Testing

Maintain reliability with PyTest:
```bash
uv run pytest tests/
```

---

## 🤝 Integration with NeuroPilot E2E

This tool is designed to work in tandem with the **NeuroPilot E2E** framework. Annotate your data here, export in YOLO format, and feed it directly into the NeuroPilot training pipeline.

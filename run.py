import subprocess
import sys
from pathlib import Path

import uvicorn

root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root))
sys.path.append(str(Path(__file__).parent.resolve()))

def check_docker():
    """Ensure docker-compose is available and start minio."""
    try:
        docker_file = Path(__file__).parent / "docker-compose.yaml"
        if docker_file.exists():
            print("🐳 Starting MinIO container...")
            subprocess.run(["docker", "compose", "-f", str(docker_file), "up", "-d"], check=True)
            print("✅ MinIO is running on http://localhost:9000")
        else:
            print("⚠️  docker-compose.yaml not found, skipping minio auto-start.")
    except Exception as e:
        print(f"❌ Error starting Docker: {e}")
        print("💡 Ensure Docker and docker-compose are installed and running.")

if __name__ == "__main__":
    check_docker()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

import socket
import sys
import uvicorn


def check_port_free(host: str, port: int) -> bool:
    """Checks whether the given host:port is free to bind."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        result = s.connect_ex((host, port))
        # connect_ex returns 0 if connection succeeds (meaning port is already occupied)
        return result != 0


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000

    print("=" * 70)
    print("Starting RubriMark AI - Research Backend Server (FastAPI)")
    print("Component: Adaptive AI-Based Rubric Generation (IT23376472)")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Health Check:      http://{host}:{port}/api/v1/health")
    print("=" * 70)

    if not check_port_free(host, port):
        print(f"\n[ERROR] Port {port} is already in use by another running process.")
        print("Please terminate any previous uvicorn/python process before restarting.")
        sys.exit(1)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["app"],
        reload_excludes=["*.db", "*.db-journal", "*.db-wal", "venv/*", "*.pyc", "__pycache__/*"],
    )

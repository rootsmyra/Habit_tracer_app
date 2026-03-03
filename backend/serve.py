import os
import pathlib
import uvicorn

BASE_DIR = pathlib.Path(__file__).resolve().parent

# Ensure reloader ignores heavy folders
ignored = [".venv", "__pycache__", "node_modules"]
os.environ.setdefault("WATCHFILES_IGNORE_DIRECTORIES", ",".join(ignored))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        reload_dirs=[str(BASE_DIR / "app")],
        reload_excludes=[
            ".venv",
            "**/.venv/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/*.pyc",
        ],
    )

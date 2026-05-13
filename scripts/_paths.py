from pathlib import Path
import os

def data_root() -> Path:
    env = os.environ.get("CAREEROPS_DATA_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()

def career_dir() -> Path:
    return data_root() / "career"

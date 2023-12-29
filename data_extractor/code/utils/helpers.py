from pathlib import Path

def create_tmp_file_path() -> Path:
    return Path(__file__).parent.resolve() / 'running'
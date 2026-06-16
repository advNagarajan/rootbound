import pytest
import shutil
from pathlib import Path

@pytest.fixture
def temp_project_dir(tmp_path):
    # Setup a helper to generate quick project layouts
    def _create_layout(files_dict):
        for path_str, content in files_dict.items():
            file_path = tmp_path / path_str
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        return tmp_path
    return _create_layout

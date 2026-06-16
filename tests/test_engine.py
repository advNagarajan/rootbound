import pytest
from pathlib import Path
from rootbound.core.engine import RootboundEngine

def test_single_file_scan(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import requests\nimport pandas as pd\n"
    })
    engine = RootboundEngine(str(project / "main.py"))
    result = engine.execute_scan()
    assert result.top_level_packages == {"requests", "pandas"}
    assert "requests" in result.import_chains
    assert "pandas" in result.import_chains

def test_local_traversal(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import utils\n",
        "utils.py": "import requests\n"
    })
    engine = RootboundEngine(str(project / "main.py"))
    result = engine.execute_scan()
    assert result.top_level_packages == {"requests"}
    assert result.import_chains["requests"] == [["main.py", "utils.py", "requests"]]

def test_stdlib_exclusion(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import os\nimport sys\nimport json\n"
    })
    engine = RootboundEngine(str(project / "main.py"))
    result = engine.execute_scan()
    assert result.top_level_packages == set()

def test_circular_import(temp_project_dir):
    project = temp_project_dir({
        "a.py": "import b\n",
        "b.py": "import a\nimport requests\n"
    })
    engine = RootboundEngine(str(project / "a.py"))
    result = engine.execute_scan()
    assert result.top_level_packages == {"requests"}

def test_relative_imports(temp_project_dir):
    project = temp_project_dir({
        "src/main.py": "from .shared import db\n",
        "src/shared/__init__.py": "",
        "src/shared/db.py": "import sqlalchemy\n"
    })
    engine = RootboundEngine(str(project / "src" / "main.py"))
    result = engine.execute_scan()
    assert result.top_level_packages == {"sqlalchemy"}
    assert result.import_chains["sqlalchemy"] == [["main.py", "db.py", "sqlalchemy"]]

def test_directory_scan(temp_project_dir):
    project = temp_project_dir({
        "a.py": "import requests\n",
        "sub/b.py": "import yaml\n"
    })
    engine = RootboundEngine(str(project), is_directory=True)
    result = engine.execute_scan()
    assert result.top_level_packages == {"requests", "pyyaml"}

def test_pypi_name_normalization(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import yaml\nimport PIL\n"
    })
    engine = RootboundEngine(str(project / "main.py"))
    result = engine.execute_scan()
    assert result.top_level_packages == {"pyyaml", "pillow"}

def test_empty_file(temp_project_dir):
    project = temp_project_dir({
        "main.py": ""
    })
    engine = RootboundEngine(str(project / "main.py"))
    result = engine.execute_scan()
    assert result.top_level_packages == set()

def test_syntax_error_file(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import requests\nthis is invalid syntax !@#\n"
    })
    engine = RootboundEngine(str(project / "main.py"))
    result = engine.execute_scan()
    # Should scan successfully prior to syntax error or skip gracefully
    # If the file is unparseable, it fails gracefully without raising exceptions
    assert result.top_level_packages == set()

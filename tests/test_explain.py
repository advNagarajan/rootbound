import pytest
from rootbound.core.explainer import explain_package

def test_explain_single_chain(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import utils\n",
        "utils.py": "import pandas\n"
    })
    result = explain_package("pandas", str(project / "main.py"))
    assert result.reachable is True
    assert result.package == "pandas"
    assert result.chains == [["main.py", "utils.py", "pandas"]]

def test_explain_multi_chain(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import utils\nimport report\n",
        "utils.py": "import pandas\n",
        "report.py": "import pandas\n"
    })
    result = explain_package("pandas", str(project / "main.py"))
    assert result.reachable is True
    assert len(result.chains) == 2
    assert ["main.py", "utils.py", "pandas"] in result.chains
    assert ["main.py", "report.py", "pandas"] in result.chains

def test_explain_not_reachable(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import utils\n",
        "utils.py": "import requests\n"
    })
    result = explain_package("pandas", str(project / "main.py"))
    assert result.reachable is False
    assert result.chains == []

def test_explain_directory_mode(temp_project_dir):
    project = temp_project_dir({
        "a.py": "import requests\n",
        "b.py": "import requests\n"
    })
    result = explain_package("requests", str(project), is_directory=True)
    assert result.reachable is True
    assert len(result.chains) == 2

def test_explain_normalized_name(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import yaml\n"
    })
    result = explain_package("pyyaml", str(project / "main.py"))
    assert result.reachable is True
    assert result.package == "pyyaml"
    assert result.chains == [["main.py", "pyyaml"]]

import json
import pytest
from typer.testing import CliRunner
from rootbound.cli.main import app

runner = CliRunner()

def test_cli_scan_basic(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import requests\n"
    })
    result = runner.invoke(app, ["scan", str(project / "main.py")])
    assert result.exit_code == 0
    assert "Discovered packages (1):" in result.output
    assert "requests" in result.output

def test_cli_scan_json(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import requests\n"
    })
    result = runner.invoke(app, ["scan", str(project / "main.py"), "--json"])
    assert result.exit_code == 0
    # Strip terminal line wrapping newlines to ensure clean JSON load on Windows paths
    normalized_output = result.output.replace("\r", "").replace("\n", "")
    data = json.loads(normalized_output)
    assert data["packages"] == ["requests"]

def test_cli_scan_output_requirements(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import requests\n"
    })
    reqs_file = project / "reqs.txt"
    result = runner.invoke(app, ["scan", str(project / "main.py"), "-o", str(reqs_file)])
    assert result.exit_code == 0
    assert reqs_file.exists()
    assert reqs_file.read_text().strip() == "requests"

def test_cli_explain_reachable(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import requests\n"
    })
    result = runner.invoke(app, ["explain", "requests", str(project / "main.py")])
    assert result.exit_code == 0
    assert "requests reachable via:" in result.output

def test_cli_explain_not_reachable(temp_project_dir):
    project = temp_project_dir({
        "main.py": "import requests\n"
    })
    result = runner.invoke(app, ["explain", "pandas", str(project / "main.py")])
    assert result.exit_code == 0
    assert "pandas is not reachable from" in result.output

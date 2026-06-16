import ast
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple

from rootbound.core.models import ScanResult
from rootbound.core.pypi_mapping import PYPI_MAPPING
from rootbound.core.stdlib_list import is_stdlib

class RootboundEngine:
    def __init__(self, target_path: str, is_directory: bool = False):
        self.target_path = Path(target_path).resolve()
        self.project_root = self.target_path if is_directory else self.target_path.parent
        self.is_directory = is_directory
        self.visited_files: Set[Path] = set()
        self.top_level_packages: Set[str] = set()
        self.import_chains: Dict[str, List[List[str]]] = {}

    def normalize_pypi_name(self, root_module: str) -> str:
        name_lower = root_module.lower()
        return PYPI_MAPPING.get(name_lower, name_lower)

    def trace_local_file(self, file_path: Path, current_chain: List[str]):
        if file_path in self.visited_files or not file_path.exists():
            return
        self.visited_files.add(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception:
            return  # Fail gracefully on unparseable files

        # Determine relative directory for import resolution
        file_dir = file_path.parent

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._process_import_string(alias.name, current_chain + [file_path.name], file_dir)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    # Resolve relative import syntax:
                    target_dir = file_dir
                    for _ in range(node.level - 1):
                        target_dir = target_dir.parent
                    
                    if node.module:
                        # e.g. from .shared import db
                        module_parts = node.module.split('.')
                        curr_dir = target_dir
                        for part in module_parts:
                            curr_dir = curr_dir / part
                        
                        # Check if node.module resolves to a file or package
                        resolved_py = target_dir
                        for part in module_parts[:-1]:
                            resolved_py = resolved_py / part
                        resolved_py = resolved_py / f"{module_parts[-1]}.py"
                        
                        if resolved_py.exists():
                            self.trace_local_file(resolved_py, current_chain + [file_path.name])
                        elif curr_dir.is_dir():
                            init_py = curr_dir / "__init__.py"
                            if init_py.exists():
                                self.trace_local_file(init_py, current_chain + [file_path.name])
                            
                            # Check if individual imports inside node.names are sub-files/dirs
                            for alias in node.names:
                                sub_py = curr_dir / f"{alias.name}.py"
                                sub_dir = curr_dir / alias.name
                                if sub_py.exists():
                                    self.trace_local_file(sub_py, current_chain + [file_path.name])
                                elif sub_dir.is_dir() and (sub_dir / "__init__.py").exists():
                                    self.trace_local_file(sub_dir / "__init__.py", current_chain + [file_path.name])
                    else:
                        # e.g., from . import db
                        for alias in node.names:
                            resolved_py = target_dir / f"{alias.name}.py"
                            resolved_dir = target_dir / alias.name
                            if resolved_py.exists():
                                self.trace_local_file(resolved_py, current_chain + [file_path.name])
                            elif resolved_dir.is_dir():
                                init_py = resolved_dir / "__init__.py"
                                if init_py.exists():
                                    self.trace_local_file(init_py, current_chain + [file_path.name])
                elif node.module:
                    self._process_import_string(node.module, current_chain + [file_path.name], file_dir)

    def _process_import_string(self, full_import_str: str, chain: List[str], file_dir: Path):
        root_module = full_import_str.split('.')[0]
        if not root_module or is_stdlib(root_module):
            return

        # Check in the current file directory or the project root
        local_py_file = file_dir / f"{root_module}.py"
        local_dir = file_dir / root_module
        
        # Fallback to project root if not in the current file dir
        if not local_py_file.exists() and not (local_dir.is_dir() and (local_dir / "__init__.py").exists()):
            local_py_file = self.project_root / f"{root_module}.py"
            local_dir = self.project_root / root_module

        if local_py_file.exists():
            self.trace_local_file(local_py_file, chain)
        elif local_dir.is_dir() and (local_dir / "__init__.py").exists():
            self.trace_local_file(local_dir / "__init__.py", chain)
        else:
            # External PyPI package leaf
            pypi_target = self.normalize_pypi_name(root_module)
            self.top_level_packages.add(pypi_target)
            if pypi_target not in self.import_chains:
                self.import_chains[pypi_target] = []
            
            new_chain = chain + [pypi_target]
            if new_chain not in self.import_chains[pypi_target]:
                self.import_chains[pypi_target].append(new_chain)

    def execute_scan(self, compute_blast_radius: bool = False) -> ScanResult:
        if self.is_directory:
            for py_file in self.target_path.rglob("*.py"):
                # Clean up initial chain to indicate it started from directory scan
                self.trace_local_file(py_file, [f"dir:{self.target_path.name}"])
        else:
            self.trace_local_file(self.target_path, [])

        return ScanResult(
            entrypoint=str(self.target_path.as_posix()),
            top_level_packages=self.top_level_packages,
            import_chains=self.import_chains,
            visited_files={Path(f).as_posix() for f in self.visited_files},
            blast_radius_tree={}
        )

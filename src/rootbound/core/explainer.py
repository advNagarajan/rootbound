from dataclasses import dataclass
from typing import List

from rootbound.core.engine import RootboundEngine

@dataclass
class ExplainResult:
    package: str
    entrypoint: str
    reachable: bool
    chains: List[List[str]]

def explain_package(package_name: str, target_path: str, is_directory: bool = False) -> ExplainResult:
    engine = RootboundEngine(target_path, is_directory)
    result = engine.execute_scan()
    
    normalized_pkg = engine.normalize_pypi_name(package_name)
    reachable = normalized_pkg in result.top_level_packages
    chains = result.import_chains.get(normalized_pkg, [])
    
    return ExplainResult(
        package=normalized_pkg,
        entrypoint=target_path,
        reachable=reachable,
        chains=chains
    )

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Dict, Optional

class NodeType(Enum):
    LOCAL_FILE = "LOCAL_FILE"
    STANDARD_LIB = "STANDARD_LIB"
    THIRD_PARTY = "THIRD_PARTY"

@dataclass
class ModuleNode:
    name: str
    node_type: NodeType
    absolute_path: Optional[str] = None
    import_path_chain: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)

@dataclass
class ScanResult:
    entrypoint: str
    top_level_packages: Set[str] = field(default_factory=set)
    import_chains: Dict[str, List[List[str]]] = field(default_factory=dict)
    visited_files: Set[str] = field(default_factory=set)
    blast_radius_tree: Dict[str, List[str]] = field(default_factory=dict)

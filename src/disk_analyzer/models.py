"""
Data models for Space Optimization module.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class NodeType(Enum):
    """Type de nœud dans l'arborescence."""
    DISK = "disk"
    DIR = "dir"
    FILE = "file"


@dataclass
class Node:
    """Représente un fichier, dossier ou disque."""
    id: Optional[int]
    parent_id: Optional[int]
    type: NodeType
    name: str
    path: str
    size: int
    mtime: float
    ctime: float
    extension: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Node':
        """Crée un Node depuis une ligne SQLite."""
        return cls(
            id=row[0],
            parent_id=row[1],
            type=NodeType(row[2]),
            name=row[3],
            path=row[4],
            size=row[5],
            mtime=row[6],
            ctime=row[7],
            extension=row[8]
        )


@dataclass
class DiskStats:
    """Statistiques d'un disque."""
    path: str
    total_size: int
    total_files: int
    total_dirs: int
    largest_files: list
    extension_stats: dict

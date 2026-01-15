"""
SQLite service for hierarchical storage and analytics.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple
from .models import Node, NodeType, DiskStats


class SQLiteService:
    """Service de gestion SQLite pour l'arborescence des fichiers."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialise la base de données et crée les tables."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Table principale
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                type TEXT NOT NULL CHECK(type IN ('disk', 'dir', 'file')),
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                size INTEGER NOT NULL DEFAULT 0,
                mtime REAL NOT NULL,
                ctime REAL NOT NULL,
                extension TEXT,
                FOREIGN KEY (parent_id) REFERENCES nodes(id) ON DELETE CASCADE
            )
        """)
        
        # Index
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_parent ON nodes(parent_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON nodes(name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_extension ON nodes(extension)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_mtime ON nodes(mtime)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_size ON nodes(size)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON nodes(path)")
        
        # FTS5 pour recherche full-text
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                name, path,
                content='nodes',
                content_rowid='id'
            )
        """)
        
        # Triggers pour synchroniser FTS5
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
                INSERT INTO nodes_fts(rowid, name, path) VALUES (new.id, new.name, new.path);
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
                DELETE FROM nodes_fts WHERE rowid = old.id;
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
                UPDATE nodes_fts SET name = new.name, path = new.path WHERE rowid = new.id;
            END
        """)
        
        self.conn.commit()
    
    def add_node(self, node: Node) -> int:
        """Ajoute un nœud et retourne son ID."""
        cursor = self.conn.execute("""
            INSERT INTO nodes (parent_id, type, name, path, size, mtime, ctime, extension)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (node.parent_id, node.type.value, node.name, node.path, 
              node.size, node.mtime, node.ctime, node.extension))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_node(self, node: Node) -> bool:
        """Met à jour un nœud existant."""
        cursor = self.conn.execute("""
            UPDATE nodes SET size = ?, mtime = ?, ctime = ?
            WHERE path = ?
        """, (node.size, node.mtime, node.ctime, node.path))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_node_by_path(self, path: str) -> Optional[Node]:
        """Récupère un nœud par son chemin."""
        cursor = self.conn.execute("""
            SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
            FROM nodes WHERE path = ?
        """, (path,))
        row = cursor.fetchone()
        return Node.from_db_row(row) if row else None
    
    def get_children(self, parent_id: int) -> List[Node]:
        """Récupère les enfants d'un nœud."""
        cursor = self.conn.execute("""
            SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
            FROM nodes WHERE parent_id = ?
            ORDER BY type, name
        """, (parent_id,))
        return [Node.from_db_row(row) for row in cursor.fetchall()]
    
    def delete_node(self, path: str) -> bool:
        """Supprime un nœud et ses enfants."""
        cursor = self.conn.execute("DELETE FROM nodes WHERE path = ?", (path,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def search_fts(self, query: str, limit: int = 100) -> List[Node]:
        """Recherche full-text sur nom et chemin."""
        cursor = self.conn.execute("""
            SELECT n.id, n.parent_id, n.type, n.name, n.path, n.size, n.mtime, n.ctime, n.extension
            FROM nodes n
            JOIN nodes_fts fts ON n.id = fts.rowid
            WHERE nodes_fts MATCH ?
            LIMIT ?
        """, (query, limit))
        return [Node.from_db_row(row) for row in cursor.fetchall()]
    
    def get_top_files(self, limit: int = 100) -> List[Node]:
        """Récupère les plus gros fichiers."""
        cursor = self.conn.execute("""
            SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
            FROM nodes WHERE type = 'file'
            ORDER BY size DESC LIMIT ?
        """, (limit,))
        return [Node.from_db_row(row) for row in cursor.fetchall()]
    
    def get_extension_stats(self) -> List[Tuple[str, int, int]]:
        """Statistiques par extension (extension, count, total_size)."""
        cursor = self.conn.execute("""
            SELECT extension, COUNT(*), SUM(size)
            FROM nodes WHERE type = 'file' AND extension IS NOT NULL
            GROUP BY extension
            ORDER BY SUM(size) DESC
        """)
        return cursor.fetchall()
    
    def get_folder_size(self, node_id: int) -> int:
        """Calcule la taille totale d'un dossier (récursif)."""
        cursor = self.conn.execute("""
            WITH RECURSIVE folder_tree AS (
                SELECT id, size FROM nodes WHERE id = ?
                UNION ALL
                SELECT n.id, n.size FROM nodes n
                JOIN folder_tree ft ON n.parent_id = ft.id
            )
            SELECT SUM(size) FROM folder_tree
        """, (node_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0
    
    def get_all_paths(self, parent_path: str) -> dict:
        """Récupère tous les chemins sous un parent avec leur ID."""
        cursor = self.conn.execute("""
            SELECT path, id FROM nodes WHERE path LIKE ?
        """, (f"{parent_path}%",))
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def close(self):
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()

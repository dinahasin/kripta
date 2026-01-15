"""
Tantivy service for fast full-text search.
"""

try:
    import tantivy
except ImportError:
    tantivy = None

from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .models import Node, NodeType


class TantivyService:
    """Service de recherche Tantivy pour indexation rapide."""
    
    def __init__(self, index_path: Path):
        self.enabled = tantivy is not None
        if not self.enabled:
            print("Warning: Tantivy module not found. Search index disabled.")
            return

        self.index_path = index_path
        self.index_path.mkdir(parents=True, exist_ok=True)
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialise l'index Tantivy."""
        # Créer le schéma
        schema_builder = tantivy.SchemaBuilder()
        schema_builder.add_text_field("name", stored=True, tokenizer_name="default")
        schema_builder.add_text_field("path", stored=True, tokenizer_name="raw")
        schema_builder.add_text_field("extension", stored=True, tokenizer_name="raw")
        schema_builder.add_integer_field("size", stored=True, indexed=True)
        schema_builder.add_date_field("mtime", stored=True, indexed=True)
        schema_builder.add_date_field("ctime", stored=True, indexed=True)
        schema_builder.add_integer_field("parent_id", stored=True, indexed=True)
        schema_builder.add_text_field("type", stored=True, tokenizer_name="raw")
        
        self.schema = schema_builder.build()
        
        # Créer ou ouvrir l'index
        try:
            self.index = tantivy.Index.open(str(self.index_path))
        except:
            self.index = tantivy.Index(self.schema, path=str(self.index_path))
        
        self.writer = self.index.writer()
    
    def add_document(self, node: Node):
        """Ajoute un document à l'index."""
        if not self.enabled:
            return

        doc = tantivy.Document()
        doc.add_text("name", node.name)
        doc.add_text("path", node.path)
        doc.add_text("type", node.type.value)
        
        if node.extension:
            doc.add_text("extension", node.extension)
        
        doc.add_integer("size", node.size)
        doc.add_date("mtime", datetime.fromtimestamp(node.mtime))
        doc.add_date("ctime", datetime.fromtimestamp(node.ctime))
        
        if node.parent_id:
            doc.add_integer("parent_id", node.parent_id)
        
        self.writer.add_document(doc)
    
    def update_document(self, node: Node):
        """Met à jour un document (supprime puis réajoute)."""
        if not self.enabled:
            return
        self.delete_document(node.path)
        self.add_document(node)
    
    def delete_document(self, path: str):
        """Supprime un document par son chemin."""
        if not self.enabled:
            return
        self.writer.delete_documents("path", path)
    
    def commit(self):
        """Commit les changements."""
        if not self.enabled:
            return
        self.writer.commit()
        self.writer = self.index.writer()
    
    def search(self, query_str: str, limit: int = 100) -> List[dict]:
        """Recherche dans l'index."""
        if not self.enabled:
            return []
            
        searcher = self.index.searcher()
        query_parser = tantivy.QueryParser.for_index(self.index, ["name", "path"])
        
        try:
            query = query_parser.parse_query(query_str)
            results = searcher.search(query, limit)
            
            docs = []
            for score, doc_address in results.hits:
                doc = searcher.doc(doc_address)
                docs.append({
                    'name': doc.get_first("name"),
                    'path': doc.get_first("path"),
                    'type': doc.get_first("type"),
                    'extension': doc.get_first("extension"),
                    'size': doc.get_first("size"),
                    'score': score
                })
            
            return docs
        except Exception as e:
            print(f"Erreur de recherche Tantivy: {e}")
            return []
    
    def close(self):
        """Ferme le writer."""
        if not self.enabled:
            return
        self.writer.commit()

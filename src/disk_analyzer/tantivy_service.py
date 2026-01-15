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
import logging
import shutil


class TantivyService:
    """Service de recherche Tantivy pour indexation rapide."""
    
    def __init__(self, index_path: Path):
        self.enabled = tantivy is not None
        self.writer = None
        self.index = None
        
        if not self.enabled:
            logging.warning("Tantivy module not found. Search index disabled.")
            return

        self.index_path = index_path
        self.index_path.mkdir(parents=True, exist_ok=True)
        self._initialize_index()
    
    def _clean_lock_file(self):
        """Nettoie le fichier de verrou orphelin si nécessaire."""
        lock_file = self.index_path / ".tantivy-writer.lock"
        meta_lock = self.index_path / ".tantivy-meta.lock"
        
        try:
            if lock_file.exists():
                logging.info(f"Suppression du verrou orphelin: {lock_file}")
                lock_file.unlink()
            if meta_lock.exists():
                logging.info(f"Suppression du verrou meta orphelin: {meta_lock}")
                meta_lock.unlink()
        except Exception as e:
            logging.warning(f"Impossible de supprimer le verrou: {e}")
    
    def _initialize_index(self):
        """Initialise l'index Tantivy."""
        # Nettoyer les verrous orphelins avant d'ouvrir l'index
        self._clean_lock_file()
        
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
            logging.info(f"Index Tantivy ouvert: {self.index_path}")
        except Exception as e:
            logging.info(f"Création d'un nouvel index Tantivy: {self.index_path}")
            self.index = tantivy.Index(self.schema, path=str(self.index_path))
        
        # Créer le writer avec gestion d'erreur
        try:
            # heap_size en bytes (50MB par défaut)
            self.writer = self.index.writer(heap_size=50_000_000)
            logging.info("IndexWriter créé avec succès")
        except Exception as e:
            logging.error(f"Erreur lors de la création du writer: {e}")
            # Si échec, essayer de nettoyer et réessayer
            self._clean_lock_file()
            try:
                self.writer = self.index.writer(heap_size=50_000_000)
                logging.info("IndexWriter créé après nettoyage des verrous")
            except Exception as e2:
                logging.error(f"Impossible de créer le writer même après nettoyage: {e2}")
                self.enabled = False
    
    def add_document(self, node: Node):
        """Ajoute un document à l'index."""
        if not self.enabled or not self.writer:
            return

        try:
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
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du document: {e}")
    
    def update_document(self, node: Node):
        """Met à jour un document (supprime puis réajoute)."""
        if not self.enabled:
            return
        self.delete_document(node.path)
        self.add_document(node)
    
    def delete_document(self, path: str):
        """Supprime un document par son chemin."""
        if not self.enabled or not self.writer:
            return
        try:
            self.writer.delete_documents("path", path)
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du document: {e}")
    
    def commit(self):
        """Commit les changements et recrée le writer."""
        if not self.enabled or not self.writer:
            return
        
        try:
            # Commit - cela consomme le writer dans Tantivy Python
            self.writer.commit()
            self.writer = None
            logging.debug("Commit Tantivy réussi")
            
            # Recréer le writer pour les prochaines opérations
            # Petit délai pour laisser le temps au verrou de se libérer
            import time
            time.sleep(0.1)  # 100ms
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.writer = self.index.writer(heap_size=50_000_000)
                    logging.debug(f"Writer recréé avec succès (tentative {attempt + 1})")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logging.warning(f"Tentative {attempt + 1} de recréation du writer échouée, nouvelle tentative...")
                        time.sleep(0.2 * (attempt + 1))  # Délai progressif
                    else:
                        logging.error(f"Impossible de recréer le writer après {max_retries} tentatives: {e}")
                        self.enabled = False
                        
        except Exception as e:
            logging.error(f"Erreur lors du commit: {e}")
            self.writer = None
            self.enabled = False
    
    def reload_writer(self):
        """Recharge le writer (à utiliser avec précaution)."""
        if not self.index:
            return False
        
        try:
            # Fermer l'ancien writer si existant
            if self.writer:
                try:
                    self.writer.commit()
                except:
                    pass
                self.writer = None
            
            # Nettoyer les verrous
            import time
            time.sleep(0.2)
            self._clean_lock_file()
            
            # Recréer le writer
            self.writer = self.index.writer(heap_size=50_000_000)
            self.enabled = True
            logging.info("Writer rechargé avec succès")
            return True
        except Exception as e:
            logging.error(f"Erreur lors du rechargement du writer: {e}")
            return False
    
    def search(self, query_str: str, limit: int = 100) -> List[dict]:
        """Recherche dans l'index."""
        if not self.enabled or not self.index:
            return []
        
        try:
            searcher = self.index.searcher()
            query_parser = tantivy.QueryParser.for_index(self.index, ["name", "path"])
            
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
            logging.error(f"Erreur de recherche Tantivy: {e}")
            return []
    
    def close(self):
        """Ferme le writer proprement."""
        if not self.enabled:
            return
        
        try:
            if self.writer:
                logging.info("Fermeture du writer Tantivy...")
                self.writer.commit()
                # Le writer sera garbage collected
                self.writer = None
                logging.info("Writer Tantivy fermé avec succès")
        except Exception as e:
            logging.error(f"Erreur lors de la fermeture du writer: {e}")
    
    def __del__(self):
        """Destructeur pour s'assurer que le writer est fermé."""
        self.close()

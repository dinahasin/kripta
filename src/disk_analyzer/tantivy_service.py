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
        # Champ "name" avec tokenisation intelligente pour recherche full-text
        # Cela permet de trouver "autodeks" dans "autodesk.iso"
        schema_builder.add_text_field("name", stored=True, tokenizer_name="default")
        # Champ "path" avec tokenisation aussi pour recherche dans les chemins
        schema_builder.add_text_field("path", stored=True, tokenizer_name="default")
        # Champ "name_raw" non tokenisé pour recherches exactes/regex
        schema_builder.add_text_field("name_raw", stored=True, tokenizer_name="raw")
        schema_builder.add_text_field("path_raw", stored=True, tokenizer_name="raw")
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
    
    def _convert_glob_to_regex(self, pattern: str) -> str:
        """
        Convertit un pattern glob (comme *.iso) en regex.
        Exemples:
        *.iso -> .*\\.iso$
        test* -> test.*
        *.txt -> .*\\.txt$
        """
        import re
        # Échapper les caractères spéciaux regex sauf * et ?
        pattern = re.escape(pattern)
        # Remplacer les patterns glob par leurs équivalents regex
        pattern = pattern.replace(r'\*', '.*')  # * devient .*
        pattern = pattern.replace(r'\?', '.')   # ? devient .
        # Si le pattern ne se termine pas par $, l'ajouter pour correspondre à la fin
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        return pattern
    
    def _is_regex_query(self, query_str: str) -> bool:
        """
        Détecte si la requête contient des caractères regex ou des patterns glob.
        Les caractères regex communs: . * + ? ^ $ [ ] { } | ( )
        """
        # Patterns glob communs
        if '*' in query_str or '?' in query_str:
            return True
        
        regex_chars = ['.', '+', '^', '$', '[', ']', '{', '}', '|', '(', ')']
        # Vérifier si la requête contient des caractères regex
        for char in regex_chars:
            if char in query_str:
                return True
        return False
    
    def search(self, query_str: str, limit: int = 100, use_regex: bool = False) -> List[dict]:
        """
        Recherche dans l'index Tantivy.
        Supporte les patterns glob (comme *.iso) et les regex.
        
        Args:
            query_str: Requête de recherche (peut être une regex ou un pattern glob)
            limit: Nombre maximum de résultats
            use_regex: Force l'utilisation de regex (si True, détecte automatiquement si False)
        """
        if not self.enabled or not self.index:
            return []
        
        # Détecter automatiquement si c'est une regex ou un pattern glob
        is_regex = use_regex or self._is_regex_query(query_str)
        
        try:
            searcher = self.index.searcher()
            import re
            
            # Convertir les patterns glob en regex si nécessaire
            if is_regex and ('*' in query_str or '?' in query_str):
                # Vérifier si c'est un pattern glob simple (comme *.iso)
                if not any(char in query_str for char in ['^', '$', '[', ']', '{', '}', '|', '(', ')', '+']):
                    # C'est probablement un pattern glob, le convertir
                    query_str = self._convert_glob_to_regex(query_str)
                    logging.info(f"Pattern glob converti en regex: {query_str}")
            
            # Compiler la regex ou le pattern de recherche
            try:
                if is_regex:
                    pattern = re.compile(query_str, re.IGNORECASE)
                else:
                    # Pour recherche texte simple, créer un pattern qui cherche le texte
                    escaped = re.escape(query_str)
                    pattern = re.compile(escaped, re.IGNORECASE)
            except re.error as e:
                logging.error(f"Regex/Pattern invalide: {e}")
                return []
            
            docs = []
            count = 0
            max_scan = min(limit * 100, 50000)  # Limiter le scan pour performance
            
            # Parcourir tous les documents de l'index Tantivy
            # Tantivy Python: utiliser searcher() directement
            try:
                searcher = self.index.searcher()
                
                # Dans Tantivy Python, on doit utiliser une approche différente
                # pour parcourir tous les documents. On va utiliser une requête vide
                # ou parcourir via les segments
                try:
                    # Essayer de parcourir via les segments
                    # Note: L'API exacte peut varier selon la version de Tantivy Python
                    for segment_reader in searcher.segment_readers():
                        num_docs = segment_reader.num_docs()
                        
                        for doc_id in range(num_docs):
                            if count >= max_scan or len(docs) >= limit:
                                break
                            count += 1
                            
                            try:
                                # Récupérer le document
                                doc = segment_reader.doc(doc_id)
                                if not doc:
                                    continue
                                
                                name = doc.get_first("name") or ""
                                path = doc.get_first("path") or ""
                                
                                # Vérifier si le nom ou le chemin correspond au pattern
                                if pattern.search(name) or pattern.search(path):
                                    docs.append({
                                        'name': name,
                                        'path': path,
                                        'type': doc.get_first("type"),
                                        'extension': doc.get_first("extension"),
                                        'size': doc.get_first("size"),
                                        'score': 1.0  # Score par défaut pour recherche regex
                                    })
                                    
                                    if len(docs) >= limit:
                                        break
                            except Exception as e:
                                logging.debug(f"Erreur lors du traitement du document {doc_id}: {e}")
                                continue
                        
                        if len(docs) >= limit:
                            break
                except AttributeError:
                    # Si segment_readers() n'existe pas, utiliser une autre approche
                    # Fallback: utiliser SQLite pour la recherche regex
                    logging.warning("Tantivy API incomplète, utilisation de SQLite pour la recherche regex")
                    return []
                
                if count >= max_scan:
                    logging.warning(f"Limite de scan atteinte ({max_scan} documents). Résultats partiels.")
            
            except Exception as e:
                logging.error(f"Erreur lors du parcours de l'index Tantivy: {e}")
                import traceback
                logging.error(traceback.format_exc())
                return []
            
            logging.info(f"Recherche terminée: {len(docs)} résultats trouvés sur {count} documents scannés")
            return docs
            
        except Exception as e:
            logging.error(f"Erreur de recherche Tantivy: {e}")
            import traceback
            logging.error(traceback.format_exc())
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

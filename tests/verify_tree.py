import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from src.core.config import SECURITY_DIR
from src.disk_analyzer.sqlite_service import SQLiteService
from src.disk_analyzer.models import Node, NodeType

def verify_data_integrity():
    print("\n=== VERIFICATION DE LA BASE DE DONNEES ===")
    
    db_path = SECURITY_DIR / "disk_analyzer" / "disk_analyzer.db"
    print(f"Chemin DB: {db_path}")
    
    if not db_path.exists():
        print("❌ Fichier DB non trouvé !")
        return

    service = SQLiteService(db_path)
    
    # 1. Lister les racines (Disques)
    print("\n--- 1. Recherche des racines (Disques) ---")
    cursor = service.conn.execute("SELECT id, name, path, size FROM nodes WHERE parent_id IS NULL")
    roots = cursor.fetchall()
    
    if not roots:
        print("⚠️ Aucune racine trouvée (parent_id IS NULL). La DB est peut-être vide ou corrompue.")
    
    for rid, name, path, size in roots:
        print(f"📁 RACINE: '{name}' (Path: {path}, ID: {rid}, Size: {size})")
        
        # 2. Vérifier les enfants directs
        verify_children(service, rid, indent=1)

def verify_children(service, parent_id, indent=1, max_depth=3):
    if indent > max_depth:
        print(f"{'  ' * indent}... (profondeur max atteinte)")
        return

    # Utilisation de la méthode officielle
    children = service.get_children(parent_id)
    
    if not children:
        print(f"{'  ' * indent}[Pas d'enfants trouvés via get_children({parent_id})]")
        
        # Test manuel au cas où get_children est buggé
        cursor = service.conn.execute("SELECT count(*) FROM nodes WHERE parent_id = ?", (parent_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"{'  ' * indent}⚠️ ERREUR: Il y a {count} enfants en SQL pur, mais get_children retourne vide !")
            # Debug des enfants
            cursor = service.conn.execute("SELECT id, name, parent_id FROM nodes WHERE parent_id = ?", (parent_id,))
            for row in cursor.fetchall():
                print(f"{'  ' * indent}   -> Enfant suspect: {row}")
    else:
        print(f"{'  ' * indent}✓ Trouvé {len(children)} enfants :")
        for child in children[:5]: # Afficher max 5
            icon = "📁" if child.type == NodeType.DIR else "📄"
            print(f"{'  ' * indent}{icon} {child.name} (ID: {child.id})")
            
        if len(children) > 5:
            print(f"{'  ' * indent}... et {len(children) - 5} autres.")
        
        # Récursion sur le premier dossier trouvé
        for child in children:
            if child.type == NodeType.DIR:
                verify_children(service, child.id, indent + 1, max_depth)
                break

def test_write_read():
    print("\n=== TEST ECRITURE / LECTURE ===")
    db_path = SECURITY_DIR / "disk_analyzer" / "disk_analyzer.db"
    service = SQLiteService(db_path)
    
    try:
        # Création Mock Parent
        timestamp = int(time.time())
        parent_path = f"C:\\TEST_PARENT_{timestamp}"
        parent = Node(
            id=None, parent_id=None, type=NodeType.DIR,
            name=f"TEST_PARENT_{timestamp}", path=parent_path,
            size=0, mtime=0, ctime=0, extension=None
        )
        pid = service.add_node(parent)
        print(f"✓ Écriture Parent OK (ID: {pid})")
        
        # Création Mock Enfant
        child_path = f"{parent_path}\\TEST_CHILD"
        child = Node(
            id=None, parent_id=pid, type=NodeType.FILE,
            name="TEST_CHILD", path=child_path,
            size=123, mtime=0, ctime=0, extension=".txt"
        )
        cid = service.add_node(child)
        print(f"✓ Écriture Enfant OK (ID: {cid}, ParentID: {pid})")
        
        # Lecture
        read_children = service.get_children(pid)
        if len(read_children) == 1 and read_children[0].id == cid:
            print("✓ Lecture Enfant OK (Relation préservée)")
        else:
            print(f"❌ Lecture Enfant ÉCHOUÉE. Lu: {read_children}")
            
        # Cleanup
        service.delete_node(parent_path)
        service.delete_node(child_path) # Devrait être fait par cascade ou manuel
        # Le service delete_node supprime par path.
        print("✓ Nettoyage OK")
            
    except Exception as e:
        print(f"❌ Erreur Test: {e}")

if __name__ == "__main__":
    verify_data_integrity()
    test_write_read()

"""
Test simple pour afficher l'URL et le titre de l'onglet actif Chrome.
"""

import sys
import os
from time import sleep

# Ajouter le chemin src au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.password_manager.chrome_tab_reader import get_active_chrome_tab


if __name__ == "__main__":
    print("Attente de 10 secondes pour vous permettre de basculer sur Chrome...")
    sleep(3)
    print("\nRecherche de l'onglet Chrome actif...\n")
    
    try:
        result = get_active_chrome_tab(debug=True)
        print("\n" + "=" * 60)
        if result:
            print(f"Titre: {result['title']}")
            print(f"URL: {result['url']}")
        else:
            print("Aucun onglet Chrome actif trouvé")
    except ImportError as e:
        print(f"Erreur: {e}")
        print("Installez pywin32 avec: pip install pywin32")
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

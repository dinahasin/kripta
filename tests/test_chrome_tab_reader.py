"""
Tests pour le module chrome_tab_reader.
"""

import sys
import os

# Ajouter le chemin src au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.password_manager.chrome_tab_reader import get_active_chrome_tab, _extract_url_from_title


def test_extract_url_from_title():
    """Test de l'extraction d'URL depuis un titre."""
    print("Test: Extraction d'URL depuis un titre")
    
    test_cases = [
        ("Google - https://www.google.com - Google Chrome", "https://www.google.com"),
        ("GitHub - https://github.com/dinahasina - Google Chrome", "https://github.com/dinahasina"),
        ("http://example.com - Google Chrome", "http://example.com"),
        ("Page Title - https://site.com/path/page - Google Chrome", "https://site.com/path/page"),
        ("Titre sans URL", "Titre sans URL"),
    ]
    
    for title, expected in test_cases:
        result = _extract_url_from_title(title)
        print(f"  Titre: {title}")
        print(f"  Attendu: {expected}")
        print(f"  Résultat: {result}")
        print(f"  {'✓ OK' if expected in result or result == expected else '✗ ÉCHEC'}")
        print()


def test_get_active_chrome_tab():
    """Test de la récupération de l'onglet actif Chrome."""
    print("Test: Récupération de l'onglet actif Chrome")
    print("(Assurez-vous que Chrome est ouvert avec au moins un onglet)")
    print()
    
    try:
        windows = get_active_chrome_tab()
        if windows:
            print(f"✓ {len(windows)} fenêtre(s) Chrome trouvée(s):")
            for i, window_text in enumerate(windows, 1):
                url = _extract_url_from_title(window_text)
                print(f"  {i}. {url}")
        else:
            print("✗ Aucune fenêtre Chrome trouvée (Chrome n'est peut-être pas ouvert)")
    except ImportError as e:
        print(f"✗ Erreur d'import: {e}")
        print("  Installez pywin32 avec: pip install pywin32")
    except Exception as e:
        print(f"✗ Erreur: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Tests du module chrome_tab_reader")
    print("=" * 60)
    print()
    
    test_extract_url_from_title()
    print()
    test_get_active_chrome_tab()
    print()
    print("=" * 60)

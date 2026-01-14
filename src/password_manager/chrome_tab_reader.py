"""
Module pour lire l'URL de l'onglet actif de Chrome via l'analyse de processus Windows.
"""

try:
    import win32gui
except ImportError:
    win32gui = None

import json
import urllib.request
import urllib.error


def _get_chrome_tab_via_debug_protocol(debug=False):
    """
    Essaie d'obtenir l'URL via Chrome Remote Debugging Protocol.
    Chrome doit être lancé avec --remote-debugging-port=9222
    
    Returns:
        dict: Dictionnaire avec 'title' et 'url', ou None
    """
    try:
        # Port par défaut de Chrome Remote Debugging
        debug_url = "http://localhost:9222/json"
        
        with urllib.request.urlopen(debug_url, timeout=1) as response:
            tabs = json.loads(response.read().decode())
            
            if debug:
                print(f"[DEBUG] Tabs trouvés via Debug Protocol: {len(tabs)}")
            
            # Trouver l'onglet actif (celui qui est visible)
            for tab in tabs:
                if tab.get('type') == 'page' and tab.get('url', '').startswith('http'):
                    if debug:
                        print(f"[DEBUG] Tab trouvé: {tab.get('title')} - {tab.get('url')}")
                    return {
                        'title': tab.get('title', 'Sans titre'),
                        'url': tab.get('url', '')
                    }
            
            # Si aucun onglet actif, prendre le premier onglet avec une URL
            for tab in tabs:
                url = tab.get('url', '')
                if url.startswith('http'):
                    return {
                        'title': tab.get('title', 'Sans titre'),
                        'url': url
                    }
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        if debug:
            print(f"[DEBUG] Impossible d'utiliser Chrome Debug Protocol: {e}")
        return None
    except Exception as e:
        if debug:
            print(f"[DEBUG] Erreur Chrome Debug Protocol: {e}")
        return None
    
    return None


def get_active_chrome_tab(debug=False):
    """
    Récupère l'URL et le titre de l'onglet actif de Chrome.
    Essaie d'abord via Chrome Remote Debugging Protocol, puis via les titres de fenêtres.
    
    NOTE: Chrome ne met généralement PAS l'URL dans le titre de la fenêtre Windows.
    Pour obtenir l'URL, Chrome doit être lancé avec: --remote-debugging-port=9222
    
    Args:
        debug (bool): Si True, affiche des informations de débogage
    
    Returns:
        dict: Dictionnaire avec 'title' et 'url', ou None si non trouvé
    """
    if win32gui is None:
        raise ImportError("pywin32 n'est pas installé. Installez-le avec: pip install pywin32")
    
    # Essayer d'abord via Chrome Remote Debugging Protocol (plus fiable pour l'URL)
    if debug:
        print("[DEBUG] Tentative via Chrome Remote Debugging Protocol...")
    result = _get_chrome_tab_via_debug_protocol(debug)
    if result:
        return result
    
    if debug:
        print("[DEBUG] Fallback: Recherche via titres de fenêtres Windows...")
        print("[DEBUG] NOTE: Chrome ne met généralement pas l'URL dans le titre de la fenêtre.")
        print("[DEBUG] Pour obtenir l'URL, lancez Chrome avec: --remote-debugging-port=9222")
    
    # Récupérer la fenêtre active
    active_hwnd = win32gui.GetForegroundWindow()
    active_title = win32gui.GetWindowText(active_hwnd)
    
    if debug:
        print(f"[DEBUG] Fenêtre active: '{active_title}'")
    
    # Vérifier si c'est une fenêtre Chrome
    active_lower = active_title.lower()
    if "chrome" in active_lower:
        if debug:
            print(f"[DEBUG] Fenêtre active détectée comme Chrome")
        
        # Extraire URL si disponible dans le titre (rare mais possible)
        url = _extract_url_from_title(active_title)
        
        # Si URL trouvée dans le titre, la retourner
        if url != active_title and url.startswith('http'):
            return {
                'title': active_title,
                'url': url
            }
    
    # Chercher toutes les fenêtres Chrome visibles
    windows = []
    all_visible_windows = []
    
    def enum_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            all_visible_windows.append(window_text)
            
            window_lower = window_text.lower()
            if "chrome" in window_lower:
                results.append(window_text)
                if debug:
                    print(f"[DEBUG] Fenêtre Chrome trouvée: '{window_text}'")
    
    win32gui.EnumWindows(enum_callback, windows)
    
    if debug:
        print(f"[DEBUG] Total fenêtres Chrome trouvées: {len(windows)}")
        print(f"[DEBUG] Total fenêtres visibles: {len(all_visible_windows)}")
    
    # Prendre la première fenêtre Chrome trouvée avec une URL dans le titre
    for window_text in windows:
        window_lower = window_text.lower()
        if "http" in window_lower:
            url = _extract_url_from_title(window_text)
            if url.startswith('http'):
                return {
                    'title': window_text,
                    'url': url
                }
    
    # Si aucune URL trouvée, retourner au moins le titre de la fenêtre active Chrome
    if windows:
        title = windows[0]
        url = _extract_url_from_title(title)
        return {
            'title': title,
            'url': url if url.startswith('http') else "URL non disponible (lancez Chrome avec --remote-debugging-port=9222)"
        }
    
    return None


def _extract_url_from_title(title):
    """
    Extrait l'URL du titre de la fenêtre Chrome.
    
    Args:
        title (str): Titre de la fenêtre Chrome
        
    Returns:
        str: URL extraite ou le titre complet si l'URL n'est pas trouvée
    """
    # Format typique: "Page Title - http://site.com - Google Chrome"
    # ou "http://site.com - Google Chrome"
    
    import re
    
    # Chercher les URLs http:// ou https://
    url_pattern = r'https?://[^\s-]+'
    match = re.search(url_pattern, title)
    
    if match:
        return match.group(0)
    
    # Si pas d'URL trouvée, retourner le titre complet
    return title

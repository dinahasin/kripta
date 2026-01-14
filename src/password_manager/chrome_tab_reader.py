"""
Module pour lire l'URL de l'onglet actif de Chrome via l'analyse de processus Windows.
"""

try:
    import win32gui
except ImportError:
    win32gui = None


def get_active_chrome_tab():
    """
    Récupère l'URL depuis le titre de la fenêtre Chrome.
    Chrome met souvent l'URL dans le titre.
    
    Returns:
        list: Liste des titres de fenêtres Chrome contenant des URLs
    """
    if win32gui is None:
        raise ImportError("pywin32 n'est pas installé. Installez-le avec: pip install pywin32")
    
    windows = []
    
    def enum_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            if "chrome" in window_text.lower() and "http" in window_text.lower():
                # Extraire URL du titre: "Page Title - http://site.com"
                results.append(window_text)
    
    win32gui.EnumWindows(enum_callback, windows)
    return windows


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

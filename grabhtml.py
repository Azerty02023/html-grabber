import os
import requests
from urllib.parse import urlparse, urljoin
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from time import sleep

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configurer la journalisation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def fetch_html(url):
    """
    Récupérer le contenu HTML de l'URL spécifiée.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la récupération de l'URL {url}: {e}")
        return None

def save_file(content, folder, filename):
    """
    Sauvegarder le contenu dans un fichier.
    """
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    logger.info(f"Contenu sauvegardé dans le fichier: {file_path}")

def extract_site_info(html_content, base_url):
    """
    Extraire les informations du site comme les métadonnées, les liens et les fichiers CSS.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extraire les métadonnées
    metadata = {}
    for meta in soup.find_all('meta'):
        if meta.get('name'):
            metadata[meta.get('name')] = meta.get('content', '')
        elif meta.get('property'):
            metadata[meta.get('property')] = meta.get('content', '')
    
    # Extraire les liens
    links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]
    
    # Extraire les fichiers CSS
    css_files = [urljoin(base_url, link['href']) for link in soup.find_all('link', rel='stylesheet', href=True)]
    
    return metadata, links, css_files

def save_site_info(folder, metadata, links, css_files):
    """
    Sauvegarder les informations du site dans des fichiers.
    """
    # Sauvegarder les métadonnées
    metadata_file = os.path.join(folder, 'metadata.txt')
    with open(metadata_file, 'w', encoding='utf-8') as file:
        for key, value in metadata.items():
            file.write(f"{key}: {value}\n")
    logger.info(f"Métadonnées sauvegardées dans le fichier: {metadata_file}")
    
    # Sauvegarder les liens
    links_file = os.path.join(folder, 'links.txt')
    with open(links_file, 'w', encoding='utf-8') as file:
        for link in links:
            file.write(f"{link}\n")
    logger.info(f"Liens sauvegardés dans le fichier: {links_file}")

    # Sauvegarder les fichiers CSS
    css_file = os.path.join(folder, 'css_files.txt')
    with open(css_file, 'w', encoding='utf-8') as file:
        for css in css_files:
            file.write(f"{css}\n")
    logger.info(f"Fichiers CSS sauvegardés dans le fichier: {css_file}")

def get_page_title(html_content):
    """
    Extraire le titre de la page HTML.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    title_tag = soup.find('title')
    return title_tag.get_text().strip() if title_tag else 'untitled'

def clean_filename(filename):
    """
    Nettoyer le nom de fichier en remplaçant les caractères invalides.
    """
    return "".join([c if c.isalnum() else "_" for c in filename])

def fetch_and_save_css(css_files, folder):
    """
    Récupérer et sauvegarder les fichiers CSS.
    """
    css_folder = os.path.join(folder, 'css')
    os.makedirs(css_folder, exist_ok=True)
    for css_url in css_files:
        logger.info(f"Récupération du fichier CSS: {css_url}")
        try:
            response = requests.get(css_url)
            response.raise_for_status()
            css_content = response.text
            css_filename = clean_filename(os.path.basename(css_url))
            save_file(css_content, css_folder, css_filename)
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération du fichier CSS {css_url}: {e}")

def explore_links_recursively(base_url, folder, visited=set(), depth=0, max_depth=2):
    """
    Explorer les liens et sauvegarder leur contenu HTML de manière récursive.
    """
    if depth > max_depth:
        return

    if base_url in visited:
        return

    visited.add(base_url)
    html_content = fetch_html(base_url)
    if not html_content:
        return

    page_title = get_page_title(html_content)
    safe_title = clean_filename(page_title)
    filename = f"{safe_title}.html"
    save_file(html_content, folder, filename)

    metadata, links, css_files = extract_site_info(html_content, base_url)
    save_site_info(folder, metadata, links, css_files)
    fetch_and_save_css(css_files, folder)

    for link in links:
        explore_links_recursively(link, folder, visited, depth + 1, max_depth)
        sleep(1)  # Petite pause pour éviter de surcharger le serveur

def main():
    url = os.getenv('SCRAPING_URL', 'https://example.com')
    logger.info(f"Récupération du contenu de l'URL: {url}")
    
    # Extraire le nom de domaine pour le dossier
    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc
    folder_name = os.path.join(os.getcwd(), domain_name)
    
    explore_links_recursively(url, folder_name)

# Décommenter pour exécuter le script
if __name__ == "__main__":
    main()
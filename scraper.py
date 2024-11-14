import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set, Dict, List
import mimetypes
import tkinter as tk
from tkinter import messagebox
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
import random
import threading

class WebsiteScraper:
    def __init__(self, base_url: str, output_dir: str, proxies: List[str] = None):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.visited_urls: Set[str] = set()
        self.dirs = {
            'html': os.path.join(output_dir, 'html'),
            'css': os.path.join(output_dir, 'css'),
            'js': os.path.join(output_dir, 'js'),
            'images': os.path.join(output_dir, 'images'),
            'fonts': os.path.join(output_dir, 'fonts'),
            'json': os.path.join(output_dir, 'json'),
            'media': os.path.join(output_dir, 'media'),
            'misc': os.path.join(output_dir, 'misc'),
            'xml': os.path.join(output_dir, 'xml'),
            'pdf': os.path.join(output_dir, 'pdf'),
            'zip': os.path.join(output_dir, 'zip'),
            'doc': os.path.join(output_dir, 'doc'),
            'xls': os.path.join(output_dir, 'xls'),
            'ppt': os.path.join(output_dir, 'ppt'),
            'svg': os.path.join(output_dir, 'svg'),
            'ico': os.path.join(output_dir, 'ico'),
            'webp': os.path.join(output_dir, 'webp'),
            'txt': os.path.join(output_dir, 'txt'),
            'api': os.path.join(output_dir, 'api'),
            'server': os.path.join(output_dir, 'server'),
            'config': os.path.join(output_dir, 'config')
        }
        
        self.user_agent = UserAgent()
        self.session.headers.update({'User-Agent': self.user_agent.random})
        
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.proxies = proxies if proxies else []
        self.proxy_index = 0

    def create_directories(self):
        for directory in self.dirs.values():
            os.makedirs(directory, exist_ok=True)

    def get_file_extension(self, url: str, content_type: str = None) -> str:
        ext = os.path.splitext(urlparse(url).path)[1]
        if ext:
            return ext.lower()

        if content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
            if ext:
                return ext

        content_type_map = {
            'text/html': '.html',
            'text/css': '.css',
            'application/javascript': '.js',
            'application/json': '.json',
            'text/plain': '.txt',
            'application/xml': '.xml',
            'application/pdf': '.pdf',
            'application/zip': '.zip',
            'application/msword': '.doc',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.ms-powerpoint': '.ppt',
            'image/svg+xml': '.svg',
            'image/x-icon': '.ico',
            'image/webp': '.webp'
        }
        return content_type_map.get(content_type, '.txt')

    def determine_directory(self, url: str, content_type: str = None) -> str:
        ext = self.get_file_extension(url, content_type).lower()
        
        if ext in ['.html', '.htm']:
            return self.dirs['html']
        elif ext in ['.css', '.scss', '.less']:
            return self.dirs['css']
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            return self.dirs['js']
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']:
            return self.dirs['images']
        elif ext in ['.woff', '.woff2', '.ttf', '.eot', '.otf']:
            return self.dirs['fonts']
        elif ext in ['.json']:
            return self.dirs['json']
        elif ext in ['.mp3', '.mp4', '.wav', '.ogg', '.webm']:
            return self.dirs['media']
        elif ext in ['.xml']:
            return self.dirs['xml']
        elif ext in ['.pdf']:
            return self.dirs['pdf']
        elif ext in ['.zip']:
            return self.dirs['zip']
        elif ext in ['.doc', '.docx']:
            return self.dirs['doc']
        elif ext in ['.xls', '.xlsx']:
            return self.dirs['xls']
        elif ext in ['.ppt', '.pptx']:
            return self.dirs['ppt']
        elif ext in ['.svg']:
            return self.dirs['svg']
        elif ext in ['.ico']:
            return self.dirs['ico']
        elif ext in ['.webp']:
            return self.dirs['webp']
        elif ext in ['.txt']:
            return self.dirs['txt']
        elif ext in ['.php', '.py', '.js', '.rb', '.java', '.go', '.sh', '.cpp', '.c', '.cs', '.pl', '.r', '.swift', '.kt', '.scala', '.groovy']:
            return self.dirs['server']
        elif ext in ['.env', '.json', '.yaml', '.yml']:
            return self.dirs['config']
        else:
            return self.dirs['misc']

    def download_file(self, url: str, directory: str = None) -> bool:
        if url in self.visited_urls:
            return False
            
        self.visited_urls.add(url)
        
        try:
            response = self.session.get(url, timeout=10, proxies=self.get_proxy())
            if response.status_code != 200:
                print(f"Failed to download {url}: Status code {response.status_code}")
                return False

            content_type = response.headers.get('content-type', '').lower()
            
            if directory is None:
                directory = self.determine_directory(url, content_type)

            filename = os.path.basename(urlparse(url).path)
            if not filename:
                ext = self.get_file_extension(url, content_type)
                filename = f"file_{len(self.visited_urls)}{ext}"

            filepath = os.path.join(directory, filename)
            
            mode = 'wb' if 'text' not in content_type else 'w'
            with open(filepath, mode, encoding='utf-8' if mode == 'w' else None) as f:
                if mode == 'w':
                    f.write(response.text)
                else:
                    f.write(response.content)
                    
            print(f"Downloaded: {filename}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")
            return False

    def extract_urls(self, soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
        urls = {
            'css': [],
            'js': [],
            'images': [],
            'fonts': [],
            'links': [],
            'xml': [],
            'pdf': [],
            'zip': [],
            'doc': [],
            'xls': [],
            'ppt': [],
            'svg': [],
            'ico': [],
            'webp': [],
            'txt': [],
            'api': [],
            'server': [],
            'config': [],
            'manifest': [],
            'license': []
        }
        
        for tag in soup.find_all('link', rel='stylesheet'):
            if href := tag.get('href'):
                urls['css'].append(urljoin(base_url, href))
                
        for style in soup.find_all('style'):
            imports = re.findall(r'@import\s+[\'"]([^\'"]+)[\'"]', style.string or '')
            urls['css'].extend([urljoin(base_url, url) for url in imports])
                
        for tag in soup.find_all('script', src=True):
            urls['js'].append(urljoin(base_url, tag['src']))
            
        for tag in soup.find_all(['img', 'picture', 'source']):
            if src := tag.get('src'):
                urls['images'].append(urljoin(base_url, src))
            if srcset := tag.get('srcset'):
                for src in srcset.split(','):
                    url = src.strip().split(' ')[0]
                    urls['images'].append(urljoin(base_url, url))
                    
        for style in soup.find_all('style'):
            if style.string:
                fonts = re.findall(r'url\([\'"]?([^\'"]+?\.(?:woff2?|ttf|eot|otf))[\'"]?\)', style.string)
                urls['fonts'].extend([urljoin(base_url, url) for url in fonts])
                
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if href.startswith(base_url) or not urlparse(href).netloc:
                urls['links'].append(urljoin(base_url, href))
                
        for tag in soup.find_all('link', href=True):
            if 'xml' in tag.get('type', ''):
                urls['xml'].append(urljoin(base_url, tag['href']))
                
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if href.endswith('.pdf'):
                urls['pdf'].append(urljoin(base_url, href))
            elif href.endswith('.zip'):
                urls['zip'].append(urljoin(base_url, href))
            elif href.endswith('.doc') or href.endswith('.docx'):
                urls['doc'].append(urljoin(base_url, href))
            elif href.endswith('.xls') or href.endswith('.xlsx'):
                urls['xls'].append(urljoin(base_url, href))
            elif href.endswith('.ppt') or href.endswith('.pptx'):
                urls['ppt'].append(urljoin(base_url, href))
            elif href.endswith('.svg'):
                urls['svg'].append(urljoin(base_url, href))
            elif href.endswith('.ico'):
                urls['ico'].append(urljoin(base_url, href))
            elif href.endswith('.webp'):
                urls['webp'].append(urljoin(base_url, href))
            elif href.endswith('.txt'):
                urls['txt'].append(urljoin(base_url, href))
            elif href.endswith('.php') or href.endswith('.py') or href.endswith('.js') or href.endswith('.rb') or href.endswith('.java') or href.endswith('.go') or href.endswith('.sh') or href.endswith('.cpp') or href.endswith('.c') or href.endswith('.cs') or href.endswith('.pl') or href.endswith('.r') or href.endswith('.swift') or href.endswith('.kt') or href.endswith('.scala') or href.endswith('.groovy'):
                urls['server'].append(urljoin(base_url, href))
            elif href.endswith('.env') or href.endswith('.json') or href.endswith('.yaml') or href.endswith('.yml'):
                urls['config'].append(urljoin(base_url, href))
                
        # Detect API endpoints
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if href.startswith('/api/') or href.startswith('/v1/') or href.startswith('/v2/') or href.startswith('/v3/'):
                urls['api'].append(urljoin(base_url, href))
        
        # Detect manifest.json
        for tag in soup.find_all('link', href=True):
            if tag.get('rel') == ['manifest']:
                urls['manifest'].append(urljoin(base_url, tag['href']))
        
        # Detect license files referenced in comments
        for tag in soup.find_all('script', src=True):
            js_url = urljoin(base_url, tag['src'])
            js_response = self.session.get(js_url, proxies=self.get_proxy())
            if js_response.status_code == 200:
                license_matches = re.findall(r'LICENSE\.txt', js_response.text)
                for match in license_matches:
                    license_url = urljoin(js_url, match)
                    urls['license'].append(license_url)
        
        return urls

    def scrape_page(self, url: str, download_linked_pages: bool = False) -> None:
        try:
            response = self.session.get(url, proxies=self.get_proxy())
            soup = BeautifulSoup(response.text, 'html.parser')
            
            page_name = os.path.basename(urlparse(url).path) or 'index.html'
            with open(os.path.join(self.dirs['html'], page_name), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            urls = self.extract_urls(soup, url)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for category, url_list in urls.items():
                    if category != 'links':
                        for url in url_list:
                            futures.append(executor.submit(self.download_file, url))
                
                for future in as_completed(futures):
                    future.result()
                
                if download_linked_pages:
                    for link in urls['links']:
                        if link not in self.visited_urls:
                            executor.submit(self.scrape_page, link, False)
                            
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    def scrape(self, download_linked_pages: bool = False):
        print(f"Starting to scrape {self.base_url}")
        self.create_directories()
        self.scrape_page(self.base_url, download_linked_pages)
        print(f"\nScraping complete. Files saved in {self.output_dir}")
        print(f"Total files downloaded: {len(self.visited_urls)}")

    def get_proxy(self):
        if self.proxies:
            proxy = self.proxies[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
            return {'http': proxy, 'https': proxy}
        return None

class ScraperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Scraper")
        
        self.url_label = tk.Label(root, text="Website URL:")
        self.url_label.pack()
        
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack()
        
        self.frontend_var = tk.BooleanVar()
        self.backend_var = tk.BooleanVar()
        
        self.frontend_check = tk.Checkbutton(root, text="Scrape Frontend", variable=self.frontend_var)
        self.frontend_check.pack()
        
        self.backend_check = tk.Checkbutton(root, text="Scrape Backend", variable=self.backend_var)
        self.backend_check.pack()
        
        self.scrape_button = tk.Button(root, text="Start Scraping", command=self.start_scraping)
        self.scrape_button.pack()
        
        self.output_text = tk.Text(root, height=10, width=50)
        self.output_text.pack()
        
    def start_scraping(self):
        website_url = self.url_entry.get()
        if not website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        
        website_name = urlparse(website_url).netloc.split('.')[-2]
        output_directory = f"{website_name}_website_files"
        scraper = WebsiteScraper(website_url, output_directory)
        
        self.output_text.insert(tk.END, f"Starting to scrape {website_url}\n")
        self.root.update()
        
        try:
            if self.frontend_var.get():
                scraper.scrape(download_linked_pages=True)
            elif self.backend_var.get():
                scraper.scrape(download_linked_pages=False)
            else:
                scraper.scrape(download_linked_pages=True)
            
            self.output_text.insert(tk.END, f"\nScraping complete. Files saved in {output_directory}\n")
            self.output_text.insert(tk.END, f"Total files downloaded: {len(scraper.visited_urls)}\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperUI(root)
    root.mainloop()
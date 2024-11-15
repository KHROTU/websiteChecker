# Website Checker

A Python script to scrape websites and download their resources (HTML, CSS, JS, images, etc.), and check for XSS/SQL/CSRF vulnerabilities. The script also includes advanced features like user-agent spoofing, proxy rotation, and retry logic to ensure efficient and undetectable scraping.

## Features

- **Multi-threaded Scraping**: Utilizes multi-threading to speed up the scraping process.
- **Extensive File Type Support**: Downloads various file types including HTML, CSS, JS, images, fonts, JSON, media, XML, PDF, ZIP, documents, and more.
- **User-Agent Rotation**: Randomly changes User-Agent headers to avoid detection and bans.
- **Proxy Support**: Supports rotating proxies to bypass IP-based rate limits and bans.
- **Selenium Integration**: Uses Selenium for dynamic content scraping and handling JavaScript-heavy websites.
- **Tor IP Rotation**: Option to rotate Tor IP addresses for enhanced anonymity.
- **Customizable Output Directories**: Organizes downloaded files into separate directories based on file types.
- **Frontend and Backend Scraping**: Allows selective scraping of frontend (HTML, CSS, JS, etc.) or backend (server-side scripts, configurations, etc.) files.
- **Advanced Anti-Detection Techniques**: Includes advanced techniques to mimic real user behavior and avoid detection.
- **Efficient Resource Handling**: Implements resource deduplication and optimized parallel processing.
- **Malicious Payloads**: Includes tools to test for XSS, SQL injection, directory traversal, CSRF, and file upload vulnerabilities.
- **Stealthy Navigation**: Mimics human-like browsing patterns with random delays and actions.
- **Error Handling and Resilience**: Advanced retry mechanisms and enhanced error logging for better analysis.

## Requirements

- Python 3.7+
- `requests` library
- `beautifulsoup4` library
- `concurrent.futures` library
- `mimetypes` library
- `tkinter` library
- `fake_useragent` library
- `selenium` library
- `stem` library (for Tor IP rotation)
- `webdriver-manager` library (optional, for managing Selenium webdrivers)
- `tor` service running (for Tor IP rotation)

## Disclaimer

- Ensure you have the necessary permissions to scrape the target website. Unauthorized scraping may violate terms of service and legal regulations.
- Use proxies and Tor IP rotation responsibly to avoid overloading servers and to maintain anonymity.

## License

This project is licensed under the MIT License.
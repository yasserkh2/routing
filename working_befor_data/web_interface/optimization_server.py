import http.server
import socketserver
import os
import sys
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastAPI app
from app.api.main import app
import uvicorn
import threading
import time

# Configuration
WEB_PORT = 8080
API_PORT = 8000
API_HOST = "localhost"
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

class OptimizationRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the optimization web interface"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=directory, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # Serve the optimization results page
        if parsed_path.path == "/" or parsed_path.path == "":
            self.path = "/optimization_results.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
        # Proxy API requests
        if parsed_path.path.startswith("/api/"):
            return self.proxy_api_request("GET", parsed_path.path, None)
        
        # Serve static files
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        # Proxy API requests
        if parsed_path.path.startswith("/api/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            return self.proxy_api_request("POST", parsed_path.path, body)
        
        # Not found
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")
    
    def proxy_api_request(self, method, path, body):
        """Proxy requests to the API server"""
        try:
            url = f"{API_BASE_URL}{path}"
            headers = {
                "Content-Type": "application/json"
            }
            
            req = urllib.request.Request(
                url=url,
                data=body,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.getheaders():
                    if header.lower() != "transfer-encoding":
                        self.send_header(header, value)
                
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            error_message = {
                "error": str(e),
                "message": f"API request failed with status {e.code}"
            }
            
            self.wfile.write(json.dumps(error_message).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            error_message = {
                "error": str(e),
                "message": "Internal server error"
            }
            
            self.wfile.write(json.dumps(error_message).encode())

def start_api_server():
    """Start the FastAPI server in a separate thread"""
    uvicorn.run(app, host=API_HOST, port=API_PORT)

def start_web_server():
    """Start the web server"""
    with socketserver.TCPServer(("", WEB_PORT), OptimizationRequestHandler) as httpd:
        print(f"Web server running at http://localhost:{WEB_PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Start API server in a separate thread
    api_thread = threading.Thread(target=start_api_server)
    api_thread.daemon = True
    api_thread.start()
    
    # Wait for API server to start
    print(f"Starting API server at {API_BASE_URL}...")
    time.sleep(2)
    
    # Start web server
    print(f"Starting web server at http://localhost:{WEB_PORT}...")
    start_web_server()
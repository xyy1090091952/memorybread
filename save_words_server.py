import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import glob
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform
import sys
import traceback

# 确保在正确的目录下运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 创建必要的目录
if not os.path.exists('database'):
    os.makedirs('database')
if not os.path.exists('images'):
    os.makedirs('images')

class DatabaseManager:
    def __init__(self, data_dir='database'):
        self.data_dir = data_dir
        self.words = []
        self.lock = threading.Lock()
        self.load_all_files()
        
        # 设置文件变更监听
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            self.event_handler = FileChangeHandler(self)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, path=self.data_dir)
            self.observer.start()
            self.has_watchdog = True
        except ImportError:
            print('警告: watchdog未安装，文件变更监听功能不可用')
            print('尝试自动安装watchdog模块...')
            try:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'watchdog'])
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler
                self.event_handler = FileChangeHandler(self)
                self.observer = Observer()
                self.observer.schedule(self.event_handler, path=self.data_dir)
                self.observer.start()
                self.has_watchdog = True
                print('watchdog模块安装成功，文件变更监听功能已启用')
            except Exception as e:
                print(f'自动安装watchdog模块失败: {str(e)}')
                print('服务器将以降级模式运行，文件变更监听功能不可用')
                self.has_watchdog = False
    
    def load_all_files(self):
        with self.lock:
            self.words = []
            for file_path in glob.glob(os.path.join(self.data_dir, 'words*.json')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.words.extend(data)
                except Exception as e:
                    print(f"Error loading {file_path}: {str(e)}")
    
    def save_to_file(self, file_path, data):
        with self.lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
    
    def get_all_words(self):
        with self.lock:
            return self.words.copy()
    
    def add_words(self, new_words):
        with self.lock:
            self.words.extend(new_words)
            self.save_to_file(os.path.join(self.data_dir, 'words.json'), self.words)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.db_manager.load_all_files()

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db_manager = DatabaseManager()
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        if self.path == '/save_words':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                words = json.loads(post_data)
                self.db_manager.add_words(words)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                print(f"Error in POST /save_words: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        try:
            if self.path == '/words.json':
                words = self.db_manager.get_all_words()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(words).encode())
            elif self.path == '/import_words':
                try:
                    words = []
                    # 使用os.path.join来处理跨平台路径
                    classtext_dir = 'classtext'
                    if not os.path.exists(classtext_dir):
                        os.makedirs(classtext_dir)
                    
                    for file_path in glob.glob(os.path.join(classtext_dir, '*.txt')):
                        # 使用os.path.basename和os.path.splitext来安全地处理文件名
                        filename = os.path.basename(file_path)
                        lesson = int(filename.split('课')[0])
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = [line.strip() for line in f.readlines() if line.strip()]
                            
                        for i in range(4, len(lines), 4):
                            if i+3 < len(lines):
                                word = {
                                    'kana': lines[i],
                                    'kanji': lines[i+1],
                                    'meaning': lines[i+2],
                                    'example': lines[i+3],
                                    'lesson': lesson
                                }
                                words.append(word)
                    
                    with open(os.path.join(self.data_dir, 'words.json'), 'w', encoding='utf-8') as f:
                        json.dump(words, f, ensure_ascii=False, indent=4)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'count': len(words)}).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            elif self.path == '/' or self.path == '/index.html':
                with open('index.html', 'r', encoding='utf-8') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f.read().encode())
            elif self.path.startswith('/images/'):
                file_path = os.path.join(*self.path[1:].split('/'))
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        self.send_response(200)
                        if file_path.endswith('.png'):
                            self.send_header('Content-type', 'image/png')
                        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                            self.send_header('Content-type', 'image/jpeg')
                        elif file_path.endswith('.gif'):
                            self.send_header('Content-type', 'image/gif')
                        elif file_path.endswith('.svg'):
                            self.send_header('Content-type', 'image/svg+xml')
                        else:
                            self.send_header('Content-type', 'application/octet-stream')
                        self.end_headers()
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"Error in GET {self.path}: {str(e)}")
            self.send_response(500)
            self.end_headers()

def main():
    try:
        port = 7023
        while True:
            try:
                server = HTTPServer(('localhost', port), RequestHandler)
                print(f'Starting server at http://localhost:{port}')
                server.serve_forever()
                break
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    print(f'Port {port} is in use, trying next port...')
                    port += 1
                    time.sleep(3)
                else:
                    raise
            except KeyboardInterrupt:
                print('\nShutting down server...')
                server.server_close()
                print('Server stopped')
                break
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()
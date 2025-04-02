import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import glob
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DatabaseManager:
    def __init__(self, data_dir='database'):
        self.data_dir = data_dir
        self.words = []
        self.dictionaries = []
        self.lock = threading.Lock()
        self.load_dictionaries()
        self.load_all_files()
        
        # 设置文件变更监听
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            self.event_handler = FileChangeHandler(self)
            self.observer = Observer()
            # 检查是否已经存在监听器
            if not hasattr(self, '_watch_scheduled'):
                self.observer.schedule(self.event_handler, path=self.data_dir)
                self.observer.start()
                self._watch_scheduled = True
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
                if not hasattr(self, '_watch_scheduled'):
                    self.observer.schedule(self.event_handler, path=self.data_dir)
                    self.observer.start()
                    self._watch_scheduled = True
                print('watchdog模块安装成功，文件变更监听功能已启用')
            except Exception as e:
                print(f'自动安装watchdog模块失败: {str(e)}')
                print('服务器将以降级模式运行，文件变更监听功能不可用')
                self.has_watchdog = False
    
    def load_dictionaries(self):
        """加载词典配置"""
        try:
            with open(os.path.join(self.data_dir, 'dictionaries.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.dictionaries = data.get('dictionaries', [])
        except Exception as e:
            print(f"Error loading dictionaries: {e}")
            self.dictionaries = []
    
    def load_all_files(self):
        """加载所有JSON文件"""
        self.words = []
        print(f"开始加载文件，词典数量: {len(self.dictionaries)}")
        for dictionary in self.dictionaries:
            print(f"处理词典: {dictionary['id']}")
            for pattern in dictionary.get('words_files', []):
                # 处理相对路径
                if '/' in pattern:
                    # 如果模式包含目录，直接使用完整路径
                    file_pattern = os.path.join(self.data_dir, pattern)
                else:
                    # 如果只有文件名，则使用词典目录
                    file_pattern = os.path.join(self.data_dir, dictionary['id'], pattern)
                
                print(f"搜索文件模式: {file_pattern}")
                # 使用glob处理通配符
                for file_path in glob.glob(file_pattern):
                    print(f"找到文件: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            print(f"文件内容类型: {type(data)}")
                            if isinstance(data, list):
                                # 处理新的数据结构
                                print(f"处理列表类型数据，项目数量: {len(data)}")
                                for item in data:
                                    if isinstance(item, dict) and 'data' in item:
                                        word = item['data']
                                        word['lesson'] = item['lesson']  # 保存课程号
                                        word['dictionary'] = dictionary['id']  # 设置词典ID
                                        print(f"添加单词，词典: {word['dictionary']}, 课程: {word['lesson']}")
                                        self.words.append(word)
                            elif isinstance(data, dict) and 'data' in data:
                                # 处理旧的数据结构
                                print(f"处理字典类型数据，单词数量: {len(data['data'])}")
                                for word in data['data']:
                                    word['lesson'] = data['lesson']  # 保存课程号
                                    word['dictionary'] = dictionary['id']  # 设置词典ID
                                    print(f"添加单词，词典: {word['dictionary']}, 课程: {word['lesson']}")
                                self.words.extend(data['data'])
                    except Exception as e:
                        print(f"Error loading {file_path}: {e}")
        print(f"加载完成，总单词数: {len(self.words)}")
    
    def save_to_file(self, file_path, data):
        with self.lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
    
    def get_all_words(self):
        with self.lock:
            # 将单词数据转换为正确的格式
            formatted_words = []
            for word in self.words:
                formatted_word = {
                    "lesson": word.get("lesson", 0),  # 使用保存的课程号
                    "dictionary": word.get("dictionary", ""),  # 将词典ID移到顶层
                    "data": {
                        "假名": word.get("假名", ""),
                        "汉字": word.get("汉字", ""),
                        "中文": word.get("中文", ""),
                        "例句": word.get("例句", ""),
                        "词性": word.get("词性", "")
                    }
                }
                formatted_words.append(formatted_word)
            return formatted_words
    
    def get_dictionaries(self):
        with self.lock:
            return self.dictionaries.copy()
    
    def add_words(self, words, dictionary_id=None):
        """添加新单词到数据库"""
        if not dictionary_id:
            dictionary_id = 'everyones_japanese'  # 默认添加到大家的日语词典
        
        # 确保词典目录存在
        dictionary_dir = os.path.join(self.data_dir, dictionary_id)
        os.makedirs(dictionary_dir, exist_ok=True)
        
        # 获取当前最大的课时号
        max_lesson = 0
        for file_name in os.listdir(dictionary_dir):
            if file_name.startswith('words') and file_name.endswith('.json'):
                try:
                    lesson_num = int(file_name[5:-5])  # 提取课时号
                    max_lesson = max(max_lesson, lesson_num)
                except ValueError:
                    continue
        
        # 创建新的课时文件
        new_lesson = max_lesson + 1
        file_path = os.path.join(dictionary_dir, f'words{new_lesson}.json')
        
        # 为每个单词添加词典ID
        for word in words:
            word['dictionary'] = dictionary_id
        
        data = {
            "lesson": new_lesson,
            "data": words
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # 重新加载所有文件
        self.load_all_files()
        return new_lesson

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.db_manager.load_all_files()

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db_manager = None
        super().__init__(*args, **kwargs)
    
    def setup(self):
        super().setup()
        if self.db_manager is None:
            self.db_manager = DatabaseManager()
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/words.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            words = self.db_manager.get_all_words()
            response = json.dumps({"words": words}, ensure_ascii=False).encode('utf-8')
            self.wfile.write(response)
        elif self.path == '/dictionaries.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            dictionaries = self.db_manager.get_dictionaries()
            response = json.dumps({"dictionaries": dictionaries}, ensure_ascii=False).encode('utf-8')
            self.wfile.write(response)
        elif self.path.startswith('/images/'):
            try:
                with open(self.path[1:], 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/png')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404)
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/add_words':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 获取词典ID，如果没有提供则使用默认值
            dictionary_id = data.get('dictionary_id', 'everyones_japanese')
            
            # 添加新单词
            lesson = self.db_manager.add_words(data['words'], dictionary_id)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({'status': 'success', 'lesson': lesson}, ensure_ascii=False).encode('utf-8')
            self.wfile.write(response)
        else:
            self.send_error(404)

if __name__ == '__main__':
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
                time.sleep(3)  # 增加延迟时间确保端口完全释放
            else:
                raise
        except KeyboardInterrupt:
            print('\nShutting down server...')
            server.server_close()
            print('Server stopped')
            break
import json
import os

def split_words_by_lesson():
    # 定义输入文件路径
    input_files = [
        os.path.join('database', 'words.json'),
        os.path.join('database', 'words2.json')
    ]
    
    # 初始化字典来存储按lesson分组的数据
    lesson_data = {}
    
    # 读取并合并所有输入文件的数据
    for input_file in input_files:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for item in data:
                    lesson = item['lesson']
                    if lesson not in lesson_data:
                        lesson_data[lesson] = []
                    lesson_data[lesson].append(item)
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
    
    # 为每个lesson创建输出文件
    for lesson, items in lesson_data.items():
        output_file = os.path.join('database', f'words{lesson}.json')
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=4)
            print(f"Successfully created {output_file}")
        except Exception as e:
            print(f"Error writing {output_file}: {e}")

if __name__ == "__main__":
    split_words_by_lesson()
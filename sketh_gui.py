import os
import sqlite3
import plistlib
import json
import logging
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_zip_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'PK\x03\x04'
    except Exception as e:
        logging.error(f"Ошибка при проверке ZIP-файла: {e}")
        return False

def is_sqlite_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
            return header.startswith(b'SQLite format 3')
    except Exception as e:
        logging.error(f"Ошибка при проверке SQLite-файла: {e}")
        return False

def read_sqlite(file_path):
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value FROM metadata")
        metadata = cursor.fetchall()
        cursor.execute("SELECT name, value FROM payload")
        payload = cursor.fetchall()
        conn.close()
        return metadata, payload
    except sqlite3.Error as e:
        logging.error(f"Ошибка при чтении SQLite базы данных: {e}")
        return [], []

def convert_bplist_to_json(bplist_data):
    try:
        return plistlib.loads(bplist_data)
    except Exception as e:
        logging.error(f"Ошибка при конвертации bplist: {e}")
        return None

def save_to_file(data, file_name):
    try:
        with open(file_name, 'w') as f:
            f.write(data)
    except Exception as e:
        logging.error(f"Ошибка при сохранении файла '{file_name}': {e}")

def save_to_xml(data, file_name):
    try:
        root = ET.Element("data")
        for key, value in data.items():
            item = ET.SubElement(root, "item")
            item.set("name", key)
            item.text = str(value)
        tree = ET.ElementTree(root)
        tree.write(file_name, encoding='utf-8', xml_declaration=True)
    except Exception as e:
        logging.error(f"Ошибка при сохранении XML файла '{file_name}': {e}")

def process_file(file_path):
    if not file_path.endswith('.sketch'):
        logging.error(f"Файл '{file_path}' не имеет расширения .sketch.")
        return "Ошибка: файл не имеет расширения .sketch."

    if is_zip_file(file_path):
        logging.info(f"Файл '{file_path}' является ZIP-архивом. Версия не поддерживается.")
        return "Ошибка: файл является ZIP-архивом."

    if not is_sqlite_file(file_path):
        logging.error(f"Файл '{file_path}' не является SQLite базой данных.")
        return "Ошибка: файл не является SQLite базой данных."

    metadata, payload = read_sqlite(file_path)

    metadata_dict = {name: value for name, value in metadata}
    logging.info(f"Данные из таблицы metadata считаны из файла '{file_path}'.")

    payload_dict = {}
    for name, value in payload:
        if name in ['main', 'UIMetadata']:
            json_data = convert_bplist_to_json(value)
            if json_data is not None:
                payload_dict[name] = json_data

    sketch_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if metadata_dict:
        save_to_file(json.dumps(metadata_dict, indent=4), f"{sketch_name}_metadata.json")
        save_to_xml(metadata_dict, f"{sketch_name}_metadata.xml")
        logging.info(f"Данные metadata сохранены в '{sketch_name}_metadata.json' и '{sketch_name}_metadata.xml'.")
    else:
        logging.warning(f"Нет данных в таблице metadata для файла '{file_path}'.")

    if payload_dict:
        save_to_file(json.dumps(payload_dict, indent=4), f"{sketch_name}_payload.json")
        save_to_xml(payload_dict, f"{sketch_name}_payload.xml")
        logging.info(f"Данные payload сохранены в '{sketch_name}_payload.json' и '{sketch_name}_payload.xml'.")
    else:
        logging.warning(f"Нет данных в таблице payload для файла '{file_path}'.")

    return "Обработка завершена успешно."

def process_files_in_folder(folder_path):
    """Обработка всех файлов в указанной папке."""
    results = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.sketch'):
            file_path = os.path.join(folder_path, file_name)
            result = process_file(file_path)
            results.append(f"{file_name}: {result}")
    return results

def select_file():
    """Выбор файла через диалоговое окно."""
    file_path = filedialog.askopenfilename(filetypes=[("Sketch files", "*.sketch")])
    if file_path:
        result = process_file(file_path)
        messagebox.showinfo("Результат", result)

def select_folder():
    """Выбор папки через диалоговое окно."""
    folder_path = filedialog.askdirectory()
    if folder_path:
        results = process_files_in_folder(folder_path)
        messagebox.showinfo("Результаты", "\n".join(results))

# Создание основного окна
root = tk.Tk()
root.title("Sketch Filee Processor")

# Кнопки для выбора файла и папки
btn_select_file = tk.Button(root, text="Выбрать файл .sketch", command=select_file)
btn_select_file.pack(pady=10)

btn_select_folder = tk.Button(root, text="Выбрать папку", command=select_folder)
btn_select_folder.pack(pady=10)

# Запуск основного цикла
root.mainloop()


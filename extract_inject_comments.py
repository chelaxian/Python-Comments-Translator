#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import re
import os
import argparse
import json

def extract_comments(filename):
    """
    Извлекает docstring-комментарии и однострочные комментарии из указанного файла.
    Исключает f-строки и другие строковые литералы в тройных кавычках.
    
    Args:
        filename (str): Путь к Python файлу
        
    Returns:
        list: Список кортежей (строка, отступ, содержимое, начальная_строка, конечная_строка, тип_комментария)
    """
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Разделяем файл на строки для определения номеров строк
    lines = content.split('\n')
    
    # Находим все комментарии (docstrings и однострочные)
    comments = []
    
    # Получаем все строки кода с тройными кавычками
    triple_quote_patterns = [
        # Исключаем f-строки и другие префиксы строк
        r'(?<!f)(?<!r)(?<!F)(?<!R)(?<!fr)(?<!rf)(?<!Fr)(?<!fR)(?<!FR)(?<!Rf)(?<!rF)(?<!RF)([ \t]*)"""([\s\S]*?)"""',
        r"(?<!f)(?<!r)(?<!F)(?<!R)(?<!fr)(?<!rf)(?<!Fr)(?<!fR)(?<!FR)(?<!Rf)(?<!rF)(?<!RF)([ \t]*)'''([\s\S]*?)'''"
    ]
    
    # Находим все потенциальные docstring-комментарии
    for pattern in triple_quote_patterns:
        for match in re.finditer(pattern, content):
            indent = match.group(1)  # Отступ перед docstring
            comment_content = match.group(2)  # Содержимое docstring
            
            # Определяем начальную и конечную строки docstring
            start_pos = match.start()
            end_pos = match.end()
            
            # Подсчитываем номера строк
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            # Проверяем контекст для определения, является ли это действительно docstring
            is_docstring = is_actual_docstring(content, start_pos, lines, start_line)
            
            if is_docstring:
                # Сохраняем инфо о docstring с учетом отступов
                if pattern.startswith('r"'):
                    # Шаблон с одинарными кавычками
                    full_comment = indent + "'''" + comment_content + "'''"
                else:
                    # Шаблон с двойными кавычками
                    full_comment = indent + '"""' + comment_content + '"""'
                comments.append((full_comment, indent, comment_content, start_line, end_line, 'docstring'))
    
    # Создаем список для отслеживания строк, которые уже обработаны (для избежания дублей)
    processed_lines = set()
    
    # Ищем однострочные комментарии с символом # в начале строки
    # Проходим по всем строкам файла
    for i, line in enumerate(lines):
        line_number = i + 1
        
        # Игнорируем строки внутри уже найденных docstrings
        is_in_docstring = False
        for _, _, _, start_l, end_l, _ in comments:
            if start_l <= line_number <= end_l:
                is_in_docstring = True
                break
        
        if is_in_docstring or line_number in processed_lines:
            continue
            
        # Ищем в строке комментарий, начинающийся с # (учитываем отступы)
        match = re.match(r'^([ \t]*)#(.+)$', line)
        if match:
            indent = match.group(1)  # Отступ перед комментарием
            comment_content = match.group(2).strip()  # Содержимое комментария без #
            
            # Пропускаем пустые комментарии
            if len(comment_content) == 0:
                continue
                
            # Сохраняем инфо о комментарии
            full_comment = indent + '#' + ' ' + comment_content
            comments.append((full_comment, indent, comment_content, line_number, line_number, 'inline'))
            processed_lines.add(line_number)
    
    # Ищем однострочные комментарии с символом # в конце строки
    for i, line in enumerate(lines):
        line_number = i + 1
        
        # Пропускаем уже обработанные строки
        if line_number in processed_lines:
            continue
            
        # Игнорируем строки внутри уже найденных docstrings
        is_in_docstring = False
        for _, _, _, start_l, end_l, _ in comments:
            if start_l <= line_number <= end_l:
                is_in_docstring = True
                break
                
        if is_in_docstring:
            continue
            
        # Ищем комментарий в конце строки (после кода)
        # Обрабатываем случаи типа: code  # комментарий
        match = re.search(r'([^#]*)(#\s*)(.+)$', line)
        if match:
            code_part = match.group(1)  # Часть строки до комментария
            comment_prefix = match.group(2)  # # и пробелы после него
            comment_content = match.group(3).strip()  # Содержимое комментария
            
            # Пропускаем случаи, когда # является частью строки в кавычках
            # Это базовая проверка, не учитывающая все возможные случаи
            quotes_count = code_part.count('"') + code_part.count("'")
            if quotes_count % 2 != 0:  # Нечетное количество кавычек — # может быть в строке
                continue
                
            # Пропускаем пустые комментарии
            if len(comment_content) == 0:
                continue
                
            # Сохраняем полную строку как она есть
            full_comment = line
            # Используем код перед комментарием как "отступ"
            indent = code_part
            comments.append((full_comment, indent, comment_content, line_number, line_number, 'inline_end'))
            processed_lines.add(line_number)
    
    return comments

def is_actual_docstring(content, start_pos, lines, start_line):
    """
    Проверяет, является ли строка в тройных кавычках реальным docstring-комментарием,
    а не обычной строкой в коде.
    
    Args:
        content (str): Содержимое файла
        start_pos (int): Позиция начала строки в тройных кавычках
        lines (list): Список строк файла
        start_line (int): Номер строки начала строки в тройных кавычках
        
    Returns:
        bool: True если это docstring-комментарий, False если это обычная строка
    """
    # Проверяем символ перед открывающими кавычками
    prev_char_pos = start_pos - 1
    if prev_char_pos >= 0:
        # Если перед кавычками есть символ f, r, b и т.д. - это не docstring
        prev_char = content[prev_char_pos]
        if prev_char.isalpha():  # Любая буква перед кавычками (f, r, b, u) указывает на строковый литерал
            return False
    
    # Получаем текущую строку и проверяем, находятся ли кавычки в начале строки (с учетом отступов)
    current_line = lines[start_line - 1]
    stripped_line = current_line.lstrip()
    
    # Если строка начинается с тройных кавычек (после отступов)
    if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
        # Проверяем контекст - строка находится после определения функции/класса или двоеточия
        if start_line > 1:
            prev_line = lines[start_line - 2].strip()
            if prev_line.startswith('def ') or prev_line.startswith('class ') or prev_line.endswith(':'):
                return True
        
        # Если это первая строка файла с тройными кавычками - считаем её docstring модуля
        if start_line == 1:
            return True
            
        # Если после отступов сразу идут тройные кавычки, но перед ними есть код в той же строке,
        # это не docstring (например: result = """строка""")
        if '=' in current_line[:current_line.find('"""' if '"""' in current_line else "'''")]:
            return False
    else:
        # Если строка не начинается с тройных кавычек - это не docstring
        return False
    
    # По умолчанию, если тройные кавычки находятся в начале строки после отступов и перед ними
    # нет префиксов f, r и т.д., считаем это docstring
    return True

def save_comments(comments, output_file, locations_file):
    """
    Сохраняет найденные комментарии в выходной файл и их расположение в файл локаций.
    
    Args:
        comments (list): Список кортежей с информацией о комментариях
        output_file (str): Имя файла для сохранения комментариев
        locations_file (str): Имя файла для сохранения информации о расположении
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, (full, indent, content, start, end, comment_type) in enumerate(comments):
            f.write(f"[COMMENT_{i}]\n{full}\n[/COMMENT_{i}]\n\n")
    
    # Сохраняем информацию о расположении комментариев
    locations = {}
    for i, (full, indent, content, start, end, comment_type) in enumerate(comments):
        locations[f"COMMENT_{i}"] = {
            "start_line": start,
            "end_line": end,
            "indent": indent,
            "type": comment_type,
            "original_comment": content  # Сохраняем оригинальный комментарий для inline_end
        }
    
    with open(locations_file, 'w', encoding='utf-8') as f:
        json.dump(locations, f, indent=2)

def replace_comments(source_file, translations_file, locations_file, output_file=None):
    """
    Заменяет комментарии в исходном файле на переведенные из файла переводов.
    
    Args:
        source_file (str): Исходный Python файл
        translations_file (str): Файл с переведенными комментариями
        locations_file (str): Файл с информацией о расположении комментариев
        output_file (str, optional): Выходной файл (если None, создается копия исходного)
    """
    # Загружаем информацию о расположении комментариев
    with open(locations_file, 'r', encoding='utf-8') as f:
        locations = json.load(f)
    
    # Загружаем переведенные комментарии
    with open(translations_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем переведенные комментарии
    translations = {}
    pattern = r'\[COMMENT_(\d+)\]\n([\s\S]*?)\n\[/COMMENT_\1\]'
    for match in re.finditer(pattern, content):
        comment_id = f"COMMENT_{match.group(1)}"
        translated_content = match.group(2)
        translations[comment_id] = translated_content
    
    # Загружаем исходный файл
    with open(source_file, 'r', encoding='utf-8') as f:
        source_content = f.read()
        source_lines = source_content.splitlines(True)  # Сохраняем символы новой строки
    
    # Если выходной файл не указан, создаем копию с суффиксом _translated
    if output_file is None:
        base_name, ext = os.path.splitext(source_file)
        output_file = f"{base_name}_translated{ext}"
    
    # Создаем новое содержимое файла
    new_content = ""
    i = 0  # Текущая позиция в файле (номер строки)
    
    while i < len(source_lines):
        current_line = i + 1  # Номер текущей строки (для сравнения с позициями комментариев)
        
        # Проверяем, является ли текущая строка началом комментария
        comment_found = False
        for comment_id, location in locations.items():
            start_line = location["start_line"]
            end_line = location["end_line"]
            comment_type = location["type"]
            
            if current_line == start_line:
                comment_found = True
                
                # Если комментарий есть в переводах
                if comment_id in translations:
                    # Добавляем переведенный комментарий
                    if comment_type == 'docstring':
                        # Docstring - добавляем с сохранением форматирования
                        translated_lines = translations[comment_id].splitlines()
                        
                        # Проверяем, есть ли переносы строк в конце последней строки исходного комментария
                        original_last_line = source_lines[end_line - 1]
                        trailing_newlines = ""
                        for ch in reversed(original_last_line):
                            if ch in ['\n', '\r']:
                                trailing_newlines = ch + trailing_newlines
                            else:
                                break
                        
                        # Добавляем переведенные строки с сохранением переносов
                        for t_line in translated_lines:
                            new_content += t_line + '\n'
                        
                        # Если последняя строка не имеет переноса, убираем лишний
                        if not trailing_newlines and new_content.endswith('\n'):
                            new_content = new_content[:-1]
                        
                        # Пропускаем оригинальные строки комментария
                        i = end_line
                    elif comment_type == 'inline':
                        # Обычный однострочный комментарий - просто заменяем
                        new_content += translations[comment_id]
                        if not translations[comment_id].endswith('\n'):
                            new_content += '\n'
                        i += 1
                    elif comment_type == 'inline_end':
                        # Комментарий в конце строки - вытаскиваем только комментарий
                        translated_line = translations[comment_id]
                        
                        # Ищем комментарий в переведенной строке
                        match = re.search(r'(.*?)(#\s*)(.+)$', translated_line)
                        if match:
                            # Извлекаем только переведенную часть комментария
                            translated_comment = match.group(3).strip()
                            
                            # Находим оригинальную строку и заменяем только часть с комментарием
                            original_line = source_lines[i]
                            # Находим позицию символа # в оригинальной строке
                            hash_pos = original_line.find('#')
                            if hash_pos != -1:
                                # Составляем новую строку: код + # + пробел + переведенный комментарий
                                new_line = original_line[:hash_pos] + '# ' + translated_comment
                                # Добавляем перенос строки, если он был в оригинале
                                if original_line.endswith('\n'):
                                    new_line += '\n'
                                new_content += new_line
                            else:
                                # Если почему-то не нашли #, оставляем строку как есть
                                new_content += original_line
                        else:
                            # Если не удалось разобрать переведенную строку, оставляем как есть
                            new_content += translated_line
                        i += 1
                else:
                    # Если комментария нет в переводах, оставляем оригинал
                    if comment_type == 'docstring':
                        for j in range(start_line - 1, end_line):
                            new_content += source_lines[j]
                        i = end_line
                    else:  # inline или inline_end
                        new_content += source_lines[i]
                        i += 1
                
                break  # Прекращаем поиск для текущей строки, т.к. комментарий найден
        
        # Если не нашли комментарий, просто добавляем строку
        if not comment_found:
            new_content += source_lines[i]
            i += 1
    
    # Сохраняем результат
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return output_file

def main():
    parser = argparse.ArgumentParser(
        description='Инструмент для работы с переводами комментариев в Python-файлах',
        epilog="""
Примеры использования:
  python3 extract_inject_comments.py main.py -o RU.txt
    Извлекает все комментарии из main.py и сохраняет их в RU.txt
    Также создает файл RU.txt.locations.json с информацией о расположении комментариев

  python3 extract_inject_comments.py main.py -i EN.txt
    Заменяет комментарии в main.py на переведенные из EN.txt
    Создает копию файла с переведенными комментариями: main_translated.py
    Использует RU.txt.locations.json для определения расположения комментариев
        """
    )
    parser.add_argument('source_file', nargs='?', help='Исходный Python файл')
    parser.add_argument('-o', '--out', help='Выходной файл для сохранения найденных комментариев')
    parser.add_argument('-i', '--in', dest='input_file', help='Входной файл с переведенными комментариями')
    parser.add_argument('-n', '--name-translated', dest='output', help='Выходной файл для сохранения переведенного кода (по умолчанию создается копия с суффиксом _translated)')
    
    args = parser.parse_args()
    
    # Проверяем обязательный аргумент
    if args.source_file is None and not (args.out or args.input_file):
        parser.print_help()
        return
    
    # Режим извлечения комментариев
    if args.out:
        comments = extract_comments(args.source_file)
        locations_file = f"{args.out}.locations.json"
        save_comments(comments, args.out, locations_file)
        
        # Подсчитываем типы найденных комментариев
        docstring_count = sum(1 for _, _, _, _, _, comment_type in comments if comment_type == 'docstring')
        inline_count = sum(1 for _, _, _, _, _, comment_type in comments if comment_type == 'inline')
        inline_end_count = sum(1 for _, _, _, _, _, comment_type in comments if comment_type == 'inline_end')
        
        print(f"Найдено {len(comments)} комментариев:")
        print(f"- {docstring_count} docstring-комментариев")
        print(f"- {inline_count} однострочных комментариев (начало строки)")
        print(f"- {inline_end_count} однострочных комментариев (конец строки)")
        print(f"Комментарии сохранены в файл: {args.out}")
        print(f"Информация о расположении сохранена в файл: {locations_file}")
    
    # Режим замены комментариев
    elif args.input_file:
        locations_file = f"{args.input_file.replace('EN', 'RU')}.locations.json"
        if not os.path.exists(locations_file):
            locations_file = f"{args.input_file}.locations.json"
            if not os.path.exists(locations_file):
                print(f"Ошибка: файл с локациями не найден: {locations_file}")
                return
        
        output_file = replace_comments(args.source_file, args.input_file, locations_file, args.output)
        print(f"Комментарии из файла {args.source_file} переведены и сохранены в файл: {output_file}")
        print(f"Оригинальный файл остался без изменений.")
        print(f"Переводы взяты из файла: {args.input_file}")

if __name__ == "__main__":
    main() 

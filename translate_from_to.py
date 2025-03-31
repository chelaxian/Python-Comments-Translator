#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import re
import sys
from pathlib import Path
from deep_translator import GoogleTranslator

# Предварительно компилируем регулярные выражения для ускорения
_LANG_PATTERNS = {
    'ru': re.compile('[а-яА-ЯёЁ]'),
    'zh': re.compile('[\u4e00-\u9fff]'),
    'ja': re.compile('[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]'),
    'ko': re.compile('[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]'),
    'ar': re.compile('[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufefc]'),
    'he': re.compile('[\u0590-\u05ff\ufb1d-\ufb4f]'),
    'el': re.compile('[\u0370-\u03ff\u1f00-\u1fff]'),
    'hi': re.compile('[\u0900-\u097f]'),
    'th': re.compile('[\u0e00-\u0e7f]')
}

# Используем кэш для ускорения повторных проверок
_CACHE_HITS = {}

def has_text_in_source_language(text, source_lang):
    """
    Проверяет наличие символов исходного языка в тексте (оптимизированная версия)
    
    Args:
        text (str): Текст для проверки
        source_lang (str): Код исходного языка (например, 'ru', 'fr', 'de')
        
    Returns:
        bool: True если текст содержит символы исходного языка
    """
    # Проверяем кэш для ускорения
    cache_key = f"{hash(text)}:{source_lang}"
    if cache_key in _CACHE_HITS:
        return _CACHE_HITS[cache_key]
    
    # Если язык поддерживается напрямую
    if source_lang in _LANG_PATTERNS:
        result = bool(_LANG_PATTERNS[source_lang].search(text))
        _CACHE_HITS[cache_key] = result
        return result
    
    # Для неподдерживаемых языков используем базовую проверку не-ASCII символов
    # При этом используем ранний выход при первом найденном символе
    for c in text:
        if ord(c) > 127:
            _CACHE_HITS[cache_key] = True
            return True
    
    _CACHE_HITS[cache_key] = False
    return False

def translate_comment_block(content, source_lang, target_lang):
    """
    Переводит блок комментария, сохраняя форматирование и отступы
    
    Args:
        content (str): Содержимое блока комментария
        source_lang (str): Исходный язык (код языка)
        target_lang (str): Целевой язык (код языка)
        
    Returns:
        str: Переведенный блок комментария с сохранением форматирования
    """
    # Создаем переводчик
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    # Разбиваем содержимое на строки
    lines = content.splitlines()
    translated_lines = []
    
    for line in lines:
        # Определяем отступы в начале строки
        indent_match = re.match(r'^(\s*)', line)
        indent = indent_match.group(1) if indent_match else ''
        
        # Получаем текст без отступов
        text = line[len(indent):]
        
        # Пропускаем маркеры [COMMENT_x] и [/COMMENT_x]
        if re.match(r'^\[COMMENT_\d+\]$', text) or re.match(r'^\[/COMMENT_\d+\]$', text):
            translated_lines.append(line)
            continue
        
        # Пропускаем пустые строки
        if not text.strip():
            translated_lines.append(line)
            continue
        
        # Проверяем, содержит ли строка код и комментарий в конце строки
        comment_at_end = re.search(r'^([^#]*)(#\s*)(.+)$', text)
        if comment_at_end:
            code_part = comment_at_end.group(1)  # Код перед комментарием
            comment_prefix = comment_at_end.group(2)  # # и пробелы после него
            comment_text = comment_at_end.group(3).strip()  # Комментарий после #
            
            # Проверяем наличие символов исходного языка только в тексте комментария
            if has_text_in_source_language(comment_text, source_lang):
                try:
                    # Переводим только текст комментария
                    translated_comment = translator.translate(comment_text)
                    # Собираем строку обратно: код + # + переведенный комментарий
                    translated_text = code_part + comment_prefix + translated_comment
                    translated_lines.append(indent + translated_text)
                except Exception as e:
                    print(f"Ошибка перевода: {str(e)}, строка: {comment_text}", file=sys.stderr)
                    translated_lines.append(line)  # Оставляем оригинал при ошибке
            else:
                # Нет символов исходного языка в комментарии - оставляем строку без изменений
                translated_lines.append(line)
            continue
        
        # Определяем, есть ли символы исходного языка в строке
        if has_text_in_source_language(text, source_lang):
            try:
                # Если это docstring с тройными кавычками, обрабатываем специально
                if text.startswith('"""') and text.endswith('"""'):
                    inner_text = text[3:-3]
                    if has_text_in_source_language(inner_text, source_lang):
                        translated_inner = translator.translate(inner_text)
                        translated_text = '"""' + translated_inner + '"""'
                    else:
                        translated_text = text
                # Если это начало или конец docstring
                elif text.startswith('"""') or text.endswith('"""'):
                    # Обрабатываем только текстовую часть, сохраняя кавычки
                    quote_start = 3 if text.startswith('"""') else 0
                    quote_end = -3 if text.endswith('"""') else None
                    
                    if quote_end:
                        inner_text = text[quote_start:quote_end]
                        quotes_end = text[quote_end:]
                    else:
                        inner_text = text[quote_start:]
                        quotes_end = ""
                    
                    if has_text_in_source_language(inner_text, source_lang):
                        translated_inner = translator.translate(inner_text)
                        if quote_start > 0:
                            translated_text = '"""' + translated_inner + quotes_end
                        else:
                            translated_text = translated_inner + quotes_end
                    else:
                        translated_text = text
                # Если это однострочный комментарий с символом #
                elif text.startswith('#'):
                    # Сохраняем символ # и пробел после него
                    comment_prefix = re.match(r'^(#\s*)', text).group(1)
                    comment_text = text[len(comment_prefix):]
                    
                    if has_text_in_source_language(comment_text, source_lang):
                        translated_comment = translator.translate(comment_text)
                        translated_text = comment_prefix + translated_comment
                    else:
                        translated_text = text
                else:
                    # Все остальные строки с символами исходного языка
                    translated_text = translator.translate(text)
            except Exception as e:
                print(f"Ошибка перевода: {str(e)}, строка: {text}", file=sys.stderr)
                translated_text = text  # В случае ошибки оставляем оригинальный текст
        else:
            # Нет символов исходного языка, оставляем строку без изменений
            translated_text = text
        
        # Добавляем отступы обратно и добавляем строку к результату
        translated_lines.append(indent + translated_text)
    
    # Объединяем строки обратно в текст
    return '\n'.join(translated_lines)

def translate_comments(input_file, output_file, source_lang, target_lang):
    """
    Переводит комментарии из исходного файла в выходной, сохраняя структуру
    
    Args:
        input_file (str): Путь к входному файлу с комментариями
        output_file (str): Путь к выходному файлу для сохранения переведенных комментариев
        source_lang (str): Исходный язык (код языка)
        target_lang (str): Целевой язык (код языка)
        
    Returns:
        bool: True в случае успешного перевода
    """
    # Проверка наличия файла ввода
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Ошибка: файл {input_file} не найден", file=sys.stderr)
        return False
    
    # Чтение входного файла
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим все блоки комментариев
    pattern = r'(\[COMMENT_\d+\]\n)([\s\S]*?)(\n\[/COMMENT_\d+\])'
    
    # Функция для обработки каждого блока комментариев
    def replace_block(match):
        start_marker = match.group(1)
        comment_content = match.group(2)
        end_marker = match.group(3)
        
        # Переводим содержимое блока
        translated_content = translate_comment_block(comment_content, source_lang, target_lang)
        
        return start_marker + translated_content + end_marker
    
    # Заменяем каждый блок комментариев переведенным блоком
    translated_content = re.sub(pattern, replace_block, content)
    
    # Запись в выходной файл
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated_content)
    
    return True

def get_supported_languages():
    """
    Получает список поддерживаемых языков GoogleTranslator
    
    Returns:
        str: Форматированный список поддерживаемых языков
    """
    try:
        languages = GoogleTranslator().get_supported_languages()
        lang_text = "Поддерживаемые языки:\n"
        
        # Форматируем список языков по 5 в строке
        for i in range(0, len(languages), 5):
            batch = languages[i:i+5]
            lang_text += ", ".join(batch) + "\n"
        
        return lang_text
    except:
        return "Не удалось получить список поддерживаемых языков. Проверьте подключение к интернету."

def main():
    # Получаем список поддерживаемых языков
    supported_languages_info = get_supported_languages()
    
    parser = argparse.ArgumentParser(
        description='Перевод комментариев из одного языка на другой с сохранением форматирования',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Примеры использования:
  python translate_ru_to_en.py input.txt output.txt --source ru --target en
    Переводит комментарии с русского на английский
    
  python translate_ru_to_en.py input.txt output.txt --source fr --target es
    Переводит комментарии с французского на испанский

{supported_languages_info}

Примечание: Для проверки наличия символов исходного языка используются 
специальные регулярные выражения для следующих языков:
ru, zh, ja, ko, ar, he, el, hi, th.
Для других языков используется общая эвристика.
"""
    )
    parser.add_argument('input_file', nargs='?', help='Путь к входному файлу (с исходными комментариями)')
    parser.add_argument('output_file', nargs='?', help='Путь к выходному файлу (для переведенных комментариев)')
    parser.add_argument('-s', '--source', default='ru', help='Исходный язык (по умолчанию: ru)')
    parser.add_argument('-t', '--target', default='en', help='Целевой язык (по умолчанию: en)')
    parser.add_argument('-l', '--list-langs', action='store_true', help='Показать список поддерживаемых языков и выйти')
    
    args = parser.parse_args()
    
    # Показываем справку, если аргументы не указаны
    if args.input_file is None or args.output_file is None:
        if not args.list_langs:
            parser.print_help()
            return
    
    # Показываем список поддерживаемых языков, если запрошено
    if args.list_langs:
        print(supported_languages_info)
        return
    
    print(f"Перевод комментариев из {args.input_file} в {args.output_file}...")
    print(f"Направление перевода: {args.source} → {args.target}")
    
    if translate_comments(args.input_file, args.output_file, args.source, args.target):
        print("Перевод успешно завершен!")
    else:
        print("Произошла ошибка при переводе.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 

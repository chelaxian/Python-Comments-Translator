# Инструменты для перевода комментариев в Python-файлах

[ENGLISH README](https://github.com/chelaxian/Python-Comments-Translator/blob/main/README_EN.md)

Этот набор скриптов позволяет автоматизировать процесс перевода комментариев в Python-файлах между различными языками, сохраняя при этом правильное форматирование и структуру исходного кода.

## Предварительные требования

Для работы скриптов вам потребуется:

1. Python 3.6 или выше
2. Библиотека `deep-translator`:
   ```
   pip install deep-translator
   ```

## Файлы в проекте

- `extract_inject_comments.py` - Скрипт для извлечения комментариев из Python-файлов и их последующей замены
- `translate_from_to.py` - Скрипт для перевода комментариев между различными языками (несмотря на название, не только с русского на английский)

## Пошаговая инструкция использования

### Шаг 1: Извлечение комментариев из Python-файла

```bash
python extract_inject_comments.py ваш_файл.py -o RU.txt
```

Это команда создаст два файла:
- `RU.txt` - содержит все найденные комментарии
- `RU.txt.locations.json` - содержит информацию о расположении комментариев в исходном файле

### Шаг 2: Перевод комментариев

```bash
python translate_from_to.py RU.txt EN.txt -s ru -t en
```

Эта команда переведёт комментарии из `RU.txt` и сохранит их в `EN.txt`. 
Скрипт интеллектуально обрабатывает разные типы комментариев:
- docstring-комментарии (в тройных кавычках)
- однострочные комментарии, начинающиеся с #
- комментарии в конце строки после кода (`код # комментарий`)

#### Перевод между любыми языками

Скрипт поддерживает перевод между любыми языками, поддерживаемыми Google Translate:

```bash
# Французский на испанский
python translate_from_to.py FR.txt ES.txt -s fr -t es

# Китайский на японский
python translate_from_to.py ZH.txt JA.txt -s zh -t ja

# Немецкий на итальянский
python translate_from_to.py DE.txt IT.txt -s de -t it
```

Вы можете увидеть полный список поддерживаемых языков с помощью:

```bash
python translate_from_to.py -l
```

### Шаг 3: Замена комментариев в исходном файле

```bash
python extract_inject_comments.py ваш_файл.py -i EN.txt
```

Эта команда создаст новый файл `ваш_файл_translated.py` с переведенными комментариями. 
Исходный файл останется без изменений.

Если вы хотите сохранить результат в другой файл, используйте параметр `--name-translated` или `-n`:

```bash
python extract_inject_comments.py ваш_файл.py -i EN.txt -n результат.py
```

## Поддерживаемые типы комментариев

Скрипты обрабатывают следующие типы комментариев:

1. **Docstring-комментарии** - многострочные комментарии в тройных кавычках (`"""` или `'''`)
   ```python
   def function():
       """
       Описание функции
       на нескольких строках
       """
   ```

2. **Однострочные комментарии** - комментарии, начинающиеся с символа `#`
   ```python
   # Это однострочный комментарий
   ```

3. **Комментарии в конце строки** - комментарии после кода
   ```python
   x = 5  # Это комментарий в конце строки
   ```

## Особенности и ограничения

- Скрипты сохраняют оригинальное форматирование комментариев
- При переводе комментариев в конце строки переводится только часть после символа `#`, а код остается неизменным
- Скрипт перевода использует Google Translate API через библиотеку `deep-translator`
- Скрипты создают копию оригинального файла, не изменяя исходный код
- Переводятся только комментарии, содержащие символы исходного языка
- Специальное определение символов разных языков доступно для: русского, китайского, японского, корейского, арабского, иврита, греческого, хинди и тайского
- Для других языков используется общая эвристика для обнаружения не-ASCII символов

## Параметры командной строки

### translate_from_to.py

- `input_file` - Путь к входному файлу с комментариями
- `output_file` - Путь для сохранения переведенных комментариев
- `-s`, `--source` - Код исходного языка (по умолчанию: 'ru')
- `-t`, `--target` - Код целевого языка (по умолчанию: 'en')
- `-l`, `--list-langs` - Показать список всех поддерживаемых языков
- `-h`, `--help` - Показать справку

### extract_inject_comments.py

- `source_file` - Исходный Python-файл
- `-o`, `--out` - Выходной файл для сохранения извлеченных комментариев
- `-i`, `--in` - Входной файл с переведенными комментариями
- `-n`, `--name-translated` - Выходной файл для сохранения переведенного кода (по умолчанию создает копию с суффиксом _translated)
- `-h`, `--help` - Показать справку 

# Python Comments Translation Tools

This set of scripts automates the process of translating comments in Python files between different languages while preserving the correct formatting and structure of the source code.

## Prerequisites

You will need:

1. Python 3.6 or higher
2. The `deep-translator` library:
   ```
   pip install deep-translator
   ```

## Project Files

- `extract_inject_comments.py` - Script for extracting comments from Python files and later replacing them
- `translate_from_to.py` - Script for translating comments between different languages (not just Russian to English despite the name)

## Step-by-Step Usage Guide

### Step 1: Extract Comments from a Python File

```bash
python extract_inject_comments.py your_file.py -o RU.txt
```

This command will create two files:
- `RU.txt` - contains all found comments
- `RU.txt.locations.json` - contains information about the location of comments in the source file

### Step 2: Translate Comments

```bash
python translate_from_to.py RU.txt EN.txt -s ru -t en
```

This command will translate comments from `RU.txt` and save them to `EN.txt`. 
The script intelligently processes different types of comments:
- docstring comments (in triple quotes)
- single-line comments starting with #
- end-of-line comments after code (`code # comment`)

#### Translation Between Any Languages

The script supports translation between any languages supported by Google Translate:

```bash
# French to Spanish
python translate_from_to.py FR.txt ES.txt -s fr -t es

# Chinese to Japanese
python translate_from_to.py ZH.txt JA.txt -s zh -t ja

# German to Italian
python translate_from_to.py DE.txt IT.txt -s de -t it
```

You can see the full list of supported languages with:

```bash
python translate_from_to.py -l
```

### Step 3: Replace Comments in the Source File

```bash
python extract_inject_comments.py your_file.py -i EN.txt
```

This command will create a new file `your_file_translated.py` with translated comments.
The original file will remain unchanged.

If you want to save the result to a different file, use the `-n` or `--name-translated` parameter:

```bash
python extract_inject_comments.py your_file.py -i EN.txt -n result.py
```

## Supported Comment Types

The scripts handle the following types of comments:

1. **Docstring comments** - multi-line comments in triple quotes (`"""` or `'''`)
   ```python
   def function():
       """
       Function description
       on multiple lines
       """
   ```

2. **Single-line comments** - comments starting with the `#` symbol
   ```python
   # This is a single-line comment
   ```

3. **End-of-line comments** - comments after code
   ```python
   x = 5  # This is an end-of-line comment
   ```

## Features and Limitations

- The scripts preserve the original formatting of comments
- When translating end-of-line comments, only the part after the `#` symbol is translated, while the code remains unchanged
- The translation script uses the Google Translate API through the `deep-translator` library
- The scripts create a copy of the original file, not changing the source code
- Only comments containing characters in the source language are translated
- Special character pattern detection is available for several languages: Russian, Chinese, Japanese, Korean, Arabic, Hebrew, Greek, Hindi, and Thai
- For other languages, a general heuristic is used to detect non-ASCII characters

## Command Line Parameters

### translate_from_to.py

- `input_file` - Path to the input file with comments
- `output_file` - Path to save translated comments
- `-s`, `--source` - Source language code (default: 'ru')
- `-t`, `--target` - Target language code (default: 'en')
- `-l`, `--list-langs` - Show a list of all supported languages
- `-h`, `--help` - Show help message

### extract_inject_comments.py

- `source_file` - The source Python file
- `-o`, `--out` - Output file to save extracted comments
- `-i`, `--in` - Input file with translated comments
- `-n`, `--name-translated` - Output file for saving translated code (by default creates a copy with the suffix _translated)
- `-h`, `--help` - Show help message 

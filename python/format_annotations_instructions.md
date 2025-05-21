# Annotations Formatter Instructions

This guide explains how to use the `format_annotations.py` script to convert your raw JSON snippets into properly formatted annotations JSON for use with the neume viewer and extractor.

## Quick Start

1. Save your raw JSON snippet to a text file (e.g., `raw_snippet.txt`)
2. Run the formatter script:
   ```bash
   cd python
   python format_annotations.py --input raw_snippet.txt
   ```
3. The formatted annotations will be saved to `../public/real-annotations.json`

## Features

The formatter script:
- Parses raw JSON snippets into properly formatted JSON objects
- Appends to existing annotation files or creates new ones
- Handles duplicate neume types intelligently
- Supports batch processing of multiple files
- Can extract neume types from filenames or manual specification

## Example Workflow

### 1. Single File Processing

For a single raw JSON snippet:

```bash
# Basic usage
python format_annotations.py --input raw_clivis.txt

# Append to existing annotations file
python format_annotations.py --input raw_pes.txt --append

# Manually specify neume type
python format_annotations.py --input raw_urls.txt --type "Virga Simple"

# Specify custom output file
python format_annotations.py --input raw_data.txt --output my_annotations.json
```

### 2. Batch Processing

For processing multiple files at once:

```bash
# Create a directory for your raw snippets
mkdir raw_snippets

# Place your raw JSON snippets in the directory
# Naming them with the neume type helps: Clivis_raw.txt, Pes_raw.txt, etc.

# Process all files in the directory
python format_annotations.py --input raw_snippets --batch --append
```

## Input Format Flexibility

The script is designed to handle various formats:

1. Proper JSON objects (preferred):
   ```
   {"type": "Clivis Episema a", "urls": ["http://..."]}
   ```

2. Partial JSON with type and URLs:
   ```
   "type": "Clivis Episema a", "urls": ["http://..."]
   ```

3. Plain text with URLs:
   ```
   http://... http://... http://...
   ```
   (requires `--type` parameter)

## Tips

- When using batch mode, name your files with the neume type as a prefix (e.g., `Clivis_data.txt`)
- Use `--append` to gradually build up your annotations file with different neume types
- If the script can't determine the neume type, use the `--type` parameter to specify it manually
- Check the output file after running to ensure everything looks correct
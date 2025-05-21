# Neume Image Export Instructions

This guide explains how to export individual neume images from your annotations file.

## Quick Start

1. Save the `export_neumes.py` script to your `python/` directory
2. Run the script with your annotations file:
   ```bash
   cd python
   python export_neumes.py
   ```
3. Find your exported images in `public/exported_neumes/`

## Features

The export script:
- Downloads each individual neume image
- Organizes them by neume type in separate folders
- Creates a metadata CSV file with details about each neume
- Allows filtering by neume type

## Usage Options

### Basic Export

```bash
python export_neumes.py
```

This will:
- Read from `../public/real-annotations.json`
- Export all neume images to `../public/exported_neumes/`
- Create a metadata file at `../public/exported_neumes/neume_metadata.csv`

### Custom Paths

```bash
python export_neumes.py --annotations path/to/annotations.json --output-dir path/to/output
```

### Filter by Neume Type

```bash
python export_neumes.py --filter-type "Clivis Simple"
```

### Custom Metadata Location

```bash
python export_neumes.py --metadata path/to/metadata.csv
```

## Output Structure

The script creates a directory structure like this:

```
exported_neumes/
├── Clivis_Episema_a/
│   ├── 007_000.jpg
│   ├── 007_001.jpg
│   └── ...
├── Clivis_Simple/
│   ├── 007_000.jpg
│   ├── 007_001.jpg
│   └── ...
└── neume_metadata.csv
```

## Metadata File

The CSV file contains detailed information about each neume:
- Filename
- Directory
- Neume type
- Manuscript
- Page
- Coordinates (x, y, width, height)
- Original URL

## Using the Exported Images

These individual images can be used for:
1. Training machine learning models
2. Creating presentations or documentation
3. Detailed analysis of neume characteristics
4. Building a reference dataset
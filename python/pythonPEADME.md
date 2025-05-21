# Python IIIF Extractor Integration

This directory contains Python scripts for extracting neume images from IIIF URLs. These scripts are designed to work with the annotations exported from the React frontend.

## Setup

1. Install required dependencies:
   ```bash
   pip install requests pillow
   ```

2. Ensure you have Python 3.6 or newer installed:
   ```bash
   python --version
   ```

## Available Scripts

### Test Extractor

Tests the basic extraction functionality:

```bash
python test_extractor.py --annotations ../public/sample-annotations.json --output ./extracted_test
```

### Integration Test

Tests the complete integration between the React frontend and Python backend:

```bash
python integration_test.py --annotations ../public/sample-annotations.json --output ./integration_test_output
```

### Advanced IIIF Extractor

For production use, extracting a complete set of neume images:

```bash
python advanced_iiif_extractor.py --annotations /path/to/exported/annotations.json --output /path/to/output/directory
```

### Parallel Extractor

For faster processing of large annotation sets:

```bash
python parallel_extractor.py --annotations /path/to/exported/annotations.json --output /path/to/output/directory --workers 4
```

## Complete Workflow

1. Start the React app:
   ```bash
   cd ..
   npm run dev
   ```

2. Load or create annotations in the React UI

3. Export annotations from the React UI (Save button)

4. Process the exported annotations using one of the Python extractors:
   ```bash
   python advanced_iiif_extractor.py --annotations /path/to/exported/annotations.json --output ./extracted_neumes
   ```

5. View the extracted images in the output directory

## Troubleshooting

If you encounter issues with the integration:

1. Run the integration test to verify all components are working:
   ```bash
   python integration_test.py
   ```

2. Check that your annotations file is valid JSON with the expected structure

3. Make sure all IIIF URLs are accessible and have the correct format

4. Ensure you have proper internet connectivity to download the images
#!/usr/bin/env python3
"""
Integration test script for connecting React frontend with Python backend.
This script:
1. Verifies the annotations JSON format
2. Tests extraction of a sample image
3. Validates that the frontend and backend can work together
"""

import os
import json
import argparse
import sys
import subprocess
from pathlib import Path
from test_extractor import test_extraction, parse_iiif_url, download_image

def validate_annotations_file(file_path):
    """Validate the structure of an annotations JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("✗ Error: Annotations must be a list of objects")
            return False
        
        for idx, item in enumerate(data):
            if 'type' not in item:
                print(f"✗ Error: Item {idx} missing 'type' field")
                return False
            if 'urls' not in item:
                print(f"✗ Error: Item {idx} missing 'urls' field")
                return False
            if not isinstance(item['urls'], list):
                print(f"✗ Error: Item {idx} 'urls' must be a list")
                return False
            
            # Validate first URL if available
            if item['urls'] and len(item['urls']) > 0:
                iiif_info = parse_iiif_url(item['urls'][0])
                if not iiif_info:
                    print(f"✗ Warning: Item {idx} has invalid IIIF URL format")
        
        print(f"✓ Annotations file validated: {len(data)} neume types found")
        return True
    except Exception as e:
        print(f"✗ Error validating annotations file: {e}")
        return False

def test_single_image(annotations_file, output_dir):
    """Test extracting a single image from the annotations file"""
    try:
        # Load annotations
        with open(annotations_file, 'r') as f:
            data = json.load(f)
        
        # Find the first URL
        for item in data:
            if item['urls'] and len(item['urls']) > 0:
                url = item['urls'][0]
                neume_type = item['type']
                
                print(f"Testing extraction of a {neume_type} image")
                iiif_info = parse_iiif_url(url)
                
                if iiif_info:
                    # Create output directory
                    test_dir = os.path.join(output_dir, "single_test")
                    success = download_image(iiif_info, test_dir, "test_image.jpg")
                    
                    if success:
                        print(f"✓ Successfully downloaded test image to {test_dir}/test_image.jpg")
                        return True
                    else:
                        print("✗ Failed to download test image")
                        return False
        
        print("✗ No valid URLs found in the annotations file")
        return False
    except Exception as e:
        print(f"✗ Error testing single image: {e}")
        return False

def check_integration_dependencies():
    """Check if required dependencies are installed"""
    try:
        # Check Python dependencies
        import requests
        from PIL import Image
        
        # Check if npm is available (for React)
        try:
            subprocess.run(["npm", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✓ npm is available")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("✗ npm is not available. React frontend may not work.")
        
        print("✓ Required Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install required packages: pip install requests pillow")
        return False

def main():
    parser = argparse.ArgumentParser(description='Integration test for Neume Mapper and Extractor')
    parser.add_argument('--annotations', default='../public/list_0390-007.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--output', default='./integration_test_output',
                       help='Output directory for test results')
    
    args = parser.parse_args()
    
    print("\n=== Neume Mapper & Extractor Integration Test ===\n")
    
    # Step 1: Check dependencies
    print("Step 1: Checking dependencies...")
    if not check_integration_dependencies():
        print("✗ Dependency check failed. Please install required dependencies.")
        return 1
    print()
    
    # Step 2: Validate annotations file
    print("Step 2: Validating annotations file...")
    if not validate_annotations_file(args.annotations):
        print("✗ Annotations file validation failed.")
        return 1
    print()
    
    # Step 3: Test single image extraction
    print("Step 3: Testing single image extraction...")
    if not test_single_image(args.annotations, args.output):
        print("✗ Single image extraction test failed.")
        return 1
    print()
    
    # Step 4: Test bulk extraction (optional)
    print("Step 4: Testing bulk extraction...")
    if not test_extraction(args.annotations, os.path.join(args.output, "bulk_test")):
        print("✗ Bulk extraction test failed.")
        return 1
    print()
    
    print("✓ All integration tests passed successfully!")
    print(f"Test output is available in: {args.output}")
    print("\nYou can now run your React app and test the complete workflow:")
    print("1. Start the React app: npm run dev")
    print("2. Upload the tested annotations file or view the sample data")
    print("3. Export annotations from the React UI")
    print("4. Process the exported annotations using the Python extractor")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Integration script for working with Neume Viewer React app (Vite) and IIIF Extractor.
This script helps with data conversion and pipeline automation.
"""

import os
import json
import argparse
import subprocess
from advanced_iiif_extractor import IIIFExtractor

def check_dependencies():
    """Check if required Python packages are installed"""
    try:
        import requests
        from PIL import Image
        print("✓ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install required packages: pip install requests pillow")
        return False

def validate_annotations(file_path):
    """Validate the annotations JSON format"""
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
        
        print(f"✓ Annotations file validated: {len(data)} neume types found")
        return True
    except Exception as e:
        print(f"✗ Error validating annotations file: {e}")
        return False

def start_react_app(app_dir):
    """Start the Vite React app for viewing and exporting annotations"""
    if not os.path.exists(os.path.join(app_dir, 'package.json')):
        print(f"✗ Error: {app_dir} does not appear to be a valid React app directory")
        return False
    
    print(f"Starting Vite React app in {app_dir}...")
    try:
        # For Vite, we use 'npm run dev' instead of 'npm start'
        subprocess.Popen(['npm', 'run', 'dev'], cwd=app_dir)
        print("✓ React app started. If it doesn't open automatically, visit http://localhost:3000 in your browser")
        return True
    except Exception as e:
        print(f"✗ Error starting React app: {e}")
        return False

def run_extraction(annotations_file, output_dir, workers=1):
    """Run the IIIF extraction process"""
    if not os.path.exists(annotations_file):
        print(f"✗ Error: Annotations file not found: {annotations_file}")
        return False
    
    if not validate_annotations(annotations_file):
        return False
    
    print(f"Starting extraction from {annotations_file}...")
    if workers > 1:
        # Use parallel extractor
        try:
            from parallel_extractor import main as parallel_main
            import sys
            sys.argv = ['parallel_extractor.py', 
                        '--annotations', annotations_file,
                        '--output', output_dir,
                        '--workers', str(workers)]
            parallel_main()
            return True
        except Exception as e:
            print(f"✗ Error running parallel extraction: {e}")
            return False
    else:
        # Use standard extractor
        try:
            extractor = IIIFExtractor(
                annotations_file=annotations_file,
                output_dir=output_dir
            )
            success = extractor.extract_all()
            if success:
                print(f"✓ Extraction complete. Output saved to {output_dir}")
            return success
        except Exception as e:
            print(f"✗ Error running extraction: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Neume Viewer and Extractor Integration Tool')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Check dependencies command
    check_parser = subparsers.add_parser('check', help='Check dependencies')
    
    # Start React app command
    start_parser = subparsers.add_parser('start', help='Start the React app')
    start_parser.add_argument('--app-dir', default='.', 
                             help='Path to React app directory')
    
    # Validate annotations command
    validate_parser = subparsers.add_parser('validate', help='Validate annotations file')
    validate_parser.add_argument('--file', required=True, 
                               help='Path to annotations JSON file')
    
    # Run extraction command
    extract_parser = subparsers.add_parser('extract', help='Run IIIF extraction')
    extract_parser.add_argument('--file', required=True, 
                              help='Path to annotations JSON file')
    extract_parser.add_argument('--output', default='./extracted_neumes',
                              help='Output directory for extracted images')
    extract_parser.add_argument('--workers', type=int, default=1,
                              help='Number of parallel workers (default: 1)')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        check_dependencies()
    elif args.command == 'start':
        start_react_app(args.app_dir)
    elif args.command == 'validate':
        validate_annotations(args.file)
    elif args.command == 'extract':
        run_extraction(args.file, args.output, args.workers)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
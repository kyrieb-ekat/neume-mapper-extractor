#!/usr/bin/env python3
"""
Integration script to connect React frontend with Python backend.
This script can be called from the React app to:
1. Generate reference images
2. Generate overlay images
3. Extract neume images
4. Return status info back to React

In a production environment, this would be implemented as a proper API.
"""

import os
import json
import argparse
import sys
import time
from pathlib import Path
import subprocess

def setup_directories():
    """Setup necessary directories for the integration"""
    os.makedirs('../public/reference_images', exist_ok=True)
    os.makedirs('./extracted_neumes', exist_ok=True)
    os.makedirs('./logs', exist_ok=True)
    return True

def run_process(command, log_file=None):
    """Run a process and capture output"""
    try:
        if log_file:
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    command,
                    stdout=f,
                    stderr=f,
                    text=True
                )
                process.wait()
                return process.returncode == 0
        else:
            process = subprocess.run(command, capture_output=True, text=True)
            return process.returncode == 0, process.stdout
    except Exception as e:
        print(f"Error running process: {e}")
        return False

def generate_overlays(annotations_file, reference_dir='../public/reference_images'):
    """Generate overlay images for the neumes on reference images"""
    setup_directories()
    
    log_file = './logs/overlays.log'
    command = [
        'python', 
        'generate_overlays.py',
        '--annotations', annotations_file,
        '--reference-dir', reference_dir
    ]
    
    print(f"Generating overlay images from {annotations_file}...")
    success = run_process(command, log_file)
    
    return {
        'success': success,
        'message': 'Overlay images generated successfully!' if success else 'Failed to generate overlay images',
        'log_file': log_file
    }

def generate_reference_images(annotations_file):
    """Generate reference images for the neumes"""
    setup_directories()
    
    log_file = './logs/reference_images.log'
    command = [
        'python', 
        'fetch_reference_images.py',
        '--annotations', annotations_file,
        '--output', '../public/reference_images'
    ]
    
    print(f"Generating reference images from {annotations_file}...")
    success = run_process(command, log_file)
    
    return {
        'success': success,
        'message': 'Reference images generated successfully!' if success else 'Failed to generate reference images',
        'log_file': log_file
    }

def extract_neume_images(annotations_file, output_dir='./extracted_neumes'):
    """Extract neume images from the annotations"""
    setup_directories()
    
    log_file = './logs/extraction.log'
    command = [
        'python',
        'test_real_data.py',
        '--annotations', annotations_file,
        '--output', output_dir
    ]
    
    print(f"Extracting neume images from {annotations_file}...")
    success = run_process(command, log_file)
    
    return {
        'success': success,
        'message': 'Neume images extracted successfully!' if success else 'Failed to extract neume images',
        'output_dir': output_dir,
        'log_file': log_file
    }

def get_status():
    """Get status information about the extraction process"""
    # Check for reference images
    reference_dir = Path('../public/reference_images')
    reference_images = list(reference_dir.glob('*.jpg')) if reference_dir.exists() else []
    
    # Check for overlay images
    overlay_images = [f for f in reference_dir.glob('*_overlay_*.jpg')] if reference_dir.exists() else []
    
    # Check for extracted neumes
    extraction_dir = Path('./extracted_neumes')
    neume_dirs = list(extraction_dir.glob('*')) if extraction_dir.exists() else []
    neume_types = [d.name for d in neume_dirs if d.is_dir()]
    
    # Count total extracted images
    total_images = 0
    for neume_dir in neume_dirs:
        if neume_dir.is_dir():
            for root, _, files in os.walk(neume_dir):
                total_images += sum(1 for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    
    return {
        'reference_images': len(reference_images),
        'overlay_images': len(overlay_images),
        'neume_types': neume_types,
        'total_extracted_images': total_images,
        'timestamp': time.time()
    }

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Neume extraction integration')
    parser.add_argument('--action', choices=['reference', 'overlay', 'extract', 'status'],
                       required=True, help='Action to perform')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--output', default='./extracted_neumes',
                       help='Output directory for extracted images')
    parser.add_argument('--reference-dir', default='../public/reference_images',
                       help='Directory containing reference images')
    
    args = parser.parse_args()
    
    if args.action == 'reference':
        result = generate_reference_images(args.annotations)
        print(json.dumps(result, indent=2))
    elif args.action == 'overlay':
        result = generate_overlays(args.annotations, args.reference_dir)
        print(json.dumps(result, indent=2))
    elif args.action == 'extract':
        result = extract_neume_images(args.annotations, args.output)
        print(json.dumps(result, indent=2))
    elif args.action == 'status':
        result = get_status()
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({
            'success': False,
            'message': f'Unknown action: {args.action}'
        }, indent=2))
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
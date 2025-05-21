#!/usr/bin/env python3
"""
Script to export individual neume images from IIIF URLs in an annotations file.
This script downloads each neume image and organizes them by type.
"""

import os
import json
import argparse
import sys
import requests
from pathlib import Path
import re
import time
import csv

def extract_neume_info(url, neume_type, index):
    """Extract information about a neume from its URL"""
    # Extract coordinates
    coords_match = re.search(r'(\d+),(\d+),(\d+),(\d+)/64,/0/default.jpg', url)
    if not coords_match:
        return None
    
    x = int(coords_match.group(1))
    y = int(coords_match.group(2))
    width = int(coords_match.group(3))
    height = int(coords_match.group(4))
    
    # Extract manuscript and page info
    url_parts = url.split('/')
    if len(url_parts) < 7:
        return None
    
    manuscript = url_parts[5]  # e.g., csg-0390
    page_full = url_parts[6].split('.')[0]  # e.g., csg-0390_007
    page_number = page_full.split('_')[1] if '_' in page_full else page_full  # e.g., 007
    
    return {
        'url': url,
        'x': x,
        'y': y,
        'width': width,
        'height': height,
        'manuscript': manuscript,
        'page': page_full,
        'page_number': page_number,
        'neume_type': neume_type,
        'index': index
    }

def download_neume_image(neume_info, output_dir, filename=None):
    """Download a neume image from its URL"""
    if not filename:
        # Generate a descriptive filename
        filename = f"{neume_info['neume_type'].replace(' ', '_')}_{neume_info['page_number']}_{neume_info['index']:03d}.jpg"
    
    output_path = os.path.join(output_dir, filename)
    
    # Check if already downloaded
    if os.path.exists(output_path):
        print(f"Image already exists: {output_path}")
        return True, output_path
    
    # Download the image
    try:
        print(f"Downloading image from {neume_info['url']}")
        response = requests.get(neume_info['url'])
        
        if response.status_code != 200:
            print(f"Failed to download image: {response.status_code}")
            return False, None
        
        # Save image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Saved image to {output_path}")
        return True, output_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False, None

def export_neumes(annotations_file, output_dir, filter_type=None, metadata_file=None):
    """Export individual neume images from annotations"""
    try:
        # Load annotations
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        print(f"Loaded {len(annotations)} neume types from {annotations_file}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare metadata collection
        metadata = []
        
        # Process each neume type
        total_neumes = 0
        downloaded_neumes = 0
        
        for annotation in annotations:
            neume_type = annotation['type']
            
            # Filter by type if specified
            if filter_type and neume_type != filter_type:
                continue
            
            print(f"\nProcessing {neume_type} ({len(annotation['urls'])} images)")
            
            # Create directory for this neume type
            neume_dir = os.path.join(output_dir, neume_type.replace(' ', '_'))
            os.makedirs(neume_dir, exist_ok=True)
            
            # Process each URL
            for i, url in enumerate(annotation['urls']):
                total_neumes += 1
                
                # Extract neume info
                neume_info = extract_neume_info(url, neume_type, i)
                if not neume_info:
                    print(f"Could not parse URL: {url}")
                    continue
                
                # Download the image
                filename = f"{neume_info['page_number']}_{i:03d}.jpg"
                success, file_path = download_neume_image(neume_info, neume_dir, filename)
                
                if success:
                    downloaded_neumes += 1
                    
                    # Add to metadata
                    metadata.append({
                        'filename': os.path.basename(file_path),
                        'directory': os.path.relpath(os.path.dirname(file_path), output_dir),
                        'neume_type': neume_type,
                        'manuscript': neume_info['manuscript'],
                        'page': neume_info['page'],
                        'x': neume_info['x'],
                        'y': neume_info['y'],
                        'width': neume_info['width'],
                        'height': neume_info['height'],
                        'url': url
                    })
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(0.2)
        
        # Export metadata if requested
        if metadata_file:
            with open(metadata_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=metadata[0].keys() if metadata else [])
                writer.writeheader()
                writer.writerows(metadata)
            print(f"Saved metadata to {metadata_file}")
        
        print(f"\nExport complete!")
        print(f"Downloaded {downloaded_neumes} of {total_neumes} neumes")
        print(f"Images saved to {output_dir}")
        
        return True
    except Exception as e:
        print(f"Error exporting neumes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Export individual neume images')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                      help='Path to annotations JSON file')
    parser.add_argument('--output-dir', default='../public/exported_neumes',
                      help='Output directory for exported images')
    parser.add_argument('--filter-type', default=None,
                      help='Only export neumes of this type')
    parser.add_argument('--metadata', default=None,
                      help='Path to save metadata CSV file')
    
    args = parser.parse_args()
    
    print(f"=== Neume Image Exporter ===")
    print(f"Annotations file: {args.annotations}")
    print(f"Output directory: {args.output_dir}")
    if args.filter_type:
        print(f"Filtering by type: {args.filter_type}")
    if args.metadata:
        print(f"Metadata file: {args.metadata}")
    
    success = export_neumes(
        args.annotations, 
        args.output_dir, 
        args.filter_type, 
        args.metadata or os.path.join(args.output_dir, 'neume_metadata.csv')
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test script specifically for working with real neume data.
This script:
1. Tests the extraction with real e-codices data
2. Organizes images by manuscript and page
3. Creates a detailed report of the extraction
"""

import os
import json
import argparse
import requests
import time
import sys
from pathlib import Path
from PIL import Image
from io import BytesIO
import re

def parse_iiif_url(url):
    """Parse an IIIF URL into its components for e-codices URLs"""
    try:
        # Extract coordinates using regex
        coords_match = re.search(r'(\d+),(\d+),(\d+),(\d+)/64,/0/default.jpg', url)
        if not coords_match:
            print(f"Invalid IIIF URL format: {url}")
            return None
        
        x = int(coords_match.group(1))
        y = int(coords_match.group(2))
        width = int(coords_match.group(3))
        height = int(coords_match.group(4))
        
        # Extract manuscript and page information
        url_parts = url.split('/')
        if len(url_parts) < 7:
            print(f"URL doesn't contain expected parts: {url}")
            return None
            
        manuscript = url_parts[5]  # e.g., csg-0390
        page = url_parts[6].split('.')[0]  # e.g., csg-0390_007
        page_number = page.split('_')[1]  # e.g., 007
        
        # Extract base URL
        base_url = '/'.join(url_parts[:-1]).rsplit('/', 1)[0]
        
        return {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'manuscript': manuscript,
            'page': page,
            'page_number': page_number,
            'base_url': base_url,
            'full_url': url
        }
    except Exception as e:
        print(f"Error parsing IIIF URL: {e}")
        return None

def download_neume_image(url, output_dir, filename=None):
    """Download a neume image from an IIIF URL"""
    iiif_info = parse_iiif_url(url)
    if not iiif_info:
        return False, None
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            filename = f"{iiif_info['manuscript']}_{iiif_info['page_number']}_{iiif_info['x']}_{iiif_info['y']}.jpg"
        
        output_path = os.path.join(output_dir, filename)
        
        # Check if already downloaded
        if os.path.exists(output_path):
            return True, output_path
        
        # Download image
        print(f"Downloading image from {url}")
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed to download image: {response.status_code}")
            return False, None
        
        # Save image
        img = Image.open(BytesIO(response.content))
        img.save(output_path)
        print(f"Saved image to {output_path}")
        
        return True, output_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False, None

def extract_real_neumes(annotations_file, output_dir):
    """Extract real neume images from annotations file"""
    try:
        # Load annotations
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        print(f"Loaded {len(annotations)} neume types")
        
        # Create base output directory
        base_dir = Path(output_dir)
        base_dir.mkdir(exist_ok=True)
        
        # Statistics
        stats = {
            'total_neumes': 0,
            'successful_downloads': 0,
            'manuscripts': set(),
            'pages': set(),
            'neume_types': []
        }
        
        # Process each neume type
        for annotation in annotations:
            neume_type = annotation['type']
            num_urls = len(annotation['urls'])
            print(f"\nProcessing {neume_type} ({num_urls} images)")
            
            # Add to statistics
            stats['total_neumes'] += num_urls
            stats['neume_types'].append({
                'type': neume_type,
                'count': num_urls,
                'successful': 0
            })
            
            # Create directory for this neume type
            neume_dir = base_dir / neume_type.replace(' ', '_')
            neume_dir.mkdir(exist_ok=True)
            
            # Process each URL
            for i, url in enumerate(annotation['urls']):
                print(f"Image {i+1}/{num_urls}: Processing...")
                
                # Parse URL to get manuscript and page info
                iiif_info = parse_iiif_url(url)
                if not iiif_info:
                    continue
                
                # Add to statistics
                stats['manuscripts'].add(iiif_info['manuscript'])
                stats['pages'].add(iiif_info['page'])
                
                # Create directories for manuscript and page
                manuscript_dir = neume_dir / iiif_info['manuscript']
                manuscript_dir.mkdir(exist_ok=True)
                
                page_dir = manuscript_dir / iiif_info['page']
                page_dir.mkdir(exist_ok=True)
                
                # Download image
                filename = f"{i:03d}_{iiif_info['x']}_{iiif_info['y']}.jpg"
                success, filepath = download_neume_image(url, str(page_dir), filename)
                
                if success:
                    stats['successful_downloads'] += 1
                    for nt in stats['neume_types']:
                        if nt['type'] == neume_type:
                            nt['successful'] += 1
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(0.5)
        
        # Generate report
        report = f"# Neume Extraction Report\n\n"
        report += f"## Summary\n\n"
        report += f"- Total neume images: {stats['total_neumes']}\n"
        report += f"- Successfully downloaded: {stats['successful_downloads']} ({stats['successful_downloads']/stats['total_neumes']*100:.1f}%)\n"
        report += f"- Manuscripts: {len(stats['manuscripts'])}\n"
        report += f"- Pages: {len(stats['pages'])}\n"
        report += f"- Neume types: {len(stats['neume_types'])}\n\n"
        
        report += f"## Neume Types\n\n"
        for nt in stats['neume_types']:
            report += f"- {nt['type']}: {nt['successful']}/{nt['count']} ({nt['successful']/nt['count']*100:.1f}%)\n"
        
        report += f"\n## Manuscripts\n\n"
        for ms in sorted(stats['manuscripts']):
            report += f"- {ms}\n"
        
        # Save report
        report_path = base_dir / "extraction_report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\nExtraction complete! Report saved to {report_path}")
        return True
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract real neume images')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                      help='Path to annotations JSON file')
    parser.add_argument('--output', default='./extracted_real_neumes',
                      help='Output directory for extracted images')
    
    args = parser.parse_args()
    
    print("=== Real Neume Data Extraction ===")
    print(f"Annotations file: {args.annotations}")
    print(f"Output directory: {args.output}")
    
    success = extract_real_neumes(args.annotations, args.output)
    
    if success:
        print("\nExtraction completed successfully!")
        return 0
    else:
        print("\nExtraction failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
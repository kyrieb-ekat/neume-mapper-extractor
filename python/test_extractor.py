#!/usr/bin/env python3
"""
Test script for extracting neume images from IIIF URLs.
"""

import os
import json
import argparse
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
import time
import sys

def parse_iiif_url(url):
    """Parse an IIIF URL into its components"""
    try:
        # Extract base URL and coordinates
        base_url = url.replace('/[\d]+,[\d]+,[\d]+,[\d]+/64,/0/default.jpg', "")
        dims_match = url.split('/')[-3].split(',')
        
        if len(dims_match) != 4:
            print(f"Invalid IIIF URL format: {url}")
            return None
        
        x, y, width, height = map(int, dims_match)
        
        # Extract page identifier
        url_parts = url.split('/')
        page_id = url_parts[6] if len(url_parts) > 6 else "unknown"
        
        return {
            'base_url': base_url,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'page_id': page_id,
            'full_url': url
        }
    except Exception as e:
        print(f"Error parsing IIIF URL: {e}")
        return None

def download_image(iiif_info, output_dir, filename=None):
    """Download and save a neume image"""
    if not iiif_info:
        return False
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Use provided filename or generate one
        if not filename:
            filename = f"{iiif_info['page_id']}_{iiif_info['x']}_{iiif_info['y']}.jpg"
        
        output_path = os.path.join(output_dir, filename)
        
        # Check if we already downloaded this image
        if os.path.exists(output_path):
            print(f"Image already exists: {output_path}")
            return True
        
        # Download the image
        print(f"Downloading image from {iiif_info['full_url']}")
        response = requests.get(iiif_info['full_url'])
        
        if response.status_code != 200:
            print(f"Failed to download image: {response.status_code}")
            return False
        
        # Save the image
        img = Image.open(BytesIO(response.content))
        img.save(output_path)
        print(f"Saved image to {output_path}")
        
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

def test_extraction(annotations_file, output_dir):
    """Test extraction from annotations file"""
    try:
        # Load annotations
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        print(f"Loaded {len(annotations)} annotation types")
        
        # Create output directory
        base_output_dir = Path(output_dir)
        base_output_dir.mkdir(exist_ok=True)
        
        # Track our progress
        total_images = sum(len(annot['urls']) for annot in annotations)
        processed_images = 0
        successful_images = 0
        
        # Process each neume type
        for annot in annotations:
            neume_type = annot['type']
            print(f"\nProcessing {neume_type} ({len(annot['urls'])} images)")
            
            # Create directory for this neume type
            neume_dir = base_output_dir / neume_type.replace(' ', '_')
            neume_dir.mkdir(exist_ok=True)
            
            # Process each URL
            for i, url in enumerate(annot['urls']):
                processed_images += 1
                print(f"Image {processed_images}/{total_images}: {url}")
                
                # Parse the URL
                iiif_info = parse_iiif_url(url)
                if not iiif_info:
                    continue
                
                # Download the image
                filename = f"{iiif_info['page_id']}_{i:03d}.jpg"
                success = download_image(iiif_info, str(neume_dir), filename)
                if success:
                    successful_images += 1
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(0.5)
        
        # Print summary
        print(f"\nExtraction test complete!")
        print(f"Processed {processed_images} images, successfully extracted {successful_images} images")
        print(f"Images saved to {base_output_dir}")
        
        return True
    except Exception as e:
        print(f"Error during test extraction: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test IIIF image extraction')
    parser.add_argument('--annotations', default='../public/sample-annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--output', default='./extracted_test',
                       help='Output directory for extracted images')
    
    args = parser.parse_args()
    
    print("=== IIIF Extractor Test ===")
    print(f"Annotations file: {args.annotations}")
    print(f"Output directory: {args.output}")
    
    success = test_extraction(args.annotations, args.output)
    
    if success:
        print("Test completed successfully")
        return 0
    else:
        print("Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
    
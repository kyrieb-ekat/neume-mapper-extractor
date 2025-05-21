#!/usr/bin/env python3
"""
Script to fetch reference images for neume comparison.
This script downloads full page images from the IIIF repository
to provide context for the neume extractions.
"""

import os
import json
import argparse
import requests
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from io import BytesIO
import re

def extract_manuscript_info(url):
    """Extract manuscript and page information from an IIIF URL"""
    try:
        url_parts = url.split('/')
        if len(url_parts) < 7:
            return None
        
        manuscript = url_parts[5]  # e.g., csg-0390
        page = url_parts[6].split('.')[0]  # e.g., csg-0390_007
        return {
            'manuscript': manuscript,
            'page': page,
            'full_url': f"http://www.e-codices.unifr.ch/loris/{url_parts[4]}/{manuscript}/{page}.jp2/full/1000,/0/default.jpg"
        }
    except Exception as e:
        print(f"Error extracting manuscript info: {e}")
        return None

def parse_iiif_url(url):
    """Parse an IIIF URL to extract coordinates"""
    try:
        coords_match = re.search(r'(\d+),(\d+),(\d+),(\d+)/64,/0/default.jpg', url)
        if not coords_match:
            return None
        
        return {
            'x': int(coords_match.group(1)),
            'y': int(coords_match.group(2)),
            'width': int(coords_match.group(3)),
            'height': int(coords_match.group(4))
        }
    except Exception as e:
        print(f"Error parsing coordinates: {e}")
        return None

def download_reference_image(info, output_dir):
    """Download a reference image for a manuscript page"""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        filename = f"{info['page']}.jpg"
        output_path = os.path.join(output_dir, filename)
        
        # Check if already downloaded
        if os.path.exists(output_path):
            print(f"Reference image already exists: {output_path}")
            return True, output_path
        
        # Download image
        print(f"Downloading reference image from {info['full_url']}")
        response = requests.get(info['full_url'])
        
        if response.status_code != 200:
            print(f"Failed to download reference image: {response.status_code}")
            return False, None
        
        # Save image
        img = Image.open(BytesIO(response.content))
        img.save(output_path)
        print(f"Saved reference image to {output_path}")
        
        return True, output_path
    except Exception as e:
        print(f"Error downloading reference image: {e}")
        return False, None

def create_overlay_image(reference_image_path, neume_coords, output_dir, neume_type):
    """Create an overlay image highlighting the neumes"""
    try:
        # Load reference image
        img = Image.open(reference_image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Determine scaling factor (reference image might be scaled)
        # For e-codices, we requested 1000px wide images
        orig_width = img.width
        scale_factor = orig_width / 1000  # Adjust if you used a different size
        
        # Draw rectangles for each neume
        for i, coords in enumerate(neume_coords):
            # Scale coordinates
            x = int(coords['x'] * scale_factor)
            y = int(coords['y'] * scale_factor)
            width = int(coords['width'] * scale_factor)
            height = int(coords['height'] * scale_factor)
            
            # Draw rectangle with some padding
            padding = 5
            draw.rectangle(
                [x-padding, y-padding, x+width+padding, y+height+padding],
                outline=(255, 0, 0),  # Red
                width=2
            )
            
            # Add a number label
            draw.text((x, y-15), str(i+1), fill=(255, 0, 0))
        
        # Save the overlay image
        output_filename = f"{os.path.basename(reference_image_path).split('.')[0]}_overlay_{neume_type}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        img.save(output_path)
        print(f"Created overlay image: {output_path}")
        
        return True, output_path
    except Exception as e:
        print(f"Error creating overlay image: {e}")
        return False, None

def fetch_reference_images(annotations_file, output_dir):
    """Fetch reference images for all manuscripts and pages in the annotations"""
    try:
        # Load annotations
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        # Create output directory
        reference_dir = Path(output_dir)
        reference_dir.mkdir(exist_ok=True)
        
        # Track pages we've processed
        processed_pages = set()
        
        # Create a mapping of pages to neume coordinates
        page_neumes = {}
        
        # Process each neume type
        for annotation in annotations:
            neume_type = annotation['type']
            print(f"\nProcessing {neume_type} ({len(annotation['urls'])} images)")
            
            # Process each URL
            for url in annotation['urls']:
                # Extract manuscript and page info
                ms_info = extract_manuscript_info(url)
                if not ms_info:
                    continue
                
                # Extract coordinates
                coords = parse_iiif_url(url)
                if not coords:
                    continue
                
                # Add to page_neumes mapping
                page_key = f"{ms_info['manuscript']}_{ms_info['page']}"
                if page_key not in page_neumes:
                    page_neumes[page_key] = {
                        'manuscript': ms_info['manuscript'],
                        'page': ms_info['page'],
                        'full_url': ms_info['full_url'],
                        'neume_types': {}
                    }
                
                if neume_type not in page_neumes[page_key]['neume_types']:
                    page_neumes[page_key]['neume_types'][neume_type] = []
                
                page_neumes[page_key]['neume_types'][neume_type].append(coords)
                
                # Download reference image if not already processed
                if page_key not in processed_pages:
                    success, _ = download_reference_image(ms_info, str(reference_dir))
                    if success:
                        processed_pages.add(page_key)
        
        # Create overlay images for each page and neume type
        for page_key, page_data in page_neumes.items():
            reference_image_path = reference_dir / f"{page_data['page']}.jpg"
            if not reference_image_path.exists():
                continue
            
            for neume_type, coords_list in page_data['neume_types'].items():
                create_overlay_image(
                    str(reference_image_path),
                    coords_list,
                    str(reference_dir),
                    neume_type.replace(' ', '_')
                )
        
        print(f"\nReference images fetched successfully!")
        print(f"Downloaded {len(processed_pages)} reference images")
        print(f"Created overlay images for {len(page_neumes)} pages")
        
        # Generate HTML report
        html_report = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Neume Reference Images</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .page-section { margin-bottom: 30px; border-bottom: 1px solid #ccc; padding-bottom: 20px; }
                .image-container { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 10px; }
                .image-card { border: 1px solid #ddd; padding: 10px; border-radius: 5px; max-width: 500px; }
                h2 { color: #333; }
                h3 { color: #666; }
                img { max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>Neume Reference Images</h1>
        """
        
        # Add each page to the report
        for page_key, page_data in sorted(page_neumes.items()):
            html_report += f"""
            <div class="page-section">
                <h2>{page_data['page']}</h2>
                <div class="image-container">
                    <div class="image-card">
                        <h3>Original Page</h3>
                        <img src="{page_data['page']}.jpg" alt="Original page">
                    </div>
            """
            
            # Add overlay images for each neume type
            for neume_type in page_data['neume_types'].keys():
                safe_type = neume_type.replace(' ', '_')
                overlay_filename = f"{page_data['page']}_overlay_{safe_type}.jpg"
                html_report += f"""
                    <div class="image-card">
                        <h3>{neume_type} Overlay</h3>
                        <img src="{overlay_filename}" alt="{neume_type} overlay">
                    </div>
                """
            
            html_report += """
                </div>
            </div>
            """
        
        html_report += """
        </body>
        </html>
        """
        
        # Save HTML report
        report_path = reference_dir / "reference_images.html"
        with open(report_path, 'w') as f:
            f.write(html_report)
        
        print(f"HTML report created: {report_path}")
        
        return True
    except Exception as e:
        print(f"Error fetching reference images: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Fetch reference images for neume comparison')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--output', default='../public/reference_images',
                       help='Output directory for reference images')
    
    args = parser.parse_args()
    
    print("=== Fetching Reference Images ===")
    print(f"Annotations file: {args.annotations}")
    print(f"Output directory: {args.output}")
    
    success = fetch_reference_images(args.annotations, args.output)
    
    if success:
        print("\nReference images fetched successfully!")
        return 0
    else:
        print("\nFailed to fetch reference images.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
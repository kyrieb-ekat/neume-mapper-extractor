#!/usr/bin/env python3
"""
Script to generate overlay images for existing reference images.
This script takes annotations and creates overlays highlighting neumes
on the reference images.
"""

import os
import json
import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re

def parse_iiif_url(url):
    """Parse an IIIF URL to extract coordinates and page info"""
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
        page_full = url_parts[6].split('.')[0]  # e.g., csg-0390_007
        page_number = page_full.split('_')[1] if '_' in page_full else page_full  # e.g., 007
        
        return {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'manuscript': manuscript,
            'page_full': page_full,
            'page_number': page_number
        }
    except Exception as e:
        print(f"Error parsing IIIF URL: {e}")
        return None

def find_reference_image(page_info, reference_dir):
    """Find the reference image file for a page"""
    # Try different possible filename formats
    possible_filenames = [
        f"SG_390-{page_info['page_number']}.jpg",  # SG_390-007.jpg
        f"{page_info['page_full']}.jpg",           # csg-0390_007.jpg
        f"{page_info['manuscript']}_{page_info['page_number']}.jpg", # csg-0390_007.jpg
        f"page_{page_info['page_number']}.jpg"     # page_007.jpg
    ]
    
    for filename in possible_filenames:
        file_path = os.path.join(reference_dir, filename)
        if os.path.exists(file_path):
            return file_path
    
    return None

def create_overlay_image(reference_image_path, coords_list, output_dir, neume_type):
    """Create an overlay image highlighting the neumes"""
    try:
        if not os.path.exists(reference_image_path):
            print(f"Reference image not found: {reference_image_path}")
            return False, None
        
        # Load reference image
        img = Image.open(reference_image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Try to determine scaling factor based on image dimensions vs original manuscript
        # For demonstration, we'll use a reasonable estimate
        # You may need to adjust this based on your specific images
        
        # Get image dimensions
        img_width, img_height = img.size
        
        # Assuming original manuscript is around 5000px wide for high-res IIIF
        # This is an estimate and may need adjustment for your specific images
        orig_width = 5000
        scale_factor = img_width / orig_width
        
        # Draw rectangles for each neume
        for i, coords in enumerate(coords_list):
            # Scale coordinates
            x = int(coords['x'] * scale_factor)
            y = int(coords['y'] * scale_factor)
            width = int(coords['width'] * scale_factor)
            height = int(coords['height'] * scale_factor)
            
            # Ensure coordinates are within image bounds
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            width = min(width, img_width - x)
            height = min(height, img_height - y)
            
            # Draw rectangle with some padding
            padding = 5
            draw.rectangle(
                [x-padding, y-padding, x+width+padding, y+height+padding],
                outline=(255, 0, 0),  # Red
                width=2
            )
            
            # Add a number label
            # Try to load a font, fall back to default if not available
            font = None
            try:
                # Try to find a font that works on most systems
                font_path = None
                for system_font in [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
                    '/Library/Fonts/Arial Bold.ttf',  # macOS
                    'C:\\Windows\\Fonts\\arialbd.ttf'  # Windows
                ]:
                    if os.path.exists(system_font):
                        font_path = system_font
                        break
                
                if font_path:
                    font = ImageFont.truetype(font_path, 20)
            except Exception:
                pass  # Fall back to default font
            
            # Draw text
            text_position = (x, y-25)
            draw.text(text_position, str(i+1), fill=(255, 0, 0), font=font)
        
        # Save the overlay image
        page_basename = os.path.basename(reference_image_path).split('.')[0]
        safe_neume_type = neume_type.replace(' ', '_')
        output_filename = f"{page_basename}_overlay_{safe_neume_type}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        img.save(output_path)
        print(f"Created overlay image: {output_path}")
        
        return True, output_path
    except Exception as e:
        print(f"Error creating overlay image: {e}")
        return False, None

def generate_overlays(annotations_file, reference_dir, output_dir=None):
    """Generate overlay images for neumes"""
    try:
        # Set output directory
        if output_dir is None:
            output_dir = reference_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load annotations
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        print(f"Loaded {len(annotations)} neume types")
        
        # Process each neume type
        results = {
            'success': True,
            'overlays_created': [],
            'errors': []
        }
        
        for annotation in annotations:
            neume_type = annotation['type']
            print(f"\nProcessing {neume_type} ({len(annotation['urls'])} images)")
            
            # Group neumes by page
            page_neumes = {}
            
            for url in annotation['urls']:
                neume_info = parse_iiif_url(url)
                if not neume_info:
                    continue
                
                page_key = f"{neume_info['manuscript']}_{neume_info['page_number']}"
                if page_key not in page_neumes:
                    page_neumes[page_key] = []
                
                page_neumes[page_key].append(neume_info)
            
            # Create overlay for each page
            for page_key, neumes in page_neumes.items():
                # Get a representative neume to find the page
                if not neumes:
                    continue
                
                reference_image_path = find_reference_image(neumes[0], reference_dir)
                if not reference_image_path:
                    error_msg = f"Reference image not found for {page_key}"
                    print(f"✗ {error_msg}")
                    results['errors'].append(error_msg)
                    continue
                
                # Create overlay
                success, overlay_path = create_overlay_image(
                    reference_image_path,
                    neumes,
                    output_dir,
                    neume_type
                )
                
                if success:
                    results['overlays_created'].append(overlay_path)
                else:
                    error_msg = f"Failed to create overlay for {page_key}, {neume_type}"
                    print(f"✗ {error_msg}")
                    results['errors'].append(error_msg)
        
        # Generate HTML report
        html_report = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Neume Overlay Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .neume-type { margin-bottom: 30px; border-bottom: 1px solid #ccc; padding-bottom: 20px; }
                .image-container { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 10px; }
                .image-card { border: 1px solid #ddd; padding: 10px; border-radius: 5px; width: 45%; }
                h2 { color: #333; }
                img { max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>Neume Overlay Report</h1>
        """
        
        for annotation in annotations:
            neume_type = annotation['type']
            html_report += f"""
            <div class="neume-type">
                <h2>{neume_type}</h2>
                <div class="image-container">
            """
            
            # Find all overlay images for this neume type
            safe_neume_type = neume_type.replace(' ', '_')
            overlay_pattern = f"*_overlay_{safe_neume_type}.jpg"
            overlay_files = list(Path(output_dir).glob(overlay_pattern))
            
            for overlay_file in overlay_files:
                # Get the base filename without the overlay part
                base_name = str(overlay_file.name).split('_overlay_')[0]
                original_file = Path(reference_dir) / f"{base_name}.jpg"
                
                html_report += f"""
                    <div class="image-card">
                        <h3>{base_name} - {neume_type}</h3>
                        <img src="{overlay_file.name}" alt="Overlay for {base_name}">
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
        report_path = os.path.join(output_dir, "overlay_report.html")
        with open(report_path, 'w') as f:
            f.write(html_report)
        
        print(f"HTML report created: {report_path}")
        
        results['report_path'] = report_path
        results['success'] = len(results['errors']) == 0
        
        return results
    except Exception as e:
        print(f"Error generating overlays: {e}")
        return {
            'success': False,
            'errors': [str(e)]
        }

def main():
    parser = argparse.ArgumentParser(description='Generate overlay images for neumes')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--reference-dir', default='../public/reference_images',
                       help='Directory containing reference images')
    parser.add_argument('--output-dir', default=None,
                       help='Output directory for overlay images (defaults to reference_dir)')
    
    args = parser.parse_args()
    
    print("=== Generating Neume Overlays ===")
    print(f"Annotations file: {args.annotations}")
    print(f"Reference directory: {args.reference_dir}")
    print(f"Output directory: {args.output_dir or args.reference_dir}")
    
    results = generate_overlays(args.annotations, args.reference_dir, args.output_dir)
    
    if results['success']:
        print(f"\nOverlay generation completed successfully!")
        print(f"Created {len(results['overlays_created'])} overlay images")
        if results.get('report_path'):
            print(f"HTML report: {results['report_path']}")
        return 0
    else:
        print(f"\nOverlay generation completed with errors:")
        for error in results['errors']:
            print(f"- {error}")
        print(f"Created {len(results['overlays_created'])} overlay images")
        if results.get('report_path'):
            print(f"HTML report: {results['report_path']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
    
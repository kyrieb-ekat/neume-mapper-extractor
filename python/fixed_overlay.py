#!/usr/bin/env python3
"""
Fixed overlay generator with adjustable scaling and visual debugging.
This script creates an overlay image with visible bounding boxes.
"""

import os
import json
import argparse
import sys
from PIL import Image, ImageDraw, ImageFont
import re

def extract_coordinates(url):
    """Extract coordinates from an IIIF URL"""
    match = re.search(r'(\d+),(\d+),(\d+),(\d+)/64,/0/default.jpg', url)
    if not match:
        return None
    
    return {
        'x': int(match.group(1)),
        'y': int(match.group(2)),
        'width': int(match.group(3)),
        'height': int(match.group(4))
    }

def draw_debug_grid(img, draw, grid_size=500):
    """Draw a debug grid on the image to help with coordinate visualization"""
    width, height = img.size
    
    # Draw grid lines
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill=(0, 0, 255, 128), width=1)
    
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill=(0, 0, 255, 128), width=1)
    
    # Draw grid labels
    for x in range(0, width, grid_size):
        draw.text((x + 5, 5), str(x), fill=(0, 0, 255))
    
    for y in range(0, height, grid_size):
        draw.text((5, y + 5), str(y), fill=(0, 0, 255))

def main():
    parser = argparse.ArgumentParser(description='Fixed overlay generator')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--image', default='../public/reference_images/SG_390-007.jpg',
                       help='Path to the reference image')
    parser.add_argument('--output', default='../public/reference_images/SG_390-007_overlay_fixed.jpg',
                       help='Path for the output overlay image')
    parser.add_argument('--scale', type=float, default=0.2,
                       help='Scale factor for coordinates (default: 0.2)')
    parser.add_argument('--line-width', type=int, default=3,
                       help='Width of the bounding box lines (default: 3)')
    parser.add_argument('--debug-grid', action='store_true',
                       help='Draw a debug grid on the image')
    parser.add_argument('--filter-page', default='007',
                       help='Only process URLs for this page number (default: 007)')
    
    args = parser.parse_args()
    
    print(f"=== Fixed Overlay Generator ===")
    print(f"Annotations file: {args.annotations}")
    print(f"Reference image: {args.image}")
    print(f"Output image: {args.output}")
    print(f"Scale factor: {args.scale}")
    print(f"Line width: {args.line_width}")
    print(f"Debug grid: {args.debug_grid}")
    print(f"Filter page: {args.filter_page}")
    
    # Check if files exist
    if not os.path.exists(args.annotations):
        print(f"Error: Annotations file not found: {args.annotations}")
        return 1
    
    if not os.path.exists(args.image):
        print(f"Error: Reference image not found: {args.image}")
        return 1
    
    # Load annotations
    try:
        with open(args.annotations, 'r') as f:
            annotations = json.load(f)
        print(f"Loaded {len(annotations)} annotation types")
    except Exception as e:
        print(f"Error loading annotations: {e}")
        return 1
    
    # Load image
    try:
        img = Image.open(args.image).convert("RGBA")
        print(f"Loaded image: {img.width}x{img.height}")
        
        # Create overlay layer
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
    except Exception as e:
        print(f"Error loading image: {e}")
        return 1
    
    # Draw debug grid if requested
    if args.debug_grid:
        print("Drawing debug grid")
        draw_debug_grid(overlay, draw)
    
    # Process annotations
    try:
        # Process only URLs for the specified page
        count = 0
        for annotation in annotations:
            neume_type = annotation['type']
            print(f"Processing {neume_type}")
            
            # Filter URLs for this specific page
            page_urls = [url for url in annotation['urls'] if f"csg-0390_{args.filter_page}" in url]
            print(f"Found {len(page_urls)} URLs for page {args.filter_page}")
            
            for i, url in enumerate(page_urls):
                coords = extract_coordinates(url)
                if not coords:
                    continue
                
                # Scale coordinates to match the reference image
                x = int(coords['x'] * args.scale)
                y = int(coords['y'] * args.scale)
                width = int(coords['width'] * args.scale)
                height = int(coords['height'] * args.scale)
                
                print(f"Neume {count+1}: Original coords: ({coords['x']},{coords['y']},{coords['width']},{coords['height']})")
                print(f"Neume {count+1}: Scaled coords: ({x},{y},{width},{height})")
                
                # Draw rectangle with more visible style
                draw.rectangle(
                    [x, y, x + width, y + height],
                    outline=(255, 0, 0, 255),  # Red, fully opaque
                    width=args.line_width
                )
                
                # Add number label with more visible style
                draw.text(
                    (x, y-20), 
                    str(count+1),
                    fill=(255, 0, 0, 255),  # Red, fully opaque
                    # Try different font options
                    # font=ImageFont.truetype("arial.ttf", 20)  # Uncomment if available
                )
                
                # Also draw indicators at corners for better visibility
                corner_size = 5
                # Top-left corner
                draw.rectangle([x, y, x + corner_size, y + corner_size], fill=(255, 255, 0, 255))
                # Top-right corner
                draw.rectangle([x + width - corner_size, y, x + width, y + corner_size], fill=(255, 255, 0, 255))
                # Bottom-left corner
                draw.rectangle([x, y + height - corner_size, x + corner_size, y + height], fill=(255, 255, 0, 255))
                # Bottom-right corner
                draw.rectangle([x + width - corner_size, y + height - corner_size, x + width, y + height], fill=(255, 255, 0, 255))
                
                count += 1
        
        print(f"Drew {count} neume boxes")
        
        # Combine the original image and overlay
        result = Image.alpha_composite(img.convert("RGBA"), overlay)
        
        # Save result
        result.convert("RGB").save(args.output)
        print(f"Saved overlay image to {args.output}")
        
        return 0
    except Exception as e:
        print(f"Error creating overlay: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
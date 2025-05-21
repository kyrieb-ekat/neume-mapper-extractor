#!/usr/bin/env python3
"""
Automatic scaling overlay generator for large-format images.
This script automatically determines the correct scaling factor based on the image dimensions.
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

def estimate_manuscript_size(coords_list):
    """Estimate the original manuscript size based on coordinates"""
    if not coords_list:
        return None
    
    # Find the maximum x and y values from all coordinates
    max_x = 0
    max_y = 0
    
    for coords in coords_list:
        # Check the right-most and bottom-most points
        max_x = max(max_x, coords['x'] + coords['width'])
        max_y = max(max_y, coords['y'] + coords['height'])
    
    # Add some padding
    estimated_width = max_x + 500  # Add 500px padding
    estimated_height = max_y + 500  # Add 500px padding
    
    return (estimated_width, estimated_height)

def calculate_scale_factor(image_size, estimated_manuscript_size):
    """Calculate the appropriate scale factor"""
    if not estimated_manuscript_size:
        return 1.0
    
    # Calculate scale factors for both dimensions
    width_scale = image_size[0] / estimated_manuscript_size[0]
    height_scale = image_size[1] / estimated_manuscript_size[1]
    
    # Use the smaller of the two to ensure all content fits
    scale = min(width_scale, height_scale)
    
    # Check if the scale is reasonable
    if scale < 0.01:
        print(f"Warning: Scale factor is very small ({scale:.4f}). Using default of 0.01")
        return 0.01
    
    if scale > 10:
        print(f"Warning: Scale factor is very large ({scale:.4f}). Using default of 10")
        return 10
    
    return scale

def main():
    parser = argparse.ArgumentParser(description='Auto-scaling overlay generator')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                      help='Path to annotations JSON file')
    parser.add_argument('--image', default='../public/reference_images/SG_390-007.jpg',
                      help='Path to the reference image')
    parser.add_argument('--output', default='../public/reference_images/SG_390-007_overlay_auto.jpg',
                      help='Path for the output overlay image')
    parser.add_argument('--filter-page', default='007',
                      help='Only process URLs for this page number (default: 007)')
    parser.add_argument('--debug-coords', action='store_true',
                      help='Print detailed coordinate information')
    parser.add_argument('--line-width', type=int, default=10,
                       help='Width of bounding box lines (default: 10)')
    parser.add_argument('--line-color', default='red',
                       help='Color of bounding boxes (red, green, blue, yellow, etc.)')
    parser.add_argument('--corner-size', type=int, default=15,
                       help='Size of corner indicators (default: 15)')
    
    args = parser.parse_args()
    
    # Color mapping
    color_map = {
        'red': (255, 0, 0, 255),
        'green': (0, 255, 0, 255),
        'blue': (0, 0, 255, 255),
        'yellow': (255, 255, 0, 255),
        'purple': (128, 0, 128, 255),
        'cyan': (0, 255, 255, 255),
        'white': (255, 255, 255, 255)
    }
    
    line_color = color_map.get(args.line_color.lower(), (255, 0, 0, 255))  # Default to red
    
    print(f"=== Auto-scaling Overlay Generator ===")
    
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
    
    # Extract all coordinates for the specified page
    all_coords = []
    neume_coords = []  # Keep track of neume coordinates we'll actually draw
    
    for annotation in annotations:
        # Filter URLs for this specific page
        page_urls = [url for url in annotation['urls'] if f"csg-0390_{args.filter_page}" in url]
        
        for url in page_urls:
            coords = extract_coordinates(url)
            if coords:
                all_coords.append(coords)
                neume_coords.append({
                    'coords': coords,
                    'type': annotation['type']
                })
    
    if not all_coords:
        print(f"Error: No valid coordinates found for page {args.filter_page}")
        return 1
    
    print(f"Found {len(all_coords)} coordinates for page {args.filter_page}")
    
    # Load image and get its dimensions
    try:
        img = Image.open(args.image)
        image_size = img.size
        print(f"Image dimensions: {image_size[0]} × {image_size[1]} pixels")
    except Exception as e:
        print(f"Error loading image: {e}")
        return 1
    
    # Estimate manuscript size and calculate scale factor
    estimated_size = estimate_manuscript_size(all_coords)
    print(f"Estimated manuscript size: {estimated_size[0]} × {estimated_size[1]} pixels")
    
    scale_factor = calculate_scale_factor(image_size, estimated_size)
    print(f"Calculated scale factor: {scale_factor:.4f}")
    
    # Create overlay
    try:
        # Create a transparent overlay
        overlay = Image.new('RGBA', image_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw bounding boxes
        for i, neume in enumerate(neume_coords):
            coords = neume['coords']
            neume_type = neume['type']
            
            # Scale coordinates
            x = int(coords['x'] * scale_factor)
            y = int(coords['y'] * scale_factor)
            width = int(coords['width'] * scale_factor)
            height = int(coords['height'] * scale_factor)
            
            if args.debug_coords:
                print(f"Neume {i+1} ({neume_type}):")
                print(f"  Original: x={coords['x']}, y={coords['y']}, w={coords['width']}, h={coords['height']}")
                print(f"  Scaled: x={x}, y={y}, w={width}, h={height}")
            
            # Ensure coordinates are within image bounds
            x = max(0, min(x, image_size[0] - 1))
            y = max(0, min(y, image_size[1] - 1))
            width = min(width, image_size[0] - x)
            height = min(height, image_size[1] - y)
            
            # Draw rectangle
            draw.rectangle(
                [x, y, x + width, y + height],
                outline=line_color,
                width=args.line_width
            )
            
            # Draw corner indicators for better visibility
            corner_size = args.corner_size
            # Top-left corner
            draw.rectangle([x, y, x + corner_size, y + corner_size], fill=line_color)
            # Top-right corner
            draw.rectangle([x + width - corner_size, y, x + width, y + corner_size], fill=line_color)
            # Bottom-left corner
            draw.rectangle([x, y + height - corner_size, x + corner_size, y + height], fill=line_color)
            # Bottom-right corner
            draw.rectangle([x + width - corner_size, y + height - corner_size, x + width, y + height], fill=line_color)
            
            # Add number label (if font available)
            try:
                # Try to find a system font
                font = None
                font_size = 50  # Larger font size for big images
                
                # Try common system font locations
                for font_path in [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
                    '/Library/Fonts/Arial Bold.ttf',  # macOS
                    'C:\\Windows\\Fonts\\arialbd.ttf'  # Windows
                ]:
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                        break
                
                if font:
                    # Draw with font
                    draw.text((x + 10, y - font_size - 10), str(i+1), fill=line_color, font=font)
                else:
                    # Draw without font (simple text)
                    draw.text((x + 10, y - 50), str(i+1), fill=line_color)
            except Exception as e:
                print(f"Warning: Couldn't add text label: {e}")
        
        # Composite the overlay onto the original image
        result = Image.alpha_composite(img.convert("RGBA"), overlay)
        
        # Save the result
        result.convert("RGB").save(args.output)
        print(f"Saved overlay image to: {args.output}")
        
        # Generate a small version for web preview
        web_output = args.output.replace('.jpg', '_web.jpg')
        web_size = (1200, int(1200 * image_size[1] / image_size[0]))  # Maintain aspect ratio
        result.resize(web_size, Image.LANCZOS).convert("RGB").save(web_output)
        print(f"Saved web-friendly version to: {web_output}")
        
        return 0
    except Exception as e:
        print(f"Error creating overlay: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
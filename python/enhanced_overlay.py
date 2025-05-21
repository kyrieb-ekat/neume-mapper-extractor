#!/usr/bin/env python3
"""
Enhanced auto-scaling overlay generator with fine-tuning options.
This script provides more control over the appearance of bounding boxes.
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

def calculate_scale_factor(image_size, estimated_manuscript_size, manual_scale=None):
    """Calculate the appropriate scale factor"""
    # If manual scale is provided, use it
    if manual_scale is not None:
        return manual_scale
    
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
    parser = argparse.ArgumentParser(description='Enhanced auto-scaling overlay generator')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                      help='Path to annotations JSON file')
    parser.add_argument('--image', default='../public/reference_images/SG_390-007.jpg',
                      help='Path to the reference image')
    parser.add_argument('--output', default='../public/reference_images/SG_390-007_overlay_enhanced.jpg',
                      help='Path for the output overlay image')
    parser.add_argument('--web-output', default=None,
                      help='Path for the web-friendly output image (defaults to output_web.jpg)')
    parser.add_argument('--filter-page', default='007',
                      help='Only process URLs for this page number (default: 007)')
    parser.add_argument('--debug-coords', action='store_true',
                      help='Print detailed coordinate information')
    parser.add_argument('--line-width', type=int, default=10,
                       help='Width of bounding box lines (default: 10)')
    parser.add_argument('--line-color', default='red',
                       help='Color of bounding boxes (red, green, blue, yellow, etc.)')
    parser.add_argument('--corner-size', type=int, default=20,
                       help='Size of corner indicators (default: 20)')
    parser.add_argument('--scale', type=float, default=None,
                       help='Manual scale factor (overrides automatic calculation)')
    parser.add_argument('--scale-adjust', type=float, default=1.0,
                       help='Adjustment factor for the calculated scale (default: 1.0)')
    parser.add_argument('--box-padding', type=int, default=5,
                       help='Padding around bounding boxes (default: 5)')
    parser.add_argument('--opacity', type=int, default=255,
                       help='Opacity of bounding boxes (0-255, default: 255)')
    parser.add_argument('--web-size', type=int, default=1200,
                       help='Width of web-friendly version (default: 1200px)')
    
    args = parser.parse_args()
    
    # Set web output path if not specified
    if args.web_output is None:
        args.web_output = args.output.replace('.jpg', '_web.jpg')
    
    # Color mapping
    color_map = {
        'red': (255, 0, 0, args.opacity),
        'green': (0, 255, 0, args.opacity),
        'blue': (0, 0, 255, args.opacity),
        'yellow': (255, 255, 0, args.opacity),
        'purple': (128, 0, 128, args.opacity),
        'cyan': (0, 255, 255, args.opacity),
        'white': (255, 255, 255, args.opacity),
        'black': (0, 0, 0, args.opacity),
        'orange': (255, 165, 0, args.opacity)
    }
    
    line_color = color_map.get(args.line_color.lower(), (255, 0, 0, args.opacity))  # Default to red
    
    print(f"=== Enhanced Auto-scaling Overlay Generator ===")
    print(f"Annotations file: {args.annotations}")
    print(f"Reference image: {args.image}")
    print(f"Output image: {args.output}")
    print(f"Web output: {args.web_output}")
    print(f"Line width: {args.line_width}")
    print(f"Line color: {args.line_color}")
    print(f"Corner size: {args.corner_size}")
    print(f"Box padding: {args.box_padding}")
    print(f"Scale adjustment: {args.scale_adjust}")
    if args.scale is not None:
        print(f"Manual scale: {args.scale}")
    
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
        print(f"Found {len(page_urls)} URLs for {annotation['type']} on page {args.filter_page}")
        
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
    
    print(f"Found {len(all_coords)} total coordinates for page {args.filter_page}")
    
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
    
    base_scale_factor = calculate_scale_factor(image_size, estimated_size, args.scale)
    scale_factor = base_scale_factor * args.scale_adjust
    print(f"Base scale factor: {base_scale_factor:.4f}")
    print(f"Adjusted scale factor: {scale_factor:.4f}")
    
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
            
            # Add padding
            pad = args.box_padding
            
            # Draw rectangle
            draw.rectangle(
                [x-pad, y-pad, x + width+pad, y + height+pad],
                outline=line_color,
                width=args.line_width
            )
            
            # Draw corner indicators for better visibility
            corner_size = args.corner_size
            # Top-left corner
            draw.rectangle([x-pad, y-pad, x-pad + corner_size, y-pad + corner_size], fill=line_color)
            # Top-right corner
            draw.rectangle([x + width+pad - corner_size, y-pad, x + width+pad, y-pad + corner_size], fill=line_color)
            # Bottom-left corner
            draw.rectangle([x-pad, y + height+pad - corner_size, x-pad + corner_size, y + height+pad], fill=line_color)
            # Bottom-right corner
            draw.rectangle([x + width+pad - corner_size, y + height+pad - corner_size, x + width+pad, y + height+pad], fill=line_color)
            
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
        web_size = (args.web_size, int(args.web_size * image_size[1] / image_size[0]))  # Maintain aspect ratio
        result.resize(web_size, Image.LANCZOS).convert("RGB").save(args.web_output)
        print(f"Saved web-friendly version to: {args.web_output}")
        
        return 0
    except Exception as e:
        print(f"Error creating overlay: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
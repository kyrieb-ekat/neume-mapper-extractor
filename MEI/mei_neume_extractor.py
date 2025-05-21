#!/usr/bin/env python3
"""
Configurable Crop MEI Neume Extractor

This script allows for configurable scaling of the crop dimensions, making it
easy to adjust how much context is included around each neume. It supports
separate width and height scale factors, as well as minimum dimensions.
# currently I like this command and ratio: ./mei_neume_extractor.py --width-scale 2.5 --height-scale 2.7
# also possible: 
# # Use default settings (1.5x width, 2.0x height)
./mei_neume_extractor.py

# Make the crops 3x wider and 5x taller
./mei_neume_extractor.py --width-scale 3.0 --height-scale 5.0

# Use smaller crops with less buffer
./mei_neume_extractor.py --width-scale 1.2 --height-scale 1.5 --buffer 5

# Ensure larger minimum dimensions
./mei_neume_extractor.py --min-width 80 --min-height 120

# Process all files with custom settings
./mei_neume_extractor.py --all --width-scale 2.0 --height-scale 4.0

also, two ways to run the script:
# Process a single MEI file (same as before)
./mei_neume_extractor.py

# Process ALL MEI files in the MEI_files directory
./mei_neume_extractor.py --all
"""

import os
import sys
import argparse
import xml.etree.ElementTree as ET
from PIL import Image
import json
from collections import defaultdict
import re

# Default scaling factors and dimensions
DEFAULT_HEIGHT_SCALE = 2.0  # Double the height
DEFAULT_WIDTH_SCALE = 1.5   # Increase width by 50%
DEFAULT_MIN_HEIGHT = 60     # Minimum height in pixels
DEFAULT_MIN_WIDTH = 40      # Minimum width in pixels
DEFAULT_BUFFER = 15         # Buffer around the crop in pixels

def extract_image_filename(mei_filename):
    """
    Extract the corresponding image filename from an MEI filename.
    
    Args:
        mei_filename: The MEI filename to extract from
    
    Returns:
        The extracted image filename or None if no pattern matched
    """
    patterns = [
        # CDN-Mlr_MS73_076r-154.mei → MS73_154.jpg
        (r'_(\d+[rv])-(\d+)', lambda m: f"MS73_{m.group(2)}.jpg"),
        # Other patterns can be added here
        (r'MS(\d+)[_-](\d+)', lambda m: f"MS{m.group(1)}_{m.group(2)}.jpg"),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, mei_filename)
        if match:
            return formatter(match)
    
    # If no pattern matches, return None
    return None

def parse_mei_file(mei_file, image_filename=None, height_scale=DEFAULT_HEIGHT_SCALE):
    """
    Parse an MEI XML file and extract neume component information.
    
    Args:
        mei_file: Path to the MEI XML file
        image_filename: Optional specific image filename to use
        height_scale: Factor to scale the height of zero-height zones
    
    Returns:
        Dictionary mapping neume types to lists of dictionaries with coordinates and source image info
    """
    print(f"Parsing MEI file: {mei_file}")
    
    # Define MEI namespace
    namespace = "http://www.music-encoding.org/ns/mei"
    namespaces = {
        'mei': namespace,
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }
    
    try:
        # Parse the XML file
        tree = ET.parse(mei_file)
        root = tree.getroot()
        
        # Determine image filename
        if image_filename is None:
            # Try to extract from MEI filename
            mei_basename = os.path.basename(mei_file)
            extracted_filename = extract_image_filename(mei_basename)
            
            if extracted_filename:
                image_filename = extracted_filename
            else:
                # Default to the hardcoded value that worked previously
                image_filename = "MS73_154.jpg"
        
        print(f"Using image filename: {image_filename}")
        
        # Find all zones to build a map of zone IDs to coordinates
        zone_map = {}
        
        # First find the facsimile element
        facsimile = root.find(f'.//{{{namespace}}}facsimile')
        if facsimile is not None:
            # Find all zones
            zones = facsimile.findall(f'.//{{{namespace}}}zone')
            print(f"Found {len(zones)} zone elements")
            
            # Build the zone map
            for zone in zones:
                # Get the zone ID
                zone_id = zone.get(f'{{{namespaces["xml"]}}}id')
                if not zone_id:
                    zone_id = zone.get('xml:id')
                if not zone_id:
                    zone_id = zone.get('id')
                
                if zone_id:
                    # Get coordinates
                    ulx = float(zone.get('ulx', 0))
                    uly = float(zone.get('uly', 0))
                    lrx = float(zone.get('lrx', 0))
                    lry = float(zone.get('lry', 0))
                    
                    # Fix coordinates if they represent horizontal or vertical lines
                    # (where upper and lower y or left and right x are the same)
                    if uly == lry:
                        # For horizontal lines, add height based on scale factor
                        base_height = 40  # Base height to scale
                        height_adjustment = int(base_height * height_scale)
                        lry = uly + height_adjustment
                        print(f"Fixed horizontal line coordinates for zone {zone_id}: {uly} → {lry}")
                    
                    if ulx == lrx:
                        # For vertical lines, add width
                        width_adjustment = 40  # Keep base width adjustment
                        lrx = ulx + width_adjustment
                        print(f"Fixed vertical line coordinates for zone {zone_id}: {ulx} → {lrx}")
                    
                    # Store in the zone map
                    zone_map[zone_id] = {
                        'ulx': ulx,
                        'uly': uly,
                        'lrx': lrx,
                        'lry': lry
                    }
        
        print(f"Created zone map with {len(zone_map)} entries")
        
        # Now find all 'nc' elements with facs attributes
        nc_elements = root.findall(f'.//{{{namespace}}}nc[@facs]')
        print(f"Found {len(nc_elements)} nc elements with facs attributes")
        
        # Group extracted components by type
        neume_data = defaultdict(list)
        
        for nc in nc_elements:
            # Get the facs attribute (reference to zone)
            facs = nc.get('facs')
            if facs and facs.startswith('#'):
                zone_id = facs[1:]  # Remove the # character
                
                # Find the zone coordinates
                if zone_id in zone_map:
                    # Get nc attributes to use as type
                    pname = nc.get('pname', '')
                    oct = nc.get('oct', '')
                    tilt = nc.get('tilt', '')
                    
                    # Combine attributes to create a type
                    if pname and oct:
                        nc_type = f"nc_{pname}{oct}"
                        if tilt:
                            nc_type += f"_{tilt}"
                    else:
                        nc_type = "nc_unknown"
                    
                    # Add to the neume data
                    neume_data[nc_type].append({
                        'ulx': zone_map[zone_id]['ulx'],
                        'uly': zone_map[zone_id]['uly'],
                        'lrx': zone_map[zone_id]['lrx'],
                        'lry': zone_map[zone_id]['lry'],
                        'zone_id': zone_id,
                        'image_filename': image_filename
                    })
                    print(f"Added {nc_type} with zone {zone_id}")
                else:
                    print(f"Warning: Referenced zone {zone_id} not found in zone map")
        
        # Report what we found
        total_components = sum(len(components) for components in neume_data.values())
        print(f"Found {len(neume_data)} neume component types with a total of {total_components} components")
        
        for nc_type, components in neume_data.items():
            print(f"  - {nc_type}: {len(components)} instances")
        
        return neume_data
    
    except Exception as e:
        print(f"Error parsing MEI file: {e}")
        import traceback
        traceback.print_exc()
        return {}

def crop_neumes(neume_data, output_dir, image_dir, width_scale=DEFAULT_WIDTH_SCALE, 
                height_scale=DEFAULT_HEIGHT_SCALE, min_width=DEFAULT_MIN_WIDTH, 
                min_height=DEFAULT_MIN_HEIGHT, buffer=DEFAULT_BUFFER):
    """
    Crop neumes from source images using the provided coordinates and save them to the output directory.
    
    Args:
        neume_data: Dictionary mapping neume types to lists of dictionaries with coordinates and image info
        output_dir: Base directory to save cropped neumes
        image_dir: Directory containing source images
        width_scale: Factor to scale the width of the crop area
        height_scale: Factor to scale the height of the crop area
        min_width: Minimum width of the crop in pixels
        min_height: Minimum height of the crop in pixels
        buffer: Additional buffer to add around the crop in pixels
    
    Returns:
        Dictionary mapping neume types to lists of cropped image paths
    """
    print(f"Cropping neumes to {output_dir}")
    print(f"Using scale factors: width={width_scale}x, height={height_scale}x")
    print(f"Minimum dimensions: {min_width}x{min_height} pixels")
    print(f"Buffer: {buffer} pixels")
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    result = {}
    
    for neume_type, neumes in neume_data.items():
        print(f"Processing {len(neumes)} instances of type '{neume_type}'")
        
        # Create a directory for this neume type
        # Replace any characters that are not valid in filenames
        safe_neume_type = re.sub(r'[\\/*?:"<>|]', '_', neume_type)
        neume_dir = os.path.join(output_dir, safe_neume_type)
        os.makedirs(neume_dir, exist_ok=True)
        
        cropped_images = []
        
        for i, neume in enumerate(neumes):
            # Get the coordinates
            ulx = neume.get('ulx', 0)
            uly = neume.get('uly', 0)
            lrx = neume.get('lrx', 0)
            lry = neume.get('lry', 0)
            
            # Check if we have valid coordinates
            if ulx >= lrx or uly >= lry:
                print(f"Warning: Invalid coordinates for {neume_type} #{i+1}: ({ulx}, {uly}, {lrx}, {lry})")
                continue
            
            # Get the source image
            image_filename = neume.get('image_filename')
            
            if not image_filename:
                print(f"Warning: No image filename for {neume_type} #{i+1}")
                continue
            
            # Look for the image in the image directory
            image_path = os.path.join(image_dir, image_filename)
            
            if not os.path.exists(image_path):
                print(f"Warning: Image file not found: {image_path}")
                
                # Try with different extensions
                for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
                    alt_path = os.path.join(image_dir, os.path.splitext(image_filename)[0] + ext)
                    if os.path.exists(alt_path):
                        image_path = alt_path
                        print(f"Found alternative image: {image_path}")
                        break
                
                # If we still can't find the image, skip this neume
                if not os.path.exists(image_path):
                    print(f"Error: Could not find image for {neume_type} #{i+1}")
                    continue
            
            try:
                # Open the source image
                with Image.open(image_path) as img:
                    # Make sure coordinates are integers
                    ulx = int(ulx)
                    uly = int(uly)
                    lrx = int(lrx)
                    lry = int(lry)
                    
                    # Determine the original dimensions
                    original_width = lrx - ulx
                    original_height = lry - uly
                    
                    # Calculate center point of the original bounding box
                    center_x = (ulx + lrx) / 2
                    center_y = (uly + lry) / 2
                    
                    # Calculate new dimensions based on scaling factors
                    new_width = max(int(original_width * width_scale), min_width)
                    new_height = max(int(original_height * height_scale), min_height)
                    
                    # Calculate new coordinates centered on the original center
                    new_ulx = max(0, int(center_x - new_width / 2 - buffer))
                    new_uly = max(0, int(center_y - new_height / 2 - buffer))
                    new_lrx = min(img.width, int(center_x + new_width / 2 + buffer))
                    new_lry = min(img.height, int(center_y + new_height / 2 + buffer))
                    
                    # Ensure minimum dimensions are met
                    if new_lrx - new_ulx < min_width:
                        diff = min_width - (new_lrx - new_ulx)
                        new_ulx = max(0, new_ulx - diff // 2)
                        new_lrx = min(img.width, new_lrx + (diff - diff // 2))
                    
                    if new_lry - new_uly < min_height:
                        diff = min_height - (new_lry - new_uly)
                        new_uly = max(0, new_uly - diff // 2)
                        new_lry = min(img.height, new_lry + (diff - diff // 2))
                    
                    # Crop the neume
                    try:
                        cropped = img.crop((new_ulx, new_uly, new_lrx, new_lry))
                        
                        # Save the cropped image
                        cropped_path = os.path.join(neume_dir, f"{safe_neume_type}_{i+1}.png")
                        cropped.save(cropped_path)
                        
                        print(f"Saved cropped neume to {cropped_path}")
                        cropped_images.append(cropped_path)
                    except Exception as crop_error:
                        print(f"Error cropping image: {crop_error} - Coordinates: ({new_ulx}, {new_uly}, {new_lrx}, {new_lry})")
            
            except Exception as e:
                print(f"Error processing {neume_type} #{i+1} from {image_path}: {e}")
        
        if cropped_images:
            result[neume_type] = cropped_images
    
    return result

def export_to_json(neume_data, output_file):
    """
    Export neume data to a JSON file in the format expected by your application.
    
    Args:
        neume_data: Dictionary mapping neume types to lists of cropped image paths
        output_file: Path to save the JSON file
    """
    print(f"Exporting data to {output_file}")
    
    # Convert the data to the expected format
    formatted_data = []
    
    for neume_type, images in neume_data.items():
        formatted_data.append({
            "type": neume_type,
            "urls": images
        })
    
    # Write the data to the output file
    with open(output_file, 'w') as f:
        json.dump(formatted_data, f, indent=2)
    
    print(f"Exported {len(formatted_data)} neume types to {output_file}")

def process_all_mei_files(mei_dir, output_dir, image_dir, json_file, width_scale, height_scale, min_width, min_height, buffer):
    """
    Process all MEI files in a directory.
    
    Args:
        mei_dir: Directory containing MEI files
        output_dir: Base directory to save cropped neumes
        image_dir: Directory containing source images
        json_file: Path to save the JSON output file
        width_scale: Factor to scale the width of the crop area
        height_scale: Factor to scale the height of the crop area
        min_width: Minimum width of the crop in pixels
        min_height: Minimum height of the crop in pixels
        buffer: Additional buffer to add around the crop in pixels
    
    Returns:
        0 if successful, 1 if an error occurred
    """
    # Check if the MEI directory exists
    if not os.path.exists(mei_dir):
        print(f"Error: MEI directory not found: {mei_dir}")
        return 1
    
    # Find all MEI files
    mei_files = [f for f in os.listdir(mei_dir) if f.endswith('.mei')]
    if not mei_files:
        print(f"No MEI files found in {mei_dir}")
        return 1
    
    # Process each MEI file
    all_neume_data = {}
    
    for mei_file in mei_files:
        mei_path = os.path.join(mei_dir, mei_file)
        print(f"\nProcessing MEI file: {mei_path}")
        
        # Create a specific output directory for this file
        file_output_dir = os.path.join(output_dir, os.path.splitext(mei_file)[0])
        
        # Extract potential image filename
        extracted_filename = extract_image_filename(mei_file)
        
        # Parse the MEI file
        neume_data = parse_mei_file(mei_path, extracted_filename, height_scale)
        
        if not neume_data:
            print(f"No neume data found in {mei_file}")
            continue
        
        # Crop the neumes and save them
        cropped_data = crop_neumes(neume_data, file_output_dir, image_dir, 
                                  width_scale, height_scale, min_width, min_height, buffer)
        
        if not cropped_data:
            print(f"No neumes were successfully cropped from {mei_file}")
            continue
        
        # Add to the combined data
        for neume_type, images in cropped_data.items():
            if neume_type not in all_neume_data:
                all_neume_data[neume_type] = []
            all_neume_data[neume_type].extend(images)
    
    # Export all data to a single JSON file
    if all_neume_data:
        formatted_data = []
        for neume_type, images in all_neume_data.items():
            formatted_data.append({
                "type": neume_type,
                "urls": images
            })
        
        with open(json_file, 'w') as f:
            json.dump(formatted_data, f, indent=2)
        
        print(f"\nExported combined data for {len(all_neume_data)} neume types to {json_file}")
        return 0
    else:
        print("No neume data was extracted from any MEI file")
        return 1

def main():
    # Check if the script is in the MEI directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get the parent directory structure
    parent_dir = os.path.dirname(script_dir)
    base_dir = script_dir  # Default to the script directory
    
    # Determine if we're in the expected directory structure
    if os.path.basename(parent_dir) == 'neume-mapper-extractor' and os.path.basename(script_dir) == 'MEI':
        base_dir = script_dir
    else:
        # Try to find the correct directories
        print("Script not in expected directory. Looking for structure...")
        
        # Try to locate the MEI directory
        if 'Documents' in script_dir and 'neume-mapper-extractor' in script_dir:
            # We might be in the Documents path
            base_components = script_dir.split(os.sep)
            for i, component in enumerate(base_components):
                if component == 'neume-mapper-extractor':
                    # Check if the next component is MEI
                    if i + 1 < len(base_components) and base_components[i + 1] == 'MEI':
                        base_dir = os.path.join(*base_components[:i+2])
                        break
    
    print(f"Using base directory: {base_dir}")
    
    # Set up paths based on the base directory
    mei_dir = os.path.join(base_dir, "MEI_files")
    image_dir = os.path.join(base_dir, "MSS_Images")
    output_dir = os.path.join(base_dir, "extracted_neumes")
    
    # Verify directories exist
    if not os.path.exists(mei_dir):
        print(f"Warning: MEI directory not found at {mei_dir}")
    if not os.path.exists(image_dir):
        print(f"Warning: Images directory not found at {image_dir}")
    
    parser = argparse.ArgumentParser(description='Extract neume components from MEI files and crop them from source images')
    parser.add_argument('--mei', default=None,
                      help=f'Path to specific MEI file (default: all files in {mei_dir})')
    parser.add_argument('--output', default=output_dir,
                      help=f'Directory to save cropped neumes (default: {output_dir})')
    parser.add_argument('--images', default=image_dir,
                      help=f'Directory containing source images (default: {image_dir})')
    parser.add_argument('--json', default=os.path.join(base_dir, "neumes.json"),
                      help='Path to save the JSON output file')
    parser.add_argument('--all', action='store_true',
                      help='Process all MEI files in the MEI directory')
    parser.add_argument('--width-scale', type=float, default=DEFAULT_WIDTH_SCALE,
                      help=f'Factor to scale the width of the crop area (default: {DEFAULT_WIDTH_SCALE})')
    parser.add_argument('--height-scale', type=float, default=DEFAULT_HEIGHT_SCALE,
                      help=f'Factor to scale the height of the crop area (default: {DEFAULT_HEIGHT_SCALE})')
    parser.add_argument('--min-width', type=int, default=DEFAULT_MIN_WIDTH,
                      help=f'Minimum width of the crop in pixels (default: {DEFAULT_MIN_WIDTH})')
    parser.add_argument('--min-height', type=int, default=DEFAULT_MIN_HEIGHT,
                      help=f'Minimum height of the crop in pixels (default: {DEFAULT_MIN_HEIGHT})')
    parser.add_argument('--buffer', type=int, default=DEFAULT_BUFFER,
                      help=f'Additional buffer to add around the crop in pixels (default: {DEFAULT_BUFFER})')
    
    args = parser.parse_args()
    
    print("=== Configurable Crop MEI Neume Extractor ===")
    
    # If --all flag is set, process all MEI files
    if args.all:
        return process_all_mei_files(mei_dir, output_dir, image_dir, args.json,
                                    args.width_scale, args.height_scale,
                                    args.min_width, args.min_height, args.buffer)
    
    # Otherwise, process a single MEI file
    mei_path = args.mei
    
    # If no specific MEI file is provided, find all MEI files
    if mei_path is None:
        if not os.path.exists(mei_dir):
            print(f"Error: MEI directory not found: {mei_dir}")
            print("You can specify a specific MEI file with --mei /path/to/file.mei")
            return 1
            
        mei_files = [f for f in os.listdir(mei_dir) if f.endswith('.mei')]
        if not mei_files:
            print(f"No MEI files found in {mei_dir}")
            return 1
        
        mei_path = os.path.join(mei_dir, mei_files[0])
        print(f"Using MEI file: {mei_path}")
    
    # Parse the MEI file
    neume_data = parse_mei_file(mei_path, height_scale=args.height_scale)
    
    if not neume_data:
        print("No neume component data found in the MEI file")
        return 1
    
    # Crop the neumes and save them
    cropped_data = crop_neumes(neume_data, args.output, args.images,
                              args.width_scale, args.height_scale,
                              args.min_width, args.min_height, args.buffer)
    
    if not cropped_data:
        print("No neume components were successfully cropped")
        return 1
    
    # Export the data to JSON
    export_to_json(cropped_data, args.json)
    
    print("Processing complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
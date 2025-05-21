#!/usr/bin/env python3
"""
Diagnostic version of the MEI Neume Extractor for troubleshooting.
This version provides more detailed information about the MEI file structure
and the image matching process.
"""

import os
import sys
import argparse
import xml.etree.ElementTree as ET
from PIL import Image
import json
from collections import defaultdict
import re

def analyze_mei_structure(mei_file):
    """
    Analyze the structure of an MEI file and print detailed information.
    
    Args:
        mei_file: Path to the MEI XML file
    """
    print(f"\n==== ANALYZING MEI FILE STRUCTURE: {mei_file} ====\n")
    
    try:
        # Parse the XML file
        tree = ET.parse(mei_file)
        root = tree.getroot()
        
        # Get the root tag and potential namespace
        print(f"Root tag: {root.tag}")
        
        namespace = None
        if root.tag.startswith('{'):
            ns_match = re.match(r'^\{(.*?)\}', root.tag)
            if ns_match:
                namespace = ns_match.group(1)
                print(f"Namespace: {namespace}")
        
        # Print all top-level elements
        print("\nTop-level elements:")
        for child in root:
            tag = child.tag
            if '{' in tag:
                tag = tag.split('}')[1]
            
            print(f"  - {tag} (Attributes: {len(child.attrib)})")
            # Print a few attributes if they exist
            if child.attrib:
                for key, value in list(child.attrib.items())[:3]:
                    print(f"    * {key}: {value}")
        
        # Look for facsimile element
        print("\nSearching for facsimile element...")
        facsimile = None
        
        # Try with namespace if detected
        if namespace:
            facsimile = root.find('.//{%s}facsimile' % namespace)
        
        # Try without namespace
        if facsimile is None:
            facsimile = root.find('.//facsimile')
        
        if facsimile is not None:
            print("Found facsimile element!")
            
            # Look for surface elements
            surfaces = []
            for search_path in [
                './/{%s}surface' % namespace if namespace else None,
                './/surface'
            ]:
                if search_path:
                    surfaces = facsimile.findall(search_path)
                    if surfaces:
                        break
            
            print(f"Found {len(surfaces)} surface elements")
            
            # Print information about each surface
            for i, surface in enumerate(surfaces[:3]):  # Show first 3 for brevity
                print(f"  - Surface {i+1}:")
                
                # Check for IDs
                for id_attr in ['{http://www.w3.org/XML/1998/namespace}id', 'xml:id', 'id']:
                    if id_attr in surface.attrib:
                        print(f"    * ID: {surface.get(id_attr)}")
                        break
                
                # Look for graphic elements
                graphics = []
                for search_path in [
                    './/{%s}graphic' % namespace if namespace else None,
                    './/graphic'
                ]:
                    if search_path:
                        graphics = surface.findall(search_path)
                        if graphics:
                            break
                
                print(f"    * Found {len(graphics)} graphic elements")
                
                for j, graphic in enumerate(graphics):
                    print(f"      - Graphic {j+1}:")
                    if 'target' in graphic.attrib:
                        print(f"        Target: {graphic.get('target')}")
                    
                    # Print other attributes
                    for key, value in list(graphic.attrib.items())[:3]:
                        if key != 'target':
                            print(f"        {key}: {value}")
            
            # Look for zone elements
            zones = []
            for search_path in [
                './/{%s}zone' % namespace if namespace else None,
                './/zone'
            ]:
                if search_path:
                    zones = facsimile.findall(search_path)
                    if zones:
                        break
            
            print(f"\nFound {len(zones)} zone elements")
            
            # Print information about a few zones
            for i, zone in enumerate(zones[:5]):  # Show first 5 for brevity
                print(f"  - Zone {i+1}:")
                
                # Check for IDs
                zone_id = None
                for id_attr in ['{http://www.w3.org/XML/1998/namespace}id', 'xml:id', 'id']:
                    if id_attr in zone.attrib:
                        zone_id = zone.get(id_attr)
                        print(f"    * ID: {zone_id}")
                        break
                
                # Check for coordinates
                coordinates = []
                for coord in ['ulx', 'uly', 'lrx', 'lry']:
                    if coord in zone.attrib:
                        coordinates.append(f"{coord}={zone.get(coord)}")
                
                if coordinates:
                    print(f"    * Coordinates: {', '.join(coordinates)}")
                
                # Check for type attribute
                if 'type' in zone.attrib:
                    print(f"    * Type: {zone.get('type')}")
        else:
            print("No facsimile element found!")
        
        # Look for neume elements
        print("\nSearching for neume-related elements...")
        
        for element_name in ['neume', 'nc', 'neuma', 'syllable', 'note', 'notehead']:
            # Try with namespace
            elements = []
            if namespace:
                elements = root.findall('.//{%s}%s' % (namespace, element_name))
            
            # Try without namespace
            if not elements:
                elements = root.findall('.//%s' % element_name)
            
            if elements:
                print(f"Found {len(elements)} '{element_name}' elements")
                
                # Print information about a few elements
                for i, element in enumerate(elements[:3]):  # Show first 3 for brevity
                    print(f"  - {element_name.capitalize()} {i+1}:")
                    
                    # Check for type attributes
                    for type_attr in ['type', 'name', 'class', 'form', 'shape']:
                        if type_attr in element.attrib:
                            print(f"    * {type_attr}: {element.get(type_attr)}")
                    
                    # Check for facs attribute (reference to zone)
                    if 'facs' in element.attrib:
                        print(f"    * facs: {element.get('facs')}")
                    
                    # Print other interesting attributes
                    for key, value in list(element.attrib.items())[:5]:
                        if key not in ['type', 'name', 'class', 'form', 'shape', 'facs']:
                            print(f"    * {key}: {value}")
        
        print("\n==== END OF MEI STRUCTURE ANALYSIS ====\n")
    
    except Exception as e:
        print(f"Error analyzing MEI file: {e}")
        import traceback
        traceback.print_exc()

def check_image_path(image_dir, mei_file):
    """
    Check for potential image files associated with the MEI file.
    
    Args:
        image_dir: Directory containing source images
        mei_file: Path to the MEI XML file
    """
    print(f"\n==== CHECKING IMAGE PATHS ====\n")
    print(f"Image directory: {image_dir}")
    print(f"MEI file: {mei_file}")
    
    try:
        # Check if the image directory exists
        if not os.path.exists(image_dir):
            print(f"WARNING: Image directory does not exist: {image_dir}")
            return
        
        # List all image files in the directory
        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))]
        print(f"Found {len(image_files)} image files in directory")
        
        if image_files:
            print("First 5 image files:")
            for i, img in enumerate(image_files[:5]):
                print(f"  - {img}")
        
        # Try to extract potential image names from the MEI filename
        mei_basename = os.path.basename(mei_file)
        print(f"MEI basename: {mei_basename}")
        
        potential_matches = []
        
        # Pattern 1: MS73_154 from CDN-Mlr_MS73_076r-154.mei
        match1 = re.search(r'MS(\d+)[_-](\d+)', mei_basename)
        if match1:
            ms_num, page_num = match1.groups()
            potential_name = f"MS{ms_num}_{page_num}.jpg"
            potential_matches.append(potential_name)
            print(f"Potential match from pattern 1: {potential_name}")
        
        # Pattern 2: Extract 076r-154 from CDN-Mlr_MS73_076r-154.mei
        match2 = re.search(r'_(\d+[rv])-(\d+)', mei_basename)
        if match2:
            potential_name = f"MS73_{match2.group(2)}.jpg"
            potential_matches.append(potential_name)
            print(f"Potential match from pattern 2: {potential_name}")
        
        # Pattern 3: Extract page numbers
        numbers = re.findall(r'\d+', mei_basename)
        for num in numbers:
            if len(num) >= 3:  # Might be a page number
                potential_name = f"MS73_{num}.jpg"
                if potential_name not in potential_matches:
                    potential_matches.append(potential_name)
                    print(f"Potential match from pattern 3: {potential_name}")
        
        # Check if any potential matches exist in the image directory
        for potential in potential_matches:
            potential_path = os.path.join(image_dir, potential)
            if os.path.exists(potential_path):
                print(f"FOUND MATCHING IMAGE: {potential}")
                try:
                    with Image.open(potential_path) as img:
                        width, height = img.size
                        print(f"Image dimensions: {width} x {height}")
                except Exception as e:
                    print(f"Error opening image: {e}")
            else:
                print(f"No match found for: {potential}")
        
        print("\n==== END OF IMAGE PATH CHECK ====\n")
    
    except Exception as e:
        print(f"Error checking image paths: {e}")
        import traceback
        traceback.print_exc()

def parse_mei_file(mei_file):
    """
    Parse an MEI XML file and extract neume information including types and coordinates.
    
    Args:
        mei_file: Path to the MEI XML file
    
    Returns:
        Dictionary mapping neume types to lists of dictionaries with coordinates and source image info
    """
    print(f"Parsing MEI file: {mei_file}")
    
    # Define common MEI namespaces
    namespaces = {
        'mei': 'http://www.music-encoding.org/ns/mei',
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }
    
    try:
        # Parse the XML file
        tree = ET.parse(mei_file)
        root = tree.getroot()
        
        # Debug: Print the root tag to understand the structure
        print(f"Root tag: {root.tag}")
        
        # Try to find the namespace from the root tag if it's not standard
        if root.tag.startswith('{'):
            ns_match = re.match(r'^\{(.*?)\}', root.tag)
            if ns_match:
                mei_ns = ns_match.group(1)
                namespaces['mei'] = mei_ns
                print(f"Detected MEI namespace: {mei_ns}")
        
        # Find all zone elements that contain coordinates
        neume_data = defaultdict(list)
        
        # First, try to find facsimile information
        facsimile = root.find('.//{%s}facsimile' % namespaces['mei'])
        
        if facsimile is None:
            print("No facsimile element found. Trying without namespace...")
            facsimile = root.find('.//facsimile')
        
        if facsimile is not None:
            print("Found facsimile element")
            
            # Find all zones with coordinates
            zones = facsimile.findall('.//{%s}zone' % namespaces['mei'])
            if not zones:
                print("No zones found with namespace. Trying without namespace...")
                zones = facsimile.findall('.//zone')
            
            print(f"Found {len(zones)} zone elements")
            
            # Extract image filename from the MEI file
            # Try to get it from the graphic element
            graphic = facsimile.find('.//{%s}graphic' % namespaces['mei'])
            if not graphic:
                graphic = facsimile.find('.//graphic')
            
            image_filename = None
            if graphic is not None:
                image_url = graphic.get('target')
                if image_url:
                    image_filename = os.path.basename(image_url)
                    print(f"Found image filename from graphic element: {image_filename}")
            
            # If we couldn't find the image filename from the graphic element,
            # try to extract it from the MEI filename itself
            if not image_filename:
                mei_basename = os.path.basename(mei_file)
                # Extract specific pattern like MS73_154 from CDN-Mlr_MS73_076r-154.mei
                match = re.search(r'MS(\d+)[_-](\d+)', mei_basename)
                if match:
                    ms_num, page_num = match.groups()
                    image_filename = f"MS{ms_num}_{page_num}.jpg"
                    print(f"Extracted image filename from MEI filename: {image_filename}")
                else:
                    # Try another pattern matching 076r-154 from CDN-Mlr_MS73_076r-154.mei
                    match = re.search(r'_(\d+[rv])-(\d+)', mei_basename)
                    if match:
                        image_filename = f"MS73_{match.group(2)}.jpg"
                        print(f"Extracted image filename from MEI filename (alt pattern): {image_filename}")
            
            # Now process each zone to extract neume information
            for zone in zones:
                # Get coordinates
                ulx = float(zone.get('ulx', 0))
                uly = float(zone.get('uly', 0))
                lrx = float(zone.get('lrx', 0))
                lry = float(zone.get('lry', 0))
                
                # Get the zone ID
                zone_id = zone.get('{%s}id' % namespaces['xml'])
                if not zone_id:
                    zone_id = zone.get('xml:id')
                if not zone_id:
                    zone_id = zone.get('id')
                
                if not zone_id:
                    print(f"Warning: Zone has no ID")
                    continue
                
                print(f"Processing zone {zone_id} with coordinates: ({ulx}, {uly}, {lrx}, {lry})")
                
                # Now we need to find which neume references this zone
                # Try different approaches to find neumes that reference this zone
                neume_found = False
                
                # Approach 1: Look for elements with a facs attribute that references this zone
                facs_query = f'.//*[@facs="#{zone_id}"]'
                neume_elements = root.findall(facs_query)
                
                if not neume_elements:
                    # Try other possible facs formats
                    alt_facs_query = f'.//*[@facs="{zone_id}"]'
                    neume_elements = root.findall(alt_facs_query)
                
                for neume in neume_elements:
                    # Try to determine the neume type
                    neume_type = None
                    
                    # Check different attributes that might contain type information
                    for attr in ['type', 'name', 'class', 'form', 'shape']:
                        if neume.get(attr):
                            neume_type = neume.get(attr)
                            break
                    
                    # If still no type, try the tag name or parent's type
                    if not neume_type:
                        neume_type = neume.tag.split('}')[-1]  # Remove namespace prefix
                    
                    if neume_type == 'neume':
                        # Try to get a more specific type
                        for attr in ['name', 'class', 'form', 'shape']:
                            if neume.get(attr):
                                neume_type = neume.get(attr)
                                break
                    
                    # If we have a neume type and valid coordinates, add it to our data
                    if neume_type:
                        neume_data[neume_type].append({
                            'ulx': ulx,
                            'uly': uly,
                            'lrx': lrx,
                            'lry': lry,
                            'zone_id': zone_id,
                            'image_filename': image_filename
                        })
                        neume_found = True
                        print(f"Found neume of type '{neume_type}' referencing zone {zone_id}")
                
                # If no neume was found for this zone, add it with a generic type based on the zone
                if not neume_found:
                    # Check if the zone has a type attribute
                    zone_type = zone.get('type')
                    
                    # If no type, use a default
                    if not zone_type:
                        zone_type = "Unknown"
                    
                    neume_data[zone_type].append({
                        'ulx': ulx,
                        'uly': uly,
                        'lrx': lrx,
                        'lry': lry,
                        'zone_id': zone_id,
                        'image_filename': image_filename
                    })
                    print(f"No neume found for zone {zone_id}, using zone type '{zone_type}'")
        
        else:
            print("No facsimile element found. Checking for neumes with direct coordinates...")
            
            # Look for neume elements with direct coordinate attributes
            for element_name in ['neume', 'nc', 'neuma', 'symbol', 'note']:
                neume_xpath = './/{%s}%s' % (namespaces['mei'], element_name)
                neumes = root.findall(neume_xpath)
                
                if not neumes:
                    # Try without namespace
                    neumes = root.findall('.//%s' % element_name)
                
                for neume in neumes:
                    # Try to determine neume type
                    neume_type = None
                    for attr in ['type', 'name', 'class', 'form', 'shape']:
                        if neume.get(attr):
                            neume_type = neume.get(attr)
                            break
                    
                    if not neume_type:
                        neume_type = element_name
                    
                    # Check if this element has coordinate attributes
                    if any(attr in neume.attrib for attr in ['ulx', 'uly', 'lrx', 'lry']):
                        ulx = float(neume.get('ulx', 0))
                        uly = float(neume.get('uly', 0))
                        lrx = float(neume.get('lrx', 0))
                        lry = float(neume.get('lry', 0))
                        
                        # If only width/height are provided, calculate lrx/lry
                        if 'width' in neume.attrib and lrx == 0:
                            lrx = ulx + float(neume.get('width'))
                        if 'height' in neume.attrib and lry == 0:
                            lry = uly + float(neume.get('height'))
                        
                        # Extract image filename from the MEI filename
                        mei_basename = os.path.basename(mei_file)
                        image_filename = None
                        
                        match = re.search(r'MS(\d+)[_-](\d+)', mei_basename)
                        if match:
                            ms_num, page_num = match.groups()
                            image_filename = f"MS{ms_num}_{page_num}.jpg"
                        
                        neume_data[neume_type].append({
                            'ulx': ulx,
                            'uly': uly,
                            'lrx': lrx,
                            'lry': lry,
                            'image_filename': image_filename
                        })
                        print(f"Found neume '{neume_type}' with direct coordinates")
        
        # Report what we found
        total_neumes = sum(len(neumes) for neumes in neume_data.values())
        print(f"Found {len(neume_data)} neume types with a total of {total_neumes} neumes")
        
        for neume_type, neumes in neume_data.items():
            print(f"  - {neume_type}: {len(neumes)} instances")
        
        return neume_data
    
    except Exception as e:
        print(f"Error parsing MEI file: {e}")
        import traceback
        traceback.print_exc()
        return {}

def crop_neumes(neume_data, output_dir, image_dir):
    """
    Crop neumes from source images using the provided coordinates and save them to the output directory.
    
    Args:
        neume_data: Dictionary mapping neume types to lists of dictionaries with coordinates and image info
        output_dir: Base directory to save cropped neumes
        image_dir: Directory containing source images
    
    Returns:
        Dictionary mapping neume types to lists of cropped image paths
    """
    print(f"Cropping neumes to {output_dir}")
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    result = {}
    
    for neume_type, neumes in neume_data.items():
        print(f"Processing {len(neumes)} instances of neume type '{neume_type}'")
        
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
                    
                    # Crop the neume
                    cropped = img.crop((ulx, uly, lrx, lry))
                    
                    # Save the cropped image
                    cropped_path = os.path.join(neume_dir, f"{safe_neume_type}_{i+1}.png")
                    cropped.save(cropped_path)
                    
                    print(f"Saved cropped neume to {cropped_path}")
                    cropped_images.append(cropped_path)
            
            except Exception as e:
                print(f"Error cropping {neume_type} #{i+1} from {image_path}: {e}")
        
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
    
    parser = argparse.ArgumentParser(description='Extract neumes from MEI files and crop them from source images')
    parser.add_argument('--mei', default=None,
                      help=f'Path to specific MEI file (default: all files in {mei_dir})')
    parser.add_argument('--output', default=output_dir,
                      help=f'Directory to save cropped neumes (default: {output_dir})')
    parser.add_argument('--images', default=image_dir,
                      help=f'Directory containing source images (default: {image_dir})')
    parser.add_argument('--json', default=os.path.join(base_dir, "neumes.json"),
                      help='Path to save the JSON output file')
    parser.add_argument('--analyze', action='store_true',
                      help='Run detailed analysis of MEI file structure without processing')
    
    args = parser.parse_args()
    
    print("=== MEI Neume Extractor (Diagnostic Version) ===")
    
    # Use the provided paths or the defaults
    mei_path = args.mei
    output_dir = args.output
    image_dir = args.images
    json_file = args.json
    
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
    
    # If analyze flag is set, run detailed analysis
    if args.analyze:
        analyze_mei_structure(mei_path)
        check_image_path(image_dir, mei_path)
        return 0
    
    # Parse the MEI file
    neume_data = parse_mei_file(mei_path)
    
    if not neume_data:
        print("No neume data found in the MEI file")
        # Run analysis to help debug
        print("\nRunning detailed analysis to help troubleshoot...")
        analyze_mei_structure(mei_path)
        check_image_path(image_dir, mei_path)
        return 1
    
    # Crop the neumes and save them
    cropped_data = crop_neumes(neume_data, output_dir, image_dir)
    
    if not cropped_data:
        print("No neumes were successfully cropped")
        # Check image paths to help debug
        check_image_path(image_dir, mei_path)
        return 1
    
    # Export the data to JSON
    export_to_json(cropped_data, json_file)
    
    print("Processing complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
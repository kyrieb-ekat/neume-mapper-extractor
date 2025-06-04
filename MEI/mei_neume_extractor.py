#!/usr/bin/env python3
"""
Enhanced Batch MEI Neume Extractor with Diagnostic Capabilities

Combines efficient batch processing with robust diagnostic features for 
troubleshooting and processing hundreds of MEI files.
"""

import os
import sys
import argparse
import xml.etree.ElementTree as ET
from PIL import Image
import json
from collections import defaultdict
import re
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from tqdm import tqdm

# Default scaling factors and dimensions
DEFAULT_HEIGHT_SCALE = 2.0
DEFAULT_WIDTH_SCALE = 1.5
DEFAULT_MIN_HEIGHT = 60
DEFAULT_MIN_WIDTH = 40
DEFAULT_BUFFER = 15

def setup_logging(log_file, verbose=False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def analyze_mei_structure(mei_file, logger=None):
    """
    Analyze the structure of an MEI file and log detailed information.
    Returns namespace and structural info for processing.
    """
    if not logger:
        logger = logging.getLogger(__name__)
    
    logger.info(f"Analyzing MEI file structure: {mei_file}")
    
    try:
        tree = ET.parse(mei_file)
        root = tree.getroot()
        
        # Detect namespace
        namespace = None
        if root.tag.startswith('{'):
            ns_match = re.match(r'^\{(.*?)\}', root.tag)
            if ns_match:
                namespace = ns_match.group(1)
                logger.debug(f"Detected namespace: {namespace}")
        
        # Check for facsimile element
        facsimile = root.find(f'.//{{{namespace}}}facsimile' if namespace else './/facsimile')
        if not facsimile and namespace:
            facsimile = root.find('.//facsimile')  # Try without namespace
        
        # Count zones and neume elements
        zones = []
        nc_elements = []
        
        if facsimile:
            zones = facsimile.findall(f'.//{{{namespace}}}zone' if namespace else './/zone')
            if not zones and namespace:
                zones = facsimile.findall('.//zone')
        
        nc_elements = root.findall(f'.//{{{namespace}}}nc[@facs]' if namespace else './/nc[@facs]')
        if not nc_elements and namespace:
            nc_elements = root.findall('.//nc[@facs]')
        
        logger.info(f"Found {len(zones)} zones and {len(nc_elements)} nc elements with facs attributes")
        
        return {
            'namespace': namespace,
            'has_facsimile': facsimile is not None,
            'zone_count': len(zones),
            'nc_count': len(nc_elements)
        }
    
    except Exception as e:
        logger.error(f"Error analyzing MEI structure: {e}")
        return None

def extract_image_filename(mei_filename, logger=None):
    """Extract the corresponding image filename from an MEI filename with multiple patterns."""
    if logger:
        logger.debug(f"Extracting image filename from: {mei_filename}")
    
    patterns = [
        # CH-E_611_001r copy.mei → CH-E-611_001r.jpg (Einsiedeln pattern - note hyphen conversion)
        (r'CH-E_(\d+)_(\d+[rv])', lambda m: f"CH-E-{m.group(1)}_{m.group(2)}.jpg"),
        # Generic CH-E pattern with just manuscript number
        (r'CH-E_(\d+)', lambda m: f"CH-E-{m.group(1)}_001r.jpg"),
        # Generic number extraction for Einsiedeln (fallback)
        (r'(\d{3,})', lambda m: f"CH-E-611_{m.group(1)}.jpg"),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, mei_filename)
        if match:
            result = formatter(match)
            if logger:
                logger.debug(f"Pattern '{pattern}' matched, extracted: {result}")
            return result
    
    if logger:
        logger.warning(f"No pattern matched for {mei_filename}")
    return None

def check_image_availability(image_dir, potential_filenames, logger=None):
    """Check which of the potential image filenames actually exist"""
    if not logger:
        logger = logging.getLogger(__name__)
    
    if not os.path.exists(image_dir):
        logger.error(f"Image directory does not exist: {image_dir}")
        return None
    
    for filename in potential_filenames:
        image_path = os.path.join(image_dir, filename)
        if os.path.exists(image_path):
            logger.debug(f"Found image: {filename}")
            return filename
        
        # Try different extensions
        base_name = os.path.splitext(filename)[0]
        for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
            alt_path = os.path.join(image_dir, base_name + ext)
            if os.path.exists(alt_path):
                alt_filename = base_name + ext
                logger.debug(f"Found alternative image: {alt_filename}")
                return alt_filename
    
    logger.warning(f"No matching image found for potential names: {potential_filenames}")
    return None

def generate_neume_filename(mei_filename, neume_type, instance_number):
    """Generate descriptive filename preserving source information"""
    base_name = os.path.splitext(mei_filename)[0]
    clean_neume_type = re.sub(r'[\\/*?:"<>|]', '_', neume_type)
    return f"{base_name}_{clean_neume_type}_{instance_number}.png"

def parse_mei_file(mei_file, image_filename=None, height_scale=DEFAULT_HEIGHT_SCALE, logger=None):
    """Parse an MEI XML file and extract neume component information with enhanced diagnostics."""
    if not logger:
        logger = logging.getLogger(__name__)
    
    logger.debug(f"Parsing MEI file: {mei_file}")
    
    namespace = "http://www.music-encoding.org/ns/mei"
    namespaces = {
        'mei': namespace,
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }
    
    try:
        tree = ET.parse(mei_file)
        root = tree.getroot()
        
        # Detect actual namespace
        if root.tag.startswith('{'):
            ns_match = re.match(r'^\{(.*?)\}', root.tag)
            if ns_match:
                namespace = ns_match.group(1)
                namespaces['mei'] = namespace
                logger.debug(f"Using detected namespace: {namespace}")
        
        # Determine image filename
        if image_filename is None:
            mei_basename = os.path.basename(mei_file)
            extracted_filename = extract_image_filename(mei_basename, logger)
            image_filename = extracted_filename if extracted_filename else "CH-E-611_001r.jpg"
        
        logger.debug(f"Using image filename: {image_filename}")
        
        # Build zone map
        zone_map = {}
        facsimile = root.find(f'.//{{{namespace}}}facsimile')
        if facsimile is None:
            facsimile = root.find('.//facsimile')
        
        if facsimile is not None:
            zones = facsimile.findall(f'.//{{{namespace}}}zone')
            if not zones:
                zones = facsimile.findall('.//zone')
            
            logger.debug(f"Found {len(zones)} zone elements")
            
            for zone in zones:
                zone_id = (zone.get(f'{{{namespaces["xml"]}}}id') or 
                          zone.get('xml:id') or 
                          zone.get('id'))
                
                if zone_id:
                    ulx = float(zone.get('ulx', 0))
                    uly = float(zone.get('uly', 0))
                    lrx = float(zone.get('lrx', 0))
                    lry = float(zone.get('lry', 0))
                    
                    # Fix zero-height/width coordinates
                    if uly == lry:
                        base_height = 40
                        height_adjustment = int(base_height * height_scale)
                        lry = uly + height_adjustment
                        logger.debug(f"Fixed horizontal line for zone {zone_id}: {uly} → {lry}")
                    
                    if ulx == lrx:
                        width_adjustment = 40
                        lrx = ulx + width_adjustment
                        logger.debug(f"Fixed vertical line for zone {zone_id}: {ulx} → {lrx}")
                    
                    zone_map[zone_id] = {
                        'ulx': ulx, 'uly': uly, 'lrx': lrx, 'lry': lry
                    }
        else:
            logger.warning("No facsimile element found")
        
        logger.debug(f"Created zone map with {len(zone_map)} entries")
        
        # Extract neume components
        nc_elements = root.findall(f'.//{{{namespace}}}nc[@facs]')
        if not nc_elements:
            nc_elements = root.findall('.//nc[@facs]')
        
        logger.debug(f"Found {len(nc_elements)} nc elements with facs attributes")
        
        neume_data = defaultdict(list)
        
        for nc in nc_elements:
            facs = nc.get('facs')
            if facs and facs.startswith('#'):
                zone_id = facs[1:]
                
                if zone_id in zone_map:
                    pname = nc.get('pname', '')
                    oct = nc.get('oct', '')
                    tilt = nc.get('tilt', '')
                    
                    if pname and oct:
                        nc_type = f"nc_{pname}{oct}"
                        if tilt:
                            nc_type += f"_{tilt}"
                    else:
                        nc_type = "nc_unknown"
                    
                    neume_data[nc_type].append({
                        'ulx': zone_map[zone_id]['ulx'],
                        'uly': zone_map[zone_id]['uly'],
                        'lrx': zone_map[zone_id]['lrx'],
                        'lry': zone_map[zone_id]['lry'],
                        'zone_id': zone_id,
                        'image_filename': image_filename
                    })
                    logger.debug(f"Added {nc_type} with zone {zone_id}")
                else:
                    logger.warning(f"Referenced zone {zone_id} not found in zone map")
        
        total_components = sum(len(components) for components in neume_data.values())
        logger.info(f"Extracted {len(neume_data)} neume types with {total_components} components")
        
        for nc_type, components in neume_data.items():
            logger.debug(f"  - {nc_type}: {len(components)} instances")
        
        return neume_data
    
    except Exception as e:
        logger.error(f"Error parsing MEI file: {e}")
        return {}

def process_single_mei_file(args):
    """Process a single MEI file - designed for multiprocessing"""
    (mei_file, mei_dir, output_base_dir, image_dir, 
     width_scale, height_scale, min_width, min_height, buffer, verbose) = args
    
    # Set up logging for this process
    log_file = os.path.join(output_base_dir, f'process_{os.getpid()}.log')
    logger = setup_logging(log_file, verbose)
    
    mei_path = os.path.join(mei_dir, mei_file)
    mei_basename = os.path.basename(mei_file)
    
    try:
        logger.info(f"Processing {mei_file}")
        
        # Analyze MEI structure first
        structure_info = analyze_mei_structure(mei_path, logger)
        if not structure_info or structure_info['nc_count'] == 0:
            logger.warning(f"No usable neume data in {mei_file}")
            return {'file': mei_file, 'status': 'no_data', 'neumes': {}}
        
        # Extract potential image filename
        extracted_filename = extract_image_filename(mei_basename, logger)
        
        # Check if image exists
        potential_names = [extracted_filename] if extracted_filename else []
        actual_image_filename = check_image_availability(image_dir, potential_names, logger)
        
        if not actual_image_filename:
            logger.error(f"No matching image found for {mei_file}")
            return {'file': mei_file, 'status': 'no_image', 'neumes': {}}
        
        # Parse the MEI file
        neume_data = parse_mei_file(mei_path, actual_image_filename, height_scale, logger)
        
        if not neume_data:
            logger.warning(f"No neume data extracted from {mei_file}")
            return {'file': mei_file, 'status': 'no_data', 'neumes': {}}
        
        # Process each neume type
        result_neumes = {}
        
        for neume_type, neumes in neume_data.items():
            # Create directory for this neume type
            safe_neume_type = re.sub(r'[\\/*?:"<>|]', '_', neume_type)
            neume_dir = os.path.join(output_base_dir, safe_neume_type)
            os.makedirs(neume_dir, exist_ok=True)
            
            cropped_images = []
            
            for i, neume in enumerate(neumes):
                # Get coordinates
                ulx, uly, lrx, lry = neume['ulx'], neume['uly'], neume['lrx'], neume['lry']
                
                if ulx >= lrx or uly >= lry:
                    logger.warning(f"Invalid coordinates for {neume_type} #{i+1}")
                    continue
                
                image_filename = neume.get('image_filename')
                if not image_filename:
                    continue
                
                # Find the source image
                image_path = os.path.join(image_dir, image_filename)
                if not os.path.exists(image_path):
                    logger.warning(f"Image not found: {image_path}")
                    continue
                
                try:
                    # Process the image
                    with Image.open(image_path) as img:
                        # Calculate scaled dimensions
                        ulx, uly, lrx, lry = int(ulx), int(uly), int(lrx), int(lry)
                        original_width = lrx - ulx
                        original_height = lry - uly
                        
                        center_x = (ulx + lrx) / 2
                        center_y = (uly + lry) / 2
                        
                        new_width = max(int(original_width * width_scale), min_width)
                        new_height = max(int(original_height * height_scale), min_height)
                        
                        # Calculate new coordinates
                        new_ulx = max(0, int(center_x - new_width / 2 - buffer))
                        new_uly = max(0, int(center_y - new_height / 2 - buffer))
                        new_lrx = min(img.width, int(center_x + new_width / 2 + buffer))
                        new_lry = min(img.height, int(center_y + new_height / 2 + buffer))
                        
                        # Ensure minimum dimensions
                        if new_lrx - new_ulx < min_width:
                            diff = min_width - (new_lrx - new_ulx)
                            new_ulx = max(0, new_ulx - diff // 2)
                            new_lrx = min(img.width, new_lrx + (diff - diff // 2))
                        
                        if new_lry - new_uly < min_height:
                            diff = min_height - (new_lry - new_uly)
                            new_uly = max(0, new_uly - diff // 2)
                            new_lry = min(img.height, new_lry + (diff - diff // 2))
                        
                        # Crop and save
                        cropped = img.crop((new_ulx, new_uly, new_lrx, new_lry))
                        
                        # Generate filename with source info
                        filename = generate_neume_filename(mei_basename, neume_type, i + 1)
                        cropped_path = os.path.join(neume_dir, filename)
                        cropped.save(cropped_path)
                        
                        cropped_images.append(cropped_path)
                        logger.debug(f"Saved {filename}")
                
                except Exception as e:
                    logger.error(f"Error processing neume {i+1} from {mei_file}: {e}")
                    continue
            
            if cropped_images:
                result_neumes[neume_type] = cropped_images
                logger.info(f"Extracted {len(cropped_images)} {neume_type} neumes")
        
        total_extracted = sum(len(images) for images in result_neumes.values())
        logger.info(f"Successfully processed {mei_file}: {total_extracted} neumes extracted")
        
        return {
            'file': mei_file,
            'status': 'success',
            'neumes': result_neumes,
            'total_extracted': total_extracted
        }
    
    except Exception as e:
        logger.error(f"Error processing MEI file {mei_file}: {e}")
        return {'file': mei_file, 'status': 'error', 'error': str(e), 'neumes': {}}

def process_all_mei_files_parallel(mei_dir, output_dir, image_dir, json_file, 
                                 width_scale, height_scale, min_width, min_height, 
                                 buffer, max_workers=None, verbose=False):
    """Process all MEI files using parallel processing with enhanced diagnostics"""
    
    # Set up main logging
    log_file = os.path.join(output_dir, 'extraction_main.log')
    os.makedirs(output_dir, exist_ok=True)
    logger = setup_logging(log_file, verbose)
    
    start_time = time.time()
    
    # Find all MEI files
    if not os.path.exists(mei_dir):
        logger.error(f"MEI directory not found: {mei_dir}")
        return 1
    
    mei_files = [f for f in os.listdir(mei_dir) if f.endswith('.mei')]
    if not mei_files:
        logger.error(f"No MEI files found in {mei_dir}")
        return 1
    
    logger.info(f"Found {len(mei_files)} MEI files to process")
    
    # Determine number of workers
    if max_workers is None:
        max_workers = min(multiprocessing.cpu_count() - 2, len(mei_files), 8)  # Cap at 8 for I/O
    
    logger.info(f"Using {max_workers} parallel workers")
    
    # Prepare arguments for each process
    process_args = [
        (mei_file, mei_dir, output_dir, image_dir, 
         width_scale, height_scale, min_width, min_height, buffer, verbose)
        for mei_file in mei_files
    ]
    
    # Process files in parallel
    all_results = []
    successful_files = 0
    total_neumes_extracted = 0
    all_neume_data = defaultdict(list)
    failed_files = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_file = {executor.submit(process_single_mei_file, args): args[0] 
                         for args in process_args}
        
        # Process completed jobs with progress bar
        for future in tqdm(as_completed(future_to_file), total=len(mei_files), 
                          desc="Processing MEI files"):
            mei_file = future_to_file[future]
            
            try:
                result = future.result()
                all_results.append(result)
                
                if result['status'] == 'success':
                    successful_files += 1
                    total_neumes_extracted += result.get('total_extracted', 0)
                    
                    # Combine neume data
                    for neume_type, images in result['neumes'].items():
                        all_neume_data[neume_type].extend(images)
                
                elif result['status'] in ['error', 'no_data', 'no_image']:
                    failed_files.append({
                        'file': mei_file,
                        'reason': result['status'],
                        'error': result.get('error', '')
                    })
                    logger.warning(f"Failed to process {mei_file}: {result['status']}")
                
            except Exception as e:
                failed_files.append({
                    'file': mei_file,
                    'reason': 'exception',
                    'error': str(e)
                })
                logger.error(f"Exception processing {mei_file}: {e}")
    
    # Generate final JSON output
    if all_neume_data:
        formatted_data = []
        for neume_type, images in all_neume_data.items():
            formatted_data.append({
                "type": neume_type,
                "urls": images,
                "count": len(images)
            })
        
        with open(json_file, 'w') as f:
            json.dump(formatted_data, f, indent=2)
        
        logger.info(f"Saved combined JSON to {json_file}")
    
    # Generate comprehensive processing report
    processing_time = time.time() - start_time
    report = {
        'processing_time_seconds': processing_time,
        'total_files_found': len(mei_files),
        'successful_files': successful_files,
        'failed_files': len(failed_files),
        'total_neumes_extracted': total_neumes_extracted,
        'neume_types_found': len(all_neume_data),
        'neume_type_counts': {nt: len(images) for nt, images in all_neume_data.items()},
        'failed_file_details': failed_files,
        'settings_used': {
            'width_scale': width_scale,
            'height_scale': height_scale,
            'min_width': min_width,
            'min_height': min_height,
            'buffer': buffer,
            'max_workers': max_workers
        }
    }
    
    report_file = os.path.join(output_dir, 'processing_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Log summary
    logger.info(f"Processing complete in {processing_time:.2f} seconds")
    logger.info(f"Successfully processed {successful_files}/{len(mei_files)} files")
    logger.info(f"Extracted {total_neumes_extracted} total neumes across {len(all_neume_data)} types")
    logger.info(f"Results saved to {json_file}")
    logger.info(f"Report saved to {report_file}")
    
    if failed_files:
        logger.warning(f"Failed to process {len(failed_files)} files - see report for details")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description='Enhanced batch MEI neume extractor with diagnostics')
    parser.add_argument('--mei-dir', required=True, help='Directory containing MEI files')
    parser.add_argument('--output', required=True, help='Base output directory')
    parser.add_argument('--images', required=True, help='Directory containing source images')
    parser.add_argument('--json', help='Path to save JSON output (default: output_dir/neumes.json)')
    parser.add_argument('--width-scale', type=float, default=DEFAULT_WIDTH_SCALE)
    parser.add_argument('--height-scale', type=float, default=DEFAULT_HEIGHT_SCALE)
    parser.add_argument('--min-width', type=int, default=DEFAULT_MIN_WIDTH)
    parser.add_argument('--min-height', type=int, default=DEFAULT_MIN_HEIGHT)
    parser.add_argument('--buffer', type=int, default=DEFAULT_BUFFER)
    parser.add_argument('--workers', type=int, help='Number of parallel workers (default: auto)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze first MEI file without processing')
    
    args = parser.parse_args()
    
    # Set default JSON output path
    if args.json is None:
        args.json = os.path.join(args.output, 'neumes.json')
    
    print("=== Enhanced Batch MEI Neume Extractor ===")
    print(f"MEI Directory: {args.mei_dir}")
    print(f"Output Directory: {args.output}")
    print(f"Images Directory: {args.images}")
    print(f"Scale factors: {args.width_scale}x width, {args.height_scale}x height")
    print(f"Verbose logging: {args.verbose}")
    
    # If analyze-only mode, just analyze the first MEI file
    if args.analyze_only:
        mei_files = [f for f in os.listdir(args.mei_dir) if f.endswith('.mei')]
        if mei_files:
            first_mei = os.path.join(args.mei_dir, mei_files[0])
            print(f"\nAnalyzing first MEI file: {first_mei}")
            
            # Set up basic logging for analysis
            logging.basicConfig(level=logging.INFO, format='%(message)s')
            logger = logging.getLogger(__name__)
            
            # Run the analysis
            try:
                structure_info = analyze_mei_structure(first_mei, logger)
                
                if structure_info:
                    print(f"\nStructure Analysis Results:")
                    print(f"  Namespace: {structure_info['namespace']}")
                    print(f"  Has facsimile: {structure_info['has_facsimile']}")
                    print(f"  Zone count: {structure_info['zone_count']}")
                    print(f"  NC elements with facs: {structure_info['nc_count']}")
                else:
                    print("Failed to analyze MEI structure")
                
                # Test image filename extraction
                mei_basename = os.path.basename(first_mei)
                extracted_filename = extract_image_filename(mei_basename, logger)
                print(f"\nImage Filename Extraction:")
                print(f"  MEI filename: {mei_basename}")
                print(f"  Extracted image name: {extracted_filename}")
                
                # Check if image exists
                if extracted_filename:
                    potential_names = [extracted_filename]
                    actual_image = check_image_availability(args.images, potential_names, logger)
                    print(f"  Image found: {actual_image is not None}")
                    if actual_image:
                        print(f"  Actual image file: {actual_image}")
                else:
                    print("  No image filename could be extracted")
                
            except Exception as e:
                print(f"Error during analysis: {e}")
                import traceback
                traceback.print_exc()
                
        else:
            print("No MEI files found for analysis")
        return 0
    
    return process_all_mei_files_parallel(
        args.mei_dir, args.output, args.images, args.json,
        args.width_scale, args.height_scale, args.min_width, args.min_height,
        args.buffer, args.workers, args.verbose
    )

if __name__ == "__main__":
    sys.exit(main())
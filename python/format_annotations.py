#!/usr/bin/env python3
"""
Script to convert raw JSON snippets into properly formatted annotations JSON.
Optimized for processing very large files with hundreds of URLs per neume type.
Fixed to properly associate URLs with their neume types.
"""

import os
import json
import argparse
import sys
import re
from collections import defaultdict

def streaming_parse_large_file(file_path):
    """
    Parse a large file using line-by-line processing to identify neume types and their URLs.
    """
    print(f"Processing large file: {file_path}")
    
    try:
        # First check if it's a well-formed JSON file
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            # If it starts with [ it might be a JSON array
            if first_line.startswith('['):
                try:
                    # Try to parse as JSON
                    f.seek(0)  # Go back to beginning
                    data = json.load(f)
                    if isinstance(data, list):
                        valid_entries = []
                        for entry in data:
                            if isinstance(entry, dict) and "type" in entry and "urls" in entry:
                                valid_entries.append(entry)
                        
                        if valid_entries:
                            print(f"Successfully parsed JSON array with {len(valid_entries)} neume types")
                            for entry in valid_entries:
                                print(f"  - {entry['type']}: {len(entry['urls'])} URLs")
                            return valid_entries
                except json.JSONDecodeError as e:
                    print(f"Not valid JSON: {e}")
                    # Will continue with line-by-line parsing
    except Exception as e:
        print(f"Error checking file format: {e}")
    
    # Process line by line for very large files
    print("Using line-by-line parsing for large file...")
    
    neume_data = {}  # Store neume type -> list of URLs
    current_type = None
    in_urls_block = False
    url_buffer = []  # Buffer to collect URLs for current type
    
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Look for neume type declarations
                type_match = re.search(r'"type"\s*:\s*"([^"]+)"', line)
                if type_match:
                    # If we were collecting URLs for a previous type, save them
                    if current_type and url_buffer:
                        neume_data[current_type] = url_buffer
                        print(f"Collected {len(url_buffer)} URLs for {current_type}")
                        url_buffer = []  # Clear buffer for new type
                    
                    current_type = type_match.group(1)
                    in_urls_block = False
                    print(f"Found neume type on line {line_num}: {current_type}")
                
                # Check for URLs array start
                if current_type and '"urls"' in line and '[' in line:
                    in_urls_block = True
                    # If the line also contains URLs, extract them
                    urls = re.findall(r'"(https?://[^"]+)"', line)
                    url_buffer.extend(urls)
                    continue
                
                # If we're in a URLs block, extract any URLs
                if in_urls_block:
                    urls = re.findall(r'"(https?://[^"]+)"', line)
                    url_buffer.extend(urls)
                    
                    # Check if this is the end of the URLs block
                    if ']' in line:
                        if current_type:
                            neume_data[current_type] = url_buffer
                            print(f"Collected {len(url_buffer)} URLs for {current_type}")
                            url_buffer = []
                        in_urls_block = False
        
        # Make sure we save the last batch of URLs if the file ended
        if current_type and url_buffer:
            neume_data[current_type] = url_buffer
            print(f"Collected {len(url_buffer)} URLs for {current_type}")
        
        # Convert to the expected list format
        result = []
        for neume_type, urls in neume_data.items():
            result.append({
                "type": neume_type,
                "urls": urls
            })
        
        if result:
            print(f"Successfully extracted {len(result)} neume types")
            return result
        else:
            print("No neume types were successfully extracted")
    
    except Exception as e:
        print(f"Error during line-by-line parsing: {e}")
        import traceback
        traceback.print_exc()
    
    # If we get here, try an even more basic approach
    print("Trying simpler parsing approach...")
    
    try:
        # Read the first ~1000 bytes to try to identify the format
        with open(file_path, 'r') as f:
            start_text = f.read(1000)
        
        # Check if this looks like a raw JSON-like format with separate neume types
        types = []
        type_matches = re.finditer(r'"type"\s*:\s*"([^"]+)"', start_text)
        types = [match.group(1) for match in type_matches]
        
        if types:
            print(f"Found {len(types)} potential neume types in file start")
            
            # Process the file in larger chunks to extract all content
            neume_data = defaultdict(list)
            current_type = None
            
            with open(file_path, 'r') as f:
                # Process chunk by chunk
                chunk_size = 10 * 1024 * 1024  # 10MB chunks
                chunk = f.read(chunk_size)
                
                while chunk:
                    # Find all type declarations in this chunk
                    for match in re.finditer(r'"type"\s*:\s*"([^"]+)"', chunk):
                        type_pos = match.start()
                        neume_type = match.group(1)
                        
                        # Find the URLs section for this type
                        urls_start = chunk.find('"urls"', type_pos)
                        if urls_start != -1:
                            # Find opening bracket of URLs array
                            bracket_pos = chunk.find('[', urls_start)
                            if bracket_pos != -1:
                                # Find the closing bracket of the URLs array
                                # Need to handle nested brackets properly
                                bracket_level = 1
                                pos = bracket_pos + 1
                                urls_end = -1
                                
                                while pos < len(chunk) and bracket_level > 0:
                                    if chunk[pos] == '[':
                                        bracket_level += 1
                                    elif chunk[pos] == ']':
                                        bracket_level -= 1
                                        if bracket_level == 0:
                                            urls_end = pos
                                            break
                                    pos += 1
                                
                                if urls_end != -1:
                                    # Extract URLs from this section
                                    urls_text = chunk[bracket_pos:urls_end+1]
                                    urls = re.findall(r'"(https?://[^"]+)"', urls_text)
                                    neume_data[neume_type].extend(urls)
                    
                    # Read next chunk
                    chunk = f.read(chunk_size)
            
            # Convert to the expected format
            result = []
            for neume_type, urls in neume_data.items():
                print(f"Extracted {neume_type}: {len(urls)} URLs")
                result.append({
                    "type": neume_type,
                    "urls": urls
                })
            
            if result:
                return result
    
    except Exception as e:
        print(f"Error during chunk parsing: {e}")
        import traceback
        traceback.print_exc()
    
    # Last resort - get all URLs without type information
    print("WARNING: Falling back to extracting all URLs without type information")
    
    try:
        urls = []
        with open(file_path, 'r') as f:
            for line in f:
                line_urls = re.findall(r'"(https?://[^"]+)"', line)
                urls.extend(line_urls)
        
        if urls:
            print(f"Found {len(urls)} URLs with basic extraction (without type information)")
            return [{
                "type": "Unknown",
                "urls": urls
            }]
    except Exception as e:
        print(f"Error during basic URL extraction: {e}")
    
    return None

def save_annotations(annotations, output_file, append):
    """Save the annotations to the output file"""
    existing = []
    
    # Load existing annotations if appending
    if append and os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                existing = json.load(f)
            print(f"Loaded {len(existing)} existing annotations from output file")
        except json.JSONDecodeError:
            print(f"Error: Output file exists but is not valid JSON. Creating new file.")
            existing = []
    
    # If not appending and file exists, confirm overwrite
    if os.path.exists(output_file) and not append:
        confirm = input(f"Output file {output_file} already exists. Overwrite? [y/N]: ").lower()
        if confirm != 'y':
            print("Operation cancelled")
            return False
    
    # Determine the final annotations
    final_annotations = []
    
    # First add existing types that will be kept
    if append:
        final_annotations = existing.copy()
    
    # Process each new annotation
    for annotation in annotations:
        neume_type = annotation["type"]
        add_to_final = True
        
        # Check if this type already exists
        for i, existing_annotation in enumerate(existing):
            if existing_annotation["type"] == neume_type:
                print(f"Neume type '{neume_type}' already exists in output file")
                choice = input("Do you want to (a)ppend to it, (r)eplace it, or (s)kip? [a/r/s]: ").lower()
                
                if choice == 'a':
                    # Append URLs to existing entry
                    existing_urls = set(existing_annotation["urls"])
                    new_urls = existing_annotation["urls"].copy()
                    
                    added = 0
                    for url in annotation["urls"]:
                        if url not in existing_urls:
                            new_urls.append(url)
                            added += 1
                    
                    if append:
                        final_annotations[i]["urls"] = new_urls
                    else:
                        annotation["urls"] = new_urls
                    
                    print(f"Appended {added} new URLs to '{neume_type}'")
                elif choice == 'r':
                    # Replace existing entry
                    if append:
                        final_annotations[i]["urls"] = annotation["urls"]
                    # For non-append mode, we'll add the new annotation and remove old ones later
                elif choice == 's':
                    # Skip this annotation
                    add_to_final = False
                
                break
        
        # Add new annotation if needed
        if add_to_final and not append:
            final_annotations.append(annotation)
    
    # For non-append mode, ensure uniqueness of types
    if not append:
        # Create a new list with unique types (keeping the last one for each type)
        unique_annotations = []
        types_seen = set()
        
        for annotation in reversed(final_annotations):
            if annotation["type"] not in types_seen:
                unique_annotations.append(annotation)
                types_seen.add(annotation["type"])
        
        final_annotations = list(reversed(unique_annotations))
    
    # Write to output file with efficient streaming for large data
    print(f"Writing {len(final_annotations)} neume types to {output_file}...")
    
    try:
        with open(output_file, 'w') as f:
            # Use a more efficient approach for very large data
            f.write("[\n")
            
            for i, annotation in enumerate(final_annotations):
                # Write each annotation as JSON
                json_str = json.dumps(annotation, indent=2)
                
                # Add comma for all but the last item
                if i < len(final_annotations) - 1:
                    f.write(json_str + ",\n")
                else:
                    f.write(json_str + "\n")
            
            f.write("]\n")
        
        print(f"Successfully saved annotations to {output_file}")
        for annotation in final_annotations:
            print(f"  - {annotation['type']}: {len(annotation['urls'])} URLs")
        
        return True
    
    except Exception as e:
        print(f"Error saving annotations: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Format raw JSON snippets into properly formatted annotations JSON')
    parser.add_argument('--input', required=True,
                      help='Path to raw JSON snippet file')
    parser.add_argument('--output', default='../public/real-annotations.json',
                      help='Path to output formatted annotations JSON file')
    parser.add_argument('--append', action='store_true',
                      help='Append to existing output file instead of overwriting')
    parser.add_argument('--type', default=None,
                      help='Manually specify neume type if not found in the input')
    parser.add_argument('--batch', action='store_true',
                      help='Process multiple files (input should be a directory)')
    
    args = parser.parse_args()
    
    print(f"=== Annotations Formatter (Large File Optimized) ===")
    
    if args.batch:
        if not os.path.isdir(args.input):
            print(f"Error: Input must be a directory when using --batch")
            return 1
        
        # Process all files in the directory
        success_count = 0
        failed_count = 0
        
        for filename in os.listdir(args.input):
            if filename.endswith('.txt') or filename.endswith('.json'):
                input_file = os.path.join(args.input, filename)
                
                print(f"\nProcessing {filename}...")
                
                # Parse the file
                annotations = streaming_parse_large_file(input_file)
                
                # If parsing failed but manual type is provided
                if not annotations and args.type:
                    print(f"Using manually specified type: {args.type}")
                    urls = []
                    
                    # Extract URLs with line-by-line approach
                    with open(input_file, 'r') as f:
                        for line in f:
                            urls.extend(re.findall(r'"(https?://[^"]+)"', line))
                    
                    if urls:
                        annotations = [{
                            "type": args.type,
                            "urls": urls
                        }]
                        print(f"Extracted {len(urls)} URLs for manual type")
                
                # If parsing failed and filename might contain type
                if not annotations and not args.type:
                    name_match = re.search(r'^(\w+)[_\s-]', filename)
                    if name_match:
                        neume_type = name_match.group(1)
                        print(f"Using filename to detect type: {neume_type}")
                        
                        urls = []
                        # Extract URLs with line-by-line approach
                        with open(input_file, 'r') as f:
                            for line in f:
                                urls.extend(re.findall(r'"(https?://[^"]+)"', line))
                        
                        if urls:
                            annotations = [{
                                "type": neume_type,
                                "urls": urls
                            }]
                            print(f"Extracted {len(urls)} URLs for filename type")
                
                if annotations:
                    # Save annotations
                    success = save_annotations(annotations, args.output, args.append)
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    print(f"Error: Could not parse file {filename}")
                    failed_count += 1
        
        print(f"\nBatch processing complete: {success_count} succeeded, {failed_count} failed")
    else:
        # Process a single file
        # Parse the file
        annotations = streaming_parse_large_file(args.input)
        
        # If parsing failed but manual type is provided
        if not annotations and args.type:
            print(f"Using manually specified type: {args.type}")
            urls = []
            
            # Extract URLs with line-by-line approach
            with open(args.input, 'r') as f:
                for line in f:
                    urls.extend(re.findall(r'"(https?://[^"]+)"', line))
            
            if urls:
                annotations = [{
                    "type": args.type,
                    "urls": urls
                }]
                print(f"Extracted {len(urls)} URLs for manual type")
        
        if annotations:
            # Save annotations
            success = save_annotations(annotations, args.output, args.append)
            if not success:
                return 1
        else:
            print(f"Error: Could not parse file {args.input}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
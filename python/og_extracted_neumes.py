#!/usr/bin/env python3
"""
Script to convert raw JSON snippets into properly formatted annotations JSON.
Optimized for processing very large files with hundreds of URLs per neume type.
"""

import os
import json
import argparse
import sys
import re
from collections import defaultdict

def streaming_json_parse(file_path):
    """
    Efficiently parse a potentially large JSON file using a streaming approach.
    Returns a list of annotation objects.
    """
    print(f"Attempting to parse large JSON file: {file_path}")
    
    try:
        # First attempt: Try direct JSON loading with higher memory efficiency
        with open(file_path, 'r') as f:
            try:
                # Use a larger chunk size for reading
                data = json.load(f)
                
                # Validate the structure
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
                    
                elif isinstance(data, dict) and "type" in data and "urls" in data:
                    print(f"Successfully parsed single neume object: {data['type']}")
                    return [data]
                    
                print(f"JSON parsed but invalid structure: {type(data)}")
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                # Fall through to alternative parsing methods
    except Exception as e:
        print(f"Error during file reading: {e}")
    
    # Second attempt: Use line-by-line regex-based parsing
    print("Attempting regex-based parsing...")
    
    try:
        # For very large files, we'll extract information line by line
        neume_types = defaultdict(list)  # Type -> list of URLs
        current_type = None
        parsing_urls = False
        
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Look for type definition
                type_match = re.search(r'"type":\s*"([^"]+)"', line)
                if type_match:
                    current_type = type_match.group(1)
                    parsing_urls = False
                    print(f"Found neume type on line {line_num}: {current_type}")
                
                # Look for start of URLs array
                if current_type and not parsing_urls and '"urls"' in line:
                    parsing_urls = True
                    continue
                
                # Extract URLs from line if we're in a URLs section
                if parsing_urls:
                    urls = re.findall(r'"(http[^"]+)"', line)
                    if urls:
                        neume_types[current_type].extend(urls)
                    
                    # Check if we've reached the end of the URLs array
                    if "]" in line and ("}" in line or line.strip() == "]"):
                        parsing_urls = False
        
        # Convert to the expected format
        result = []
        for neume_type, urls in neume_types.items():
            print(f"Extracted {neume_type}: {len(urls)} URLs")
            result.append({
                "type": neume_type,
                "urls": urls
            })
        
        if result:
            return result
        
    except Exception as e:
        print(f"Error during regex parsing: {e}")
    
    # Last attempt: Basic URL extraction
    print("Attempting basic URL extraction...")
    
    try:
        urls = []
        with open(file_path, 'r') as f:
            # Read in chunks to handle large files
            chunk_size = 1024 * 1024  # 1MB chunks
            chunk = f.read(chunk_size)
            
            while chunk:
                # Extract URLs from this chunk
                chunk_urls = re.findall(r'"(http[^"]+)"', chunk)
                urls.extend(chunk_urls)
                
                # Read next chunk
                chunk = f.read(chunk_size)
        
        if urls:
            print(f"Found {len(urls)} URLs with basic extraction")
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
                annotations = streaming_json_parse(input_file)
                
                # If parsing failed but manual type is provided
                if not annotations and args.type:
                    print(f"Using manually specified type: {args.type}")
                    urls = []
                    
                    # Extract URLs with line-by-line approach
                    with open(input_file, 'r') as f:
                        for line in f:
                            urls.extend(re.findall(r'"(http[^"]+)"', line))
                    
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
                                urls.extend(re.findall(r'"(http[^"]+)"', line))
                        
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
        annotations = streaming_json_parse(args.input)
        
        # If parsing failed but manual type is provided
        if not annotations and args.type:
            print(f"Using manually specified type: {args.type}")
            urls = []
            
            # Extract URLs with line-by-line approach
            with open(args.input, 'r') as f:
                for line in f:
                    urls.extend(re.findall(r'"(http[^"]+)"', line))
            
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
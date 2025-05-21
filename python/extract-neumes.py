# extract_neumes.py
import json
import os
import re
import time
from urllib.parse import unquote
import requests
from PIL import Image
from io import BytesIO
import traceback

def extract_neume_images():
    # 1. Load the annotations JSON file
    json_file_path = '/Users/kyriebouressa/Documents/neume-mapper-extractor/public/real-annotationsZ.json'
    with open(json_file_path, 'r', encoding='utf-8') as f:
        # Load the JSON data
        annotations = json.load(f)
    
    # Print the structure for debugging
    print(f"JSON data type: {type(annotations)}")
    if isinstance(annotations, list):
        print(f"List has {len(annotations)} items")
        if len(annotations) > 0:
            print(f"First item type: {type(annotations[0])}")
            if isinstance(annotations[0], dict):
                print(f"First item keys: {annotations[0].keys()}")
    
    # Original output directory (commented out)
    # output_dir = 'extracted_neumes'
    
    # New output directory on external drive
    output_dir = '/Volumes/Expansion/extracted_neumes'
    os.makedirs(output_dir, exist_ok=True)
    
    # Add headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # Check the type of the loaded data
    if isinstance(annotations, list):
        # Process each annotation in the list
        for annotation in annotations:
            if not isinstance(annotation, dict) or 'type' not in annotation or 'urls' not in annotation:
                print(f"Skipping invalid annotation: {annotation}")
                continue
                
            neume_type = annotation['type']
            print(f"Processing {neume_type} ({len(annotation['urls'])} images)")
            
            # Create directory for this neume type
            neume_dir = os.path.join(output_dir, neume_type.replace(' ', '_'))
            os.makedirs(neume_dir, exist_ok=True)
            
            # Process each URL
            for i, url in enumerate(annotation['urls']):
                process_url(url, i, neume_type, len(annotation['urls']), neume_dir, headers)
    elif isinstance(annotations, dict) and 'type' in annotations and 'urls' in annotations:
        # It's a single annotation object
        neume_type = annotations['type']
        print(f"Processing {neume_type} ({len(annotations['urls'])} images)")
        
        # Create directory for this neume type
        neume_dir = os.path.join(output_dir, neume_type.replace(' ', '_'))
        os.makedirs(neume_dir, exist_ok=True)
        
        # Process each URL
        for i, url in enumerate(annotations['urls']):
            process_url(url, i, neume_type, len(annotations['urls']), neume_dir, headers)
    else:
        print(f"Unsupported JSON format: {type(annotations)}")
        
    print("Extraction complete!")
    
def process_url(url, i, neume_type, total_urls, neume_dir, headers):
    """Process a single URL and save the image"""
    try:
        # Print the raw URL for debugging
        print(f"Original URL: {url}")
        
        # Extract base URL (without the region parameter) - keep original logic
        base_url = re.sub(r'/[\d]+,[\d]+,[\d]+,[\d]+/64,/0/default.jpg', '', url)
        print(f"Base URL: {base_url}")
        
        # Extract bounding box coordinates - keep original logic
        coords_match = re.search(r'([\d]+),([\d]+),([\d]+),([\d]+)', url)
        if not coords_match:
            print(f"Could not find coordinates in URL: {url}")
            return
            
        x = int(coords_match.group(1))
        y = int(coords_match.group(2))
        width = int(coords_match.group(3))
        height = int(coords_match.group(4))
        print(f"Extracted coordinates: x={x}, y={y}, width={width}, height={height}")
        
        # CHANGE: Instead of trying to download the full image and crop,
        # just download the direct URL which already contains the neume
        print(f"Downloading image {i+1}/{total_urls} for {neume_type}")
        
        # Download the image directly from the URL
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to download {url}: {response.status_code}")
            print(f"Response content (first 200 chars): {response.content[:200]}")
            return
        
        # Extract page identifier from URL - keep original logic
        url_parts = url.split('/')
        page_id = url_parts[6] if len(url_parts) > 6 else f"page_{i}"
        
        # Open the downloaded image
        img = Image.open(BytesIO(response.content))
        
        # Save the image directly
        # Original path (commented out)
        # output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
        
        # New path on external drive
        output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
        img.save(output_path)
        print(f"Saved {output_path}")
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(0.5)
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        # Print exception traceback for better debugging
        traceback.print_exc()

if __name__ == "__main__":
    extract_neume_images()
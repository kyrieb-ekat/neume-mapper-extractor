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
    #with open(annotations.json', 'r') as f: # was annotations.json, original is 'real-annotations.json', testing with 'real-annotationsZ.json'
    json_file_path = '/Users/kyriebouressa/Documents/neume-mapper-extractor/public/real-annotationsZ.json'
    with open(json_file_path, 'r', encoding='utf-8') as f:
        # Load the JSON data
        annotations = json.load(f)
    
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
    
    # Process each annotation type
    for annotation in annotations:
        neume_type = annotation['type']
        print(f"Processing {neume_type} ({len(annotation['urls'])} images)")
        
        # Create directory for this neume type
        # Original path (commented out)
        # neume_dir = os.path.join(output_dir, neume_type.replace(' ', '_'))
        
        # New path on external drive
        neume_dir = os.path.join(output_dir, neume_type.replace(' ', '_'))
        os.makedirs(neume_dir, exist_ok=True)
        
        # Process each URL
        for i, url in enumerate(annotation['urls']):
            try:
                # Print the raw URL for debugging
                print(f"Original URL: {url}")
                
                # Extract base URL (without the region parameter)
                base_url = re.sub(r'/[\d]+,[\d]+,[\d]+,[\d]+/64,/0/default.jpg', '', url)
                
                # Print the base URL for debugging
                print(f"Base URL: {base_url}")
                
                # Extract bounding box coordinates
                coords_match = re.search(r'([\d]+),([\d]+),([\d]+),([\d]+)', url)
                if not coords_match:
                    print(f"Could not find coordinates in URL: {url}")
                    continue
                    
                x = int(coords_match.group(1))
                y = int(coords_match.group(2))
                width = int(coords_match.group(3))
                height = int(coords_match.group(4))
                
                print(f"Extracted coordinates: x={x}, y={y}, width={width}, height={height}")
                
                # Get the full image URL - use a specific size instead of "max"
                # Using "full" for the region and a large specific size like "3000," instead of "max"
                full_image_url = f"{base_url}/full/3000,/0/default.jpg"
                print(f"Full image URL: {full_image_url}")
                print(f"Downloading image {i+1}/{len(annotation['urls'])} for {neume_type}")
                
                # Download the full image with headers and longer timeout
                response = requests.get(full_image_url, headers=headers, timeout=30)
                
                # Print status code for debugging
                print(f"Response status code: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Failed to download {full_image_url}: {response.status_code}")
                    # Print the response content for error diagnosis
                    print(f"Response content (first 200 chars): {response.content[:200]}")
                    
                    # Try an alternate URL format if the first one fails
                    alt_image_url = f"{base_url}/full/,1000/0/default.jpg"
                    print(f"Trying alternate URL: {alt_image_url}")
                    response = requests.get(alt_image_url, headers=headers, timeout=30)
                    print(f"Alternate URL response status: {response.status_code}")
                    
                    if response.status_code != 200:
                        print(f"Failed to download alternate URL: {response.status_code}")
                        continue
                    
                # Extract page identifier from URL
                url_parts = url.split('/')
                page_id = url_parts[6] if len(url_parts) > 6 else f"page_{i}"
                
                # Open and crop the image
                img = Image.open(BytesIO(response.content))
                
                # Check if cropping coordinates are valid
                if x < 0 or y < 0 or x+width > img.width or y+height > img.height:
                    print(f"Warning: Invalid crop coordinates for image size {img.width}x{img.height}")
                    # Adjust coordinates to be valid
                    x = max(0, x)
                    y = max(0, y)
                    width = min(width, img.width - x)
                    height = min(height, img.height - y)
                    print(f"Adjusted to: x={x}, y={y}, width={width}, height={height}")
                
                cropped_img = img.crop((x, y, x + width, y + height))
                
                # Save the cropped image
                # Original path (commented out)
                # output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
                
                # New path on external drive
                output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
                cropped_img.save(output_path)
                print(f"Saved {output_path}")
                
                # Add a delay to avoid overwhelming the server
                time.sleep(1.0)
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                # Print exception traceback for better debugging
                traceback.print_exc()
    
    print("Extraction complete!")

if __name__ == "__main__":
    extract_neume_images()
    
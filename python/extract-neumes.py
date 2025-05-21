# extract_neumes.py
import json
import os
import re
import time
from urllib.parse import unquote
import requests
from PIL import Image
from io import BytesIO

def extract_neume_images():
    # 1. Load the annotations JSON file
    with open('annotations.json', 'r') as f:
        annotations = json.load(f)
    
    # Original output directory (commented out)
    # output_dir = 'extracted_neumes'
    
    # New output directory on external drive
    output_dir = '/Volumes/Expansion/extracted_neumes'
    os.makedirs(output_dir, exist_ok=True)
    
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
                # Extract base URL (without the region parameter)
                base_url = re.sub(r'/[\d]+,[\d]+,[\d]+,[\d]+/64,/0/default.jpg', '', url)
                
                # Extract bounding box coordinates
                coords_match = re.search(r'([\d]+),([\d]+),([\d]+),([\d]+)', url)
                if not coords_match:
                    print(f"Could not find coordinates in URL: {url}")
                    continue
                    
                x = int(coords_match.group(1))
                y = int(coords_match.group(2))
                width = int(coords_match.group(3))
                height = int(coords_match.group(4))
                
                # Get the full image URL
                full_image_url = f"{base_url}/full/max/0/default.jpg"
                print(f"Downloading image {i+1}/{len(annotation['urls'])} for {neume_type}")
                
                # Download the full image
                response = requests.get(full_image_url)
                if response.status_code != 200:
                    print(f"Failed to download {full_image_url}: {response.status_code}")
                    continue
                    
                # Extract page identifier from URL
                url_parts = url.split('/')
                page_id = url_parts[6] if len(url_parts) > 6 else f"page_{i}"
                
                # Open and crop the image
                img = Image.open(BytesIO(response.content))
                cropped_img = img.crop((x, y, x + width, y + height))
                
                # Save the cropped image
                # Original path (commented out)
                # output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
                
                # New path on external drive
                output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
                cropped_img.save(output_path)
                print(f"Saved {output_path}")
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
    
    print("Extraction complete!")

if __name__ == "__main__":
    extract_neume_images()
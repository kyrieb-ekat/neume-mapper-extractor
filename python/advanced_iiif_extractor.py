# advanced_iiif_extractor.py
import json
import os
import re
import time
import csv
from urllib.parse import unquote
import requests
from PIL import Image
from io import BytesIO

class IIIFExtractor:
    def __init__(self, annotations_file='annotations.json', output_dir='extracted_neumes'):
        self.annotations_file = annotations_file
        self.output_dir = output_dir
        self.annotations = None
        self.metadata = []
    
    def load_annotations(self):
        """Load the annotations data from JSON file"""
        try:
            with open(self.annotations_file, 'r') as f:
                self.annotations = json.load(f)
            print(f"Loaded {len(self.annotations)} annotation types")
            return True
        except Exception as e:
            print(f"Error loading annotations: {e}")
            return False
    
    def setup_directories(self):
        """Create necessary output directories"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_image_info(self, url):
        """Extract IIIF image information from URL"""
        # Example URL: http://www.e-codices.unifr.ch/loris/csg/csg-0390/csg-0390_007.jp2/1425,1005,67,76/64,/0/default.jpg
        base_url = re.sub(r'/[\d]+,[\d]+,[\d]+,[\d]+/64,/0/default.jpg', '', url)
        
        # Extract coordinates
        coords_match = re.search(r'([\d]+),([\d]+),([\d]+),([\d]+)', url)
        if not coords_match:
            raise ValueError(f"Could not extract coordinates from URL: {url}")
        
        x = int(coords_match.group(1))
        y = int(coords_match.group(2))
        width = int(coords_match.group(3))
        height = int(coords_match.group(4))
        
        # Extract manuscript and page info
        parts = base_url.split('/')
        manuscript = '/'.join(parts[-3:-1]) if len(parts) >= 3 else "unknown"
        page = parts[-1] if parts else "unknown"
        
        return {
            'base_url': base_url,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'manuscript': manuscript,
            'page': page
        }
    
    def download_region(self, info, size='full'):
        """Download image region directly using IIIF parameters"""
        region = f"{info['x']},{info['y']},{info['width']},{info['height']}"
        
        # For IIIF, we can request just the region we want
        # size options: 'full', 'max', or specific dimensions
        region_url = f"{info['base_url']}/{region}/{size}/0/default.jpg"
        
        response = requests.get(region_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download region: {response.status_code}")
        
        return Image.open(BytesIO(response.content))
    
    def export_metadata(self):
        """Export metadata to CSV file"""
        csv_path = os.path.join(self.output_dir, 'neume_metadata.csv')
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['filename', 'neume_type', 'manuscript', 'page', 'x', 'y', 'width', 'height', 'original_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metadata)
        print(f"Metadata exported to {csv_path}")
    
    def extract_all(self):
        """Extract all neume images from the annotations"""
        if not self.annotations and not self.load_annotations():
            return False
        
        self.setup_directories()
        
        for annotation in self.annotations:
            neume_type = annotation['type']
            print(f"Processing {neume_type} ({len(annotation['urls'])} images)")
            
            # Create directory for this neume type
            neume_dir = os.path.join(self.output_dir, re.sub(r'[^\w\-_]', '_', neume_type))
            os.makedirs(neume_dir, exist_ok=True)
            
            for i, url in enumerate(annotation['urls']):
                try:
                    print(f"Processing image {i+1}/{len(annotation['urls'])} for {neume_type}")
                    
                    # Extract image information
                    info = self.extract_image_info(url)
                    
                    # Download the region directly
                    img = self.download_region(info)
                    
                    # Determine filename
                    filename = f"{info['page']}_{i:04d}.jpg"
                    output_path = os.path.join(neume_dir, filename)
                    
                    # Save the image
                    img.save(output_path)
                    
                    # Add to metadata
                    self.metadata.append({
                        'filename': filename,
                        'neume_type': neume_type,
                        'manuscript': info['manuscript'],
                        'page': info['page'],
                        'x': info['x'],
                        'y': info['y'],
                        'width': info['width'],
                        'height': info['height'],
                        'original_url': url
                    })
                    
                    print(f"Saved {output_path}")
                    
                    # Add a small delay
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
        
        # Export metadata
        self.export_metadata()
        print("Extraction complete!")
        return True

if __name__ == "__main__":
    extractor = IIIFExtractor()
    extractor.extract_all()
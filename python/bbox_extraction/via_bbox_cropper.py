import csv
import json
import os
import argparse
from PIL import Image
import requests
from io import BytesIO
from urllib.parse import urlparse
import time

class VIABoundingBoxCropper:
    def __init__(self, output_dir='cropped_images', delay=0.1):
        self.output_dir = output_dir
        self.delay = delay
        os.makedirs(output_dir, exist_ok=True)
    
    def load_image_from_url(self, url):
        """Download image from URL"""
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to download image: {response.status_code}")
        return Image.open(BytesIO(response.content))
    
    def load_image_from_path(self, path):
        """Load image from local file path"""
        return Image.open(path)
    
    def parse_json_field(self, json_str):
        """Parse JSON field from VIA CSV (handles double quotes)"""
        if not json_str or json_str == '{}':
            return {}
        
        # Handle different quote escaping patterns
        cleaned = json_str.strip()
        
        # Remove outer quotes if they exist
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        
        # Replace escaped double quotes
        cleaned = cleaned.replace('""', '"')
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON '{json_str}': {e}")
            return {}
    
    def process_via_csv(self, csv_path, image_dir=None, image_url_template=None):
        """
        Process VIA CSV annotations
        
        Args:
            csv_path: Path to VIA CSV file
            image_dir: Directory containing images (for local files)
            image_url_template: Template for image URLs (e.g., "https://example.com/{filename}")
        """
        processed_images = {}
        total_annotations = 0
        successful_crops = 0
        
        try:
            # Open with UTF-8-sig to handle BOM (Byte Order Mark)
            with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
                # First, let's check the headers
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                print(f"CSV headers found: {headers}")
                
                # Find the filename column (might have BOM prefix)
                filename_col = None
                for header in headers:
                    if header.strip().endswith('filename'):
                        filename_col = header
                        break
                
                if not filename_col:
                    print(f"Error: 'filename' column not found. Available columns: {headers}")
                    return
                
                print(f"Using filename column: '{filename_col}'")
                
                for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
                    try:
                        # Debug: print first few rows to see structure
                        if row_num <= 3:
                            print(f"Row {row_num}: {dict(row)}")
                        
                        filename = row.get(filename_col, '').strip()
                        if not filename:
                            print(f"Row {row_num}: Empty filename, skipping")
                            continue
                        
                        # Skip empty annotations
                        region_shape = row.get('region_shape_attributes', '').strip()
                        if not region_shape or region_shape == '{}':
                            print(f"Row {row_num}: No shape attributes for {filename}, skipping")
                            continue
                        
                        total_annotations += 1
                        
                        # Parse JSON fields
                        shape_attrs = self.parse_json_field(region_shape)
                        region_attrs = self.parse_json_field(row.get('region_attributes', '{}'))
                        
                        # Skip if not a rectangle
                        if shape_attrs.get('name') != 'rect':
                            print(f"Row {row_num}: Skipping non-rectangle annotation for {filename}")
                            continue
                        
                        # Extract bounding box coordinates
                        try:
                            x = int(shape_attrs['x'])
                            y = int(shape_attrs['y'])
                            width = int(shape_attrs['width'])
                            height = int(shape_attrs['height'])
                        except (KeyError, ValueError) as e:
                            print(f"Row {row_num}: Invalid bounding box coordinates for {filename}: {e}")
                            continue
                        
                        # Get label - try different possible keys
                        label = 'unknown'
                        for key, value in region_attrs.items():
                            if value and value != 'undefined':
                                label = str(value).strip()
                                break
                        
                        # Load image (only once per filename)
                        if filename not in processed_images:
                            try:
                                if image_url_template:
                                    image_url = image_url_template.format(filename=filename)
                                    print(f"Loading {filename} from URL...")
                                    image = self.load_image_from_url(image_url)
                                elif image_dir:
                                    image_path = os.path.join(image_dir, filename)
                                    if not os.path.exists(image_path):
                                        print(f"Row {row_num}: Image file not found: {image_path}")
                                        continue
                                    print(f"Loading {filename} from {image_path}...")
                                    image = self.load_image_from_path(image_path)
                                else:
                                    print(f"Row {row_num}: No image source specified for {filename}")
                                    continue
                                
                                processed_images[filename] = image
                            except Exception as e:
                                print(f"Row {row_num}: Error loading image {filename}: {e}")
                                continue
                        else:
                            image = processed_images[filename]
                        
                        # Create label directory
                        safe_label = label.replace(' ', '_').replace('/', '_').replace('\\', '_')
                        label_dir = os.path.join(self.output_dir, safe_label)
                        os.makedirs(label_dir, exist_ok=True)
                        
                        # Validate crop coordinates
                        img_width, img_height = image.size
                        if x < 0 or y < 0 or x + width > img_width or y + height > img_height:
                            print(f"Row {row_num}: Bounding box out of image bounds for {filename}")
                            print(f"  Image size: {img_width}x{img_height}, bbox: ({x},{y},{x+width},{y+height})")
                            continue
                        
                        # Crop image
                        cropped_image = image.crop((x, y, x + width, y + height))
                        
                        # Create unique filename
                        region_id = row.get('region_id', 'unknown')
                        base_name = os.path.splitext(filename)[0]
                        output_filename = f"{base_name}_region_{region_id}_{safe_label}.jpg"
                        output_path = os.path.join(label_dir, output_filename)
                        
                        # Save cropped image
                        cropped_image.save(output_path, 'JPEG')
                        print(f"Saved: {output_path}")
                        successful_crops += 1
                        
                        # Add delay to avoid overwhelming servers
                        if self.delay > 0:
                            time.sleep(self.delay)
                            
                    except Exception as e:
                        print(f"Row {row_num}: Error processing annotation for {filename}: {str(e)}")
                        continue
                        
        except FileNotFoundError:
            print(f"Error: CSV file not found: {csv_path}")
            return
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return
        
        print(f"\nProcessing complete!")
        print(f"Total annotations: {total_annotations}")
        print(f"Successful crops: {successful_crops}")
        print(f"Unique images processed: {len(processed_images)}")
    
    def convert_via_to_standard_json(self, csv_path, output_json_path, image_dir=None, image_url_template=None):
        """
        Convert VIA CSV to standard JSON format
        """
        annotations = []
        
        with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                filename = row['filename']
                
                # Skip empty annotations
                if not row.get('region_shape_attributes') or row.get('region_shape_attributes') == '{}':
                    continue
                
                try:
                    # Parse JSON fields
                    shape_attrs = self.parse_json_field(row['region_shape_attributes'])
                    region_attrs = self.parse_json_field(row['region_attributes'])
                    
                    # Skip if not a rectangle
                    if shape_attrs.get('name') != 'rect':
                        continue
                    
                    # Extract data
                    x = int(shape_attrs['x'])
                    y = int(shape_attrs['y'])
                    width = int(shape_attrs['width'])
                    height = int(shape_attrs['height'])
                    
                    # Get label
                    label = 'unknown'
                    for key, value in region_attrs.items():
                        if value and value != 'undefined':
                            label = value
                            break
                    
                    # Create annotation
                    annotation = {
                        "bbox": [x, y, width, height],
                        "label": label,
                        "id": f"{filename}_{row.get('region_id', 'unknown')}"
                    }
                    
                    # Add image source
                    if image_url_template:
                        annotation["image_url"] = image_url_template.format(filename=filename)
                    elif image_dir:
                        annotation["image_path"] = os.path.join(image_dir, filename)
                    else:
                        annotation["filename"] = filename
                    
                    annotations.append(annotation)
                    
                except Exception as e:
                    print(f"Error converting annotation for {filename}: {str(e)}")
                    continue
        
        # Save to JSON
        output_data = {"annotations": annotations}
        with open(output_json_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Converted {len(annotations)} annotations to {output_json_path}")
        return output_json_path

def main():
    parser = argparse.ArgumentParser(description='Crop bounding boxes from VIA CSV annotations')
    parser.add_argument('csv_file', help='Path to VIA CSV file')
    parser.add_argument('--image-dir', help='Directory containing image files')
    parser.add_argument('--image-url-template', 
                       help='URL template for images (e.g., "https://example.com/images/{filename}")')
    parser.add_argument('--output', default='cropped_images', help='Output directory')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between downloads (seconds)')
    parser.add_argument('--convert-only', help='Convert to standard JSON format and exit')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.image_dir and not args.image_url_template:
        print("Error: Must specify either --image-dir or --image-url-template")
        return
    
    cropper = VIABoundingBoxCropper(args.output, args.delay)
    
    if args.convert_only:
        cropper.convert_via_to_standard_json(
            args.csv_file, 
            args.convert_only,
            args.image_dir,
            args.image_url_template
        )
    else:
        cropper.process_via_csv(
            args.csv_file,
            args.image_dir,
            args.image_url_template
        )

if __name__ == "__main__":
    main()
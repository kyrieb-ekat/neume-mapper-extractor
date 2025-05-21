# parallel_extractor.py
import json
import os
import argparse
import concurrent.futures
from python.advanced_iiif_extractor import IIIFExtractor

def process_annotation_batch(annotation, output_dir, batch_id):
    """Process a single annotation batch"""
    extractor = IIIFExtractor(
        annotations_file=None,  # We're passing the annotation directly
        output_dir=os.path.join(output_dir, f"batch_{batch_id}")
    )
    
    # Set the annotation directly
    extractor.annotations = [annotation]
    
    # Extract the images
    extractor.extract_all()
    
    return batch_id, annotation['type'], len(annotation['urls'])

def main():
    parser = argparse.ArgumentParser(description='Extract neume images in parallel')
    parser.add_argument('--annotations', default='annotations.json', help='Path to annotations JSON file')
    parser.add_argument('--output', default='extracted_neumes', help='Output directory')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    args = parser.parse_args()
    
    # Load annotations
    with open(args.annotations, 'r') as f:
        annotations = json.load(f)
    
    print(f"Processing {len(annotations)} annotation types with {args.workers} workers")
    
    # Create main output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Process annotations in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        
        for i, annotation in enumerate(annotations):
            future = executor.submit(
                process_annotation_batch, 
                annotation, 
                args.output, 
                i
            )
            futures.append(future)
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_id, neume_type, count = future.result()
                results.append((batch_id, neume_type, count))
                print(f"Completed batch {batch_id}: {neume_type} ({count} images)")
            except Exception as e:
                print(f"Batch processing failed: {e}")
    
    # Merge metadata files
    merge_metadata(args.output)
    
    print(f"All batches complete! Processed {sum(count for _, _, count in results)} images")

def merge_metadata(base_dir):
    """Merge all metadata CSV files into one"""
    import csv
    import glob
    
    # Find all metadata files
    metadata_files = glob.glob(os.path.join(base_dir, "batch_*/neume_metadata.csv"))
    if not metadata_files:
        print("No metadata files found to merge")
        return
    
    # Prepare merged file
    merged_file = os.path.join(base_dir, "neume_metadata.csv")
    
    # Get header from first file
    with open(metadata_files[0], 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
    
    # Write merged file
    with open(merged_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        
        # Append data from each file
        for file_path in metadata_files:
            with open(file_path, 'r', newline='') as infile:
                reader = csv.reader(infile)
                next(reader)  # Skip header
                for row in reader:
                    writer.writerow(row)
    
    print(f"Merged metadata saved to {merged_file}")

if __name__ == "__main__":
    main()
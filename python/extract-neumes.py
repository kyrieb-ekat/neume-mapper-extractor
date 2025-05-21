#!/usr/bin/env python3
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
import concurrent.futures
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Volumes/Expansion/extracted_neumes/extraction_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def streaming_json_parse(file_path):
    """
    Efficiently parse a potentially large JSON file with irregular formatting.
    Adapts the parsing approach from the formatting script.
    """
    logger.info(f"Attempting to parse large JSON file: {file_path}")
    
    # Second attempt: Use line-by-line regex-based parsing
    logger.info("Using regex-based parsing...")
    
    try:
        # For very large files, extract information line by line
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
                    logger.info(f"Found neume type on line {line_num}: {current_type}")
                
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
            logger.info(f"Extracted {neume_type}: {len(urls)} URLs")
            result.append({
                "type": neume_type,
                "urls": urls
            })
        
        if result:
            return result
        
    except Exception as e:
        logger.error(f"Error during regex parsing: {str(e)}")
        traceback.print_exc()
    
    # Last attempt: Basic URL extraction
    logger.info("Attempting basic URL extraction...")
    
    try:
        type_url_map = {}
        current_type = None
        
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Find all type definitions
            type_matches = re.finditer(r'"type":\s*"([^"]+)"', content)
            for match in type_matches:
                type_name = match.group(1)
                start_pos = match.end()
                
                # Find URL list
                urls_start = content.find('"urls":', start_pos)
                if urls_start > -1:
                    urls_start = content.find('[', urls_start)
                    if urls_start > -1:
                        # Find where the URL list ends
                        bracket_count = 1
                        urls_end = urls_start + 1
                        while bracket_count > 0 and urls_end < len(content):
                            if content[urls_end] == '[':
                                bracket_count += 1
                            elif content[urls_end] == ']':
                                bracket_count -= 1
                            urls_end += 1
                        
                        # Extract URLs
                        urls_section = content[urls_start:urls_end]
                        urls = re.findall(r'"(http[^"]+)"', urls_section)
                        
                        if urls:
                            type_url_map[type_name] = urls
                            logger.info(f"Found {len(urls)} URLs for type {type_name}")
        
        # Convert to the expected format
        result = []
        for neume_type, urls in type_url_map.items():
            result.append({
                "type": neume_type,
                "urls": urls
            })
        
        if result:
            return result
            
    except Exception as e:
        logger.error(f"Error during detailed parsing: {str(e)}")
        traceback.print_exc()
        
    # If all else fails, try just extracting all URLs
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            all_urls = re.findall(r'"(http[^"]+)"', content)
            
            if all_urls:
                logger.info(f"Found {len(all_urls)} URLs with basic extraction")
                return [{
                    "type": "Unknown",
                    "urls": all_urls
                }]
    
    except Exception as e:
        logger.error(f"Error during basic URL extraction: {str(e)}")
    
    return None

def extract_neume_images():
    # 1. Load the annotations JSON file
    #with open(annotations.json', 'r') as f: # was annotations.json, original is 'real-annotations.json', testing with 'real-annotationsZ.json'
    json_file_path = '/Users/kyriebouressa/Documents/neume-mapper-extractor/public/large-scale-test-2.json' # large-scale-test-2 is a 1,000+ image test
    
    # Parse the file using the advanced streaming parser
    annotations = streaming_json_parse(json_file_path)
    
    if not annotations:
        logger.error("Failed to parse JSON file")
        return
    
    logger.info(f"Successfully parsed {len(annotations)} neume types")
    
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
        'Referer': 'http://www.e-codices.unifr.ch/',
    }
    
    # Process each annotation
    for annotation in annotations:
        neume_type = annotation['type']
        urls = annotation['urls']
        logger.info(f"Processing {neume_type} ({len(urls)} images)")
        
        # Create directory for this neume type
        # Original path (commented out)
        # neume_dir = os.path.join(output_dir, neume_type.replace(' ', '_'))
        
        # New path on external drive
        neume_dir = os.path.join(output_dir, neume_type.replace(' ', '_'))
        os.makedirs(neume_dir, exist_ok=True)
        
        # Process URLs in batches with parallel processing
        process_urls_in_batches(urls, neume_type, neume_dir, headers)
    
    logger.info("Extraction complete!")
    
def process_urls_in_batches(urls, neume_type, neume_dir, headers, batch_size=20):
    """Process URLs in batches for better memory management"""
    total_urls = len(urls)
    logger.info(f"Processing {total_urls} URLs for {neume_type} in batches of {batch_size}")
    
    successful = 0
    failed = 0
    skipped = 0
    
    for i in range(0, total_urls, batch_size):
        batch_urls = urls[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (total_urls+batch_size-1)//batch_size
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_urls)} URLs)")
        
        # Create a new session for each batch to avoid resource issues
        session = requests.Session()
        
        # Process batch using ThreadPoolExecutor for parallel downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Create a list of futures
            future_to_url = {
                executor.submit(
                    process_url, 
                    url, 
                    i+idx, 
                    neume_type, 
                    total_urls, 
                    neume_dir, 
                    session, 
                    headers
                ): url for idx, url in enumerate(batch_urls)
            }
            
            # Process completed futures as they complete
            batch_successful = 0
            batch_failed = 0
            batch_skipped = 0
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result == 'success':
                        batch_successful += 1
                        successful += 1
                    elif result == 'skipped':
                        batch_skipped += 1
                        skipped += 1
                    else:
                        batch_failed += 1
                        failed += 1
                except Exception as exc:
                    logger.error(f"URL {url} generated an exception: {exc}")
                    batch_failed += 1
                    failed += 1
            
            logger.info(f"Batch {batch_num} completed: {batch_successful} successful, {batch_skipped} skipped, {batch_failed} failed")
        
        # Add a delay between batches to avoid overwhelming the server
        if batch_num < total_batches:
            delay = min(3.0, (batch_failed / max(1, len(batch_urls))) * 10.0)  # Adaptive delay based on failure rate
            logger.info(f"Pausing for {delay:.1f}s before next batch...")
            time.sleep(delay)
    
    logger.info(f"Completed all batches for {neume_type}: {successful} successful, {skipped} skipped, {failed} failed")
    
def process_url(url, i, neume_type, total_urls, neume_dir, session, headers):
    """Process a single URL and save the image"""
    try:
        # Extract page identifier from URL
        url_parts = url.split('/')
        page_id = url_parts[6] if len(url_parts) > 6 else f"page_{i}"
        
        # Create output path
        # Original path (commented out)
        # output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
        
        # New path on external drive
        output_path = os.path.join(neume_dir, f"{page_id}_{i}.jpg")
        
        # Skip if file already exists
        if os.path.exists(output_path):
            logger.debug(f"File already exists, skipping: {output_path}")
            return 'skipped'
        
        # Download the image directly from the URL
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Add a small random delay to avoid thundering herd
                time.sleep(0.1 * (retry + 1))
                
                response = session.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    break
                    
                # If we get rate limited or server error, back off more aggressively
                if response.status_code in (429, 500, 502, 503, 504):
                    delay = (retry + 1) * 2
                    logger.warning(f"Got status {response.status_code}, retrying in {delay}s...")
                    time.sleep(delay)
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if retry < max_retries - 1:
                    delay = (retry + 1) * 2  # Exponential backoff
                    logger.warning(f"Retry {retry+1}/{max_retries} after {delay}s due to: {str(e)}")
                    time.sleep(delay)
                else:
                    raise
        
        if response.status_code != 200:
            logger.error(f"Failed to download {url}: {response.status_code}")
            return None
        
        # Open the downloaded image
        img = Image.open(BytesIO(response.content))
        
        # Save the image directly
        img.save(output_path)
        logger.info(f"Saved {os.path.basename(output_path)}")
        
        return 'success'
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        return None

if __name__ == "__main__":
    extract_neume_images()
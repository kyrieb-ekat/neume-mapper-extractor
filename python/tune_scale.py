#!/usr/bin/env python3
"""
Script to help fine-tune the scale factor and other parameters.
This script creates multiple overlays with different settings.
"""

import os
import subprocess
import argparse
from pathlib import Path
import time

def main():
    parser = argparse.ArgumentParser(description='Scale and parameter tuner')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--image', default='../public/reference_images/SG_390-007.jpg',
                       help='Path to the reference image')
    parser.add_argument('--output-dir', default='../public/reference_images',
                       help='Directory for output images')
    parser.add_argument('--base-scale', type=float, default=None,
                       help='Base scale factor (default: auto)')
    parser.add_argument('--adjustments', type=str, default="0.9,1.0,1.1,1.2,1.3",
                       help='Comma-separated list of scale adjustments to try (default: 0.9,1.0,1.1,1.2,1.3)')
    parser.add_argument('--line-width', type=int, default=10,
                       help='Width of bounding box lines (default: 10)')
    parser.add_argument('--box-padding', type=int, default=5,
                       help='Padding around bounding boxes (default: 5)')
    parser.add_argument('--corner-size', type=int, default=20,
                       help='Size of corner indicators (default: 20)')
    parser.add_argument('--color', default='red',
                       help='Color of bounding boxes (default: red)')
    
    args = parser.parse_args()
    
    # Parse the scale adjustments
    try:
        adjustments = [float(x) for x in args.adjustments.split(',')]
    except ValueError:
        print(f"Error: Invalid scale adjustments format. Using default values.")
        adjustments = [0.9, 1.0, 1.1, 1.2, 1.3]
    
    print(f"=== Scale and Parameter Tuner ===")
    print(f"Testing {len(adjustments)} different scale adjustments: {adjustments}")
    print(f"Line width: {args.line_width}")
    print(f"Box padding: {args.box_padding}")
    print(f"Corner size: {args.corner_size}")
    print(f"Color: {args.color}")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Base scale parameter
    scale_param = f"--scale {args.base_scale}" if args.base_scale is not None else ""
    
    # Generate overlays with different scale adjustments
    results = {}
    
    for adjustment in adjustments:
        timestamp = int(time.time())
        output_filename = f"overlay_adjust_{adjustment:.2f}_{timestamp}.jpg"
        output_path = os.path.join(args.output_dir, output_filename)
        web_output_path = output_path.replace('.jpg', '_web.jpg')
        
        print(f"\nGenerating overlay with scale adjustment {adjustment:.2f}")
        command = [
            'python', 'enhanced_overlay.py',
            '--annotations', args.annotations,
            '--image', args.image,
            '--output', output_path,
            '--web-output', web_output_path,
            '--line-width', str(args.line_width),
            '--box-padding', str(args.box_padding),
            '--corner-size', str(args.corner_size),
            '--line-color', args.color,
            '--scale-adjust', str(adjustment),
            '--debug-coords'
        ]
        
        if args.base_scale is not None:
            command.extend(['--scale', str(args.base_scale)])
        
        try:
            start_time = time.time()
            process = subprocess.run(command, check=True, capture_output=True, text=True)
            end_time = time.time()
            
            # Extract scale factor from output
            scale_line = None
            for line in process.stdout.split('\n'):
                if "Adjusted scale factor:" in line:
                    scale_line = line
                    break
            
            results[adjustment] = {
                'output': output_filename,
                'web_output': os.path.basename(web_output_path),
                'time': end_time - start_time,
                'scale_info': scale_line,
                'success': True
            }
            
            print(f"Generated {output_path}")
            print(f"Web version: {web_output_path}")
            print(f"Time taken: {end_time - start_time:.2f} seconds")
            if scale_line:
                print(scale_line)
            
        except Exception as e:
            print(f"Error generating overlay with adjustment {adjustment}: {e}")
            results[adjustment] = {
                'success': False,
                'error': str(e)
            }
    
    # Create an HTML file to view all the overlays
    html_path = os.path.join(args.output_dir, "adjustment_comparison.html")
    
    with open(html_path, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Scale Adjustment Comparison</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        .image-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .adjustment-container {{ margin-bottom: 30px; border: 1px solid #ccc; padding: 20px; border-radius: 5px; }}
        .image-card {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; }}
        img {{ max-width: 100%; border: 1px solid #eee; }}
        .settings {{ background-color: #f5f5f5; padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>Scale Adjustment Comparison</h1>
    <div class="settings">
        <h3>Settings:</h3>
        <ul>
            <li><strong>Base Scale:</strong> {args.base_scale if args.base_scale is not None else "Auto"}</li>
            <li><strong>Line Width:</strong> {args.line_width}</li>
            <li><strong>Box Padding:</strong> {args.box_padding}</li>
            <li><strong>Corner Size:</strong> {args.corner_size}</li>
            <li><strong>Color:</strong> {args.color}</li>
        </ul>
    </div>
    
    <h2>Web-Friendly Versions</h2>
    <div class="image-grid">
""")
        
        # Add web-friendly versions first
        for adjustment, result in sorted(results.items()):
            if result['success']:
                f.write(f"""
        <div class="image-card">
            <h3>Adjustment: {adjustment:.2f}</h3>
            <p>{result.get('scale_info', '')}</p>
            <img src="{result['web_output']}" alt="Adjustment {adjustment:.2f}">
            <p><a href="{result['web_output']}" target="_blank">View Full Size</a></p>
        </div>
""")
        
        f.write("""
    </div>
    
    <h2>Full-Size Versions</h2>
    <div class="image-grid">
""")
        
        # Add full-size versions
        for adjustment, result in sorted(results.items()):
            if result['success']:
                f.write(f"""
        <div class="image-card">
            <h3>Adjustment: {adjustment:.2f}</h3>
            <p>{result.get('scale_info', '')}</p>
            <img src="{result['output']}" alt="Adjustment {adjustment:.2f}">
            <p><a href="{result['output']}" target="_blank">View Full Size</a></p>
        </div>
""")
            else:
                f.write(f"""
        <div class="image-card">
            <h3>Adjustment: {adjustment:.2f}</h3>
            <p class="error">Error: {result.get('error', 'Unknown error')}</p>
        </div>
""")
        
        f.write("""
    </div>
</body>
</html>
""")
    
    print(f"\nCreated comparison HTML file: {html_path}")
    print(f"Open this file in your browser to compare different scale adjustments")
    print(f"Once you find the best settings, use them with enhanced_overlay.py")
    
    return 0

if __name__ == "__main__":
    main()
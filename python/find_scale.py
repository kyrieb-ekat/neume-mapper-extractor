#!/usr/bin/env python3
"""
Script to help find the right scaling factor for your reference image.
This script creates multiple overlay images with different scaling factors.
"""

import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Find the right scaling factor')
    parser.add_argument('--annotations', default='../public/real-annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--image', default='../public/reference_images/SG_390-007.jpg',
                       help='Path to the reference image')
    parser.add_argument('--output-dir', default='../public/reference_images',
                       help='Directory for output images')
    parser.add_argument('--min-scale', type=float, default=0.05,
                       help='Minimum scale factor (default: 0.05)')
    parser.add_argument('--max-scale', type=float, default=0.5,
                       help='Maximum scale factor (default: 0.5)')
    parser.add_argument('--steps', type=int, default=5,
                       help='Number of scale steps to try (default: 5)')
    
    args = parser.parse_args()
    
    print(f"=== Scale Factor Finder ===")
    print(f"Testing {args.steps} different scale factors from {args.min_scale} to {args.max_scale}")
    
    # Calculate scale steps
    scale_step = (args.max_scale - args.min_scale) / (args.steps - 1) if args.steps > 1 else 0
    scales = [args.min_scale + i * scale_step for i in range(args.steps)]
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate overlays with different scales
    for scale in scales:
        output_filename = f"overlay_scale_{scale:.3f}.jpg"
        output_path = os.path.join(args.output_dir, output_filename)
        
        print(f"\nGenerating overlay with scale factor {scale:.3f}")
        command = [
            'python', 'fixed_overlay.py',
            '--annotations', args.annotations,
            '--image', args.image,
            '--output', output_path,
            '--scale', str(scale),
            '--debug-grid'
        ]
        
        try:
            subprocess.run(command, check=True)
            print(f"Generated {output_path}")
        except Exception as e:
            print(f"Error generating overlay with scale {scale}: {e}")
    
    # Create an HTML file to view all the overlays
    html_path = os.path.join(args.output_dir, "scale_comparison.html")
    
    with open(html_path, 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Scale Factor Comparison</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .scale-container { margin-bottom: 30px; border: 1px solid #ccc; padding: 20px; border-radius: 5px; }
        img { max-width: 100%; border: 1px solid #eee; }
    </style>
</head>
<body>
    <h1>Scale Factor Comparison</h1>
    <p>Compare different scale factors to find the best one for your image.</p>
""")
        
        for scale in scales:
            output_filename = f"overlay_scale_{scale:.3f}.jpg"
            
            f.write(f"""
    <div class="scale-container">
        <h2>Scale Factor: {scale:.3f}</h2>
        <img src="{output_filename}" alt="Scale {scale:.3f}">
    </div>
""")
        
        f.write("""
</body>
</html>
""")
    
    print(f"\nCreated comparison HTML file: {html_path}")
    print(f"Open this file in your browser to compare different scale factors")
    print(f"Then use the best scale factor with fixed_overlay.py")
    
    return 0

if __name__ == "__main__":
    main()
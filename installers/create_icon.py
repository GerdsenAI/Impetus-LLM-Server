#!/usr/bin/env python3
"""
App Icon Generator for Impetus LLM Server
Creates a professional brain/AI-themed icon in multiple resolutions
"""

from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
from pathlib import Path

def create_brain_icon(size):
    """Create a brain/AI themed icon"""
    
    # Create base image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate proportions
    margin = size // 10
    brain_size = size - (2 * margin)
    center = size // 2
    
    # Color scheme - modern tech gradient
    bg_color = (45, 55, 72, 255)  # Dark blue-gray
    primary_color = (99, 102, 241, 255)  # Purple
    accent_color = (139, 69, 255, 255)  # Bright purple
    highlight_color = (255, 255, 255, 180)  # Semi-transparent white
    
    # Create circular background
    circle_margin = margin // 2
    draw.ellipse([circle_margin, circle_margin, size - circle_margin, size - circle_margin], 
                fill=bg_color)
    
    # Draw stylized brain outline
    brain_margin = margin
    brain_left = brain_margin
    brain_top = brain_margin
    brain_right = size - brain_margin
    brain_bottom = size - brain_margin
    
    # Main brain shape (rounded rectangle)
    draw.rounded_rectangle([brain_left, brain_top, brain_right, brain_bottom], 
                          radius=brain_size//4, fill=primary_color)
    
    # Brain hemispheres divider
    mid_x = center
    divider_width = max(2, size // 64)
    draw.rectangle([mid_x - divider_width//2, brain_top + brain_size//6, 
                   mid_x + divider_width//2, brain_bottom - brain_size//6], 
                  fill=bg_color)
    
    # Brain folds/wrinkles (simplified neural network pattern)
    fold_thickness = max(1, size // 96)
    
    # Left hemisphere folds
    for i in range(3):
        y_offset = brain_size // 6 + (i * brain_size // 8)
        x_start = brain_left + brain_size // 8
        x_end = mid_x - brain_size // 16
        
        draw.arc([x_start, brain_top + y_offset, x_end, brain_top + y_offset + brain_size//6], 
                start=0, end=180, fill=accent_color, width=fold_thickness)
    
    # Right hemisphere folds
    for i in range(3):
        y_offset = brain_size // 6 + (i * brain_size // 8)
        x_start = mid_x + brain_size // 16
        x_end = brain_right - brain_size // 8
        
        draw.arc([x_start, brain_top + y_offset, x_end, brain_top + y_offset + brain_size//6], 
                start=0, end=180, fill=accent_color, width=fold_thickness)
    
    # Neural connection dots
    dot_size = max(2, size // 48)
    for i in range(5):
        for j in range(3):
            if i == 2 and j == 1:  # Skip center dot
                continue
            dot_x = brain_left + (i + 1) * brain_size // 6
            dot_y = brain_top + (j + 1) * brain_size // 4
            draw.ellipse([dot_x - dot_size, dot_y - dot_size, 
                         dot_x + dot_size, dot_y + dot_size], 
                        fill=highlight_color)
    
    # Highlight/shine effect
    highlight_size = brain_size // 3
    highlight_x = center - highlight_size // 2
    highlight_y = brain_top + brain_size // 6
    
    # Create gradient highlight
    for i in range(highlight_size // 4):
        alpha = int(60 * (1 - i / (highlight_size // 4)))
        color = (*highlight_color[:3], alpha)
        draw.ellipse([highlight_x + i, highlight_y + i, 
                     highlight_x + highlight_size - i, highlight_y + highlight_size - i], 
                    fill=color)
    
    return img

def create_iconset(output_dir):
    """Create complete iconset with all required sizes"""
    
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    iconset_dir = output_dir / "AppIcon.iconset"
    iconset_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎨 Creating app icon in multiple resolutions...")
    
    for size in sizes:
        print(f"  Creating {size}x{size} icon...")
        
        # Create standard resolution
        icon = create_brain_icon(size)
        icon.save(iconset_dir / f"icon_{size}x{size}.png")
        
        # Create @2x resolution for retina displays
        if size <= 512:  # Don't create @2x for 1024 (would be 2048)
            retina_size = size * 2
            retina_icon = create_brain_icon(retina_size)
            retina_icon.save(iconset_dir / f"icon_{size}x{size}@2x.png")
    
    return iconset_dir

def convert_to_icns(iconset_dir, output_path):
    """Convert iconset to .icns file using iconutil"""
    
    print("🔧 Converting to .icns format...")
    
    cmd = ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_path)]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Created app icon: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create .icns file: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ iconutil not found. This script must be run on macOS.")
        return False

def main():
    """Main icon creation function"""
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    assets_dir = script_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    print("🧠 Impetus App Icon Generator")
    print("=" * 40)
    
    # Create iconset
    iconset_dir = create_iconset(assets_dir)
    
    # Convert to .icns
    icns_path = assets_dir / "AppIcon.icns"
    success = convert_to_icns(iconset_dir, icns_path)
    
    if success:
        print("\n🎉 App icon created successfully!")
        print(f"📁 Location: {icns_path}")
        
        # Clean up iconset directory
        import shutil
        shutil.rmtree(iconset_dir)
        print("🧹 Cleaned up temporary files")
    else:
        print("\n❌ Failed to create app icon")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
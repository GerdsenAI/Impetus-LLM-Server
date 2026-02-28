#!/usr/bin/env python3
"""
DMG Background Image Generator for Impetus LLM Server
Creates a professional branded background for the DMG installer
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from pathlib import Path

def create_gradient_background(width, height):
    """Create a subtle gradient background"""
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Create subtle gradient from light blue to white
    for y in range(height):
        # Gradient from light blue at top to white at bottom
        ratio = y / height
        
        # Top color: light blue-gray
        r1, g1, b1 = 248, 250, 252
        # Bottom color: very light blue
        r2, g2, b2 = 241, 245, 249
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img

def add_branding(img, width, height):
    """Add Impetus branding to the background"""
    draw = ImageDraw.Draw(img)
    
    # Try to load a system font, fallback to default
    try:
        # Try different font paths
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ]
        
        title_font = None
        subtitle_font = None
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    title_font = ImageFont.truetype(font_path, 36)
                    subtitle_font = ImageFont.truetype(font_path, 18)
                    break
                except:
                    continue
        
        if not title_font:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Title text
    title_text = "Impetus LLM Server"
    title_color = (30, 41, 59)  # Dark blue-gray
    
    # Get text dimensions
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    
    # Position title at top center
    title_x = (width - title_width) // 2
    title_y = 40
    
    # Draw title with shadow effect
    shadow_offset = 2
    draw.text((title_x + shadow_offset, title_y + shadow_offset), title_text, 
              fill=(0, 0, 0, 30), font=title_font)
    draw.text((title_x, title_y), title_text, fill=title_color, font=title_font)
    
    # Subtitle
    subtitle_text = "High-Performance Local AI Server for Apple Silicon"
    subtitle_color = (71, 85, 105)  # Medium gray
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + title_height + 10
    
    draw.text((subtitle_x, subtitle_y), subtitle_text, fill=subtitle_color, font=subtitle_font)
    
    return img

def add_installation_instructions(img, width, height):
    """Add installation instructions with arrow"""
    draw = ImageDraw.Draw(img)
    
    # Try to load font
    try:
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf"
        ]
        
        instruction_font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    instruction_font = ImageFont.truetype(font_path, 16)
                    break
                except:
                    continue
        
        if not instruction_font:
            instruction_font = ImageFont.load_default()
    except:
        instruction_font = ImageFont.load_default()
    
    # Instruction text
    instruction_text = "Drag Impetus to Applications to install"
    instruction_color = (55, 65, 81)  # Dark gray
    
    # Position at bottom center
    instruction_bbox = draw.textbbox((0, 0), instruction_text, font=instruction_font)
    instruction_width = instruction_bbox[2] - instruction_bbox[0]
    
    instruction_x = (width - instruction_width) // 2
    instruction_y = height - 80
    
    draw.text((instruction_x, instruction_y), instruction_text, 
              fill=instruction_color, font=instruction_font)
    
    # Draw arrow from left to right (app icon to Applications folder)
    arrow_y = height // 2 + 20
    arrow_start_x = width // 2 - 80
    arrow_end_x = width // 2 + 80
    arrow_color = (99, 102, 241)  # Purple accent color
    
    # Arrow shaft
    draw.line([(arrow_start_x, arrow_y), (arrow_end_x - 15, arrow_y)], 
              fill=arrow_color, width=3)
    
    # Arrow head
    arrow_head_size = 10
    arrow_points = [
        (arrow_end_x, arrow_y),
        (arrow_end_x - arrow_head_size, arrow_y - arrow_head_size//2),
        (arrow_end_x - arrow_head_size, arrow_y + arrow_head_size//2)
    ]
    draw.polygon(arrow_points, fill=arrow_color)
    
    return img

def add_decorative_elements(img, width, height):
    """Add subtle decorative elements"""
    draw = ImageDraw.Draw(img)
    
    # Add subtle circuit pattern in corners
    accent_color = (99, 102, 241, 40)  # Semi-transparent purple
    
    # Top left corner decoration
    for i in range(3):
        x = 20 + i * 15
        y = 20 + i * 15
        draw.rectangle([x, y, x + 8, y + 2], fill=accent_color)
        draw.rectangle([x, y, x + 2, y + 8], fill=accent_color)
    
    # Bottom right corner decoration
    for i in range(3):
        x = width - 40 - i * 15
        y = height - 40 - i * 15
        draw.rectangle([x, y, x + 8, y + 2], fill=accent_color)
        draw.rectangle([x + 6, y, x + 8, y + 8], fill=accent_color)
    
    return img

def create_dmg_background():
    """Create the complete DMG background image"""
    
    # DMG window dimensions
    width = 600
    height = 400
    
    print("🎨 Creating DMG background image...")
    
    # Create base gradient
    img = create_gradient_background(width, height)
    
    # Add branding
    img = add_branding(img, width, height)
    
    # Add installation instructions
    img = add_installation_instructions(img, width, height)
    
    # Add decorative elements
    img = add_decorative_elements(img, width, height)
    
    return img

def main():
    """Main background creation function"""
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    assets_dir = script_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    print("🖼️  Impetus DMG Background Generator")
    print("=" * 40)
    
    # Create background image
    background = create_dmg_background()
    
    # Save the image
    output_path = assets_dir / "dmg-background.png"
    background.save(output_path, "PNG", optimize=True)
    
    print(f"✅ DMG background created: {output_path}")
    print(f"📐 Dimensions: {background.width}x{background.height} pixels")
    
    # Also create a @2x version for retina displays
    retina_background = background.resize((1200, 800), Image.Resampling.LANCZOS)
    retina_path = assets_dir / "dmg-background@2x.png"
    retina_background.save(retina_path, "PNG", optimize=True)
    
    print(f"✅ Retina background created: {retina_path}")
    
    return 0

if __name__ == "__main__":
    exit(main())
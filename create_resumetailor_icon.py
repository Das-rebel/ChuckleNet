#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFont
import sys

def create_app_icon():
    # Create a 1024x1024 icon
    size = 1024
    img = Image.new('RGB', (size, size), '#667eea')
    draw = ImageDraw.Draw(img)
    
    # Create gradient background
    for y in range(size):
        # Gradient from #667eea to #764ba2
        r = int(0x66 + (0x76 - 0x66) * y / size)
        g = int(0x7e + (0x4b - 0x7e) * y / size)
        b = int(0xea + (0xa2 - 0xea) * y / size)
        color = (r, g, b)
        draw.line([(0, y), (size, y)], fill=color)
    
    # Add rounded corners
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = size // 6
    mask_draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    
    # Apply mask
    img.putalpha(mask)
    
    # Add document icon
    doc_size = size // 2
    doc_x = (size - doc_size) // 2
    doc_y = (size - doc_size) // 2
    
    # Document background
    draw.rounded_rectangle([doc_x, doc_y, doc_x + doc_size, doc_y + doc_size], 
                          radius=size//20, fill='white', outline=None)
    
    # Add text lines
    line_height = doc_size // 12
    line_width = doc_size * 0.7
    line_x = doc_x + doc_size * 0.15
    
    for i in range(8):
        y = doc_y + doc_size * 0.2 + i * line_height * 1.3
        width = line_width if i < 7 else line_width * 0.6
        draw.rounded_rectangle([line_x, y, line_x + width, y + line_height//2], 
                              radius=2, fill='#667eea')
    
    # Add AI sparkle icon
    sparkle_size = size // 8
    sparkle_x = doc_x + doc_size - sparkle_size
    sparkle_y = doc_y
    
    # Simple star shape for AI indicator
    points = []
    for i in range(10):
        angle = i * 36 * 3.14159 / 180
        radius = sparkle_size//2 if i % 2 == 0 else sparkle_size//4
        x = sparkle_x + sparkle_size//2 + radius * cos(angle)
        y = sparkle_y + sparkle_size//2 + radius * sin(angle)
        points.append((x, y))
    
    try:
        draw.polygon(points, fill='#FFD700', outline='#FFA500')
    except:
        # Fallback: simple circle
        draw.ellipse([sparkle_x, sparkle_y, sparkle_x + sparkle_size, sparkle_y + sparkle_size], 
                    fill='#FFD700', outline='#FFA500')
    
    return img

def cos(angle):
    import math
    return math.cos(angle)

def sin(angle):
    import math
    return math.sin(angle)

# Create all required icon sizes
icon_sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

try:
    base_icon = create_app_icon()
    iconset_path = "/Users/Subho/Applications/ResumeTailor.app/Contents/Resources/AppIcon.iconset"
    
    for size, filename in icon_sizes:
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_path, filename))
    
    print("✅ Icon files created successfully")
    
except ImportError:
    print("⚠️ PIL/Pillow not available, creating simple text-based icon")
    # Create a simple 512x512 PNG with system tools
    pass

except Exception as e:
    print(f"⚠️ Icon creation error: {e}")
    print("App will work without custom icon")
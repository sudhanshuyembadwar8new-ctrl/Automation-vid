"""
🖼️ Visual Generator — Pollinations.ai (100% FREE)
Generates AI images for video backgrounds and YouTube thumbnails.
No API key required. No payment. No limits.
"""

import os
import json
import requests
import urllib.parse
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))

# Pollinations.ai — 100% free AI image generation
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"


# ════════════════════════════════════════════
# Image Style Presets
# ════════════════════════════════════════════

VISUAL_STYLES = {
    "tech_dark": {
        "suffix": ", dark futuristic background, neon blue and purple accents, cyberpunk tech aesthetic, cinematic lighting, 4K, ultra detailed, professional",
    },
    "gradient_abstract": {
        "suffix": ", abstract gradient background, vibrant colors, modern minimal design, clean professional, 4K, no text",
    },
    "screen_mockup": {
        "suffix": ", laptop screen showing code and AI interface, dark room, programmer aesthetic, moody lighting, realistic, 4K",
    },
    "money_success": {
        "suffix": ", concept of financial success and digital income, green and gold tones, futuristic, motivational, 4K",
    },
    "ai_concept": {
        "suffix": ", artificial intelligence neural network visualization, glowing connections, dark background, sci-fi aesthetic, 4K",
    },
    "workspace": {
        "suffix": ", modern tech workspace with multiple monitors, dark theme, ambient lighting, productivity setup, 4K",
    },
    "data_viz": {
        "suffix": ", data visualization dashboard, charts and graphs, dark UI, blue and cyan accents, professional analytics, 4K",
    }
}

THUMBNAIL_STYLES = {
    "dark_neon": {
        "suffix": ", youtube thumbnail style background, dark background, neon glowing effects, dramatic lighting, high contrast, bold eye-catching, 4K",
    },
    "gradient_bold": {
        "suffix": ", youtube thumbnail background, vibrant gradient, bold layout, professional, high contrast, clean, 4K",
    },
    "tech_glow": {
        "suffix": ", tech youtube thumbnail background, glowing blue accents, futuristic, dark theme, premium look, 4K",
    }
}


def generate_image(prompt, width=1920, height=1080, style="tech_dark", output_filename=None):
    """
    Generate an image using Pollinations.ai (FREE, no API key).
    
    Args:
        prompt: Image description
        width: Width in pixels
        height: Height in pixels
        style: Style preset name
        output_filename: Custom filename
    
    Returns:
        Path to saved image
    """
    style_config = VISUAL_STYLES.get(style, VISUAL_STYLES["tech_dark"])
    full_prompt = prompt + style_config["suffix"]
    
    # Add random seed for variety
    seed = random.randint(1, 999999)
    encoded_prompt = urllib.parse.quote(full_prompt)
    url = f"{POLLINATIONS_URL}/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}"
    
    print(f"🖼️ Generating: {prompt[:60]}...")
    
    response = requests.get(url, timeout=180, stream=True)
    
    if response.status_code != 200:
        raise Exception(f"❌ Image generation failed: HTTP {response.status_code}")
    
    # Save
    output_dir = OUTPUT_DIR / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"visual_{timestamp}_{seed}.jpg"
    
    output_path = output_dir / output_filename
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    file_size = os.path.getsize(output_path) / 1024
    print(f"✅ Saved: {output_path} ({file_size:.0f} KB)")
    return str(output_path)


def generate_thumbnail(thumbnail_text, topic_keyword="AI tool", style="dark_neon", output_filename=None):
    """
    Generate YouTube thumbnail background + add text overlay.
    """
    style_config = THUMBNAIL_STYLES.get(style, THUMBNAIL_STYLES["dark_neon"])
    prompt = f"youtube thumbnail background for {topic_keyword}, space for bold text, energetic feel" + style_config["suffix"]
    
    seed = random.randint(1, 999999)
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_URL}/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
    
    print(f"🖼️ Generating thumbnail for: {thumbnail_text}")
    
    response = requests.get(url, timeout=180, stream=True)
    
    if response.status_code != 200:
        raise Exception(f"❌ Thumbnail generation failed: HTTP {response.status_code}")
    
    # Save
    output_dir = OUTPUT_DIR / "thumbnails"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"thumb_{timestamp}.jpg"
    
    output_path = output_dir / output_filename
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Add text overlay
    try:
        _add_text_overlay(str(output_path), thumbnail_text)
        print(f"✅ Thumbnail with text: {output_path}")
    except Exception as e:
        print(f"⚠️ Text overlay skipped: {e}")
    
    return str(output_path)


def _add_text_overlay(image_path, text, font_size=80):
    """Add bold text overlay with shadow effect to thumbnail."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("⚠️ pip install Pillow — for thumbnail text overlay")
        return
    
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Try to find a bold font
    font = None
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except (OSError, IOError):
            continue
    
    if not font:
        font = ImageFont.load_default()
    
    text_upper = text.upper()
    bbox = draw.textbbox((0, 0), text_upper, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (img.width - text_w) // 2
    y = (img.height - text_h) // 2 + 60
    
    # Draw shadow/outline
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            draw.text((x + dx, y + dy), text_upper, font=font, fill="black")
    
    # Main text in bright neon green
    draw.text((x, y), text_upper, font=font, fill="#00FF88")
    
    img.save(image_path, quality=95)


def generate_video_visuals(script_data, video_type="short"):
    """
    Generate all visuals needed for a video.
    
    Returns:
        dict with "images" list and "thumbnail" path
    """
    print(f"🎨 Generating visuals for {video_type} video...")
    
    results = {"images": [], "thumbnail": None}
    
    # Generate thumbnail
    thumbnail_text = script_data.get("thumbnail_text", "AI TOOL")
    topic = script_data.get("topic_category", "AI tools")
    
    try:
        thumb_path = generate_thumbnail(thumbnail_text, topic)
        results["thumbnail"] = thumb_path
    except Exception as e:
        print(f"⚠️ Thumbnail failed: {e}")
    
    # Number of background images
    num_images = 3 if video_type == "short" else 8
    
    title = script_data.get("title", "AI tool tutorial")
    styles = list(VISUAL_STYLES.keys())
    
    # Generate prompts from script content
    base_prompts = [
        f"visualization of {title}",
        f"futuristic AI technology concept for {topic}",
        f"digital automation and artificial intelligence",
        f"modern tech workspace with AI tools",
        f"data visualization and machine learning",
        f"concept of earning money online with technology",
        f"programming and software development dark theme",
        f"AI assistant robot helping with digital tasks",
        f"neural network and deep learning visualization",
        f"cloud computing and API connections diagram"
    ]
    
    # Resolution based on video type
    if video_type == "short":
        width, height = 1080, 1920  # 9:16 vertical
    else:
        width, height = 1920, 1080  # 16:9 horizontal
    
    for i in range(num_images):
        prompt = base_prompts[i % len(base_prompts)]
        style = styles[i % len(styles)]
        
        try:
            img_path = generate_image(
                prompt=prompt, width=width, height=height, style=style
            )
            results["images"].append(img_path)
        except Exception as e:
            print(f"  ❌ Image {i+1}/{num_images} failed: {e}")
    
    print(f"\n🎉 Generated {len(results['images'])} images + {'thumbnail' if results['thumbnail'] else 'no thumbnail'}")
    return results


# ════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🖼️ Generate visuals with Pollinations.ai (FREE)")
    parser.add_argument("--mode", choices=["image", "thumbnail", "full"], default="image")
    parser.add_argument("--prompt", type=str, default="futuristic AI technology concept")
    parser.add_argument("--text", type=str, default="FREE AI TOOL")
    parser.add_argument("--style", type=str, default="tech_dark")
    parser.add_argument("--type", choices=["short", "long"], default="short")
    parser.add_argument("--script", type=str, help="Script JSON path for full generation")
    
    args = parser.parse_args()
    
    if args.mode == "image":
        generate_image(prompt=args.prompt, style=args.style)
    elif args.mode == "thumbnail":
        generate_thumbnail(thumbnail_text=args.text)
    elif args.mode == "full" and args.script:
        with open(args.script, "r", encoding="utf-8") as f:
            script_data = json.load(f)
        generate_video_visuals(script_data, video_type=args.type)

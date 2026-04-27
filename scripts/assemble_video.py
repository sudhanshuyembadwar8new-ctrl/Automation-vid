"""
🎬 Video Assembler — FFmpeg Pipeline
Combines voice audio + AI images + background music → final YouTube-ready video.
Supports 16:9 (long form) and 9:16 (shorts/reels).
Features: Ken Burns zoom, crossfade transitions, audio mixing, subtitle burning.
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
MUSIC_DIR = Path(__file__).parent.parent / "templates" / "music"


def check_ffmpeg():
    """Verify FFmpeg is installed."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg: {version[:60]}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    raise EnvironmentError(
        "❌ FFmpeg not found!\n"
        "   Install: winget install FFmpeg\n"
        "   Or download: https://ffmpeg.org/download.html"
    )


def get_audio_duration(audio_path):
    """Get audio duration in seconds."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        audio_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except Exception:
        return 60.0


def create_slideshow_video(image_paths, audio_path, output_path=None, 
                           video_type="short", add_zoom=True, add_music=True):
    """
    Create video from images + audio with Ken Burns zoom effect.
    
    Args:
        image_paths: List of image file paths
        audio_path: Path to voiceover audio
        output_path: Output file path
        video_type: "short" (9:16) or "long" (16:9)
        add_zoom: Enable Ken Burns zoom/pan
        add_music: Mix background music under voiceover
    
    Returns:
        Path to final video
    """
    check_ffmpeg()
    
    print(f"🎬 Assembling {video_type} video...")
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get audio duration
    audio_duration = get_audio_duration(audio_path)
    print(f"⏱️ Audio: {audio_duration:.1f}s")
    
    num_images = len(image_paths)
    if num_images == 0:
        raise ValueError("❌ No images provided!")
    
    duration_per_image = audio_duration / num_images
    print(f"🖼️ {num_images} images × {duration_per_image:.1f}s each")
    
    # Resolution
    if video_type == "short":
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080
    
    # ── Step 1: Create slideshow ──
    slideshow_path = str(TEMP_DIR / "slideshow.mp4")
    
    # Build FFmpeg command for slideshow
    filter_parts = []
    input_args = []
    
    for i, img_path in enumerate(image_paths):
        input_args.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img_path])
        
        if add_zoom:
            # Ken Burns: slow zoom from 100% to 115%
            zoom_speed = 0.0006
            fps = 25
            frames = int(duration_per_image * fps)
            filter_parts.append(
                f"[{i}:v]scale={width*2}:{height*2},"
                f"zoompan=z='min(zoom+{zoom_speed},1.15)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={width}x{height}:fps={fps}[v{i}]"
            )
        else:
            filter_parts.append(
                f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
                f"setsar=1[v{i}]"
            )
    
    # Concatenate
    concat_inputs = "".join([f"[v{i}]" for i in range(num_images)])
    filter_parts.append(f"{concat_inputs}concat=n={num_images}:v=1:a=0[slideshow]")
    filter_complex = ";".join(filter_parts)
    
    cmd = ["ffmpeg", "-y"] + input_args + [
        "-filter_complex", filter_complex,
        "-map", "[slideshow]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p", "-t", str(audio_duration),
        slideshow_path
    ]
    
    print("📹 Creating slideshow...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    if result.returncode != 0:
        print(f"⚠️ Zoom failed, trying simple slideshow...")
        # Fallback without zoom
        simple_filter = ";".join([
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1[v{i}]"
            for i in range(num_images)
        ] + [
            "".join([f"[v{i}]" for i in range(num_images)]) +
            f"concat=n={num_images}:v=1:a=0[slideshow]"
        ])
        
        cmd_simple = ["ffmpeg", "-y"] + input_args + [
            "-filter_complex", simple_filter,
            "-map", "[slideshow]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-pix_fmt", "yuv420p", "-t", str(audio_duration),
            slideshow_path
        ]
        subprocess.run(cmd_simple, capture_output=True, text=True, timeout=600, check=True)
    
    # ── Step 2: Mix background music ──
    final_audio_path = audio_path
    
    if add_music:
        music_file = _find_background_music()
        if music_file:
            print("🎵 Mixing background music at 12% volume...")
            mixed_path = str(TEMP_DIR / "mixed_audio.aac")
            
            mix_cmd = [
                "ffmpeg", "-y",
                "-i", audio_path,
                "-i", str(music_file),
                "-filter_complex",
                "[1:a]volume=0.12,afade=t=in:d=2:st=0,afade=t=out:d=3:st=" + 
                str(max(0, audio_duration - 3)) + "[bg];"
                "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=3",
                "-c:a", "aac", "-b:a", "192k",
                mixed_path
            ]
            
            mix_result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=120)
            if mix_result.returncode == 0:
                final_audio_path = mixed_path
                print("✅ Music mixed!")
            else:
                print("⚠️ Music mixing failed, using voiceover only")
        else:
            print("ℹ️ No background music found. Add .mp3 to templates/music/")
    
    # ── Step 3: Combine video + audio ──
    output_dir = OUTPUT_DIR / "videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(output_dir / f"final_{video_type}_{timestamp}.mp4")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    print("🔗 Combining video + audio...")
    
    final_cmd = [
        "ffmpeg", "-y",
        "-i", slideshow_path,
        "-i", final_audio_path,
        "-c:v", "libx264",
        "-preset", "slow",        # Better quality
        "-crf", "18",              # High quality for YouTube
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",  # YouTube streaming optimization
        output_path
    ]
    
    subprocess.run(final_cmd, capture_output=True, text=True, timeout=600, check=True)
    
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Final video: {output_path}")
    print(f"📊 Size: {file_size:.1f}MB | Duration: {audio_duration:.1f}s | {width}x{height}")
    
    _cleanup_temp()
    return output_path


def _find_background_music():
    """Find a background music file."""
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    
    for ext in ["*.mp3", "*.wav", "*.aac", "*.m4a"]:
        files = list(MUSIC_DIR.glob(ext))
        if files:
            return files[0]
    return None


def add_captions_to_video(video_path, script_text, output_path=None):
    """Burn captions/subtitles into video (critical for Shorts)."""
    if not output_path:
        base = Path(video_path)
        output_path = str(base.parent / f"{base.stem}_captioned{base.suffix}")
    
    # Simple centered caption
    # Escape special characters for FFmpeg drawtext
    clean_text = script_text[:200].replace("'", "\\'").replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", (
            f"drawtext=text='{clean_text}':"
            f"fontsize=36:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=h-150:"
            f"font='Arial Bold'"
        ),
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-c:a", "copy",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    if result.returncode == 0:
        print(f"✅ Captioned: {output_path}")
    else:
        print(f"⚠️ Captions failed, using original")
        output_path = video_path
    
    return output_path


def _cleanup_temp():
    """Remove temp files."""
    if TEMP_DIR.exists():
        for f in TEMP_DIR.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass
        print("🧹 Temp cleaned")


# ════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🎬 Assemble video with FFmpeg")
    parser.add_argument("--images", nargs="+", required=True, help="Image paths")
    parser.add_argument("--audio", required=True, help="Audio path")
    parser.add_argument("--output", default=None, help="Output path")
    parser.add_argument("--type", choices=["short", "long"], default="short")
    parser.add_argument("--no-zoom", action="store_true")
    parser.add_argument("--no-music", action="store_true")
    
    args = parser.parse_args()
    
    create_slideshow_video(
        image_paths=args.images,
        audio_path=args.audio,
        output_path=args.output,
        video_type=args.type,
        add_zoom=not args.no_zoom,
        add_music=not args.no_music
    )

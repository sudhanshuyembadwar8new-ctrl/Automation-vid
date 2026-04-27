"""
🎙️ Voice Generator — Edge TTS (100% FREE)
Converts scripts to natural-sounding voiceovers.
No API key needed. No payment. No limits. Neural voices.

Uses Microsoft Edge TTS which provides WaveNet-quality voices for FREE.
Best Hindi voice: hi-IN-MadhurNeural (male, energetic, young)
"""

import os
import re
import json
import asyncio
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
CONFIG_DIR = Path(__file__).parent.parent / "config"


def ensure_edge_tts():
    """Install edge-tts if not present."""
    try:
        import edge_tts
        return True
    except ImportError:
        print("⚠️ Installing edge-tts (one-time, takes ~10 seconds)...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "edge-tts"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("✅ edge-tts installed!")
        return True


def load_voice_config():
    """Load voice configuration."""
    config_path = CONFIG_DIR / "voices.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Defaults if config not found
    return {
        "edge_tts": {
            "recommended": {
                "voice": "hi-IN-MadhurNeural",
                "rate": "-5%",
                "pitch": "+0Hz"
            }
        }
    }


def preprocess_script(script_text, video_type="short"):
    """
    Clean and prepare script text for TTS.
    Splits at [PAUSE] markers for natural breaks.
    Removes editing cues like [SHOW SCREEN].
    """
    # Remove editing markers but keep text
    text = re.sub(r'\[SHOW SCREEN\]', '', script_text)
    text = re.sub(r'\[CHAPTER:\s*(.*?)\]', r'\1.', text)
    text = re.sub(r'\[B-ROLL\]', '', text)
    text = re.sub(r'\[CUT\]', '', text)
    
    # Split at [PAUSE] markers
    segments = re.split(r'\[PAUSE\]', text)
    
    cleaned = []
    for seg in segments:
        s = seg.strip()
        # Remove any remaining bracket markers
        s = re.sub(r'\[.*?\]', '', s)
        # Clean multiple spaces/newlines
        s = re.sub(r'\s+', ' ', s).strip()
        if s and len(s) > 3:
            cleaned.append(s)
    
    return cleaned


async def _generate_with_edge_tts(text, output_path, voice="hi-IN-MadhurNeural", 
                                   rate="-5%", pitch="+0Hz"):
    """Internal async function for Edge TTS generation."""
    import edge_tts
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


def generate_voice(script_text, output_filename=None, voice=None, 
                   rate=None, video_type="short"):
    """
    Generate voiceover from script using Edge TTS (FREE).
    
    Args:
        script_text: Script text to convert to speech
        output_filename: Optional custom filename
        voice: Edge TTS voice name (default: from config)
        rate: Speaking rate adjustment (e.g., "-5%", "+10%")
        video_type: "short" or "long"
    
    Returns:
        tuple: (audio_path, estimated_duration)
    """
    ensure_edge_tts()
    
    # Load config
    config = load_voice_config()
    recommended = config["edge_tts"]["recommended"]
    
    if not voice:
        voice = recommended["voice"]
    if not rate:
        # Shorts slightly faster, long form slightly slower
        rate = "-3%" if video_type == "short" else "-8%"
    
    pitch = recommended.get("pitch", "+0Hz")
    
    print(f"🎙️ Generating voice with Edge TTS (FREE)...")
    print(f"🗣️ Voice: {voice} | Rate: {rate} | Type: {video_type}")
    
    # Preprocess script
    segments = preprocess_script(script_text, video_type)
    
    if not segments:
        raise ValueError("❌ No speakable text found in script!")
    
    # Prepare output directory
    output_dir = OUTPUT_DIR / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"voice_{video_type}_{timestamp}.mp3"
    
    output_path = str(output_dir / output_filename)
    
    # If single segment, generate directly
    if len(segments) == 1:
        print(f"📝 Generating single segment...")
        asyncio.run(_generate_with_edge_tts(
            segments[0], output_path, voice, rate, pitch
        ))
    else:
        # Multiple segments — generate each, then concatenate with pauses
        print(f"📝 Generating {len(segments)} segments...")
        temp_dir = Path(os.getenv("TEMP_DIR", "./temp")) / "audio_segments"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        segment_paths = []
        for i, segment in enumerate(segments):
            seg_path = str(temp_dir / f"seg_{i:03d}.mp3")
            print(f"  🔊 Segment {i+1}/{len(segments)}: {segment[:50]}...")
            
            try:
                asyncio.run(_generate_with_edge_tts(
                    segment, seg_path, voice, rate, pitch
                ))
                segment_paths.append(seg_path)
            except Exception as e:
                print(f"  ⚠️ Segment {i+1} failed: {e}")
                continue
        
        if not segment_paths:
            raise Exception("❌ All segments failed!")
        
        # Concatenate segments with silence gaps using FFmpeg
        _concatenate_audio_segments(segment_paths, output_path, video_type)
        
        # Cleanup temp segments
        for sp in segment_paths:
            try:
                os.remove(sp)
            except Exception:
                pass
    
    # Get duration
    duration = _get_audio_duration(output_path)
    
    print(f"✅ Voice generated: {output_path}")
    print(f"⏱️ Duration: {duration:.1f}s")
    
    # Duration warnings
    if video_type == "short" and duration > 65:
        print(f"⚠️ Short form audio is {duration:.0f}s — should be under 60s!")
    
    return output_path, duration


def _concatenate_audio_segments(segment_paths, output_path, video_type="short"):
    """Concatenate audio segments with natural pauses between them."""
    pause_ms = 300 if video_type == "short" else 500
    
    # Create a concat file for FFmpeg
    temp_dir = Path(os.getenv("TEMP_DIR", "./temp"))
    concat_file = temp_dir / "concat_list.txt"
    
    # Generate silence file
    silence_path = str(temp_dir / "silence.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(pause_ms / 1000),
        "-c:a", "libmp3lame", "-q:a", "9",
        silence_path
    ], capture_output=True, timeout=30)
    
    # Write concat file — use forward slashes for FFmpeg compatibility on Windows
    with open(concat_file, "w") as f:
        for i, seg_path in enumerate(segment_paths):
            safe_path = os.path.abspath(seg_path).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")
            if i < len(segment_paths) - 1 and os.path.exists(silence_path):
                safe_silence = os.path.abspath(silence_path).replace("\\", "/")
                f.write(f"file '{safe_silence}'\n")
    
    # Concatenate
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    ], capture_output=True, timeout=120, check=True)
    
    # Cleanup
    try:
        os.remove(str(concat_file))
        os.remove(silence_path)
    except Exception:
        pass


def _get_audio_duration(audio_path):
    """Get audio duration in seconds using FFprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            audio_path
        ], capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except Exception:
        # Rough estimate: ~150 words per minute for Hindi
        return 60.0  # Default fallback


def generate_voice_from_file(script_json_path, voice=None, rate=None):
    """Generate voice from a saved script JSON file."""
    with open(script_json_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    script_text = script_data.get("script", "")
    video_type = script_data.get("video_type", "short")
    
    if not script_text:
        raise ValueError(f"❌ No script text in {script_json_path}")
    
    return generate_voice(
        script_text=script_text,
        voice=voice,
        rate=rate,
        video_type=video_type
    )


async def list_available_voices(language="hi"):
    """List all available Edge TTS voices for a language."""
    import edge_tts
    voices = await edge_tts.list_voices()
    matching = [v for v in voices if v["Locale"].startswith(language)]
    return matching


# ════════════════════════════════════════════
# CLI Entry Point
# ════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🎙️ Generate voiceover with Edge TTS (FREE)")
    parser.add_argument("--script", type=str, help="Path to script JSON or raw text")
    parser.add_argument("--text", type=str, help="Raw text to speak")
    parser.add_argument("--voice", type=str, default=None, help="Voice name")
    parser.add_argument("--rate", type=str, default=None, help="Rate adjustment (e.g. '-5%%')")
    parser.add_argument("--type", choices=["short", "long"], default="short")
    parser.add_argument("--list-voices", action="store_true", help="List available Hindi voices")
    
    args = parser.parse_args()
    
    if args.list_voices:
        ensure_edge_tts()
        voices = asyncio.run(list_available_voices("hi"))
        print(f"\n🗣️ Available Hindi voices ({len(voices)}):")
        for v in voices:
            print(f"  {v['ShortName']:30s} {v['Gender']:8s} {v.get('FriendlyName', '')}")
        
        voices_en = asyncio.run(list_available_voices("en-IN"))
        print(f"\n🗣️ Available Indian English voices ({len(voices_en)}):")
        for v in voices_en:
            print(f"  {v['ShortName']:30s} {v['Gender']:8s} {v.get('FriendlyName', '')}")
    elif args.script and args.script.endswith(".json"):
        audio_path, duration = generate_voice_from_file(args.script, args.voice, args.rate)
        print(f"\n🎉 Audio: {audio_path} ({duration:.1f}s)")
    elif args.text:
        audio_path, duration = generate_voice(args.text, voice=args.voice, rate=args.rate, video_type=args.type)
        print(f"\n🎉 Audio: {audio_path} ({duration:.1f}s)")
    else:
        parser.print_help()

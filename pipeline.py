"""
MASTER PIPELINE -- YouTube Automation Engine GOD MODE
One command: Topic -> Script -> Voice -> Visuals -> Video -> Upload

Usage:
  python pipeline.py --type short                    # Auto short
  python pipeline.py --type long --dry-run           # Long form, skip upload
  python pipeline.py --type short --topic "free AI"  # Custom topic
  python pipeline.py --batch 7 --type short          # 7 shorts in one go
"""

import sys, io
# Force UTF-8 output on Windows to prevent emoji encoding crashes (cp1252)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

load_dotenv()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))


def banner():
    """Print the startup banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║  🚀 YOUTUBE AUTOMATION ENGINE — GOD MODE                     ║
║  ─────────────────────────────────────────────────────────── ║
║  Niche: AI Tools + Make Money Online | Language: Hinglish    ║
║  Cost: ₹0 | Quality: Premium | Mode: Fully Automated        ║
║  Stack: Gemini + Edge TTS + Pollinations + FFmpeg            ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def run_pipeline(video_type="short", custom_topic=None, dry_run=False,
                 skip_upload=False, voice=None, rate=None, skip_visuals=False):
    """
    Execute the complete video creation pipeline.
    
    Pipeline Steps:
    1. 🧠 Generate script (Gemini API — FREE)
    2. 🎙️ Generate voiceover (Edge TTS — FREE)
    3. 🖼️ Generate visuals (Pollinations.ai — FREE)
    4. 🎬 Assemble video (FFmpeg — FREE)
    5. 📤 Upload to YouTube (optional)
    
    Total cost: ₹0
    """
    banner()
    
    start_time = time.time()
    pipeline_log = {
        "started_at": datetime.now().isoformat(),
        "video_type": video_type,
        "steps": {}
    }
    
    # ═══════════════════════════════════════
    # STEP 1: Generate Script
    # ═══════════════════════════════════════
    print("\n" + "═" * 60)
    print("STEP 1/5: 🧠 GENERATING SCRIPT (Gemini API — FREE)")
    print("═" * 60)
    
    from generate_script import generate_script
    
    topic = None
    if custom_topic:
        topic = {"category": "Custom", "prompt": custom_topic, "category_id": "custom"}
    
    try:
        script_data, script_path = generate_script(video_type=video_type, custom_topic=topic)
        pipeline_log["steps"]["script"] = {"status": "success", "path": script_path}
        print(f"✅ Script: {script_data.get('title', 'Untitled')}")
    except Exception as e:
        print(f"❌ Script generation failed: {e}")
        pipeline_log["steps"]["script"] = {"status": "failed", "error": str(e)}
        _save_log(pipeline_log)
        return None
    
    # ═══════════════════════════════════════
    # STEP 2: Generate Voice
    # ═══════════════════════════════════════
    print("\n" + "═" * 60)
    print("STEP 2/5: 🎙️ GENERATING VOICE (Edge TTS — FREE)")
    print("═" * 60)
    
    from generate_voice import generate_voice
    
    script_text = script_data.get("script", "")
    
    try:
        audio_path, audio_duration = generate_voice(
            script_text=script_text,
            voice=voice,
            rate=rate,
            video_type=video_type
        )
        pipeline_log["steps"]["voice"] = {
            "status": "success",
            "path": audio_path,
            "duration": audio_duration
        }
        print(f"✅ Voice: {audio_duration:.1f}s")
    except Exception as e:
        print(f"❌ Voice failed: {e}")
        pipeline_log["steps"]["voice"] = {"status": "failed", "error": str(e)}
        _save_log(pipeline_log)
        return None
    
    # ═══════════════════════════════════════
    # STEP 3: Generate Visuals
    # ═══════════════════════════════════════
    if skip_visuals:
        print("\n" + "═" * 60)
        print("STEP 3/5: 🖼️ VISUALS SKIPPED")
        print("═" * 60)
        visuals = {"images": [], "thumbnail": None}
        pipeline_log["steps"]["visuals"] = {"status": "skipped"}
    else:
        print("\n" + "═" * 60)
        print("STEP 3/5: 🖼️ GENERATING VISUALS (Pollinations.ai — FREE)")
        print("═" * 60)
        
        from generate_visuals import generate_video_visuals
        
        try:
            visuals = generate_video_visuals(script_data, video_type=video_type)
            pipeline_log["steps"]["visuals"] = {
                "status": "success",
                "images": len(visuals.get("images", [])),
                "thumbnail": visuals.get("thumbnail")
            }
            print(f"✅ Visuals: {len(visuals['images'])} images")
        except Exception as e:
            print(f"❌ Visuals failed: {e}")
            pipeline_log["steps"]["visuals"] = {"status": "failed", "error": str(e)}
            _save_log(pipeline_log)
            return None
    
    if not visuals.get("images"):
        print("❌ No images available. Cannot create video.")
        _save_log(pipeline_log)
        return None
    
    # ═══════════════════════════════════════
    # STEP 4: Assemble Video
    # ═══════════════════════════════════════
    print("\n" + "═" * 60)
    print("STEP 4/5: 🎬 ASSEMBLING VIDEO (FFmpeg — FREE)")
    print("═" * 60)
    
    from assemble_video import create_slideshow_video
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_output = str(OUTPUT_DIR / "videos" / f"final_{video_type}_{timestamp}.mp4")
    
    try:
        final_video = create_slideshow_video(
            image_paths=visuals["images"],
            audio_path=audio_path,
            output_path=video_output,
            video_type=video_type,
            add_zoom=True,
            add_music=True
        )
        pipeline_log["steps"]["video"] = {"status": "success", "path": final_video}
        print(f"✅ Video: {final_video}")
    except Exception as e:
        print(f"❌ Video assembly failed: {e}")
        pipeline_log["steps"]["video"] = {"status": "failed", "error": str(e)}
        _save_log(pipeline_log)
        return None
    
    # ═══════════════════════════════════════
    # STEP 5: Upload
    # ═══════════════════════════════════════
    if dry_run or skip_upload:
        print("\n" + "═" * 60)
        print("STEP 5/5: 📤 UPLOAD SKIPPED (dry run)")
        print("═" * 60)
        pipeline_log["steps"]["upload"] = {"status": "skipped"}
    else:
        print("\n" + "═" * 60)
        print("STEP 5/5: 📤 UPLOADING TO YOUTUBE")
        print("═" * 60)
        
        from upload_youtube import upload_video, build_description
        
        title = script_data.get("title", f"AI Tool — {timestamp}")
        description = build_description(script_data)
        tags = script_data.get("tags", script_data.get("hashtags", []))
        
        try:
            upload_result = upload_video(
                video_path=final_video,
                title=title,
                description=description,
                tags=tags,
                thumbnail_path=visuals.get("thumbnail"),
                privacy="public"
            )
            pipeline_log["steps"]["upload"] = {
                "status": "success",
                "video_id": upload_result["video_id"],
                "url": upload_result["url"]
            }
            print(f"✅ Live: {upload_result['url']}")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            pipeline_log["steps"]["upload"] = {"status": "failed", "error": str(e)}
    
    # ═══════════════════════════════════════
    # DONE
    # ═══════════════════════════════════════
    elapsed = time.time() - start_time
    pipeline_log["completed_at"] = datetime.now().isoformat()
    pipeline_log["elapsed_seconds"] = elapsed
    
    _save_log(pipeline_log)
    
    title_display = script_data.get('title', 'N/A')[:45]
    video_name = Path(final_video).name
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║  ✅ PIPELINE COMPLETE                                         ║
╠═══════════════════════════════════════════════════════════════╣
║  📝 {title_display:<55s}  ║
║  🎬 {video_name:<55s}  ║
║  ⏱️  Duration: {audio_duration:.1f}s | Total time: {elapsed:.0f}s{' ' * 30} ║
║  💰 Cost: ₹0{' ' * 47} ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    return {
        "script": script_data,
        "audio": audio_path,
        "visuals": visuals,
        "video": final_video,
        "upload": pipeline_log["steps"].get("upload", {}),
        "log": pipeline_log
    }


def run_batch(count=7, video_type="short", dry_run=True):
    """Run pipeline N times for batch content generation."""
    print(f"\n🏭 BATCH MODE: Generating {count} {video_type} videos...")
    
    results = []
    for i in range(count):
        print(f"\n{'=' * 40}")
        print(f"  [BATCH] VIDEO {i+1}/{count} | {video_type.upper()}")
        print(f"{'=' * 40}")
        
        result = run_pipeline(video_type=video_type, dry_run=dry_run)
        if result:
            results.append(result)
        
        # Delay between videos to avoid rate limiting
        if i < count - 1:
            print("⏳ Waiting 10s before next video...")
            time.sleep(10)
    
    print(f"\n🎉 Batch complete: {len(results)}/{count} videos generated!")
    return results


def _save_log(log_data):
    """Save pipeline execution log."""
    log_dir = OUTPUT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"pipeline_{timestamp}.json"
    
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════
# CLI Entry Point
# ════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🚀 YouTube Automation Engine — GOD MODE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py --type short                          # Generate a short
  python pipeline.py --type long --dry-run                 # Long form, no upload
  python pipeline.py --type short --topic "free AI tool"   # Custom topic
  python pipeline.py --batch 7 --type short --dry-run      # 7 shorts batch
  python pipeline.py --type short --voice hi-IN-SwaraNeural  # Female voice
        """
    )
    
    parser.add_argument("--type", choices=["short", "long"], default="short",
                        help="Video type: short (30-60s) or long (8-15min)")
    parser.add_argument("--topic", type=str, default=None,
                        help="Custom topic (overrides auto-rotation)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip YouTube upload")
    parser.add_argument("--voice", type=str, default=None,
                        help="Edge TTS voice (default: hi-IN-MadhurNeural)")
    parser.add_argument("--rate", type=str, default=None,
                        help="Voice rate adjustment (e.g. '-5%%')")
    parser.add_argument("--batch", type=int, default=0,
                        help="Generate N videos in batch mode")
    parser.add_argument("--skip-visuals", action="store_true",
                        help="Skip image generation (use existing)")
    
    args = parser.parse_args()
    
    if args.batch > 0:
        results = run_batch(
            count=args.batch,
            video_type=args.type,
            dry_run=args.dry_run
        )
    else:
        result = run_pipeline(
            video_type=args.type,
            custom_topic=args.topic,
            dry_run=args.dry_run,
            voice=args.voice,
            rate=args.rate,
            skip_visuals=args.skip_visuals
        )
        
        if result:
            print("\n🎉 Your video is ready!")
        else:
            print("\n❌ Pipeline failed. Check errors above.")
            sys.exit(1)

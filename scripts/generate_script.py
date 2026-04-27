"""
📝 Script Generator — Gemini API (FREE)
Generates viral Hinglish YouTube scripts for shorts and long-form videos.
Uses rotating topics, hook formulas, and authentic YouTuber writing style.
Zero cost: Gemini gives 1500 free requests/day.
"""

import os
import json
import random
import requests
import re
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
CONFIG_DIR = Path(__file__).parent.parent / "config"


# ════════════════════════════════════════════
# SYSTEM PROMPTS — The secret sauce
# These prompts force Gemini to write like a
# real Indian YouTuber, NOT like an AI
# ════════════════════════════════════════════

SHORT_FORM_SYSTEM = """You are a VIRAL Hinglish YouTube Shorts scriptwriter.
Your channel: AI tools + making money online.
Your audience: Indian students & young professionals (18-28 years old).

═══ WRITING RULES (CRITICAL — follow exactly) ═══

1. LANGUAGE: Casual Hinglish — mix Hindi + English naturally.
   ✅ "Bhai dekh, ye tool literally free hai aur koi bata nahi raha"
   ✅ "Ek kaam karo abhi — phone uthao aur ye download karo"
   ✅ "Seriously bata raha hoon, maine isse ₹15K kamaye ek hafte me"
   ❌ "Aaj hum dekhenge ki kaise..." (boring 2015 YouTube)
   ❌ "Hello everyone, welcome to my channel" (corporate AI slop)

2. TONE: You're a 22-year-old excited friend sharing a secret.
   - Use: "bhai", "yaar", "dekh", "sun", "sach me", "trust me"
   - Use specific numbers: "₹5000", "10 minutes me", "3 simple steps"
   - Sound EXCITED, not professional

3. HOOK (first 3 seconds): Must STOP the scroll.
   Pick ONE hook style:
   - CONTROVERSY: "Ye tool Google ko band karwa dega bhai"
   - CURIOSITY GAP: "Maine ek kaam kiya, ₹5000 aa gaye — seedha batata hoon"
   - RELATABILITY: "Bhai paise nahi hain, phone purana hai, aur fir bhi..."
   - SHOCK: "Ye AI tool jo maine dhunda, iska price guess karo — ZERO"
   - URGENCY: "Ye free hai abhi, kal se paid ho jayega — jaldi sun"

4. BODY: Show value fast. No filler. Every sentence earns its place.
   - Mention SPECIFIC tool names (real ones)
   - Give SPECIFIC steps (not vague "use AI")
   - Add pattern interrupt every 15 seconds

5. CTA (last 5 sec): "Like karo, subscribe karo, comment me batao..."

═══ OUTPUT FORMAT (return ONLY valid JSON, no markdown) ═══
{
  "title": "Clickbait but REAL title with emoji 🔥",
  "script": "Full script (45-60 sec spoken). Include [PAUSE] for natural breaks. Include [SHOW SCREEN] for editing cues.",
  "hashtags": ["#AITools", "#MakeMoneyOnline", "#FreeAI"],
  "thumbnail_text": "MAX 4 WORDS — bold, attention-grabbing",
  "description": "Short YouTube description with keywords",
  "hook_type": "Which hook formula used"
}"""


LONG_FORM_SYSTEM = """You are a PRO Hinglish YouTube tutorial creator.
Channel: AI tools + making money online for Indian students.
Videos: 8-15 minute deep-dive tutorials with screen recordings.

═══ WRITING RULES ═══

1. LANGUAGE: Casual Hinglish like a knowledgeable friend.
   - "Bhai dekh, ye part important hai — dhyan se sun"
   - "Matlab samjho, iska use karke tum literally..."
   - "Simple hai bhai, 3 steps me ho jayega"
   - Add personality: jokes, reactions, "haan bhai sach me!"

2. STRUCTURE:
   [HOOK] (0-30 sec): Show the END RESULT first → big promise
   [INTRO] (30-60 sec): What, why, for whom
   [CHAPTER 1: Title] (2-3 min): First major point + demo
   [CHAPTER 2: Title] (2-3 min): Second point + demo  
   [CHAPTER 3: Title] (2-3 min): Third point + demo
   [BONUS] (1-2 min): Unexpected extra value
   [CTA] (30-60 sec): Subscribe + comment question + next video

3. ENGAGEMENT HACKS:
   - Re-hook every 2-3 minutes: "Aur bhai, ab next part aur crazy hai"
   - Use "Ab ye part important hai" before key sections
   - Ask rhetorical questions: "Toh bhai tu kya karega? Seedha batata hoon"
   - Add [SHOW SCREEN] markers for screen recording cuts

═══ OUTPUT FORMAT (return ONLY valid JSON) ═══
{
  "title": "SEO optimized title with emoji",
  "script": "Full 8-15 min script with [CHAPTER: Title], [PAUSE], [SHOW SCREEN] markers",
  "chapters": [{"time": "0:00", "title": "Chapter name"}],
  "hashtags": ["5-8 relevant hashtags"],
  "thumbnail_text": "Max 4 words",
  "description": "Full description with timestamps, links section, keywords",
  "tags": ["15-20 SEO tags"],
  "hook_type": "Which hook formula used"
}"""


def load_topics():
    """Load topic categories from config."""
    config_path = CONFIG_DIR / "topics.json"
    if not config_path.exists():
        raise FileNotFoundError(f"❌ Topics config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_topic(video_type="short"):
    """Pick a trending topic based on day of week and weighted categories."""
    topics_config = load_topics()
    day = datetime.now().strftime("%A").lower()
    
    # Get category for today
    category_id = topics_config["daily_rotation"].get(day, "free_ai_tools")
    
    # Find the category
    category = None
    for cat in topics_config["categories"]:
        if cat["id"] == category_id:
            category = cat
            break
    
    if not category:
        category = topics_config["categories"][0]
    
    # Pick random prompt from category
    topic_prompt = random.choice(category["prompts"])
    
    return {
        "category": category["name"],
        "prompt": topic_prompt,
        "category_id": category_id
    }


def pick_hook_formula():
    """Pick a random hook formula for variety."""
    try:
        topics_config = load_topics()
        formulas = topics_config.get("hook_formulas", [])
        if formulas:
            return random.choice(formulas)
    except Exception:
        pass
    return "curiosity_gap: Tease a result without revealing the method"


def call_gemini(prompt, system_prompt, max_retries=3):
    """
    Call Gemini API with retry logic.
    Free tier: 1500 requests/day, 15 requests/minute.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "❌ GEMINI_API_KEY not set!\n"
            "   1. Go to: https://aistudio.google.com/apikey\n"
            "   2. Click 'Create API Key'\n"
            "   3. Add to .env: GEMINI_API_KEY=AIza..."
        )
    
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n---\n\n{prompt}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }
    
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 429:
                # Rate limited — wait and retry
                wait = (attempt + 1) * 5
                print(f"⏳ Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error {response.status_code}: {response.text[:200]}")
            
            result = response.json()
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return generated_text
            
        except requests.exceptions.Timeout:
            print(f"⏳ Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(3)
            continue
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected Gemini response format: {e}")
    
    raise Exception(f"❌ Gemini API failed after {max_retries} attempts")


def parse_json_response(text):
    """Robustly parse JSON from Gemini response."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try stripping and parsing
    stripped = text.strip()
    if stripped.startswith('{'):
        # Find the matching closing brace
        brace_count = 0
        for i, char in enumerate(stripped):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    try:
                        return json.loads(stripped[:i+1])
                    except json.JSONDecodeError:
                        break
    
    raise json.JSONDecodeError("Could not parse JSON from Gemini response", text, 0)


def generate_script(video_type="short", custom_topic=None):
    """
    Generate a complete video script using Gemini API.
    
    Args:
        video_type: "short" (30-60 sec) or "long" (8-15 min)
        custom_topic: Optional dict with category/prompt override
    
    Returns:
        tuple: (script_data dict, output_path string)
    """
    # Pick topic
    topic = custom_topic or pick_topic(video_type)
    hook = pick_hook_formula()
    
    # Select system prompt
    system_prompt = SHORT_FORM_SYSTEM if video_type == "short" else LONG_FORM_SYSTEM
    
    # Build user message
    user_message = f"""Generate a {video_type} form video script about: {topic['prompt']}

Category: {topic['category']}
Date: {datetime.now().strftime('%Y-%m-%d')}
Preferred hook style: {hook}

CRITICAL REQUIREMENTS:
- Make it FRESH and UNIQUE — not the same generic advice everyone gives
- Include a SPECIFIC tool, method, or hack — not vague "use AI to make money"  
- The hook must make someone STOP scrolling immediately
- Sound like a real 22-year-old Indian creator, NOT an AI
- Return ONLY valid JSON, no markdown formatting"""

    print(f"🧠 Generating {video_type} form script...")
    print(f"📌 Topic: {topic['prompt'][:60]}...")
    print(f"📂 Category: {topic['category']}")
    print(f"🎣 Hook: {hook.split(':')[0]}")
    
    # Call Gemini
    generated_text = call_gemini(user_message, system_prompt)
    
    # Parse response
    script_data = parse_json_response(generated_text)
    
    # Add metadata
    script_data["video_type"] = video_type
    script_data["topic_category"] = topic["category"]
    script_data["topic_prompt"] = topic["prompt"]
    script_data["generated_at"] = datetime.now().isoformat()
    script_data["hook_formula"] = hook
    
    # Save to output
    output_dir = OUTPUT_DIR / "scripts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{video_type}_{timestamp}.json"
    output_path = output_dir / filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Script saved: {output_path}")
    print(f"📝 Title: {script_data.get('title', 'Untitled')}")
    print(f"🖼️ Thumbnail: {script_data.get('thumbnail_text', 'N/A')}")
    
    return script_data, str(output_path)


def generate_batch_scripts(count=7, video_type="short"):
    """Generate a batch of scripts with variety across categories."""
    scripts = []
    topics_config = load_topics()
    
    for i in range(count):
        cat_index = i % len(topics_config["categories"])
        category = topics_config["categories"][cat_index]
        topic = {
            "category": category["name"],
            "prompt": random.choice(category["prompts"]),
            "category_id": category["id"]
        }
        
        try:
            script_data, path = generate_script(video_type, custom_topic=topic)
            scripts.append({"data": script_data, "path": path})
            print(f"✅ [{i+1}/{count}] Done: {script_data.get('title', 'Untitled')}")
            # Small delay to avoid rate limiting
            if i < count - 1:
                time.sleep(2)
        except Exception as e:
            print(f"❌ [{i+1}/{count}] Failed: {e}")
    
    print(f"\n🎉 Generated {len(scripts)}/{count} scripts!")
    return scripts


# ════════════════════════════════════════════
# CLI Entry Point
# ════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🧠 Generate YouTube scripts with Gemini AI")
    parser.add_argument("--type", choices=["short", "long"], default="short", help="Video type")
    parser.add_argument("--batch", type=int, default=0, help="Generate batch of N scripts")
    parser.add_argument("--topic", type=str, default=None, help="Custom topic override")
    
    args = parser.parse_args()
    
    if args.batch > 0:
        generate_batch_scripts(count=args.batch, video_type=args.type)
    else:
        topic = None
        if args.topic:
            topic = {"category": "Custom", "prompt": args.topic, "category_id": "custom"}
        
        script_data, path = generate_script(video_type=args.type, custom_topic=topic)
        print(f"\n{'═'*60}")
        print(f"SCRIPT PREVIEW:")
        print(f"{'═'*60}")
        print(script_data.get("script", "No script generated")[:500])
        print(f"{'═'*60}")

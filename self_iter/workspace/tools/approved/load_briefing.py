from agents import function_tool
import os
import json

@function_tool
def load_briefing() -> str:
    """Load user profile and roadmap summary from /workspace/memory.

    Returns a short briefing string for the current session.
    """
    profile_path = "/workspace/memory/profile.json"
    roadmap_path = "/workspace/roadmap.md"
    bits = []

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
            name = profile.get("name", "user")
            topic = profile.get("favorite_topic", "")
            note = profile.get("note", "")
            bits.append(f"Profile: {name} | favorite topic: {topic} | {note}")
    except FileNotFoundError:
        bits.append("Profile: not found")
    except Exception as e:
        bits.append(f"Profile error: {e}")

    try:
        with open(roadmap_path, "r", encoding="utf-8", errors="replace") as f:
            roadmap = f.read().strip()
            # keep only first 500 chars in context
            preview = roadmap[:500]
            bits.append(f"Roadmap preview: {preview if preview else 'empty'}")
    except FileNotFoundError:
        bits.append("Roadmap: not found")
    except Exception as e:
        bits.append(f"Roadmap error: {e}")

    return "\n".join(bits)
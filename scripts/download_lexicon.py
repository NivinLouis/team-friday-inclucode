#!/usr/bin/env python3
"""
Download everyday English words as .pose files from the sign-mt API
and register them in assets/dummy_lexicon_en/index.csv.

Usage (run from the project root):
    python3 scripts/download_lexicon.py

The script:
  1. Tries Indian Sign Language (ins) first, then falls back to ASL (ase).
  2. Verifies the response is a valid binary .pose file (checks the POSE magic header).
  3. Saves each word's pose file into assets/dummy_lexicon_en/<signed_lang>/
  4. Appends new entries to assets/dummy_lexicon_en/index.csv (skips already-present words).
"""

import csv
import os
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LEXICON_DIR = os.path.join(PROJECT_ROOT, "assets", "dummy_lexicon_en")
INDEX_CSV = os.path.join(LEXICON_DIR, "index.csv")
API_URL = "https://us-central1-sign-mt.cloudfunctions.net/spoken_text_to_signed_pose"
SPOKEN = "en"

# Delay between requests (seconds) to avoid rate limiting
REQUEST_DELAY = 0.75

# ---------------------------------------------------------------------------
# Top everyday English words to download
# Curated list of high-frequency, everyday-use words
# ---------------------------------------------------------------------------

EVERYDAY_WORDS = [
    # ── Greetings & social ──────────────────────────────────────────────────
    "hello", "goodbye", "please", "thank you", "sorry", "yes", "no",
    "help", "welcome", "excuse me", "good morning", "good night",
    "good afternoon", "how are you", "nice to meet you",

    # ── Pronouns ─────────────────────────────────────────────────────────────
    "I", "you", "he", "she", "we", "they", "it", "me", "my", "your",
    "his", "her", "our", "their",

    # ── Core verbs ───────────────────────────────────────────────────────────
    "go", "come", "eat", "drink", "sleep", "walk", "run", "sit", "stand",
    "work", "play", "read", "write", "speak", "listen", "see", "know",
    "like", "love", "want", "need", "have", "give", "get", "make",
    "think", "feel", "call", "look", "find", "use", "tell", "ask",
    "buy", "pay", "learn", "study", "teach", "stop", "wait",
    "open", "close", "start", "finish", "bring", "take",

    # ── Extra everyday verbs ─────────────────────────────────────────────────
    "see", "meet", "try", "show", "put", "keep", "send", "receive",
    "return", "leave", "arrive", "stay", "move", "change", "check",
    "remember", "forget", "understand", "agree", "disagree", "choose",
    "decide", "allow", "repeat", "share", "save", "join", "lose",
    "win", "break", "fix", "carry", "pull", "push", "turn", "cut",
    "wash", "cook", "clean", "drive", "swim", "dance", "sing", "draw",
    "paint", "count", "measure", "type", "search", "download", "print",
    "cry", "laugh", "smile", "pray", "celebrate", "apologize",
    "borrow", "lend", "sell", "rent", "order", "reserve",

    # ── People & relationships ────────────────────────────────────────────────
    "man", "woman", "child", "baby", "mother", "father", "sister", "brother",
    "family", "friend", "doctor", "teacher", "student", "police",
    "husband", "wife", "son", "daughter", "grandfather", "grandmother",
    "uncle", "aunt", "cousin", "neighbor", "boss", "colleague",
    "nurse", "engineer", "lawyer", "farmer", "driver", "chef",
    "soldier", "priest", "king", "queen",

    # ── Places ───────────────────────────────────────────────────────────────
    "home", "school", "hospital", "market", "store", "office", "park",
    "library", "restaurant", "airport", "station", "city", "country",
    "road", "water", "bathroom",
    "village", "town", "state", "district", "temple", "church", "mosque",
    "bank", "hotel", "stadium", "farm", "forest", "beach", "mountain",
    "river", "lake", "ocean", "sea", "desert", "garden", "field",
    "factory", "museum", "theater", "mall", "gym", "clinic",
    "pharmacy", "police station", "fire station", "post office",

    # ── Body parts ───────────────────────────────────────────────────────────
    "head", "hair", "face", "eye", "ear", "nose", "mouth", "teeth",
    "tongue", "neck", "shoulder", "arm", "elbow", "hand", "finger",
    "thumb", "chest", "stomach", "back", "leg", "knee", "foot", "toe",
    "heart", "brain", "skin", "blood", "bone",

    # ── Food & drink ─────────────────────────────────────────────────────────
    "food", "water", "milk", "tea", "coffee", "juice", "rice", "bread",
    "egg", "meat", "fish", "chicken", "vegetable", "fruit", "apple",
    "banana", "orange", "mango", "potato", "onion", "tomato", "sugar",
    "salt", "oil", "butter", "cheese", "sweet", "cake", "chocolate",
    "soup", "lunch", "dinner", "breakfast", "snack", "restaurant",

    # ── Animals ──────────────────────────────────────────────────────────────
    "dog", "cat", "cow", "horse", "elephant", "lion", "tiger", "bear",
    "monkey", "bird", "fish", "snake", "rabbit", "sheep", "goat",
    "pig", "duck", "hen", "crow", "parrot",

    # ── Household items ───────────────────────────────────────────────────────
    "money", "phone", "car", "book", "door", "window",
    "table", "chair", "bed", "clothes", "medicine",
    "house", "room", "floor", "ceiling", "wall", "roof", "stairs",
    "kitchen", "toilet", "lamp", "fan", "television", "computer",
    "laptop", "bag", "key", "lock", "mirror", "clock", "calendar",
    "pen", "paper", "cup", "plate", "spoon", "knife", "fork", "glass",
    "box", "bottle", "bucket", "broom", "soap", "towel", "blanket",
    "pillow", "umbrella", "shoe", "hat", "shirt", "dress",

    # ── Time words ────────────────────────────────────────────────────────────
    "today", "tomorrow", "yesterday", "now", "later", "morning",
    "afternoon", "evening", "night", "week", "month", "year",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "hour", "minute", "second", "early", "late", "soon", "before",
    "after", "past", "future",

    # ── Numbers ──────────────────────────────────────────────────────────────
    "zero", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "twenty", "fifty",
    "hundred", "thousand", "million", "first", "second", "third",
    "half", "quarter",

    # ── Question words ────────────────────────────────────────────────────────
    "what", "where", "when", "who", "why", "how", "which",
    "how much", "how many", "how long", "how old",

    # ── Adjectives – descriptive ─────────────────────────────────────────────
    "good", "bad", "big", "small", "hot", "cold", "fast", "slow",
    "easy", "hard", "new", "old", "happy", "sad", "sick", "healthy",
    "hungry", "thirsty", "tired", "ready", "important", "beautiful",
    "clean", "dirty", "safe", "dangerous", "far", "near",
    "tall", "short", "long", "wide", "narrow", "heavy", "light",
    "strong", "weak", "rich", "poor", "full", "empty", "open", "closed",
    "correct", "wrong", "same", "different", "possible", "impossible",
    "free", "busy", "quiet", "loud", "dark", "bright", "fresh",
    "broken", "lost", "found", "special", "normal", "strange",
    "angry", "afraid", "surprised", "excited", "bored", "worried",
    "comfortable", "uncomfortable", "expensive", "cheap",

    # ── Modals / auxiliaries ─────────────────────────────────────────────────
    "can", "will", "must", "should", "could", "would",

    # ── Directions & positions ───────────────────────────────────────────────
    "left", "right", "up", "down", "here", "there", "inside", "outside",
    "north", "south", "east", "west", "front", "behind", "between",
    "next to", "above", "below", "far", "near", "straight",

    # ── Colors ───────────────────────────────────────────────────────────────
    "red", "blue", "green", "yellow", "black", "white",
    "orange", "purple", "brown", "pink", "grey",

    # ── Weather & nature ─────────────────────────────────────────────────────
    "sun", "moon", "star", "sky", "cloud", "rain", "wind", "storm",
    "snow", "fog", "hot", "cold", "weather", "temperature", "season",
    "summer", "winter", "spring", "autumn", "day", "night",
    "fire", "earth", "air", "tree", "flower", "grass", "plant", "seed",

    # ── Health & medical ─────────────────────────────────────────────────────
    "medicine", "hospital", "doctor", "nurse", "health", "pain",
    "fever", "cough", "cold", "headache", "accident", "emergency",
    "surgery", "injection", "tablet", "blood pressure", "diabetes",
    "allergy", "heart attack", "ambulance", "first aid", "pharmacy",

    # ── School & education ───────────────────────────────────────────────────
    "school", "class", "teacher", "student", "lesson", "homework",
    "exam", "question", "answer", "pass", "fail", "college",
    "university", "subject", "English", "mathematics", "science",
    "history", "geography", "certificate", "degree", "library",

    # ── Transport & travel ────────────────────────────────────────────────────
    "bus", "train", "car", "bike", "airplane", "ship", "taxi",
    "ticket", "journey", "travel", "map", "address", "direction",
    "passport", "visa", "hotel", "luggage", "station", "airport",

    # ── Sports & activities ──────────────────────────────────────────────────
    "sport", "football", "cricket", "basketball", "tennis", "swimming",
    "running", "cycling", "yoga", "exercise", "game", "team", "player",
    "win", "lose", "score", "match", "practice",

    # ── Technology ───────────────────────────────────────────────────────────
    "computer", "laptop", "phone", "internet", "email", "message",
    "video", "camera", "television", "radio", "battery", "charge",
    "password", "website", "application", "social media",

    # ── Feelings & emotions ──────────────────────────────────────────────────
    "love", "hate", "fear", "hope", "trust", "respect", "care",
    "emotion", "feeling", "happiness", "sadness", "anger", "peace",
    "dream", "wish", "believe",

    # ── Money & shopping ─────────────────────────────────────────────────────
    "money", "price", "cost", "pay", "buy", "sell", "market", "shop",
    "discount", "expensive", "cheap", "cash", "bank", "loan",

    # ── Common adverbs & connectors ──────────────────────────────────────────
    "more", "less", "enough", "again", "together", "alone", "always",
    "never", "sometimes", "very", "maybe", "already", "still",
    "also", "only", "just", "really", "too", "so", "then", "because",
    "but", "and", "or", "if", "when", "while", "although",
    "quickly", "slowly", "carefully", "clearly", "suddenly",

    # ── Speeches & Presentations ─────────────────────────────────────────────
    "audience", "topic", "presentation", "slide", "speech", "present",
    "introduce", "speaker", "microphone", "stage", "event", "host",
    "guest", "honor", "award", "appreciate", "attention", "conclusion",
    "summary", "discuss", "explain", "feedback", "lady", "gentleman", 
    "point", "thank", "vision", "goal", "strategy", "impact", "result",
    
    # ── Technical & Workshops ────────────────────────────────────────────────
    "technology", "workshop", "code", "program", "software", "hardware",
    "system", "network", "data", "database", "server", "client", "frontend",
    "backend", "bug", "error", "fix", "solution", "test", "deploy",
    "project", "team", "agile", "sprint", "meeting", "brainstorm",
    "innovate", "design", "architecture", "cloud", "artificial intelligence",
    "machine learning", "learning", "model", "train", "algorithm",
    "developer", "engineer", "user", "interface", "experience", "web",
    "app", "application", "mobile", "internet", "security", "privacy",
]

# Deduplicate while preserving order
_seen = set()
WORDS = []
for _w in EVERYDAY_WORDS:
    _key = _w.lower()
    if _key not in _seen:
        _seen.add(_key)
        WORDS.append(_w)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# The .pose format begins with 4 bytes encoding the float 0.3 (version/fps marker)
# followed by component metadata containing the string 'POSE_LANDMARKS'.
# Confirmed by inspecting both local dummy.pose and live API responses.
POSE_MAGIC = b"\xcd\xccL>"  # little-endian float32 0.3


def is_valid_pose(data: bytes) -> bool:
    """Check whether the raw bytes look like a .pose binary file."""
    if len(data) < 20:
        return False
    # Must start with the known float magic and contain POSE_LANDMARKS marker
    return data[:4] == POSE_MAGIC and b"POSE_LANDMARKS" in data[:64]


def load_existing_words(index_path: str) -> set:
    """Return the set of words already present in index.csv (lowercase)."""
    if not os.path.exists(index_path):
        return set()
    with open(index_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["words"].lower() for row in reader}


FIELDNAMES = ["path", "spoken_language", "signed_language", "start", "end", "words", "glosses", "priority"]


def append_to_index(index_path: str, row: dict):
    """Append a single row to index.csv."""
    file_exists = os.path.exists(index_path) and os.path.getsize(index_path) > 0
    with open(index_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def download_pose(word: str, signed: str) -> bytes | None:
    """
    Try to download a .pose file for `word` from the API.
    Returns raw bytes on success, None on failure.
    """
    params = {"text": word, "spoken": SPOKEN, "signed": signed}
    try:
        resp = requests.get(API_URL, params=params, timeout=30)
    except requests.RequestException as e:
        print(f"    ⚠ Network error for '{word}' ({signed}): {e}")
        return None

    if resp.status_code != 200:
        print(f"    ✗ HTTP {resp.status_code} for '{word}' ({signed})")
        return None

    data = resp.content
    ct = resp.headers.get("Content-Type", "")
    print(f"    Content-Type: {ct}  |  Size: {len(data)} bytes")

    if not is_valid_pose(data):
        print(f"    ✗ Response is NOT a valid .pose file. First 16 bytes: {data[:16]!r}")
        return None

    print(f"    ✓ Valid .pose file ({len(data):,} bytes)")
    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    existing_words = load_existing_words(INDEX_CSV)
    print(f"📖 Existing lexicon has {len(existing_words)} word(s).")
    print(f"📋 Words to process: {len(WORDS)}\n")

    downloaded = 0
    skipped = 0
    failed = 0

    for i, word in enumerate(WORDS, 1):
        word_lower = word.lower()
        print(f"[{i:3}/{len(WORDS)}] '{word}'", end="")

        if word_lower in existing_words:
            print("  → already in lexicon, skipping.")
            skipped += 1
            continue

        print()  # newline before per-lang output

        # Try INS first, then ASL as fallback
        pose_data = None
        signed_lang = None

        for lang in ("ins", "ase"):
            print(f"    Trying signed={lang}...")
            pose_data = download_pose(word, lang)
            if pose_data is not None:
                signed_lang = lang
                break
            time.sleep(REQUEST_DELAY)

        if pose_data is None:
            print(f"    ✗ FAILED for '{word}' — skipping.\n")
            failed += 1
            time.sleep(REQUEST_DELAY)
            continue

        # Save pose file
        lang_dir = os.path.join(LEXICON_DIR, signed_lang)
        os.makedirs(lang_dir, exist_ok=True)
        filename = f"{word_lower.replace(' ', '_')}.pose"
        filepath = os.path.join(lang_dir, filename)

        with open(filepath, "wb") as f:
            f.write(pose_data)

        # Register in index.csv (word → gloss e.g. "thank you" → "THANK_YOU")
        relative_path = f"{signed_lang}/{filename}"
        gloss = word.upper().replace(" ", "_")
        row = {
            "path": relative_path,
            "spoken_language": SPOKEN,
            "signed_language": signed_lang,
            "start": 0,
            "end": 0,
            "words": word_lower,
            "glosses": gloss,
            "priority": 0,
        }
        append_to_index(INDEX_CSV, row)
        existing_words.add(word_lower)

        print(f"    ✅ Saved → {relative_path}\n")
        downloaded += 1
        time.sleep(REQUEST_DELAY)

    print("=" * 60)
    print(f"✅ Downloaded : {downloaded}")
    print(f"⏭  Skipped   : {skipped}  (already present)")
    print(f"❌ Failed     : {failed}")
    print(f"📦 Lexicon CSV: {os.path.abspath(INDEX_CSV)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
optimize_content_combined_fullwords.py

Same behavior as before but variable names use full, descriptive words (no short abbreviations).
This improves readability and makes the code easier to understand.

Run:
    python optimize_content_combined_fullwords.py
"""

import os
import re
import shutil
from pathlib import Path
from collections import Counter

import pandas as pd
from textblob import TextBlob

# -------------------------
# Configuration
# -------------------------
CSV_FILE = "generated_content1.csv"
BACKUP_SUFFIX = ".bak"
TRENDING_KEYWORDS = ["AI", "Automation", "Digital", "Marketing", "Innovation", "Technology"]
TRENDING_HASHTAGS = ["#AI", "#Marketing", "#Innovation", "#Digital", "#Automation", "#Tech"]
MAX_HASHTAGS = 3
MIN_WORDS = 50
MAX_WORDS = 100
APPLY_GRAMMAR_CORRECTION = True  # set False if TextBlob.correct() is too aggressive

# -------------------------
# Helper functions
# -------------------------

def ensure_backup(path: Path):
    """Create a backup copy of the CSV before overwriting."""
    backup = path.with_suffix(path.suffix + BACKUP_SUFFIX)
    try:
        shutil.copy2(path, backup)
        print(f"🔁 Backup created: {backup}")
    except Exception as e:
        print(f"⚠️  Could not create backup: {e} — continuing without backup.")

def clean_text(text: str) -> str:
    """Basic cleanup: collapse whitespace and strip."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text).strip()

def analyze_sentiment(text: str):
    """Return sentiment polarity (-1..1) and a simple label."""
    try:
        polarity = round(TextBlob(text).sentiment.polarity, 3)
    except Exception:
        polarity = 0.0
    if polarity > 0.3:
        label = "Positive"
    elif polarity >= 0:
        label = "Neutral"
    else:
        label = "Negative"
    return polarity, label

def calculate_readability(text: str):
    """Simple readability: based on average sentence length."""
    words = text.split()
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    avg_sentence_len = len(words) / max(len(sentences), 1)
    if avg_sentence_len <= 12:
        return "Easy"
    if avg_sentence_len <= 20:
        return "Medium"
    return "Complex"

def extract_hashtags(text: str):
    """Return list of hashtags like ['#AI'].""" 
    if not isinstance(text, str):
        return []
    return re.findall(r"#\w+", text)

def calculate_trend_relevance(text: str):
    """Fraction of trending keywords present (0..1)."""
    if not text:
        return 0.0
    matches = sum(1 for kw in TRENDING_KEYWORDS if kw.lower() in text.lower())
    return round(matches / max(1, len(TRENDING_KEYWORDS)), 2)

def calculate_engagement_score(text: str):
    """
    Heuristic engagement score:
      - word count * 0.1
      - hashtag count * 5
      - sentiment * 10
    """
    if not text:
        return 0.0
    word_count = len(text.split())
    hashtags_count = len(extract_hashtags(text))
    sentiment_value, _ = analyze_sentiment(text)
    score = (word_count * 0.1) + (hashtags_count * 5.0) + (sentiment_value * 10.0)
    return round(score, 2)

def contains_call_to_action(text: str):
    """Detect presence of common CTAs."""
    ctas = ["follow", "subscribe", "learn more", "click", "visit", "try", "join", "buy", "shop"]
    return any(phrase in text.lower() for phrase in ctas)

# -------------------------
# Optimization rules
# -------------------------

def limit_hashtags(text: str, max_tags: int = MAX_HASHTAGS) -> str:
    """Keep at most max_tags hashtags; preserve first occurrences."""
    tags = extract_hashtags(text)
    if len(tags) <= max_tags:
        return text
    kept = tags[:max_tags]
    text_no_tags = re.sub(r"#\w+\b", "", text)
    sep = " " if text_no_tags.endswith((".", "!", "?")) else " "
    return (text_no_tags.strip() + sep + " ".join(kept)).strip()

def ensure_hashtags_from_keywords(text: str, keywords=None, max_tags=MAX_HASHTAGS):
    """Add up to max_tags hashtags derived from keywords if not present."""
    if keywords is None:
        keywords = TRENDING_KEYWORDS
    existing_lower = [t.lower() for t in extract_hashtags(text)]
    hashtags_to_add = []
    for keyword in keywords:
        tag = "#" + re.sub(r"\W+", "", keyword)
        if tag.lower() not in existing_lower and tag.lower() not in [h.lower() for h in hashtags_to_add]:
            hashtags_to_add.append(tag)
        if len(hashtags_to_add) >= max_tags:
            break
    if not hashtags_to_add:
        return text
    sep = " " if text.endswith((".", "!", "?")) else " · "
    return (text + sep + " ".join(hashtags_to_add)).strip()

def truncate_or_pad_words(text: str, min_words=MIN_WORDS, max_words=MAX_WORDS):
    """Truncate if too long; pad with hashtags if too short."""
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    if len(words) < min_words:
        padding = " " + " ".join(TRENDING_HASHTAGS[:2])
        return (text + padding).strip()
    return text

def grammar_correction(text: str, apply_correction=APPLY_GRAMMAR_CORRECTION):
    """Use TextBlob.correct() optionally (may be slow/aggressive)."""
    if not apply_correction or not text:
        return text
    try:
        return str(TextBlob(text).correct())
    except Exception:
        return text

def optimize_content(text: str):
    """
    Full optimization pipeline (rule-based):
      1. Clean text
      2. Optional grammar correction
      3. Ensure CTA
      4. Limit hashtags and/or add trending hashtags
      5. Truncate/pad length
      6. Final cleanup
    """
    if not isinstance(text, str):
        return ""

    output_text = clean_text(text)

    # 1. Grammar correction (optional)
    output_text = grammar_correction(output_text)

    # 2. Add CTA if missing
    if not contains_call_to_action(output_text):
        output_text += " Learn more and join the movement!"

    # 3. Limit existing hashtags to MAX_HASHTAGS
    output_text = limit_hashtags(output_text, MAX_HASHTAGS)

    # 4. If fewer hashtags than desired, append trending ones (up to MAX_HASHTAGS)
    current_tags = extract_hashtags(output_text)
    if len(current_tags) < MAX_HASHTAGS:
        output_text = ensure_hashtags_from_keywords(output_text, keywords=TRENDING_KEYWORDS, max_tags=MAX_HASHTAGS - len(current_tags))

    # 5. Truncate or pad to desired word range
    output_text = truncate_or_pad_words(output_text, MIN_WORDS, MAX_WORDS)

    # 6. Capitalize first character and collapse extra spaces
    output_text = output_text.strip()
    if output_text:
        output_text = output_text[0].upper() + output_text[1:]
    output_text = re.sub(r"\s+", " ", output_text)

    return output_text

# -------------------------
# Main CSV processing
# -------------------------

def optimize_csv(filename=CSV_FILE):
    """Load CSV, compute analytics, optimize text, and save (with backup)."""
    path = Path(filename)
    if not path.exists():
        print(f"❌ File '{filename}' not found. Make sure generated content exists.")
        return

    # Create a backup
    ensure_backup(path)

    # Read CSV (use python engine to be a bit more tolerant of messy rows)
    try:
        df = pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return

    # Validate expected columns and create placeholders if missing
    if "Generated_Content" not in df.columns:
        print("⚠️  Column 'Generated_Content' not found. Creating empty column.")
        df["Generated_Content"] = ""

    # Keep Topic and Platform if present else add default placeholders
    if "Topic" not in df.columns:
        df["Topic"] = "General"
    if "Platform" not in df.columns:
        df["Platform"] = "unknown"

    # -------------------------
    # Prepare descriptive result containers (full words)
    # -------------------------
    cleaned_contents = []
    optimized_contents = []
    original_sentiment_scores = []
    original_sentiment_labels = []
    optimized_sentiment_scores = []
    optimized_sentiment_labels = []
    readability_levels = []
    trend_relevance_scores = []
    engagement_estimates = []
    hashtag_counts = []
    contains_call_to_action_flags = []

    # Process rows
    for idx, row in df.iterrows():
        original_text = str(row.get("Generated_Content", "") or "")
        topic = row.get("Topic", "General")
        platform = row.get("Platform", "unknown")

        cleaned_text_value = clean_text(original_text)
        original_sentiment_score, original_sentiment_label = analyze_sentiment(cleaned_text_value)
        readability_label = calculate_readability(cleaned_text_value)
        hashtags_in_text = extract_hashtags(cleaned_text_value)
        trend_score_value = calculate_trend_relevance(cleaned_text_value)
        engagement_score_value = calculate_engagement_score(cleaned_text_value)
        cta_present_flag = contains_call_to_action(cleaned_text_value)

        # Optimize the content
        optimized_text_value = optimize_content(cleaned_text_value)
        optimized_sentiment_score_value, optimized_sentiment_label_value = analyze_sentiment(optimized_text_value)

        # Append to descriptive lists
        cleaned_contents.append(cleaned_text_value)
        optimized_contents.append(optimized_text_value)
        original_sentiment_scores.append(original_sentiment_score)
        original_sentiment_labels.append(original_sentiment_label)
        optimized_sentiment_scores.append(optimized_sentiment_score_value)
        optimized_sentiment_labels.append(optimized_sentiment_label_value)
        readability_levels.append(readability_label)
        trend_relevance_scores.append(trend_score_value)
        engagement_estimates.append(engagement_score_value)
        hashtag_counts.append(len(hashtags_in_text))
        contains_call_to_action_flags.append(cta_present_flag)

        print(f"Processed row {idx+1}: Topic='{topic}' Platform='{platform}'")

    # Add computed columns to DataFrame (overwriting / adding)
    df["Cleaned_Content"] = cleaned_contents
    df["Original_Sentiment_Score"] = original_sentiment_scores
    df["Original_Sentiment_Label"] = original_sentiment_labels
    df["Optimized_Content"] = optimized_contents
    df["Optimized_Sentiment_Score"] = optimized_sentiment_scores
    df["Optimized_Sentiment_Label"] = optimized_sentiment_labels
    df["Readability"] = readability_levels
    df["Trend_Relevance"] = trend_relevance_scores
    df["Engagement_Score"] = engagement_estimates
    df["Hashtag_Count"] = hashtag_counts
    df["Contains_CTA"] = contains_call_to_action_flags

    # Save back to CSV
    try:
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"\n✅ Optimization completed. Results saved to '{filename}'. Backup saved with suffix '{BACKUP_SUFFIX}'.")
    except Exception as e:
        print(f"❌ Failed to save CSV: {e}")

# -------------------------
# Run when executed directly
# -------------------------
if __name__ == "__main__":
    optimize_csv()

"""
Milestone 3: Sentiment Analysis + Performance Metrics Hub + A/B Testing
- Uses ONE CSV: milestone3_metrics.csv
- Links to Milestone 1–2 sheet via post_id (you choose the ID)
"""

import os
import csv
from datetime import datetime

# ================================
# CONFIG
# ================================

METRICS_FILE = "milestone3_metrics.csv"   # <-- NEW FILE, SAFE FOR M3
SLACK_WEBHOOK_ENV = "SLACK_WEBHOOK_URL"  # put your webhook in env if needed

POSITIVE_WORDS = {
    "great", "good", "love", "amazing", "excellent",
    "nice", "wow", "super", "fantastic", "awesome", "happy"
}

NEGATIVE_WORDS = {
    "bad", "hate", "poor", "terrible", "worst",
    "boring", "awful", "angry", "sad", "disappointing"
}

# ================================
# CSV SETUP (Milestone 3 file)
# ================================

def init_metrics_file_if_needed():
    """Create milestone3_metrics.csv with proper header if it doesn't exist."""
    if not os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "post_id",          # link to Milestone 2 row
                "variant",          # A / B (or single)
                "text",             # content/comment used for sentiment
                "sentiment_score",
                "sentiment_label",
                "impressions",
                "clicks",
                "likes",
                "comments",
                "ctr",
                "engagement_rate",
                "ab_test_id",       # campaign_01, etc.
                "ab_winner",        # A/B/tie
                "ab_reason"         # higher CTR / higher engagement
            ])

def append_metrics_row(post_id, variant, text,
                       impressions, clicks, likes, comments,
                       sentiment_score, sentiment_label,
                       ab_test_id=None, ab_winner=None, ab_reason=None):
    """Append one row of metrics + sentiment to the CSV."""
    init_metrics_file_if_needed()

    impressions = max(1, impressions)
    ctr = clicks / impressions
    eng = (likes + comments) / impressions
    ts = datetime.utcnow().isoformat()

    with open(METRICS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            ts,
            post_id,
            variant,
            text,
            round(sentiment_score, 4),
            sentiment_label,
            impressions,
            clicks,
            likes,
            comments,
            round(ctr, 4),
            round(eng, 4),
            ab_test_id or "",
            ab_winner or "",
            ab_reason or ""
        ])

    return ctr, eng

# ================================
# SENTIMENT ANALYSIS (automatic)
# ================================

def analyze_sentiment(text: str):
    text = (text or "").lower()
    tokens = text.split()

    if not tokens:
        return 0.0, "neutral"

    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)

    if pos == 0 and neg == 0:
        return 0.0, "neutral"

    score = (pos - neg) / (pos + neg)

    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"

    return score, label

# ================================
# SLACK ALERTS (optional)
# ================================

def send_slack_message(text: str):
    webhook = os.getenv(SLACK_WEBHOOK_ENV)

    if not webhook:
        print("\n[SLACK DISABLED] Would send:\n" + text)
        return

    import json
    from urllib import request

    data = json.dumps({"text": text}).encode("utf-8")
    req = request.Request(webhook, data=data,
                          headers={"Content-Type": "application/json"})

    try:
        request.urlopen(req)
        print("[Slack] Sent!")
    except Exception as e:
        print("[Slack Error]", e)

def maybe_send_alert(post_id, variant, ctr, eng, sentiment):
    HIGH_CTR = 0.10
    HIGH_ENG = 0.15
    LOW_CTR = 0.02

    if ctr >= HIGH_CTR or eng >= HIGH_ENG:
        msg = (
            f"🔥 High Performing Post!\n"
            f"Post: {post_id} ({variant})\n"
            f"CTR={ctr*100:.2f}% | ENG={eng*100:.2f}%\n"
            f"Sentiment={sentiment:.2f}"
        )
        send_slack_message(msg)

    elif ctr <= LOW_CTR and sentiment < 0:
        msg = (
            f"⚠️ Low Performance + Negative Sentiment\n"
            f"Post: {post_id} ({variant})\n"
            f"CTR={ctr*100:.2f}% | Sentiment={sentiment:.2f}"
        )
        send_slack_message(msg)

# ================================
# A/B TESTING
# ================================

def evaluate_ab_test(ab_test_id, A, B):
    """A and B are dicts with impressions, clicks, likes, comments."""
    def ctr(x):
        return x["clicks"] / max(1, x["impressions"])

    def eng(x):
        return (x["likes"] + x["comments"]) / max(1, x["impressions"])

    a_ctr, b_ctr = ctr(A), ctr(B)
    a_eng, b_eng = eng(A), eng(B)

    if a_ctr > b_ctr:
        winner = "A"
        reason = "higher CTR"
    elif b_ctr > a_ctr:
        winner = "B"
        reason = "higher CTR"
    else:
        if a_eng > b_eng:
            winner = "A"
            reason = "higher engagement"
        elif b_eng > a_eng:
            winner = "B"
            reason = "higher engagement"
        else:
            winner = "tie"
            reason = "similar performance"

    explanation = (
        f"A/B Test ({ab_test_id}):\n"
        f"A: CTR={a_ctr*100:.2f}%, ENG={a_eng*100:.2f}%\n"
        f"B: CTR={b_ctr*100:.2f}%, ENG={b_eng*100:.2f}%\n"
        f"Winner: {winner} ({reason})"
    )

    return winner, reason, explanation, a_ctr, a_eng, b_ctr, b_eng

# ================================
# REPORT
# ================================

def generate_report():
    if not os.path.exists(METRICS_FILE):
        print("No metrics yet.")
        return

    total = 0
    sum_ctr = 0.0
    sum_eng = 0.0

    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ctr = float(row["ctr"])
                eng = float(row["engagement_rate"])
            except (ValueError, KeyError):
                continue
            sum_ctr += ctr
            sum_eng += eng
            total += 1

    if total == 0:
        print("File empty or no valid rows.")
        return

    avg_ctr = sum_ctr / total
    avg_eng = sum_eng / total

    print("\n=== PERFORMANCE REPORT ===")
    print("Total Logged Posts:", total)
    print(f"Average CTR: {avg_ctr*100:.2f}%")
    print(f"Average Engagement: {avg_eng*100:.2f}%")
    print("========================================\n")

# ================================
# MENU (what you run)
# ================================

def menu():
    while True:
        print("\n=== Milestone 3 Menu ===")
        print("1. Analyze Sentiment (only)")
        print("2. Log Post Metrics + Sentiment")
        print("3. Run A/B Test + Log")
        print("4. Report")
        print("5. Exit")

        ch = input("Choose (1-5): ").strip()

        if ch == "1":
            text = input("Enter comment or content text:\n> ")
            score, label = analyze_sentiment(text)
            print(f"Sentiment Score={score:.2f}, Label={label}")

            post_id = input("Post ID to link (optional, e.g. topic or row id): ") or ""
            variant = input("Variant (A/B or single): ") or ""

            # store with zero metrics
            append_metrics_row(
                post_id=post_id,
                variant=variant,
                text=text,
                impressions=0,
                clicks=0,
                likes=0,
                comments=0,
                sentiment_score=score,
                sentiment_label=label
            )
            print(f"[CSV] Sentiment-only row saved to {METRICS_FILE}")

        elif ch == "2":
            post_id = input("Post ID (match Milestone 2 row): ") or "post_1"
            variant = input("Variant (A/B or single): ") or "A"
            text = input("Post text / caption (for sentiment):\n> ")

            imp = int(input("Impressions: ") or "1000")
            clk = int(input("Clicks: ") or "100")
            lik = int(input("Likes: ") or "150")
            com = int(input("Comments: ") or "20")

            score, label = analyze_sentiment(text)
            print(f"Auto Sentiment → Score={score:.2f}, Label={label}")

            ctr, eng = append_metrics_row(
                post_id, variant, text,
                imp, clk, lik, com,
                score, label
            )
            print(f"Saved! CTR={ctr*100:.2f}%, ENG={eng*100:.2f}%")
            maybe_send_alert(post_id, variant, ctr, eng, score)

        elif ch == "3":
            ab_id = input("A/B Test ID (e.g. campaign_01): ") or "campaign_01"
            base_post = input("Base Post ID to link (optional): ") or "post_1"

            print("\n--- Variant A ---")
            text_a = input("Text for A (optional, for sentiment):\n> ")
            A = {
                "impressions": int(input("Impressions A: ") or "1000"),
                "clicks": int(input("Clicks A: ") or "120"),
                "likes": int(input("Likes A: ") or "180"),
                "comments": int(input("Comments A: ") or "25")
            }

            print("\n--- Variant B ---")
            text_b = input("Text for B (optional, for sentiment):\n> ")
            B = {
                "impressions": int(input("Impressions B: ") or "1000"),
                "clicks": int(input("Clicks B: ") or "110"),
                "likes": int(input("Likes B: ") or "160"),
                "comments": int(input("Comments B: ") or "30")
            }

            winner, reason, explanation, a_ctr, a_eng, b_ctr, b_eng = evaluate_ab_test(ab_id, A, B)
            print("\n" + explanation)

            # sentiment of A & B texts (optional)
            score_a, label_a = analyze_sentiment(text_a) if text_a.strip() else (0.0, "neutral")
            score_b, label_b = analyze_sentiment(text_b) if text_b.strip() else (0.0, "neutral")

            # log A row
            append_metrics_row(
                post_id=base_post,
                variant="A",
                text=text_a,
                impressions=A["impressions"],
                clicks=A["clicks"],
                likes=A["likes"],
                comments=A["comments"],
                sentiment_score=score_a,
                sentiment_label=label_a,
                ab_test_id=ab_id,
                ab_winner=winner if winner == "A" else "",
                ab_reason=reason if winner == "A" else ""
            )

            # log B row
            append_metrics_row(
                post_id=base_post,
                variant="B",
                text=text_b,
                impressions=B["impressions"],
                clicks=B["clicks"],
                likes=B["likes"],
                comments=B["comments"],
                sentiment_score=score_b,
                sentiment_label=label_b,
                ab_test_id=ab_id,
                ab_winner=winner if winner == "B" else "",
                ab_reason=reason if winner == "B" else ""
            )

            print(f"[CSV] A/B test rows saved to {METRICS_FILE}")

        elif ch == "4":
            generate_report()

        elif ch == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid choice!")

# ================================
# RUN
# ================================

if __name__ == "__main__":
    print("Milestone 3 – Sentiment + Metrics + A/B Testing (milestone3_metrics.csv)")
    menu() 
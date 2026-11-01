from datetime import datetime
from collections import Counter

class MathEngine:
    def __init__(self):
        self.name = "Math & Behavior Engine"

    def analyze(self, raw_data: dict) -> dict:
        """Processes raw profile data to extract engagement and temporal metrics."""
        if not raw_data or "profile" not in raw_data or not raw_data.get("posts"):
            return {"error": "Not enough data to calculate metrics."}

        profile = raw_data["profile"]
        posts = raw_data["posts"]
        followers = profile.get("followers", 0)

        # 1. Format Strategy (Photos vs Reels vs Carousels)
        format_counts = Counter(post.get("typename") for post in posts)
        total_posts = len(posts)

        # 2. Engagement Metrics
        total_likes = sum(post.get("likes", 0) for post in posts)
        total_comments = sum(post.get("comments_count", 0) for post in posts)
        
        avg_likes = total_likes / total_posts
        avg_comments = total_comments / total_posts
        
        # ER% Formula: (Avg Likes + Avg Comments) / Total Followers * 100
        er_pct = 0.0
        if followers > 0:
            er_pct = round(((avg_likes + avg_comments) / followers) * 100, 2)
        
        # Find Viral Outliers (Posts with 1.5x more likes than their average)
        outliers = [
            post.get("shortcode") for post in posts 
            if post.get("likes", 0) > (avg_likes * 1.5)
        ]
        
        # 3. Temporal Rhythm (Chronotype based on UTC post timestamps)
        hours = []
        for post in posts:
            # Handle ISO string from our Data Contract
            dt_str = post.get("timestamp_utc", "").replace("Z", "")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str)
                    hours.append(dt.hour)
                except ValueError:
                    continue
        
        chronotype = "Unknown"
        if hours:
            # Calculate average posting hour
            avg_hour = sum(hours) / len(hours)
            if 5 <= avg_hour < 12:
                chronotype = "Early Bird (Morning Poster)"
            elif 12 <= avg_hour < 18:
                chronotype = "Afternoon Active"
            elif 18 <= avg_hour < 23:
                chronotype = "Evening Poster"
            else:
                chronotype = "Night Owl (Late Night)"

        # Return the structured intelligence payload
        return {
            "engagement_rate_pct": er_pct,
            "avg_likes_per_post": round(avg_likes, 1),
            "format_strategy": {
                "photo_pct": round(format_counts.get("GraphImage", 0) / total_posts * 100, 1),
                "carousel_pct": round(format_counts.get("GraphSidecar", 0) / total_posts * 100, 1),
                "reels_pct": round(format_counts.get("GraphVideo", 0) / total_posts * 100, 1)
            },
            "viral_outlier_count": len(outliers),
            "chronotype": chronotype
        }

# --- Quick Local Test ---
if __name__ == "__main__":
    import json
    import os
    
    # Load the raw_profile.json you generated earlier with fetcher.py
    if os.path.exists("raw_profile.json"):
        with open("raw_profile.json", "r", encoding="utf-8") as f:
            sample_data = json.load(f)
            
        engine = MathEngine()
        result = engine.analyze(sample_data)
        
        print("\n[*] Math Engine Analysis Complete:")
        print(json.dumps(result, indent=2))
    else:
        print("[!] raw_profile.json not found. Run fetcher.py first to get sample data.")

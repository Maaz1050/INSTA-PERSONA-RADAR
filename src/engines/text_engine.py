import re
import emoji
from collections import Counter

class TextEngine:
    def __init__(self):
        self.name = "Text & Graph Engine"

    def decode_bio_emojis(self, bio: str) -> str:
        """Converts emojis in the bio to readable text (e.g., 🎸 -> :guitar:)."""
        if not bio:
            return "No bio"
        return emoji.demojize(bio)

    def extract_graph(self, posts: list) -> dict:
        """Extracts top hashtags and @mentions to build a social network graph."""
        hashtags = []
        mentions = []
        
        for post in posts:
            caption = post.get("raw_caption", "")
            if caption:
                # Regex to find all #hashtags
                tags = re.findall(r"#(\w+)", caption.lower())
                hashtags.extend(tags)
                
                # Regex to find all @mentions in text
                users = re.findall(r"@([\w\.]+)", caption.lower())
                mentions.extend(users)
                
            # Add explicit tagged users from the Instagram metadata
            tagged = post.get("tagged_users", [])
            if tagged:
                mentions.extend([u.lstrip("@").lower() for u in tagged])

        return {
            "top_hashtags": [tag for tag, count in Counter(hashtags).most_common(10)],
            "top_mentions": [user for user, count in Counter(mentions).most_common(5)]
        }

    def analyze(self, raw_data: dict) -> dict:
        """Processes text metadata to build a linguistic and social profile."""
        if not raw_data or "profile" not in raw_data:
            return {"error": "No profile data to analyze."}

        profile = raw_data["profile"]
        posts = raw_data.get("posts", [])

        decoded_bio = self.decode_bio_emojis(profile.get("raw_bio", ""))
        social_graph = self.extract_graph(posts)

        return {
            "decoded_bio": decoded_bio,
            "top_hashtags": social_graph["top_hashtags"],
            "top_collaborators": social_graph["top_mentions"]
        }


import os
import instaloader
import requests

class InstagramIngestor:
    def __init__(self):
        self.name = "Ingestion Engine"
        # Initialize Instaloader in anonymous/public mode
        self.L = instaloader.Instaloader(quiet=True)
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_profile(self, username: str) -> dict:
        """Pulls public profile metadata and recent posts."""
        print(f"[*] Ingesting profile: @{username}")
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            
            # The Data Contract required by downstream engines
            data = {
                "profile": {
                    "username": profile.username,
                    "full_name": profile.full_name,
                    "raw_bio": profile.biography,
                    "followers": profile.followers,
                    "business_category": getattr(profile, 'business_category_name', 'Unknown')
                },
                "posts": []
            }

            # Scrape only the 10 most recent posts to avoid Meta rate limits
            for i, post in enumerate(profile.get_posts()):
                if i >= 10:
                    break
                
                # Download thumbnail manually for the Vision Engine
                img_path = os.path.join(self.cache_dir, f"{username}_{post.shortcode}.jpg")
                if not os.path.exists(img_path):
                    response = requests.get(post.url)
                    if response.status_code == 200:
                        with open(img_path, "wb") as f:
                            f.write(response.content)

                post_data = {
                    "shortcode": post.shortcode,
                    "typename": post.typename, # GraphImage, GraphVideo, GraphSidecar
                    "likes": post.likes,
                    "comments_count": post.comments,
                    "timestamp_utc": post.date_utc.isoformat() + "Z",
                    "raw_caption": post.caption if post.caption else "",
                    "tagged_users": post.tagged_users,
                    "local_thumbnail_path": img_path
                }
                data["posts"].append(post_data)

            return data

        except Exception as e:
            print(f"[!] Error fetching @{username}: {e}")
            return {}

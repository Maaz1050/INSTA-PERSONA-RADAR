import os
import requests

class InstagramIngestor:
    def __init__(self):
        self.name = "Ingestion Engine"
        self.access_token = os.environ.get("META_ACCESS_TOKEN")
        self.ig_user_id = os.environ.get("META_IG_USER_ID")
        self.base_url = "https://graph.facebook.com/v18.0"
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_profile(self, username: str) -> dict:
        """Pulls public profile metadata and recent posts via Meta Graph API."""
        print(f"[*] Ingesting profile via Graph API: @{username}")
        
        if not self.access_token or not self.ig_user_id:
            print("[!] Missing Meta API credentials (META_ACCESS_TOKEN or META_IG_USER_ID).")
            return {}

        # Construct the Business Discovery query
        endpoint = f"{self.base_url}/{self.ig_user_id}"
        
        # Requests username, biography, followers, and up to 10 recent media posts with metrics
        fields = (
            f"business_discovery.username({username}) {{"
            f"username,name,biography,followers_count,profile_picture_url,"
            f"media.limit(10) {{"
            f"id,caption,media_type,media_url,timestamp,like_count,comments_count,permalink"
            f"}} }}"
        )
        
        params = {
            "fields": fields,
            "access_token": self.access_token
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            json_response = response.json()
            raw_data = json_response.get("business_discovery", {})
            
            if not raw_data:
                print(f"[!] No business discovery data returned for @{username}. Ensure it is a Business/Creator account.")
                return {}

            # Map the Graph API response to your downstream Data Contract
            data = {
                "profile": {
                    "username": raw_data.get("username"),
                    "full_name": raw_data.get("name", "Unknown"),
                    "raw_bio": raw_data.get("biography", ""),
                    "followers": raw_data.get("followers_count", 0),
                    "business_category": "Business/Creator"
                },
                "posts": []
            }

            # Process the recent posts edge
            media_edges = raw_data.get("media", {}).get("data", [])
            for post in media_edges:
                shortcode = post.get("id")
                media_type = post.get("media_type") # IMAGE, VIDEO, CAROUSEL_ALBUM
                media_url = post.get("media_url")
                
                # Download thumbnail/media locally for the Vision Engine if URL is available
                img_path = os.path.join(self.cache_dir, f"{username}_{shortcode}.jpg")
                if media_url and not os.path.exists(img_path):
                    try:
                        img_res = requests.get(media_url, timeout=10)
                        if img_res.status_code == 200:
                            with open(img_path, "wb") as f:
                                f.write(img_res.content)
                    except Exception as img_err:
                        print(f"[!] Could not download thumbnail for post {shortcode}: {img_err}")

                post_data = {
                    "shortcode": shortcode,
                    "typename": media_type,
                    "likes": post.get("like_count", 0),
                    "comments_count": post.get("comments_count", 0),
                    "timestamp_utc": post.get("timestamp", ""),
                    "raw_caption": post.get("caption", ""),
                    "tagged_users": [], # Graph API public discovery doesn't expose tagged users directly
                    "local_thumbnail_path": img_path if os.path.exists(img_path) else None
                }
                data["posts"].append(post_data)

            return data

        except requests.exceptions.HTTPError as e:
            print(f"[!] HTTP Error fetching @{username}: {e.response.text}")
            return {}
        except Exception as e:
            print(f"[!] Error fetching @{username}: {e}")
            return {}

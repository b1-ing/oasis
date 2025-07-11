import json
from datetime import datetime
from collections import defaultdict

# Load posts
with open("reddit_structured_posts.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

# Step 1: Assign consistent author_id to each unique author
author_to_id = {}
next_author_id = 0

for post in posts:
    author = post["author"]
    if author not in author_to_id:
        author_to_id[author] = next_author_id
        next_author_id += 1
    post["author_id"] = author_to_id[author]

# Step 2: Compute timestep (2-hour interval from earliest post)
timestamps = [
    datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))
    for post in posts
]
earliest_time = min(timestamps)

for post in posts:
    post_time = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))
    delta_seconds = (post_time - earliest_time).total_seconds()
    post["timestep"] = int(delta_seconds // (24 * 3600))  # 2 hours = 7200 seconds

# Save result
with open("processed_posts.json", "w", encoding="utf-8") as f:
    json.dump(posts, f, indent=2, ensure_ascii=False)

print("✅ Processed and saved to processed_posts.json")

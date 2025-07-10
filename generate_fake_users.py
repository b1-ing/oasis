import json
import random
import argparse
from faker import Faker

fake = Faker()

def generate_fake_users(n):
    users = []


    for i in range(n):
        username = fake.user_name()
        location = "Singapore"
        interest = random.choice([
            "technology", "news", "politics", "sports",
            "entertainment", "science", "culture", "memes"
        ])
        profile = {
            "username": username,
            "country": location,
            "realname": "",
            "bio": "",
            "persona": "",
            "age": random.randint(12,70),
            "gender": "",
            "mbti": "",
            "profession": "",
            "interested_topics": ["photography"]
        }
        users.append(profile)

    return users

def main():
    parser = argparse.ArgumentParser(description="Generate N fake users.")
    parser.add_argument("-n", "--num", type=int, required=True, help="Number of users to generate")
    parser.add_argument("-o", "--output", default="fake_users.json", help="Output JSON file name")
    args = parser.parse_args()

    users = generate_fake_users(args.num)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

    print(f"✅ Generated {args.num} fake users → {args.output}")

if __name__ == "__main__":
    main()

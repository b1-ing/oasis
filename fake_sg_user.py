import json
import random
import csv
import random

# Generate 30 fake usernames
usernames = [
    "singaporean_vibes", "techy_tiger", "islandfoodie", "urbanorchid", "merlion_moves",
    "citylights_sg", "sundaysatmarina", "hdbhustler", "kopikulture", "mrt_muse",
    "sentosasunshine", "eastcoastdreamer", "red_dot_runner", "singapopstar", "sgcloudwatcher",
    "orchardoracle", "bukitbiker", "circuitbreakerbaby", "jurongjungle", "nasilemaklife",
    "hawkerhunter", "tigerbeerboy", "rafflesroamer", "bishanbuddy", "pandanpilot",
    "toapayohtraveller", "tehtarikdreams", "rochorrambler", "littleindiatrail", "sghistorynerd"
]

# Construct the dataset
fake_users = [
    {
        "username": uname,
        "country": "Singapore",
        "realname": "",
        "bio": "",
        "persona": "",
        "age": random.randint(12,70),
        "gender": "",

        "mbti": "",
        "profession": "",
        "interested_topics": []
    }
    for uname in usernames
]

# Convert to JSON string
json_output = json.dumps(fake_users, indent=2)
json_output[:1000]  # Show a preview of the JSON output
file_name="fake_users.json"
try:
    with open(file_name, 'w', newline='') as f:
       json.dump(fake_users,f)
except IOError as e:
    print(f"error: {e}")
import requests

VLLM_API_URL = "http://localhost:8000/v1/chat/completions"
prompt = """"
            2025-07-23 16:36:15,101 - social.agent - INFO - Agent 199 observing environment:
After refreshing, you see some posts [
    {
        "post_id": 23,
        "user_id": 29,
        "content": "What can I get for a single security camera that records 24/7 without a DVR setup?\n\nI'm trying to get a security camera setup for my room, Since I live with a
 questionable drug addict who I don't trust at all. I also lock my door, But have 1 day a week that I'm not able to do that, and want to make sure my stuff isnt stolen or tampered 
with. I've tried looking for different type of CCTV type cameras, But almost all the ones I've seen require a whole DVR setup. I just want 1 single camera that can constantly recor
d, and save to an SD card or something similar, and to have the ability to set up my camera to wifi and check on it from my phone, or go back and watch the recording. Any recommendations?",
        "created_at": "2025-06-19 19:39:04.495860",
        "num_likes": 0,
        "num_dislikes": 0,
        "num_shares": 0,
        "num_reports": 0,
        "comments": []
    },
    {
        "post_id": 24,
        "user_id": 25,
        "content": "Whole House Recommendations\n\nHey all! New to the wireless security world and could use some help. Also, I\u2019m not specifically worried about local storage 
or subscriptions. I\u2019m am look a quality brand of camera for a wired doorbell, internal camera, and external camera. I have had a Ring doorbell in the past and enjoyed it and the app, but never had anything else Ring. I currently have a Blink doorbell and few camera, but despise the app and the reaction time for motion. Thanks!",
        "created_at": "2025-06-20 03:40:32.367000",
        "num_likes": 0,
        "num_dislikes": 0,
        "num_shares": 0,
        "num_reports": 0,
        "comments": []
    },
    {
        "post_id": 25,
        "user_id": 26,
        "content": "Camera no audio or pan and tilt\n\nI live in a apartment and the rules are I can have a security camera inside my apartment but it can't have the ability to rec
ord audio and it can't be able to pan and tilt. Is there any simple wifi camera that has this ideally I'd be able to connect it to my Synology nas or the cloud so if I am robbed the footage is safe?",
        "created_at": "2025-06-20 03:40:33.447540",
        "num_likes": 0,
        "num_dislikes": 0,
        "num_shares": 0,
        "num_reports": 0,
        "comments": []
    }
    {
    "post_id": 26,
        "user_id": 26,
        "content": "Our AirBnb has these throughout the home with privacy shield open - what are they and how to tell if these are live?

Airbnb has motion sensors with what looks like camera lens through the living areas, hallways etc. we've been here a few days and I didn't notice. 

Are these cameras or are they part of the motion sensor lens? Unsure - help appreciated. I've met the host and can't imagine her to do something sinister.",
        "created_at": "2025-06-20 03:40:33.447540",
        "num_likes": 0,
        "num_dislikes": 0,
        "num_shares": 0,
        "num_reports": 0,
        "comments": []
    
    }
]🧠 Community Virality Insight:
In this community, posts that go viral typically:
- contain questions in the post text
- express emotions like *anger*, *frustration*, or *sadness*
- use keywords such as *booking*, *complaint*, *training*, *weekend*, *saf*
- have strong emotional sentiment (positive or negative)
- are longer than 50 words
Always explain your reasoning behind the action.

Respond in the following format:
- Action: [action type] on Post [id or index]
- Reason: [short explanation based on post content and virality signals]
analyse the sentiment, keywords, and emotions of the post. which post has the more viral content? pick one you want to perform action that best reflects your current inclination based on your profile and posts content. 
            remember to indicate clearly which post you are acting on.
            """



agent_memory = {
    "agent_1": [{"role": "system", "content": prompt}],
    "agent_2": [{"role": "system", "content": prompt}]
}

payload = {
    "model": "qwen-2",  # Or whatever your model name is
    "messages": [
        {
            "role": "user",
            "content": prompt,
        }
    ],
    "temperature": 0.7,
    "max_tokens": 100,
    "top_p": 0.9,
    "stop": None,
    "stream": False
}

headers = {
    "Content-Type": "application/json"
}

for agent_id, history in agent_memory.items():
    response = requests.post(VLLM_API_URL, json={
        "model": "qwen-2",
        "messages": history,
        "temperature": 0.7,
        "max_tokens": 100,
        "top_p": 0.9,
        "stream": False
    })

    reply = response.json()["choices"][0]["message"]["content"]
    print(f"🧠 Agent {agent_id} says:\n{reply.strip()}\n")

    # Add assistant reply to history
    agent_memory[agent_id].append({"role": "assistant", "content": reply})


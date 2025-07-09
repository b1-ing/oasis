import asyncio
import os
import json

from camel.models import ModelFactory
from camel.types import ModelPlatformType
import oasis
from oasis import (ActionType, LLMAction, ManualAction, generate_reddit_agent_graph)
from oasis.clock.clock import Clock



async def main():
    # Load scraped post data
    with open("reddit_structured_posts.json", "r", encoding="utf-8") as f:
        scraped_posts = json.load(f)

    # Initialize model
    tinyllama_model = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type="qwen-2",
        url="http://localhost:8000/v1",
    )

    available_actions = [
        ActionType.LIKE_POST,
        ActionType.DISLIKE_POST,
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.LIKE_COMMENT,
        ActionType.DISLIKE_COMMENT,
        ActionType.SEARCH_POSTS,
        ActionType.SEARCH_USER,
        ActionType.TREND,
        ActionType.REFRESH,
        ActionType.DO_NOTHING,
        ActionType.FOLLOW,
        ActionType.MUTE,
    ]

    agent_graph = await generate_reddit_agent_graph(
        profile_path="fake_users.json",
        model=tinyllama_model,
        available_actions=available_actions,
    )

    db_path = "./data/reddit_simulation.db"
    if os.path.exists(db_path):
        os.remove(db_path)

        # 6 hours per real second in simulated time
        six_hours_in_seconds = 6 * 60 * 60
        clock = Clock(k=six_hours_in_seconds)


    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
        clock=clock,
    )



    await env.reset()

    # Step 1: Assign real posts to agents as CREATE_POST actions
    actions_1 = {}
    agents = list(env.agent_graph.get_agents())
    for i, (agent_id, agent) in enumerate(agents):
        if i >= len(scraped_posts):
            break
        post = scraped_posts[i]
        post_title = post.get("post_title", "Untitled Post")
        post_content = post.get("post_text", "No content")
        print(post_content)

        actions_1[agent] = ManualAction(
            action_type=ActionType.CREATE_POST,
            action_args={

                "content": post_title
            }
        )

    await env.step(actions_1)

    # Step 2: Let agents act using the model
    num_steps = 15  # ← Change this to how many total LLM-driven steps you want

    for step_num in range(num_steps):
        print(f"\n🌐 Step {step_num + 1}/{num_steps}")
        actions = {
            agent: LLMAction()
            for _, agent in env.agent_graph.get_agents()
        }
        await env.step(actions)

    await env.close()


if __name__ == "__main__":
    print(list(ModelPlatformType))
    asyncio.run(main())

import asyncio
import os
import json
from oasis.social_platform.platform import Platform
from camel.models import ModelFactory
from camel.types import ModelPlatformType
import oasis
from oasis import (
    ActionType,
    LLMAction,
    ManualAction,
    generate_reddit_agent_graph
)
from oasis.clock.clock import Clock


async def main():
    # ========== Load real Reddit thread data ==========
    with open("reddit_structured_posts.json", "r", encoding="utf-8") as f:
        scraped_posts = json.load(f)

    # ========== Initialize model ==========
    model = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type="qwen-2",
        url="http://localhost:8000/v1",
    )

    # ========== Define available agent actions ==========
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

    # ========== Load agents from fake profile ==========
    agent_graph = await generate_reddit_agent_graph(
        profile_path="fake_users.json",
        model=model,
        available_actions=available_actions,
    )

    # ========== Setup environment and simulation clock ==========
    db_path = "./data/reddit_simulation.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Simulate 6 hours per real second
    from oasis.social_platform.channel import Channel


    # Set up clock
    hours_per_real_second = 6
    sim_clock = Clock(k=hours_per_real_second * 3600)

    # Create the channel for communication
    channel = Channel()

    # Create platform manually, injecting the clock
    platform = Platform(
        db_path=db_path,
        channel=channel,
        sandbox_clock=sim_clock,
    )

    # Now build the environment
    env = oasis.make(
        agent_graph=agent_graph,
        platform=platform,  # ✅ pass actual Platform object, not enum
    )


    await env.reset()

    # ========== Step 1: Post real threads ==========
    actions_init = {}
    agents = list(env.agent_graph.get_agents())

    for i, (_, agent) in enumerate(agents):
        if i >= len(scraped_posts):
            break
        post = scraped_posts[i]
        title = post.get("post_title", "Untitled Post")
        body = post.get("post_text", "")

        print(f"Posting: {title}")
        actions_init[agent] = ManualAction(
            action_type=ActionType.CREATE_POST,
            action_args={"content": f"{title}\n\n{body}"}
        )

    await env.step(actions_init)

    # ========== Step 2: Let agents act with LLM ==========
    num_steps = 15  # Adjust as needed
    for step_num in range(num_steps):
        print(f"\n🌐 Simulation Step {step_num + 1}/{num_steps}")
        llm_actions = {
            agent: LLMAction()
            for _, agent in env.agent_graph.get_agents()
        }
        await env.step(llm_actions)

    await env.close()
    print("✅ Simulation complete.")


if __name__ == "__main__":
    asyncio.run(main())

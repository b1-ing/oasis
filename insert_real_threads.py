import asyncio
import os
import json
from datetime import datetime
from oasis.social_platform.platform import Platform
from oasis.social_platform.channel import Channel
from oasis.clock.clock import Clock
from oasis import (
    ActionType,
    ManualAction,
    LLMAction,
    generate_reddit_agent_graph,
    make,
)
from camel.models import ModelFactory
from camel.types import ModelPlatformType
import time
from oasis.social_agent.agent import SocialAgent, ManualPosterAgent
from oasis.social_agent.agent_graph import AgentGraph

async def generate_hybrid_agent_graph(model, available_actions, llm_count=100, normal_count=3000):
    agent_graph = AgentGraph()

    # Load your fake profiles (e.g., scraped Reddit users)
    with open("fake_users.json", "r", encoding="utf-8") as f:
        profiles = json.load(f)

    count = 1

    # Choose LLM-backed authors first
    llm_profiles = profiles[:llm_count]
    for p in llm_profiles:
        agent = SocialAgent(user_info=p,agent_id=count, model=model, available_actions=available_actions)
        agent_graph.add_agent(agent)
        count+=1

    # Then normal agents (do nothing or only simple actions)
    normal_profiles = profiles[llm_count:llm_count + normal_count]
    for p in normal_profiles:
        agent = ManualPosterAgent(user_info=p, model=None, available_actions=[
            ActionType.LIKE_POST,
            ActionType.DISLIKE_POST,
            ActionType.LIKE_COMMENT,
            ActionType.DISLIKE_COMMENT,
            ActionType.SEARCH_POSTS,
            ActionType.REFRESH,
        ])
        agent_graph.add_agent(agent)

    return agent_graph



async def main():
    # Load the structured post data with author_id and timestep
    with open("processed_posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    # Build a mapping from timestep → list of posts
    posts_by_timestep = {}
    for post in posts:
        timestep = post["timestep"]
        posts_by_timestep.setdefault(timestep, []).append(post)

    # Init model
    model = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type="qwen-2",
        url="http://localhost:8000/v1",
    )

    # Actions
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



    # Load agents
    agent_graph = await generate_reddit_agent_graph(
        model=model,
        available_actions=available_actions,
        profile_path="fake_users.json"

    )

    # Init environment
    db_path = "./data/reddit_simulation_1d.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    clock = Clock(k=180)  # 2hr/timestep
    start_time = datetime(2025, 6, 19, 5, 0)
    channel = Channel()
    platform = Platform(
        db_path=db_path,
        channel=channel,
        sandbox_clock=clock,
        start_time=start_time,

    )

    env = make(agent_graph=agent_graph, platform=platform)
    await env.reset()

    # Run simulation for each timestep
    max_timestep = max(posts_by_timestep.keys())
    agents = dict(agent_graph.get_agents())

    for t in range(max_timestep + 1):
        print(f"\n🕒 Timestep {t}")
        start_real_time = time.perf_counter()

        actions = {}
        agents = dict(agent_graph.get_agents())
        llm_author_ids = {a.user_info.user_id for a in agents.values()}


        # Post threads scheduled for this timestep
        for post in posts_by_timestep.get(t, []):
            author_id = post["author_id"]
            if author_id not in llm_author_ids:
                continue
            elif author_id not in agents:
                print(f"❌ Skipping post by author_id {author_id} (not in agent list)")
                continue

            agent = agents[author_id]
            title = post.get("title", "Untitled Post")
            body = post.get("post_text") or ""
            content = f"{title}\n\n{body}".strip()
            actions[agent] = ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": content}
            )

        # Step: post them
        if actions:
            await env.step(actions)

        # Then let everyone act
        llm_actions = {
            agent: LLMAction()
            for _, agent in agent_graph.get_agents()
            if agent.model is not None
        }

        await env.step(llm_actions)
        end_real_time = time.perf_counter()  # ⏱️ end timing
        elapsed_time = end_real_time - start_real_time
        print(f"⏱️ Real time taken for timestep {t}: {elapsed_time:.2f} seconds")

    await env.close()
    print("✅ Simulation complete.")


if __name__ == "__main__":
    asyncio.run(main())

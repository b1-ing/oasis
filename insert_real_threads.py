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
from typing import List, Optional, Union
from camel.models import BaseModelBackend, ModelManager
from oasis.social_platform.config import Neo4jConfig, UserInfo
#
# async def generate_reddit_agent_graph(
#     profile_path: str,
#     model: Optional[Union[BaseModelBackend, List[BaseModelBackend],
#                           ModelManager]] = None,
#     available_actions: list[ActionType] = None,
# ) -> AgentGraph:
#     agent_graph = AgentGraph()
#     with open(profile_path, "r", encoding="utf-8") as file:
#         agent_info = json.load(file)
#
#     async def process_agent(i):
#         # Instantiate an agent
#         profile = {
#             "nodes": [],  # Relationships with other agents
#             "edges": [],  # Relationship details
#             "other_info": {},
#         }
#         # Update agent profile with additional information
#         if isinstance(agent_info[i], dict) and "persona" in agent_info[i]:
#             profile["other_info"]["user_profile"] = agent_info[i]["persona"]
#         else:
#             print("⚠️ agent_info[i] is not a dict or missing 'persona':", agent_info[i])
#
#         profile["other_info"]["mbti"] = agent_info[i]["mbti"]
#         profile["other_info"]["gender"] = agent_info[i]["gender"]
#         profile["other_info"]["age"] = agent_info[i]["age"]
#         profile["other_info"]["country"] = agent_info[i]["country"]
#
#         user_info = UserInfo(
#             name=agent_info[i]["username"],
#             description=agent_info[i]["bio"],
#             profile=profile,
#             recsys_type="reddit",
#         )
#
#         agent = SocialAgent(
#             agent_id=i,
#             user_info=user_info,
#             agent_graph=agent_graph,
#             model=model,
#             available_actions=available_actions,
#         )
#
#         # Add agent to the agent graph
#         agent_graph.add_agent(agent)
#
#     tasks = [process_agent(i) for i in range(len(agent_info))]
#     await asyncio.gather(*tasks)
#     return agent_graph

async def generate_hybrid_agent_graph(
    profile_path: str,
    model: Optional[Union[BaseModelBackend, List[BaseModelBackend],
                          ModelManager]] = None,
    available_actions: list[ActionType] = None,
    llm_count=100,
    normal_count=100)-> AgentGraph:


    agent_graph = AgentGraph()

    # Load your fake profiles (e.g., scraped Reddit users)
    with open("fake_users.json", "r", encoding="utf-8") as f:
        agent_info = json.load(f)


    async def process_agent(i, llm_count):
            # Instantiate an agent
            profile = {
                "nodes": [],  # Relationships with other agents
                "edges": [],  # Relationship details
                "other_info": {},
            }

            if isinstance(agent_info[i], dict) and "persona" in agent_info[i]:
                profile["other_info"]["user_profile"] = agent_info[i]["persona"]
            else:
                print("⚠️ agent_info[i] is not a dict or missing 'persona':", agent_info[i])

                # Fill other profile metadata
            profile["other_info"]["mbti"] = agent_info[i].get("mbti")
            profile["other_info"]["gender"] = agent_info[i].get("gender")
            profile["other_info"]["age"] = agent_info[i].get("age")
            profile["other_info"]["country"] = agent_info[i].get("country")
            user_info = UserInfo(

                                name=agent_info[i]["username"],
                                description=agent_info[i].get("bio", ""),
                                profile=profile,
                                recsys_type="llm" if i < llm_count else "normal"
                            )

            is_llm = i < llm_count

            print(model)

            if is_llm:
                print(i)

                agent = SocialAgent(
                                    agent_id=i,
                                    user_info=user_info,
                                    agent_graph=agent_graph,
                                    model=model,
                                    available_actions=available_actions,
                                )

                agent_graph.add_agent(agent)
                print(f"agent {agent.user_info.id} added")
            else:
                agent = ManualPosterAgent(
                                                    agent_id=i,
                                                    user_info=user_info,
                                                    agent_graph=agent_graph,
                                                    available_actions=available_actions if is_llm else [
                                                        ActionType.LIKE_POST,
                                                        ActionType.DISLIKE_POST,
                                                        ActionType.LIKE_COMMENT,
                                                        ActionType.DISLIKE_COMMENT,
                                                        ActionType.SEARCH_POSTS,
                                                        ActionType.REFRESH,
                                                    ],
                                                )

                agent_graph.add_agent(agent)
                print(f"agent {agent.agent_id} added")


    tasks = [process_agent(i, llm_count) for i in range(llm_count + normal_count)]
    await asyncio.gather(*tasks)
    return agent_graph



async def main():
    # Load the structured post data with author_id and timestep
    with open("processed_posts_security.json", "r", encoding="utf-8") as f:
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
    db_path = "./data/reddit_simulation_stat.db"
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
        llm_author_ids = {a.social_agent_id for a in agents.values()}
        print("llm_author_ids" , llm_author_ids)


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
            if isinstance(agent, SocialAgent)
        }

        await env.step(llm_actions)
        end_real_time = time.perf_counter()  # ⏱️ end timing
        elapsed_time = end_real_time - start_real_time
        print(f"⏱️ Real time taken for timestep {t}: {elapsed_time:.2f} seconds")

    await env.close()
    print("✅ Simulation complete.")


if __name__ == "__main__":
    asyncio.run(main())

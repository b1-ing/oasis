import asyncio
import os

from camel.models import ModelFactory
from camel.types import ModelPlatformType

import oasis
from oasis import (ActionType, LLMAction, ManualAction,
                   generate_twitter_agent_graph)


async def main():
    # NOTE: You need to deploy the vllm server first
    tinyllama_model = ModelFactory.create(
            model_platform=ModelPlatformType.VLLM,
            model_type="qwen-2",
            url="http://localhost:8000/v1",
        )
    # Define the models for agents. Agents will select models based on
    # pre-defined scheduling strategies
    models = [tinyllama_model]

    # Define the available actions for the agents
    available_actions = [
        ActionType.CREATE_POST,
        ActionType.LIKE_POST,
        ActionType.REPOST,
        ActionType.FOLLOW,
        ActionType.DO_NOTHING,
        ActionType.QUOTE_POST,
    ]

    agent_graph = await generate_twitter_agent_graph(
        profile_path="data/twitter_dataset/group_polarization/197_progressive.csv",
        model=models,
        available_actions=available_actions,
    )

    # Define the path to the database
    db_path = "./data/twitter_simulation_progressive.db"

    # Delete the old database
    if os.path.exists(db_path):
        os.remove(db_path)

    # Make the environment
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=db_path,
    )

    # Run the environment
    await env.reset()

    actions_1 = {}

    actions_1[env.agent_graph.get_agent(0)] = ManualAction(
        action_type=ActionType.CREATE_POST,
        action_args={"content": "Earth is flat."})
    await env.step(actions_1)

    actions_2 = {
        agent: LLMAction()
        # Activate 5 agents with id 1, 3, 5, 7, 9
        for _, agent in env.agent_graph.get_agents([1, 3, 5, 7, 9])
    }

    await env.step(actions_2)

    actions_3 = {}

    actions_3[env.agent_graph.get_agent(1)] = ManualAction(
        action_type=ActionType.CREATE_POST,
        action_args={"content": "Earth is not flat."})
    await env.step(actions_3)

    actions_4 = {
        agent: LLMAction()
        # get all agents
        for _, agent in env.agent_graph.get_agents()
    }
    await env.step(actions_4)

    actions_5 = {
            agent: LLMAction()
            # get all agents
            for _, agent in env.agent_graph.get_agents()
        }
    await env.step(actions_5)

    # Close the environment
    await env.close()


if __name__ == "__main__":
    asyncio.run(main())
# ollama_model.py

from openai import OpenAI
from camel.models.base_model import BaseModel
from camel.types import ModelPlatformType

class OllamaModel(BaseModel):
    def __init__(self, base_url="http://localhost:11434/v1", model_name="tinyllama"):
        self._client = OpenAI(
            base_url=base_url,
            api_key="fake-key",
        )
        self._model_name = model_name
        self._model_platform = ModelPlatformType.OLLAMA  # Required by CAMEL agents

    async def arun(self, messages, response_format=None, tools=None):
        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=messages
        )
        return response

    def run(self, messages, response_format=None, tools=None):
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages
        )
        return response

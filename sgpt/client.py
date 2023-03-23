import requests
from pathlib import Path
from typing import List, Dict

from sgpt import config, Cache, ChatCache


CHAT_CACHE_LENGTH = int(config.get("CHAT_CACHE_LENGTH"))
CHAT_CACHE_PATH = Path(config.get("CHAT_CACHE_PATH"))
CACHE_LENGTH = int(config.get("CACHE_LENGTH"))
CACHE_PATH = Path(config.get("CACHE_PATH"))
REQUEST_TIMEOUT = int(config.get("REQUEST_TIMEOUT"))


class OpenAIClient:
    cache = Cache(CACHE_LENGTH, CACHE_PATH)
    chat_cache = ChatCache(CHAT_CACHE_LENGTH, CHAT_CACHE_PATH)

    def __init__(self, api_host: str, api_key: str) -> None:
        self.api_key = api_key
        self.api_host = api_host

    @cache
    def _request(
        self,
        messages: List,
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        top_probability: float = 1,
    ) -> Dict:
        """
        Make request to OpenAI ChatGPT API, read more:
        https://platform.openai.com/docs/api-reference/chat

        :param messages: List of messages {"role": user or assistant, "content": message_string}
        :param model: String gpt-3.5-turbo or gpt-3.5-turbo-0301
        :param temperature: Float in 0.0 - 1.0 range.
        :param top_probability: Float in 0.0 - 1.0 range.
        :return: Response body JSON.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "top_p": top_probability,
        }
        endpoint = f"{self.api_host}/v1/chat/completions"
        response = requests.post(
            endpoint, headers=headers, json=data, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    @chat_cache
    def get_completion(
        self,
        message: List[str],
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        top_probability: float = 1,
        caching: bool = True,
    ) -> str:
        """
        Generates single completion for prompt (message).

        :param message: String prompt to generate completion for.
        :param model: String gpt-3.5-turbo or gpt-3.5-turbo-0301.
        :param temperature: Float in 0.0 - 1.0 range.
        :param top_probability: Float in 0.0 - 1.0 range.
        :param caching: Boolean value to enable/disable caching.
        :return: String generated completion.
        """
        # TODO: Move prompt context to system role when GPT-4 will be available over API.
        return self._request(
            message, model, temperature, top_probability, caching=caching
        )["choices"][0]["message"]["content"].strip()

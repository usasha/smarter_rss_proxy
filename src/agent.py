import logging
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from cachetools import LRUCache
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider


class ContainsThisTypes(BaseModel):
    contains: bool
    types: list[str]


@dataclass
class MyDeps:
    feed_entry: dict
    http_client: httpx.AsyncClient


class FeedGuard:
    def __init__(self, api_key: str, model: str, cache_size: int) -> None:
        """
        :param api_key: OpenRouter API key
        :param model: model name in provider/name format
        :param cache_size: size of the cache for storing results of the agent
        """
        model = OpenAIModel(
            model_name=model,
            provider=OpenRouterProvider(api_key=api_key),
        )
        self.cache = LRUCache(maxsize=cache_size)
        self.agent = Agent(
            model,
            output_type=ContainsThisTypes,
            retries=4,
            instructions='Return true if entry contains any of specified content types. Return the types.'
                         'Check article preview if not sure by title.',
            deps_type=MyDeps,
            tools=[self._get_article_preview],
        )

    async def _get_article_preview(self, ctx: RunContext[MyDeps]) -> str:
        """
        Get an article preview.
        :param ctx: Run context.
        :return: Article preview.
        """
        logging.info('tool call')
        try:
            text = self._html_to_text(ctx.deps.feed_entry['content'][0]['value'])[:2000]
            assert len(text) > 500
            logging.info('access description')
            return text
        except (KeyError, AssertionError) as _:
            pass

        try:
            response = await ctx.deps.http_client.get(ctx.deps.feed_entry['link'])
        except httpx.HTTPError as _:
            logging.info('access article link failed')
            return ''
        text = self._html_to_text(response.text)[:2000]
        logging.info('access article text')
        return text

    @staticmethod
    def _html_to_text(html: str) -> str:
        """
        Converts HTML to text.
        :param html: HTML to be converted.
        :return: Text content of the HTML page.
        """
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    async def check_entry(self, entry: dict, content_types: list[str]) -> ContainsThisTypes:
        """
        Checks if an entry contains specified content types
        :param entry: RSS entry to be checked.
        :param content_types: content types to match against the entry.
        :return: flag and triggers list.
        """
        cache_key = f"{entry['title']}_{entry['link']}_{content_types}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        async with httpx.AsyncClient() as client:
            result = await self.agent.run(
                f"Content types: {content_types}."
                f"Entry title: {entry['title']}",
                deps=MyDeps(feed_entry=entry, http_client=client),
            )

        self.cache[cache_key] = result.output
        return result.output

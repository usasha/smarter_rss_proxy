import json

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import respx
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel, AgentInfo
from pydantic_ai.models.test import TestModel
from src.agent import FeedGuard, MyDeps, ContainsThisTypes
# from pydantic_ai.model import JsonPart

@pytest.fixture
def feed_guard():
    guard = FeedGuard(api_key='test_key', model='test_model', cache_size=10)
    guard.agent.model = TestModel()
    return guard

@pytest.fixture
def test_model():
    return TestModel()


class TestFeedGuard:
    def test_html_to_text(self):
        html = '<html><body><h1>Test Title</h1><p>Test paragraph.</p></body></html>'
        expected_text = 'Test Title Test paragraph.'
        result = FeedGuard._html_to_text(html)
        assert result == expected_text

    def test_html_to_text_empty(self):
        html = ''
        expected_text = ''
        result = FeedGuard._html_to_text(html)
        assert result == expected_text

    def test_html_to_text_malformed(self):
        html = '<html><body><h1>Unclosed tag'
        result = FeedGuard._html_to_text(html)
        assert 'Unclosed tag' in result

    def test_init(self, feed_guard):
        assert feed_guard.cache.maxsize == 10

    @pytest.mark.asyncio
    async def test_check_entry_cached(self, feed_guard):
        entry = {'title': 'Test Title', 'link': 'http://example.com'}
        content_types = ['politics', 'news']

        feed_guard.agent.run = AsyncMock()
        await feed_guard.check_entry(entry, content_types)

        assert feed_guard.agent.run.call_count == 1
        await feed_guard.check_entry(entry, content_types)
        assert feed_guard.agent.run.call_count == 1

    @pytest.mark.asyncio
    async def test_cached_result_is_the_same(self, feed_guard):
        entry = {'title': 'Test Title', 'link': 'http://example.com'}
        content_types = ['politics', 'news']

        result_1 = await feed_guard.check_entry(entry, content_types)
        result_2 = await feed_guard.check_entry(entry, content_types)

        assert result_1 == result_2

    @pytest.mark.asyncio
    async def test_check_entry_not_cached(self, feed_guard):
        entry = {'title': 'Test Title', 'link': 'http://example.com'}

        feed_guard.agent.run = AsyncMock()

        await feed_guard.check_entry(entry, ['politics', 'news'])
        assert feed_guard.agent.run.call_count == 1
        await feed_guard.check_entry(entry, ['politics', 'news', 'dogs'])
        assert feed_guard.agent.run.call_count == 2

    @pytest.mark.asyncio
    async def test_get_article_preview_from_content(self, feed_guard):
        html_content = "<html><body><p>This is a test article with more than 500 characters. " + "x" * 500 + "</p></body></html>"
        feed_entry = {'content': [{'value': html_content}]}
        ctx = MagicMock()
        ctx.deps = MyDeps(feed_entry=feed_entry, http_client=None)

        result = await feed_guard._get_article_preview(ctx)

        assert 'This is a test article' in result
        assert len(result) <= 2000

    @pytest.mark.asyncio
    async def test_get_article_preview_from_link(self, feed_guard):
        html_content = '<html><body><p>This is a test article fetched from the link.</p></body></html>'
        feed_entry = {
            'content': [{'value': 'Short content'}],  # too short, will fail assertion
            'link': 'http://example.com'
        }
        with respx.mock:
            route = respx.get('http://example.com').respond(content=html_content, status_code=200)
            async with httpx.AsyncClient() as client:
                ctx = MagicMock()
                ctx.deps = MyDeps(feed_entry=feed_entry, http_client=client)

                result = await feed_guard._get_article_preview(ctx)

                assert 'This is a test article fetched from the link.' in result
                assert route.call_count == 1

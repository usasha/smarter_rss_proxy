import json

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import respx
from pydantic_ai import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, TextPart
from pydantic_ai.models.function import FunctionModel, AgentInfo
from src.agent import FeedGuard, MyDeps, ContainsThisTypes


@pytest.fixture
def content_types():
    return ['politics', 'news']


@pytest.fixture
def feed_guard(content_types):
    call_counter = Mock()
    def detect_topic(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        title = messages[0].parts[0].content.split('Entry title')[1].lower()
        found = [word for word in content_types if word in title]
        call_counter()
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='final_result',
                    args={
                        'contains': bool(found),
                        'types': found,
                    },
                    tool_call_id='pyd_ai_tool_call_id',
                )
            ]
        )

    guard = FeedGuard(api_key='test_key', model='test_model', cache_size=10)
    guard.call_counter = call_counter
    with guard.agent.override(model=FunctionModel(detect_topic)):
        yield guard


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

    @pytest.mark.asyncio
    async def test_check_entry_contains_content_types(self, feed_guard, content_types):
        entry = {'title': 'News about politics and elections', 'link': 'http://example.com'}

        result = await feed_guard.check_entry(entry, content_types)

        assert result.contains is True
        assert 'politics' in result.types
        assert 'news' in result.types
        cache_key = f"{entry['title']}_{entry['link']}_{content_types}"
        assert cache_key in feed_guard.cache
        assert feed_guard.call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_check_entry_does_not_contain_content_types(self, feed_guard, content_types):
        entry = {'title': 'Toys became cheaper!', 'link': 'http://example.com'}

        result = await feed_guard.check_entry(entry, content_types)

        assert result.contains is False
        assert result.types == []
        cache_key = f"{entry['title']}_{entry['link']}_{content_types}"
        assert cache_key in feed_guard.cache
        assert feed_guard.call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_check_entry_contains_content_types_cached(self, feed_guard, content_types):
        entry = {'title': 'News about politics and elections', 'link': 'http://example.com'}

        _ = await feed_guard.check_entry(entry, content_types)
        result = await feed_guard.check_entry(entry, content_types)

        assert result.contains is True
        assert 'politics' in result.types
        assert 'news' in result.types
        cache_key = f"{entry['title']}_{entry['link']}_{content_types}"
        assert cache_key in feed_guard.cache
        assert feed_guard.call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_check_entry_does_not_contain_content_types_cached(self, feed_guard, content_types):
        entry = {'title': 'Toys became cheaper!', 'link': 'http://example.com'}

        _ = await feed_guard.check_entry(entry, content_types)
        result = await feed_guard.check_entry(entry, content_types)

        assert result.contains is False
        assert result.types == []
        cache_key = f"{entry['title']}_{entry['link']}_{content_types}"
        assert cache_key in feed_guard.cache
        assert feed_guard.call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_check_entry_with_test_model_error(self, feed_guard):
        entry = {"title": "Error test", "link": "http://example.com/error"}
        content_types = ["politics", "news"]

        call_counter = Mock()
        def foo(*args, **kwargs):
            call_counter()
            return ModelResponse(parts=[TextPart('wont pass validation')])

        with feed_guard.agent.override(
                model=FunctionModel(foo)
        ):
            with pytest.raises(UnexpectedModelBehavior):
                await feed_guard.check_entry(entry, content_types)

        cache_key = f"{entry['title']}_{entry['link']}_{content_types}"
        assert cache_key not in feed_guard.cache
        assert call_counter.call_count == 5

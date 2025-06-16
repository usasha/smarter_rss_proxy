import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import Response
import uvicorn

from agent import FeedGuard
from rss_loader import Feed


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info('Starting API server...')
    load_dotenv()
    app.state.guard = FeedGuard(os.getenv('OPEN_ROUTER_API_KEY'))
    yield

app = FastAPI(lifespan=lifespan)


@app.get('/rss/keywords/exclude')
async def keywords_exclude(url: str, keywords: str) -> Response:
    """
    Fetch and filter an RSS feed to exclude entries containing specified keywords in their titles.
    :param url: The RSS feed URL to fetch for processing
    :param keywords: A comma-separated string of keywords to exclude from the RSS feed entries
    :return: Filtered RSS feed
    """
    keyword_list = [k.strip().lower() for k in keywords.split(',')]
    feed = Feed(url).filter(
        lambda entry: not any(
            kw in entry.get('title', '').lower() for kw in keyword_list
        )
    )
    return Response(content=feed.raw_content, media_type='application/rss+xml')


@app.get('/rss/content_type/exclude')
async def content_type_exclude(url: str, content_types: str) -> Response:
    """
    Fetch and filter an RSS feed to exclude entries containing specified content types.
    :param url: The RSS feed URL to fetch for processing
    :param content_types: A comma-separated string of content types to exclude from the RSS feed entries
    :return: Filtered RSS feed
    """
    content_types = [k.strip().lower() for k in content_types.split(',')]
    feed = Feed(url).filter(
        lambda entry: not app.state.guard.check_entry(entry, content_types).contains
    )
    return Response(content=feed.raw_content, media_type='application/rss+xml')


if __name__ == '__main__':
    uvicorn.run('api:app', reload=True)

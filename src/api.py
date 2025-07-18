import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

import config
from agent import FeedGuard
from rss_loader import Feed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info('Starting API server...')
    app.state.guard = FeedGuard(
        config.OPENROUTER_API_KEY,
        config.MODEL_NAME,
        config.CACHE_SIZE,
    )
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Serve the main page with the RSS filter form.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/rss/keywords/include')
async def keywords_include(url: str, keywords: str) -> Response:
    """
    Fetch and filter an RSS feed to include only entries containing specified keywords in their titles.
    :param url: The RSS feed URL to fetch for processing
    :param keywords: A comma-separated string of keywords to exclude from the RSS feed entries
    :return: Filtered RSS feed
    """
    keywords = {k.strip().lower() for k in keywords.split(',')}
    feed = Feed(url).filter(
        lambda entry: any(
            word in keywords for word in entry.get('title', '').lower().split()
        )
    )
    return Response(content=feed.raw_content, media_type='application/rss+xml')


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


@app.get('/rss/content_type/include')
async def content_type_include(url: str, content_types: str, request: Request) -> Response:
    """
    Fetch and filter an RSS feed to include only entries containing specified content types.
    :param url: The RSS feed URL to fetch for processing
    :param content_types: A comma-separated string of content types to exclude from the RSS feed entries
    :param request: request object, passed automatically by FastAPI
    :return: Filtered RSS feed
    """
    content_types = [k.strip().lower() for k in content_types.split(',')]
    feed = Feed(url)
    tasks = [
        request.app.state.guard.check_entry(entry, content_types)
        for entry in feed.entries
    ]
    entry_to_result = dict(zip(
        [entry['title'] for entry in feed.entries],
        await asyncio.gather(*tasks))
    )

    feed = feed.filter(lambda entry: entry_to_result[entry['title']].contains)
    return Response(content=feed.raw_content, media_type='application/rss+xml')


@app.get('/rss/content_type/exclude')
async def content_type_exclude(url: str, content_types: str, request: Request) -> Response:
    """
    Fetch and filter an RSS feed to exclude entries containing specified content types.
    :param url: The RSS feed URL to fetch for processing
    :param content_types: A comma-separated string of content types to exclude from the RSS feed entries
    :param request: request object, passed automatically by FastAPI
    :return: Filtered RSS feed
    """
    content_types = [k.strip().lower() for k in content_types.split(',')]
    feed = Feed(url)
    tasks = [
        request.app.state.guard.check_entry(entry, content_types)
        for entry in feed.entries
    ]
    entry_to_result = dict(zip(
        [entry['title'] for entry in feed.entries],
        await asyncio.gather(*tasks))
    )

    feed = feed.filter(lambda entry: not entry_to_result[entry['title']].contains)
    return Response(content=feed.raw_content, media_type='application/rss+xml')


if __name__ == '__main__':
    uvicorn.run('api:app', reload=True)

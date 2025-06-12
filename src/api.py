import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
import uvicorn

from rss_loader import Feed


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info('Starting API server...')
    yield

app = FastAPI(lifespan=lifespan)


@app.get('/rss/keyword_filter')
async def keyword_filter(url: str, keywords: str) -> Response:
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


if __name__ == '__main__':
    uvicorn.run('api:app', reload=True)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
import uvicorn

from rss_loader import Feed


feed_main = None
feed_filtered_out = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    feed_main = (
        Feed('https://news.ycombinator.com/rss')
        # Feed('https://demo.tt-rss.org/public.php?op=rss&id=0&is_cat=1&q=&key=6t72yu68472f4d3f084')
        .filter(lambda entry: 'llm' not in entry.get('title', '').lower())
        .filter(lambda entry: 'ai ' not in entry.get('title', '').lower())
    )
    feed_filtered_out = (
        Feed('https://news.ycombinator.com/rss')
        # Feed('https://demo.tt-rss.org/public.php?op=rss&id=0&is_cat=1&q=&key=6t72yu68472f4d3f084')
        .filter(lambda entry: "llm" in entry.get("title", "").lower())
        .filter(lambda entry: "ai " in entry.get("title", "").lower())
    )
    print("Feed size: ", len(feed_main.entries))
    print("Filtered out: ", len(feed_filtered_out.entries))
    yield

app = FastAPI(lifespan=lifespan)


@app.get('/rss')
async def get_rss_feed():
    """
    Get the RSS feed content in XML format for standard RSS clients.
    Uses the feed that was previously loaded into the Feed class.

    Returns:
        RSS feed content in XML format with appropriate content type
    """
    return Response(
        content=feed_main.raw_content,
        media_type='application/rss+xml'
    )


@app.get('/rss/filtered_out')
async def get_filtered_out_rss_feed():
    """
    Get the RSS feed content in XML format for standard RSS clients.
    Uses the feed that was previously loaded into the Feed class.

    Returns:
        RSS feed content in XML format with appropriate content type
    """
    return Response(
        content=feed_filtered_out.raw_content,
        media_type='application/rss+xml'
    )


if __name__ == '__main__':
    uvicorn.run('api:app', reload=True)

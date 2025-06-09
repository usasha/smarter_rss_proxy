from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
import uvicorn

from rss_loader import Feed


feed = Feed('https://news.ycombinator.com/rss')
app = FastAPI()


@asynccontextmanager
async def lifespan(server: FastAPI):
    server.state.feed = (
        Feed('https://news.ycombinator.com/rss')
        .filter(lambda entry: 'llm' not in entry.get('title', '').lower())
        .filter(lambda entry: 'ai ' not in entry.get('title', '').lower())
    )
    print("Feed size: ", len(server.state.feed.entries))
    yield

@app.get('/rss')
async def get_rss_feed():
    """
    Get the RSS feed content in XML format for standard RSS clients.
    Uses the feed that was previously loaded into the Feed class.

    Returns:
        RSS feed content in XML format with appropriate content type
    """
    global feed
    return Response(
        content=feed.raw_content,
        media_type='application/rss+xml'
    )


if __name__ == '__main__':
    uvicorn.run('api:app', reload=True)

# Smarter RSS proxy

Dead simple Python service for on-the-fly RSS filtering. Specify URL, topics you want to exclude and fetch the new feed.

## Features
- Excluding content of specified topics 
- Excluding content with certain keywords in the title
- Web interface for easy setup

## How to run
Sign in to [OpenRouter](https://openrouter.ai/settings/keys) and generate the API key. 
Important: set credit limit for a newly generated key.
   ```
   git clone https://github.com/usasha/smarter_rss_proxy.git
   cd smarter_rss_proxy
   docker build -t smarter_rss_proxy .
   docker run -p 8000:8000 -e OPENROUTER_API_KEY=YOUR_API_KEY smarter_rss_proxy
   ```

## Usage
Fetch news.ycombinator.com RSS feed and exclude anything about AI or politics and news in general: 
```
curl http://localhost:8000/rss/content_type/exclude?url=https%3A%2F%2Fnews.ycombinator.com%2Frss&content_types=politics%2C%20news%2C%20ai
```
Fetch news.ycombinator.com RSS feed and exclude with "OpenAI" in the title:
```
curl http://localhost:8000/rss/keywords/exclude?url=https%3A%2F%2Fnews.ycombinator.com%2Frss&keywords=OpenAI
```
You can use a web UI to construct these URLs: http://localhost:8000

### API Documentation
Swagger interactive docs: http://localhost:8000/docs

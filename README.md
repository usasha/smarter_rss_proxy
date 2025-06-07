# RSS Feed Loader

A simple Python script for loading and displaying RSS feeds from specified URLs.

## Features

- Load RSS feeds from any valid URL
- Display feed information (title, link, description)
- Display feed entries with title, publication date, link, and summary
- Command-line interface with customizable options
- Error handling for network and parsing issues
- Can be used as a standalone script or imported as a module

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/smart_rss_proxy.git
   cd smart_rss_proxy
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Command-line Usage

Basic usage:
```
python src/rss_loader.py URL
```

Or if you've made the script executable:
```
./src/rss_loader.py URL
```

Where `URL` is the URL of the RSS feed you want to load.

#### Options

- `-l, --limit N`: Display only N entries (default: 10)
- `-i, --info-only`: Display only feed information, not entries

#### Examples

Load and display a feed with default settings:
```
python src/rss_loader.py https://news.ycombinator.com/rss
```

Load a feed and display only 5 entries:
```
python src/rss_loader.py https://news.ycombinator.com/rss --limit 5
```

Load a feed and display only the feed information:
```
python src/rss_loader.py https://news.ycombinator.com/rss --info-only
```

### Using as a Module

You can also import the RSS loader functions in your own Python scripts:

```python
from rss_loader import load_rss_feed

# Load an RSS feed
feed = load_rss_feed("https://news.ycombinator.com/rss")

# Access feed information
feed_title = feed['feed'].get('title', 'Unknown')
print(f"Feed Title: {feed_title}")

# Process feed entries
entries = feed.get('entries', [])
for entry in entries[:5]:
    print(entry.get('title', 'No title'))
```

See `src/example_usage.py` for a complete example of using the RSS loader as a module.

## Testing

To test the RSS loader functionality:

```
python tests/test_rss_loader.py
```

Or if you've made the test script executable:
```
./tests/test_rss_loader.py
```

## Error Handling

The script handles various error scenarios:
- Network connection issues
- Invalid URLs
- Invalid RSS feed format
- Timeouts

If an error occurs, an appropriate error message will be displayed, and the script will exit with a non-zero status code.

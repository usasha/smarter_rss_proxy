import feedparser
import requests
from typing import Dict, List, Any, Optional, Callable


class Feed:
    def __init__(self, url) -> None:
        self.url = url
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        self.feed = feedparser.parse(response.content)

        assert self.feed.get('bozo') != 1 and self.feed.get('entries'), 'Error parsing feed'

    @property
    def info(self) -> Dict[str, Any]:
        """
        Information about the feed
        :return: main info about the feed
        """
        feed_info = self.feed.get('feed', {})
        return {
            'title': feed_info.get('title', 'Unknown'),
            'link': feed_info.get('link', 'Unknown'),
            'description': feed_info.get('subtitle', 'No description available'),
            'entry_count': len(self.feed.get('entries', [])),
            'url': self.url
        }

    @property
    def entries(self) -> List[Dict[str, Any]]:
        """
        :return: Feed entries.
        """
        return self.feed.get('entries', [])

    def filter_entries(self, filter_function: Callable) -> List[Dict[str, Any]]:
        """
        Filter feed entries by a provided function.
        :param filter_function: accepts entry, return True if entry should be kept, False otherwise
        :return: feed entries filtered by the provided function
        """
        return [
            entry
            for entry in self.feed.entries
            if filter_function(entry)
        ]

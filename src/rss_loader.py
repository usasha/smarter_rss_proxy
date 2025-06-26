import feedparser
import requests
from typing import Dict, List, Any, Callable
import xml.etree.ElementTree as ET


class Feed:
    def __init__(self, url) -> None:
        self.url = url.lower().strip()
        response = requests.get(self.url, timeout=10)
        response.raise_for_status()
        self.raw_content = response.content
        self.feed = feedparser.parse(self.raw_content)

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

    def filter(self, filter_function: Callable) -> 'Feed':
        """
        Filter feed entries by a provided function.
        :param filter_function: accepts entry, returns True if entry should be kept, False otherwise
        :return: self with filtered entries
        """
        root = ET.fromstring(self.raw_content)
        channel = root.find('channel')
        for item in channel.findall('item'):
            if not filter_function(feedparser.parse(ET.tostring(item)).entries[0]):
                channel.remove(item)
                
        self.raw_content = ET.tostring(root)
        self.feed = feedparser.parse(self.raw_content)
        return self

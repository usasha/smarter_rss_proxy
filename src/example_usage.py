#!/usr/bin/env python3
"""
Example script demonstrating how to use the RSS loader as a module.
"""
from typing import Any

from rss_loader import Feed


def filter_clickbait(entry: Any) -> bool:
    """
    Filters out entries containing specific keywords to avoid clickbait.

    :param entry: A dictionary-like object containing an entry, which
        includes a 'title' key with a string value representing the title
        of the entry.
    :return: A boolean value - True if the entry is not classified as
        clickbait, otherwise False.
    """
    return (
        'llm' not in entry.get('title', '').lower()
        and 'ai ' not in entry.get('title', '').lower()
    )


def main():
    feed_url = "https://news.ycombinator.com/rss"
    print(f"Loading RSS feed from: {feed_url}")

    feed = Feed(feed_url)

    print("-" * 50)
    entries = feed.entries
    print(f"Retrieved {len(entries)} entries")

    for i, entry in enumerate(entries[:5]):
        title = entry.get('title', 'No title')
        link = entry.get('link', 'No link')
        print(f"{i+1}. {title}")
        print(f"   Link: {link}")

    print("-" * 50)
    print(f"Entries before filters: {len(feed.entries)}")
    print(f"Entries after filters: {len(feed.filter(filter_clickbait).entries)}")


if __name__ == "__main__":
    main()

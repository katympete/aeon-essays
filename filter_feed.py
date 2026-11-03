#!/usr/bin/env python3
"""Fetch Aeon's RSS feed and write a copy with video items removed.

Usage:
    python filter_feed.py [SOURCE] [OUTPUT]

SOURCE  feed URL or local file path (default: https://aeon.co/feed.rss)
OUTPUT  where to write the filtered feed (default: docs/feed.xml)

Standard library only. Exits with an error (leaving any existing output
untouched) if the fetch fails or no items survive the filter.
"""
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

SOURCE = sys.argv[1] if len(sys.argv) > 1 else "https://aeon.co/feed.rss"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "docs/feed.xml"

# Keep items whose link contains this; everything else (videos) is dropped.
KEEP = "/essays/"

# Register namespaces so the output keeps the dc: and atom: prefixes.
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")


def read(source: str) -> bytes:
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(
            source, headers={"User-Agent": "aeon-essays-filter/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    with open(source, "rb") as f:
        return f.read()


def main() -> int:
    root = ET.fromstring(read(SOURCE))
    channel = root.find("channel")
    if channel is None:
        print("No <channel> found; not an RSS feed?", file=sys.stderr)
        return 1

    items = channel.findall("item")
    kept = 0
    for item in items:
        link = (item.findtext("link") or "").strip()
        if KEEP in link:
            kept += 1
        else:
            channel.remove(item)

    if kept == 0:
        print(f"0 of {len(items)} items kept; refusing to write.", file=sys.stderr)
        return 1

    title = channel.find("title")
    if title is not None:
        title.text = (title.text or "Aeon") + " (essays only)"

    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    ET.ElementTree(root).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Kept {kept} of {len(items)} items -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

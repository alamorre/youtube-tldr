#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["youtube-transcript-api==1.2.4"]
# ///
"""Fetch timestamped YouTube captions and basic metadata; never summarize."""

import argparse
import json
import re
import sys
from urllib.parse import parse_qs, urlsplit


def video_id(value):
    """Accept a video ID or known YouTube video URL, never an arbitrary host."""
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    parsed = urlsplit(value if "://" in value else "https://" + value)
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise ValueError("Expected a YouTube video URL or 11-character video ID.")
    host = parsed.hostname
    parts = parsed.path.strip("/").split("/")
    candidate = ""
    if host in {"youtu.be", "www.youtu.be"} and len(parts) == 1:
        candidate = parts[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parts == ["watch"]:
            candidates = parse_qs(parsed.query).get("v", [])
            candidate = candidates[0] if len(candidates) == 1 else ""
        elif len(parts) == 2 and parts[0] in {"shorts", "live", "embed"}:
            candidate = parts[1]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        raise ValueError("Expected a YouTube watch/share/Shorts/live URL with a valid video ID.")
    return candidate


def timestamp(seconds):
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{secs:02}" if hours else f"{minutes}:{secs:02}"


def transcript_payload(fetched, metadata=None, metadata_error=None):
    url = f"https://www.youtube.com/watch?v={fetched.video_id}"
    segments = [
        {
            "start_seconds": item.start,
            "duration_seconds": item.duration,
            "timestamp": timestamp(item.start),
            "url": f"{url}&t={max(0, int(item.start))}s",
            "text": item.text,
        }
        for item in fetched
    ]
    if not segments:
        raise ValueError("YouTube returned an empty transcript.")
    return {
        "video_id": fetched.video_id,
        "url": url,
        "metadata": metadata,
        "metadata_error": metadata_error,
        "language": fetched.language,
        "language_code": fetched.language_code,
        "is_generated": fetched.is_generated,
        "last_caption_end_seconds": max(s["start_seconds"] + s["duration_seconds"] for s in segments),
        "segments": segments,
    }


def fetch(identifier):
    import requests
    from youtube_transcript_api import YouTubeTranscriptApi

    class TimeoutSession(requests.Session):
        def request(self, method, url, **kwargs):
            kwargs.setdefault("timeout", 20)
            return super().request(method, url, **kwargs)

    with TimeoutSession() as session:
        fetched = YouTubeTranscriptApi(http_client=session).fetch(
            identifier, languages=["en", "en-US", "en-GB"]
        )
        metadata, metadata_error = None, None
        try:
            response = session.get("https://www.youtube.com/oembed", params={
                "url": f"https://www.youtube.com/watch?v={identifier}", "format": "json"
            })
            response.raise_for_status()
            raw = response.json()
            metadata = {key: raw.get(key) for key in ("title", "author_name", "author_url")}
        except (requests.RequestException, ValueError) as exc:
            metadata_error = type(exc).__name__
        return transcript_payload(fetched, metadata, metadata_error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="YouTube video URL or video ID")
    args = parser.parse_args()
    try:
        identifier = video_id(args.url)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        payload = fetch(identifier)
    except Exception as exc:
        # Do not dump response bodies or tracebacks into an agent's context.
        print(json.dumps({
            "error": type(exc).__name__,
            "video_id": identifier,
            "message": "Caption retrieval failed. Try YouTube's transcript UI or a user-provided transcript; do not infer content from the title.",
        }), file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

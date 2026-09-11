# youtube-tldr

The takeaway and the evidence, in about a minute.

An agent skill that turns a YouTube video from any creator into:

- A **1–2 sentence TLDR** of the actual argument.
- **3–5 key points** prioritizing statistics, demonstrations, and primary evidence, with timestamps and source links where available.

Skips sponsors, repetition, and clickbait framing. Separates opinions from verified facts. Targets 120–180 words. When a video has little hard evidence, it says so; when a transcript cannot be accessed, it asks for one instead of inventing a summary.

## Install

For Codex, clone into your personal skills directory:

```sh
git clone https://github.com/alamorre/youtube-tldr.git "${CODEX_HOME:-$HOME/.codex}/skills/youtube-tldr"
```

Start a new session if the skill does not appear in your current session's skill list. For another agent that supports `SKILL.md`, place this folder in its documented skill directory.

## Use

```text
$youtube-tldr https://www.youtube.com/watch?v=VIDEO_ID
```

Replace `VIDEO_ID` with a real video ID. You can use a `youtu.be` share link too, or provide a transcript directly.

## Transcript access

The agent needs access to video captions through a transcript tool, browser, or the included helper. Primary-source verification also needs browsing. The helper requires Python 3.10+ and [uv](https://docs.astral.sh/uv/):

```sh
uv run scripts/fetch_transcript.py 'https://www.youtube.com/watch?v=VIDEO_ID'
```

`uv` installs the script's declared dependency in an isolated environment. The helper uses [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) and YouTube metadata, with no API key. It retrieves captions only; the agent performs the summary. YouTube can block automated access or have no captions. The skill then tries another available transcript route or asks for a pasted transcript. It does not bypass access restrictions.

Full transcripts are temporary working material, not intended output or repository content.

## Development

```sh
python3 -m unittest discover -s tests -v
```

MIT licensed. Created by Adam La Morre. Unofficial; not affiliated with YouTube or any video creator.

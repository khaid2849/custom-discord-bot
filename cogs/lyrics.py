import asyncio
import re
import unicodedata

import aiohttp
import discord
from discord.ext import commands

from logger import get_logger

logger = get_logger("Lyrics")

LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"
USER_AGENT = "custom-discord-bot (https://github.com/khaid2849/custom-discord-bot)"

# Embed descriptions are capped at 4096 chars; leave room for the "..." marker
PAGE_SIZE = 4000
MAX_PAGES = 3

# Noise commonly found in YouTube titles that hurts lyric search
_BRACKETS = re.compile(r"[\(\[【「].*?[\)\]】」]")
_NOISE = re.compile(
    r"\b(official\s*(music\s*)?(video|audio|mv|lyrics?(\s*video)?)|lyrics?\s*video|lyrics?|"
    r"mv|m/v|audio|video|hd|4k|visualizer|live|karaoke|vietsub|engsub)\b",
    re.IGNORECASE,
)
_TIMESTAMP = re.compile(r"^\[\d+:\d+(?:\.\d+)?\]\s?", re.MULTILINE)


def _clean_part(text):
    text = _NOISE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip(" -–—~,.")


def clean_artist(channel):
    """YouTube channels look like 'Artist - Topic', 'ArtistVEVO' or 'Artist Official'; drop the suffix"""
    if not channel:
        return None
    channel = re.sub(r"\s*-\s*Topic$", "", channel)
    channel = re.sub(r"VEVO$|\s+Official$", "", channel, flags=re.IGNORECASE)
    return channel.strip() or None


def parse_title(title, channel=None):
    """Guess (song, artist) from a YouTube title such as 'Artist - Song (Official MV)' or 'Artist | Song | MV'"""
    stripped = _BRACKETS.sub(" ", title)
    parts = [_clean_part(p) for p in re.split(r"\s+[-–—|]\s+|\|", stripped)]
    parts = [p for p in parts if p]
    if len(parts) >= 2:
        return parts[1], parts[0]
    return (parts[0] if parts else title), clean_artist(channel)


def _normalize(text):
    """Lowercase, drop Vietnamese/other diacritics and punctuation for loose comparison"""
    text = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", " ", text.casefold()).split()


def is_match(title, artist, item):
    """Check an LRCLIB result is really the song we asked for, not just a word-level hit"""
    wanted = set(_normalize(title))
    track = set(_normalize(item.get("trackName") or ""))
    if not wanted or len(wanted & track) / len(wanted) < 0.6:
        return False
    if artist and set(_normalize(artist)) & set(_normalize(item.get("artistName") or "")):
        return True
    # Artist unknown or unreliable (e.g. uploader channel): the track names must be near-identical
    return len(wanted & track) / len(track) >= 0.8


def split_pages(text):
    """Split lyrics into embed-sized pages, breaking on line boundaries"""
    pages, current = [], ""
    for line in text.splitlines():
        if len(current) + len(line) + 1 > PAGE_SIZE:
            pages.append(current)
            current = ""
        current += line + "\n"
    if current.strip():
        pages.append(current)
    return pages


class Lyrics(commands.Cog):
    """Lyrics lookup for the current song"""

    def __init__(self, bot):
        self.bot = bot
        self.session = None
        logger.info("Lyrics cog initialized")

    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=10),
        )

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def _search(self, params, retries=2):
        for attempt in range(retries + 1):
            async with self.session.get(LRCLIB_SEARCH_URL, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                # LRCLIB returns 5xx intermittently under load; a short wait usually fixes it
                if resp.status < 500 or attempt == retries:
                    logger.warning(f"LRCLIB returned HTTP {resp.status} for {params}")
                    return []
            await asyncio.sleep(1 + attempt)

    async def find_lyrics(self, title, artist=None):
        """Return the best LRCLIB match that has lyrics, or None"""
        attempts = []
        if artist:
            attempts.append({"track_name": title, "artist_name": artist})
            attempts.append({"q": f"{artist} {title}"})
        attempts.append({"q": title})

        for params in attempts:
            results = await self._search(params)
            for item in results:
                if item.get("instrumental") or not is_match(title, artist, item):
                    continue
                if item.get("plainLyrics") or item.get("syncedLyrics"):
                    return item
        return None

    @commands.command(name='lyrics', aliases=['ly'], help='Show lyrics of the current song (or a given song)')
    async def lyrics(self, ctx, *, query: str = None):
        """
        Show lyrics of the current song
        Usage: !lyrics            -> current song
               !lyrics <song name> -> search a specific song
        """
        artist = None
        if query:
            title = query
        else:
            source = ctx.voice_client.source if ctx.voice_client else None
            if not source or not getattr(source, 'title', None):
                await ctx.send("❌ No music is playing! Use `!lyrics <song name>` to search.")
                return
            data = getattr(source, 'data', {}) or {}
            # yt-dlp fills track/artist for music uploads; otherwise guess from the video title
            if data.get('track'):
                title, artist = data['track'], data.get('artist')
            else:
                title, artist = parse_title(source.title, getattr(source, 'channel', None))

        async with ctx.typing():
            try:
                result = await self.find_lyrics(title, artist)
            except Exception as e:
                logger.error(f"Lyrics lookup failed for '{title}': {e}")
                await ctx.send("❌ Could not reach the lyrics service. Please try again later.")
                return

        if not result:
            logger.info(f"No lyrics found for '{title}' (artist: {artist})")
            await ctx.send(f"❌ No lyrics found for **{title}**. Try `!lyrics <artist> <song name>`.")
            return

        text = result.get("plainLyrics") or _TIMESTAMP.sub("", result.get("syncedLyrics", ""))
        pages = split_pages(text.strip())
        truncated = len(pages) > MAX_PAGES
        pages = pages[:MAX_PAGES]
        if truncated:
            pages[-1] += "\n..."

        logger.info(f"Lyrics found for '{title}': {result.get('artistName')} - {result.get('trackName')}")

        for i, page in enumerate(pages):
            embed = discord.Embed(description=page, color=discord.Color.purple())
            if i == 0:
                embed.title = f"🎤 {result.get('trackName', title)}"
                embed.set_author(name=result.get('artistName', 'Unknown artist'))
            if i == len(pages) - 1:
                embed.set_footer(text="Lyrics from LRCLIB")
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Lyrics(bot))
    logger.info("Lyrics cog loaded successfully")

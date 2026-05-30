"""
audio_engine.py
Handles all music data fetching:
  - ytmusicapi  → search, radio queue, playlist metadata
  - yt-dlp      → extract best audio-only stream URL (Opus 160kbps)
"""

import yt_dlp
from ytmusicapi import YTMusic


class AudioEngine:

    def __init__(self):
        # YTMusic() with no args = unauthenticated (works for search + radio)
        self.ytm = YTMusic()

    # ── Search ─────────────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 20) -> list:
        """
        Returns list of dicts: {title, artist, video_id}
        Uses YouTube Music's search so results are music-focused,
        not random YouTube uploads.
        """
        try:
            results = self.ytm.search(query, filter="songs", limit=limit)
            tracks = []
            for r in results:
                vid = r.get('videoId')
                if not vid:
                    continue
                tracks.append({
                    'title':    r.get('title', 'Unknown'),
                    'artist':   r['artists'][0]['name'] if r.get('artists') else 'Unknown Artist',
                    'video_id': vid,
                })
            return tracks
        except Exception as e:
            print(f"[AudioEngine] Search error: {e}")
            return []

    # ── Radio / Endless Queue ──────────────────────────────────────────────

    def get_radio_queue(self, video_id: str, limit: int = 25) -> list:
        """
        Uses YouTube Music's internal watch playlist (the same engine as
        YT Music's radio feature) to get ~25 related tracks seeded by
        a single video ID.
        """
        try:
            data = self.ytm.get_watch_playlist(videoId=video_id, limit=limit)
            tracks = []
            for t in data.get('tracks', []):
                vid = t.get('videoId')
                if not vid:
                    continue
                tracks.append({
                    'title':    t.get('title', 'Unknown'),
                    'artist':   t['artists'][0]['name'] if t.get('artists') else 'Unknown Artist',
                    'video_id': vid,
                })
            return tracks
        except Exception as e:
            print(f"[AudioEngine] Radio queue error: {e}")
            return []

    # ── Playlist ───────────────────────────────────────────────────────────

    def get_playlist(self, url_or_id: str, limit: int = 100) -> list:
        """
        Loads a YouTube Music playlist by URL or playlist ID.
        Accepts full URLs like:
          https://music.youtube.com/playlist?list=PLxxxxxxxx
        or just the ID: PLxxxxxxxx
        """
        try:
            # Extract playlist ID from URL if needed
            playlist_id = url_or_id.strip()
            if 'list=' in playlist_id:
                playlist_id = playlist_id.split('list=')[1].split('&')[0]

            data = self.ytm.get_playlist(playlist_id, limit=limit)
            tracks = []
            for t in data.get('tracks', []):
                vid = t.get('videoId')
                if not vid:
                    continue
                tracks.append({
                    'title':    t.get('title', 'Unknown'),
                    'artist':   t['artists'][0]['name'] if t.get('artists') else 'Unknown Artist',
                    'video_id': vid,
                })
            return tracks
        except Exception as e:
            print(f"[AudioEngine] Playlist error: {e}")
            return []

    # ── Stream URL Extraction ──────────────────────────────────────────────

    def get_stream_url(self, video_id: str) -> str | None:
        """
        Uses yt-dlp to extract a direct audio stream URL.
        Format priority:
          1. Best Opus/WebM (160kbps — most efficient, excellent quality)
          2. Best M4A/AAC   (fallback)
          3. Any best audio (last resort)
        No downloading — just extracts the temporary stream URL.
        """
        ydl_opts = {
            # Prefer audio-only Opus (most battery-efficient, best quality/size ratio)
            'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'skip_download': True,
            # Prevent yt-dlp from trying to merge video+audio
            'postprocessors': [],
        }
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info.get('url')
                if stream_url:
                    print(f"[AudioEngine] Stream ready: {info.get('ext')} "
                          f"{info.get('abr', '?')}kbps")
                return stream_url
        except Exception as e:
            print(f"[AudioEngine] Stream URL error for {video_id}: {e}")
            return None

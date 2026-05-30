"""
MyMusic - main.py
Dark-themed KivyMD music player UI.
Tabs: Search | Speed Dials | Now Playing
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, TwoLineListItem
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivy.clock import Clock
from kivy.lang import Builder
import threading
import json
import os

from audio_engine import AudioEngine
from player_service import PlayerService

KV = '''
MDBoxLayout:
    orientation: "vertical"

    MDBottomNavigation:
        panel_color: 0.1, 0.1, 0.1, 1
        selected_color_background: 0.4, 0.2, 0.8, 0.2
        text_color_active: 0.7, 0.4, 1, 1

        # ── TAB 1: SEARCH ──────────────────────────────────
        MDBottomNavigationItem:
            name: "search"
            text: "Search"
            icon: "magnify"

            MDBoxLayout:
                orientation: "vertical"
                padding: "12dp"
                spacing: "10dp"
                md_bg_color: 0.07, 0.07, 0.07, 1

                MDLabel:
                    text: "MyMusic"
                    font_style: "H4"
                    halign: "left"
                    size_hint_y: None
                    height: "48dp"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.4, 1, 1

                MDTextField:
                    id: search_field
                    hint_text: "Search songs, artists, albums..."
                    mode: "rectangle"
                    line_color_focus: 0.7, 0.4, 1, 1
                    on_text_validate: app.do_search(self.text)
                    size_hint_y: None
                    height: "48dp"

                MDRaisedButton:
                    text: "Search"
                    md_bg_color: 0.4, 0.2, 0.8, 1
                    size_hint_x: 1
                    on_release: app.do_search(search_field.text)

                MDScrollView:
                    MDList:
                        id: search_results

        # ── TAB 2: SPEED DIALS ─────────────────────────────
        MDBottomNavigationItem:
            name: "dials"
            text: "Dials"
            icon: "lightning-bolt"

            MDScrollView:
                md_bg_color: 0.07, 0.07, 0.07, 1

                MDBoxLayout:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "16dp"
                    adaptive_height: True

                    MDLabel:
                        text: "Speed Dials"
                        font_style: "H5"
                        size_hint_y: None
                        height: "48dp"
                        theme_text_color: "Custom"
                        text_color: 0.7, 0.4, 1, 1

                    MDCard:
                        orientation: "vertical"
                        padding: "12dp"
                        spacing: "8dp"
                        size_hint_y: None
                        height: "160dp"
                        md_bg_color: 0.13, 0.13, 0.13, 1
                        radius: [12]
                        MDLabel:
                            text: "⚡ Dial 1"
                            font_style: "H6"
                            size_hint_y: None
                            height: "32dp"
                        MDTextField:
                            id: dial1_field
                            hint_text: "YouTube Music playlist URL"
                            mode: "rectangle"
                        MDRaisedButton:
                            text: "Save & Play Dial 1"
                            md_bg_color: 0.4, 0.2, 0.8, 1
                            on_release: app.save_and_play_dial(1, dial1_field.text)

                    MDCard:
                        orientation: "vertical"
                        padding: "12dp"
                        spacing: "8dp"
                        size_hint_y: None
                        height: "160dp"
                        md_bg_color: 0.13, 0.13, 0.13, 1
                        radius: [12]
                        MDLabel:
                            text: "⚡ Dial 2"
                            font_style: "H6"
                            size_hint_y: None
                            height: "32dp"
                        MDTextField:
                            id: dial2_field
                            hint_text: "YouTube Music playlist URL"
                            mode: "rectangle"
                        MDRaisedButton:
                            text: "Save & Play Dial 2"
                            md_bg_color: 0.4, 0.2, 0.8, 1
                            on_release: app.save_and_play_dial(2, dial2_field.text)

                    MDCard:
                        orientation: "vertical"
                        padding: "12dp"
                        spacing: "8dp"
                        size_hint_y: None
                        height: "160dp"
                        md_bg_color: 0.13, 0.13, 0.13, 1
                        radius: [12]
                        MDLabel:
                            text: "⚡ Dial 3"
                            font_style: "H6"
                            size_hint_y: None
                            height: "32dp"
                        MDTextField:
                            id: dial3_field
                            hint_text: "YouTube Music playlist URL"
                            mode: "rectangle"
                        MDRaisedButton:
                            text: "Save & Play Dial 3"
                            md_bg_color: 0.4, 0.2, 0.8, 1
                            on_release: app.save_and_play_dial(3, dial3_field.text)

        # ── TAB 3: NOW PLAYING ─────────────────────────────
        MDBottomNavigationItem:
            name: "playing"
            text: "Playing"
            icon: "music-note"

            MDBoxLayout:
                orientation: "vertical"
                padding: "24dp"
                spacing: "20dp"
                md_bg_color: 0.07, 0.07, 0.07, 1

                MDLabel:
                    id: np_title
                    text: "No track playing"
                    font_style: "H5"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    id: np_artist
                    text: "Tap Search to find music"
                    font_style: "Subtitle1"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.6, 0.6, 0.6, 1

                MDLabel:
                    id: np_status
                    text: ""
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.4, 1, 1

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "64dp"
                    spacing: "16dp"
                    padding: "24dp", 0

                    MDIconButton:
                        icon: "skip-previous"
                        theme_icon_color: "Custom"
                        icon_color: 0.7, 0.4, 1, 1
                        on_release: app.prev_track()

                    MDRaisedButton:
                        id: play_pause_btn
                        text: "▶  Play"
                        md_bg_color: 0.4, 0.2, 0.8, 1
                        size_hint_x: 1
                        on_release: app.toggle_play()

                    MDIconButton:
                        icon: "skip-next"
                        theme_icon_color: "Custom"
                        icon_color: 0.7, 0.4, 1, 1
                        on_release: app.next_track()

                MDLabel:
                    id: queue_label
                    text: "Queue: empty"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.5, 0.5, 0.5, 1
'''


class MyMusicApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"

        self.audio = AudioEngine()
        self.player = PlayerService()

        self.queue = []
        self.current_index = 0
        self.dials = self._load_dials()

        root = Builder.load_string(KV)
        self._restore_dial_fields(root)
        return root

    # ── Persistence ────────────────────────────────────────

    def _dials_path(self):
        return os.path.join(os.path.dirname(__file__), "dials.json")

    def _load_dials(self):
        p = self._dials_path()
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
        return {"1": "", "2": "", "3": ""}

    def _save_dials(self):
        with open(self._dials_path(), "w") as f:
            json.dump(self.dials, f)

    def _restore_dial_fields(self, root):
        nav = root.children[0]  # MDBottomNavigation
        for item in nav.children:
            if hasattr(item, 'name') and item.name == 'dials':
                try:
                    scroll = item.children[0]
                    box = scroll.children[0]
                    cards = [c for c in box.children if isinstance(c, MDCard)]
                    for i, card in enumerate(reversed(cards)):
                        for child in card.children:
                            if isinstance(child, MDTextField):
                                child.text = self.dials.get(str(i + 1), "")
                except Exception:
                    pass

    # ── Search ─────────────────────────────────────────────

    def do_search(self, query):
        if not query.strip():
            return
        self.root.ids.np_status.text = "Searching..."
        threading.Thread(
            target=self._search_thread, args=(query,), daemon=True
        ).start()

    def _search_thread(self, query):
        results = self.audio.search(query)
        Clock.schedule_once(lambda dt: self._show_results(results), 0)

    def _show_results(self, results):
        result_list = self.root.ids.search_results
        result_list.clear_widgets()
        self.root.ids.np_status.text = f"{len(results)} results"
        for track in results:
            label = f"{track['title']}  •  {track['artist']}"
            item = TwoLineListItem(
                text=track['title'],
                secondary_text=track['artist'],
                on_release=lambda x, t=track: self._start_radio(t)
            )
            result_list.add_widget(item)

    # ── Radio / Playback ───────────────────────────────────

    def _start_radio(self, seed_track):
        self.root.ids.np_title.text = seed_track['title']
        self.root.ids.np_artist.text = seed_track['artist']
        self.root.ids.np_status.text = "Building radio queue..."
        threading.Thread(
            target=self._radio_thread, args=(seed_track,), daemon=True
        ).start()

    def _radio_thread(self, seed_track):
        queue = self.audio.get_radio_queue(seed_track['video_id'])
        if not queue:
            Clock.schedule_once(
                lambda dt: setattr(self.root.ids.np_status, 'text', 'Radio failed — try again'), 0
            )
            return
        self.queue = queue
        self.current_index = 0
        Clock.schedule_once(lambda dt: self._play_current(), 0)

    def save_and_play_dial(self, number, url):
        if not url.strip():
            return
        self.dials[str(number)] = url.strip()
        self._save_dials()
        self.root.ids.np_status.text = f"Loading Dial {number}..."
        threading.Thread(
            target=self._playlist_thread, args=(url,), daemon=True
        ).start()

    def _playlist_thread(self, url):
        tracks = self.audio.get_playlist(url)
        if not tracks:
            Clock.schedule_once(
                lambda dt: setattr(self.root.ids.np_status, 'text', 'Playlist load failed'), 0
            )
            return
        self.queue = tracks
        self.current_index = 0
        Clock.schedule_once(lambda dt: self._play_current(), 0)

    def _play_current(self):
        if not self.queue or self.current_index >= len(self.queue):
            return
        track = self.queue[self.current_index]
        self.root.ids.np_title.text = track.get('title', 'Unknown')
        self.root.ids.np_artist.text = track.get('artist', '')
        self.root.ids.np_status.text = "Buffering stream..."
        self.root.ids.queue_label.text = (
            f"Track {self.current_index + 1} of {len(self.queue)}"
        )
        self.root.ids.play_pause_btn.text = "⏸  Pause"
        threading.Thread(
            target=self._stream_thread, args=(track,), daemon=True
        ).start()

    def _stream_thread(self, track):
        url = self.audio.get_stream_url(track['video_id'])
        if url:
            self.player.play(url)
            self.player.set_on_complete(self.next_track)
            Clock.schedule_once(
                lambda dt: setattr(self.root.ids.np_status, 'text', 'Playing  ♫'), 0
            )
        else:
            Clock.schedule_once(
                lambda dt: self.next_track(), 0  # skip broken tracks
            )

    # ── Controls ───────────────────────────────────────────

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.root.ids.play_pause_btn.text = "▶  Play"
            self.root.ids.np_status.text = "Paused"
        else:
            self.player.resume()
            self.root.ids.play_pause_btn.text = "⏸  Pause"
            self.root.ids.np_status.text = "Playing  ♫"

    def next_track(self):
        if self.current_index < len(self.queue) - 3:
            self.current_index += 1
            Clock.schedule_once(lambda dt: self._play_current(), 0)
        else:
            # Refill radio queue near the end
            threading.Thread(target=self._refill_queue, daemon=True).start()

    def prev_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            Clock.schedule_once(lambda dt: self._play_current(), 0)

    def _refill_queue(self):
        if not self.queue:
            return
        last = self.queue[-1]
        new_tracks = self.audio.get_radio_queue(last['video_id'])
        # Avoid duplicates
        existing_ids = {t['video_id'] for t in self.queue}
        fresh = [t for t in new_tracks[1:] if t['video_id'] not in existing_ids]
        self.queue.extend(fresh)
        self.current_index += 1
        Clock.schedule_once(lambda dt: self._play_current(), 0)


if __name__ == "__main__":
    MyMusicApp().run()

"""
player_service.py

Android native audio playback via Pyjnius.
On Android:  Uses MediaPlayer + PARTIAL_WAKE_LOCK (screen-off safe)
Off Android: Stub mode so the app can be tested on desktop
"""

# ── Try to import Android / Pyjnius ───────────────────────────────────────

ANDROID = False
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method

    MediaPlayer      = autoclass('android.media.MediaPlayer')
    AudioAttributes  = autoclass('android.media.AudioAttributes')
    AABuilder        = autoclass('android.media.AudioAttributes$Builder')
    Context          = autoclass('android.content.Context')
    PowerManager     = autoclass('android.os.PowerManager')
    PythonActivity   = autoclass('org.kivy.android.PythonActivity')

    ANDROID = True
    print("[PlayerService] Android mode active")
except Exception as e:
    print(f"[PlayerService] Stub mode (not Android): {e}")


# ── Listener classes (only defined when Pyjnius is available) ─────────────

if ANDROID:

    class _OnPreparedListener(PythonJavaClass):
        """Fires when MediaPlayer has buffered enough to start playing."""
        __javainterfaces__ = ['android/media/MediaPlayer$OnPreparedListener']

        def __init__(self, callback):
            super().__init__()
            self._cb = callback

        @java_method('(Landroid/media/MediaPlayer;)V')
        def onPrepared(self, mp):
            self._cb(mp)

    class _OnCompletionListener(PythonJavaClass):
        """Fires when a track finishes playing naturally."""
        __javainterfaces__ = ['android/media/MediaPlayer$OnCompletionListener']

        def __init__(self, callback):
            super().__init__()
            self._cb = callback

        @java_method('(Landroid/media/MediaPlayer;)V')
        def onCompletion(self, mp):
            self._cb()

    class _OnErrorListener(PythonJavaClass):
        """Fires if MediaPlayer hits a streaming error."""
        __javainterfaces__ = ['android/media/MediaPlayer$OnErrorListener']

        def __init__(self, callback):
            super().__init__()
            self._cb = callback

        @java_method('(Landroid/media/MediaPlayer;II)Z')
        def onError(self, mp, what, extra):
            self._cb(what, extra)
            return True  # True = error handled


# ── Main PlayerService class ───────────────────────────────────────────────

class PlayerService:

    def __init__(self):
        self._player        = None
        self._wake_lock     = None
        self._on_complete   = None
        self._playing       = False

        # Refs to keep listeners alive (prevents Python GC from killing them)
        self._prepared_listener   = None
        self._completion_listener = None
        self._error_listener      = None

        if ANDROID:
            self._init_wake_lock()

    # ── Wake Lock ─────────────────────────────────────────────────────────

    def _init_wake_lock(self):
        """
        Grabs a PARTIAL_WAKE_LOCK.
        This keeps the CPU running when the screen is off so audio doesn't stop.
        This is NOT a full wake lock — it won't prevent the screen from dimming.
        """
        try:
            activity = PythonActivity.mActivity
            pm = cast(PowerManager, activity.getSystemService(Context.POWER_SERVICE))
            self._wake_lock = pm.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK,
                "MyMusic::AudioWakeLock"
            )
            print("[PlayerService] Wake lock created")
        except Exception as e:
            print(f"[PlayerService] Wake lock error: {e}")

    def _acquire_wake(self):
        try:
            if self._wake_lock and not self._wake_lock.isHeld():
                self._wake_lock.acquire()
        except Exception as e:
            print(f"[PlayerService] acquire wake lock: {e}")

    def _release_wake(self):
        try:
            if self._wake_lock and self._wake_lock.isHeld():
                self._wake_lock.release()
        except Exception as e:
            print(f"[PlayerService] release wake lock: {e}")

    # ── Playback ──────────────────────────────────────────────────────────

    def play(self, stream_url: str):
        """Start playing a new stream URL. Stops any current track first."""
        if ANDROID:
            self._play_android(stream_url)
        else:
            print(f"[PlayerService STUB] Playing: {stream_url[:80]}...")
            self._playing = True

    def _play_android(self, stream_url: str):
        # 1. Release old player
        self._release_player()

        # 2. Acquire wake lock so audio survives screen-off
        self._acquire_wake()

        try:
            # 3. Build AudioAttributes (tells Android this is music, not ringtone/alarm)
            audio_attrs = (
                AABuilder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                .build()
            )

            # 4. Create MediaPlayer and configure
            self._player = MediaPlayer()
            self._player.setAudioAttributes(audio_attrs)
            self._player.setDataSource(stream_url)

            # 5. Attach listeners (hold refs to prevent GC)
            self._prepared_listener   = _OnPreparedListener(self._on_prepared)
            self._completion_listener = _OnCompletionListener(self._on_completion)
            self._error_listener      = _OnErrorListener(self._on_error)

            self._player.setOnPreparedListener(self._prepared_listener)
            self._player.setOnCompletionListener(self._completion_listener)
            self._player.setOnErrorListener(self._error_listener)

            # 6. Async prepare — calls _on_prepared when ready to play
            self._player.prepareAsync()
            self._playing = True

        except Exception as e:
            print(f"[PlayerService] _play_android error: {e}")
            self._release_wake()

    def _on_prepared(self, mp):
        """Called by Android when the stream is buffered and ready."""
        try:
            mp.start()
            print("[PlayerService] Playback started")
        except Exception as e:
            print(f"[PlayerService] start error: {e}")

    def _on_completion(self):
        """Called when the current track ends naturally."""
        print("[PlayerService] Track complete")
        self._playing = False
        self._release_wake()
        if self._on_complete:
            self._on_complete()

    def _on_error(self, what, extra):
        """Called on a MediaPlayer error (e.g. expired stream URL)."""
        print(f"[PlayerService] MediaPlayer error: what={what} extra={extra}")
        self._playing = False
        self._release_wake()
        # Treat errors the same as completion → skip to next track
        if self._on_complete:
            self._on_complete()

    # ── Controls ──────────────────────────────────────────────────────────

    def pause(self):
        if ANDROID and self._player:
            try:
                if self._player.isPlaying():
                    self._player.pause()
                    self._playing = False
            except Exception as e:
                print(f"[PlayerService] pause error: {e}")
        else:
            self._playing = False

    def resume(self):
        if ANDROID and self._player:
            try:
                self._player.start()
                self._playing = True
                self._acquire_wake()
            except Exception as e:
                print(f"[PlayerService] resume error: {e}")
        else:
            self._playing = True

    def stop(self):
        self._release_player()
        self._release_wake()

    def is_playing(self) -> bool:
        if ANDROID and self._player:
            try:
                return self._player.isPlaying()
            except Exception:
                return False
        return self._playing

    def set_on_complete(self, callback):
        """Register a callback to call when a track finishes."""
        self._on_complete = callback

    # ── Cleanup ───────────────────────────────────────────────────────────

    def _release_player(self):
        if self._player:
            try:
                self._player.stop()
            except Exception:
                pass
            try:
                self._player.release()
            except Exception:
                pass
            self._player = None
        self._playing = False
        # Clear listener refs
        self._prepared_listener   = None
        self._completion_listener = None
        self._error_listener      = None

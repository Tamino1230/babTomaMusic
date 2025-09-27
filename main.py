
# todo playing soundboard on your microphone


# import online
import sys
from urllib.parse import quote_plus
import tkinter as tk
from tkinter import filedialog, Listbox, ttk, messagebox, simpledialog
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
from tkinter import Toplevel
import requests
import os
from mutagen.mp3 import MP3
from yt_dlp import YoutubeDL
import random
from pypresence import Presence
import time
import pygame
import json
from collections import defaultdict
import webbrowser
import tkinter as tk
import threading
import keyboard
import shutil


# import files
import scripts.config as config
import scripts.show_help as hp


#! Pygame mixer init
pygame.mixer.init()


# var Global variables
by = config.by
playlist = []
current_index = 0
repeat_mode = False
is_playing = False
bgcolor = config.bgcolor
default_folder = config.default_folder
shuffle_mode = False
start_time = 0
rich_presence_enabled = config.default_discord_rich_presence
original_playlist = []
last_activity_time = time.time()
sjksaahd = by
max_volume = config.max_volume
record_actions = config.record_actions
error_message = config.error_message
cancel_flag = False
volume = 0.5  # safe default volume so RPC/state text and mixer volume have a value
rpc_status_var = None  # will be created only in debug (error_message)

#* not recommended
use_old_rpc_settings = config.use_old_rpc_settings


# var Sleep Timer
sleeptimer = config.sleeptimer
time_format = config.time_format.lower()

original_time_input = config.sleeplength

# var Time
start_time = time.time()


#? turning into different time format
try:
    if time_format == "s" or time_format == "second" or time_format == "seconds":
        sleeplength = config.sleeplength
    elif time_format == "m" or time_format == "minute" or time_format == "minutes":
        sleeplength = config.sleeplength * 60
    elif time_format == "h" or time_format == "hour" or time_format == "hours":
        sleeplength = config.sleeplength * 3600
    else:
        print(f"{time_format} isn't a real timeformat")
        time.sleep(3)
        exit()
except Exception as e:
    print(f"{time_format} isn't a real timeformat")
    time.sleep(3)
    exit()


# var Discord RPC Presence
show_repeat_shuffle = config.show_repeat_shuffle
playing_presence = config.playing_presence
paused_presence = config.paused_presence
idle_presence = config.idle_presence
default_discord_rich_presence = config.default_discord_rich_presence


# var HotKey Settings
hotkeys_active = config.hotkeys_active
pause_unpause_hotkey = config.pause_unpause_hotkey
next_song_hotkey = config.next_song_hotkey
last_song_hotkey = config.last_song_hotkey
sleep_mode_start_hotkey = config.sleep_mode_start_hotkey
add_volume_hotkey = config.add_volume_hotkey
remove_volume_hotkey = config.remove_volume_hotkey
repeat_toggle_hotkey = config.repeat_toggle_hotkey
deactivate_add_remove_volume = config.deactivate_add_remove_volume

volume_onhotkey = config.volume_onhotkey

#* Debugging
current_generated_details = ""
current_generated_state = ""
last_rpc_payload = {"details": None, "state": None, "large_image": None}

# var Global Hardcoded Presence
#? main.py
hardcoded_presence = config.hardcoded_presence
hardcoded_icon_path = config.hardcoded_icon_path
hardcoded_root_title = config.hardcoded_root_title
hardcoded_geometry = config.hardcoded_geometry
hardcoded_resizeable = config.hardcoded_resizeable
hardcoded_config = config.hardcoded_config
hardcoded_contact_url = config.hardcoded_contact_url
hardcoded_join_url = config.hardcoded_join_url
hardcoded_feedback_url = config.hardcoded_feedback_url
hardcoded_idea_url = config.hardcoded_idea_url
hardcoded_github_url = config.hardcoded_github_url
#? helping window
hardcoded_resizeable_hp = config.hardcoded_resizeable_hp
hardcoded_geometry_hp = config.hardcoded_geometry_hp
hardcoded_root_title_hp = config.hardcoded_root_title_hp


# var Soundboard
microphone_active = False


# var help
helpingtext = hp.helpingtext


# var  errors
errorcounter = 0


def erroradd():
    global errorcounter
    errorcounter = errorcounter + 1


def show_help():
    help_window = tk.Toplevel()
    help_window.title(hardcoded_root_title_hp)
    help_window.geometry(hardcoded_geometry_hp)
    help_window.resizable(False, False)
    try:
        help_window.iconbitmap(hardcoded_icon_path)
    except Exception:
        pass
    help_window.resizable(hardcoded_resizeable_hp, hardcoded_resizeable_hp)

    scrollbar = tk.Scrollbar(help_window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text = tk.Text(help_window, wrap=tk.WORD, yscrollcommand=scrollbar.set)
    text.pack(expand=True, fill=tk.BOTH)
    scrollbar.config(command=text.yview)
    
    help_text = helpingtext
    
    text.insert(tk.END, help_text)
    text.config(state=tk.DISABLED)
    
    close_button = tk.Button(help_window, text="Close", command=help_window.destroy)
    close_button.pack(pady=20)


# var custom presence settings
only_custom_rpc = config.only_custom_rpc
custom_rpc_text = config.custom_rpc_text

playing_custom_text_behind = config.playing_custom_text_behind
paused_custom_text_behind = config.paused_custom_text_behind
idle_custom_text_behind = config.idle_custom_text_behind


# var discord connection settings
CLIENT_ID = config.hardcoded_client_id #- will not work anymore if changed
RPC = Presence(CLIENT_ID)


try:
    RPC.connect()
    if error_message == True:
        print("Successfully connected with discord.")
    else:
        pass
except Exception as e:
    if error_message == True:
        print(f"Error while connecting with discord: {e}")
    else:
        pass


# RPC resiliency: throttle and backoff to keep the app smooth on poor connections
rpc_fail_count = 0
rpc_backoff_until = 0.0
last_rpc_call_at = 0.0
MIN_RPC_UPDATE_INTERVAL = 10  # seconds; avoid spamming Discord RPC


def _in_rpc_backoff():
    return time.time() < rpc_backoff_until


def _schedule_rpc_backoff():
    global rpc_fail_count, rpc_backoff_until
    rpc_fail_count = min(rpc_fail_count + 1, 8) # cap exponential growth
    delay = min(300, 2 ** rpc_fail_count) # up to 5 minutes
    rpc_backoff_until = time.time() + delay
    if error_message:
        print(f"RPC backoff for {int(delay)}s due to connection issue.")


def _reset_rpc_backoff():
    global rpc_fail_count, rpc_backoff_until
    rpc_fail_count = 0
    rpc_backoff_until = 0.0


def _safe_rpc_update(*, force: bool = False, **kwargs):
    global last_rpc_call_at
    if not rich_presence_enabled:
        return
    if _in_rpc_backoff():
        return
    now = time.time()
    if (not force) and (now - last_rpc_call_at < MIN_RPC_UPDATE_INTERVAL):
        return
    try:
        RPC.update(**kwargs)
        last_rpc_call_at = now
        _reset_rpc_backoff()
        _set_rpc_status("RPC: OK")
    except Exception as e:
        # Any pipe/timeout/connection related issue triggers backoff
        _schedule_rpc_backoff()
        if error_message:
            print(f"RPC update skipped: {e}")
        _set_rpc_status("RPC: error, backing off…")


def _safe_rpc_clear():
    if _in_rpc_backoff():
        return
    try:
        RPC.clear()
        _set_rpc_status("RPC: cleared")
    except Exception as e:
        _schedule_rpc_backoff()
        if error_message:
            print(f"RPC clear skipped: {e}")
        _set_rpc_status("RPC: error on clear, backing off…")


def _set_rpc_status(text: str):
    # Update small debug label when available
    try:
        if error_message and rpc_status_var is not None:
            rpc_status_var.set(text)
    except Exception:
        pass


def _presence_changed(details: str | None, state: str | None, large_image: str | None) -> bool:
    """Return True if any part differs from the last sent payload; update cache."""
    global last_rpc_payload
    prev = last_rpc_payload
    changed = (details != prev["details"]) or (state != prev["state"]) or (large_image != prev["large_image"])
    if changed:
        last_rpc_payload = {"details": details, "state": state, "large_image": large_image}
    return changed


#! saves
song_playtimes = defaultdict(int)

# file used to store playtimes (absolute path)
song_playtimes_file = os.path.abspath("song_playtimes.json")

# runtime tracking helpers
last_tick_time = None # timestamp of the last tracker tick
# Discord session start: used for rich presence elapsed time across song changes
discord_session_start = None

def _safe_json_load(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # ensure values are ints
                return {str(k): int(v) for k, v in data.items()}
    except FileNotFoundError:
        return {}
    except Exception as e:
        if error_message:
            print(f"Error loading playtimes: {e}")
    return {}

def _atomic_write(path: str, data: dict):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        if error_message:
            print(f"Error saving playtimes: {e}")

if record_actions:
    if error_message:
        print("Actions are getting Recorded!")

    def load_playtimes():
        global song_playtimes
        data = _safe_json_load(song_playtimes_file)
        song_playtimes = defaultdict(int, data)

    def save_playtimes():
        # convert defaultdict to normal dict for JSON
        _atomic_write(song_playtimes_file, dict(song_playtimes))
else:
    if error_message:
        print("Actions are NOT getting Recorded!")

    def load_playtimes():
        return

    def save_playtimes():
        return


if default_discord_rich_presence == True:
    at_start_rich_button = "ON"
else:
    at_start_rich_button = "OFF"


#? reconnection your client to discord
def reconnect_rpc():
    global last_activity_time
    last_activity_time = time.time()
    try:
        RPC.connect()
        print("Successfully reconnected with Discord.")
    except Exception as e:
        print(f"Error while reconnecting with Discord: {e}")


# var making default folder if it doesnt exist
if not os.path.exists(default_folder):
    os.makedirs(default_folder)


#? loads a new song
def load_songs():
    global playlist, original_playlist, last_activity_time, current_virtual_playlist
    last_activity_time = time.time()
    folder_path = filedialog.askdirectory(initialdir=default_folder)
    if folder_path:
        # clear any virtual playlist context when loading a real folder
        on_switching_playlist()
        current_virtual_playlist = None
        song_list.delete(0, tk.END)
        playlist = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith((".mp3", ".wav")):
                    full_path = os.path.join(root, file)
                    playlist.append(full_path)
                    song_list.insert(tk.END, file)
        original_playlist = list(playlist)


#! NOT USED
#? should delete a selected song directly in the app
def delete_selected_song():
    global current_index, playlist, last_activity_time
    last_activity_time = time.time()
    current_selection = song_list.curselection()
    if current_selection:
        selected_index = current_selection[0]
        file_to_delete = playlist[selected_index]
        song_list.delete(selected_index)
        del playlist[selected_index]
        if os.path.exists(file_to_delete):
            os.remove(file_to_delete)
        if selected_index < current_index:
            current_index -= 1
        elif selected_index == current_index:
            stop_sound()
            if playlist:
                play_next_song()


#? downloads a song through the url (not only youtube)
def download_youtube_mp3():
    global last_activity_time
    last_activity_time = time.time()
    url = url_entry.get()
    if url:
        threading.Thread(target=download_and_process_mp3, args=(url,)).start()


#? hiding process
def download_and_process_mp3(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(default_folder, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'ffmpeg_location': 'ffmpeg-8.0-essentials_build/bin/ffmpeg.exe'
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error during download or processing: {e}")
    messagebox.showinfo("Downloaded.", f"Downloaded in {default_folder} (to change where its getting downloaded go into config.py)")


#? tracks your playtime of songs (if enabled)
def track_playtime():
    """Background ticker: add the seconds played since last tick to the current song.
    This avoids double-counting and keeps a single source of truth for playtime.
    """
    global last_tick_time
    try:
        if is_playing and playlist:
            now = int(time.time())
            if last_tick_time is None:
                last_tick_time = now
            delta = now - last_tick_time
            if delta > 0:
                current_song = os.path.basename(playlist[current_index])
                song_playtimes[current_song] += delta
                save_playtimes()
                last_tick_time = now
    except Exception as e:
        if error_message:
            print(f"track_playtime error: {e}")
    root.after(1000, track_playtime)


#? updates your discord rich presence
def update_presence(song_name=None, rpc_start=0, duration=0):
    # rpc_start is the timestamp callers pass (may be a session start).
    # Read the module-level song start time from globals() to compute elapsed
    # time relative to the currently playing song. This avoids clearing the
    # presence when rpc_start is a session-wide start that predates the song.
    global last_activity_time, current_generated_details, current_generated_state, max_details_length
    global discord_session_start
    # module-level song start (may be absent); fallback to rpc_start
    song_start_time = globals().get('start_time', rpc_start)
    if rich_presence_enabled:
        try:
            if song_name and is_playing:
                mode = []
                if show_repeat_shuffle:
                    if repeat_mode:
                        mode.append("Repeat")
                    if shuffle_mode:
                        mode.append("Shuffle")
                    mode_str = " & ".join(mode) if mode else ""
                else:
                    if repeat_mode:
                        mode.append("")
                    if shuffle_mode:
                        mode.append("")
                    mode_str = "".join(mode) if mode else ""

                max_details_length = 128
                # listening
                if not only_custom_rpc:
                    if mode_str == "":
                        if use_old_rpc_settings:
                            details_message = f"{playing_presence} {song_name[:64].replace('.mp3', '')}"
                        else:
                            details_message = f"Listening to {song_name[:64].replace('.mp3', '')}"
                    else:
                        if use_old_rpc_settings:
                            details_message = f"{playing_presence} {song_name[:64].replace('.mp3', '')} ({mode_str})"
                            details_message = details_message[:max_details_length]
                        else:
                            details_message = f"Listening to {song_name[:64].replace('.mp3', '')} ({mode_str})"
                else:
                    if use_old_rpc_settings:
                        details_message = f"{custom_rpc_text}{hardcoded_presence}"
                        details_message = details_message[:max_details_length]
                    else:
                        details_message = f"{custom_rpc_text}"
                # compute elapsed relative to the session or song start
                rpc_ref_start = discord_session_start if discord_session_start is not None else song_start_time
                elapsed_time = int(time.time()) - rpc_ref_start

                # ensure volume safe and state length
                vol_pct = max(0, min(int(max_volume), int((volume if isinstance(volume, (int, float)) else 0.5) * 1000)))
                if use_old_rpc_settings:
                    state_text = f"on {vol_pct}% Volume {hardcoded_presence}{playing_custom_text_behind}"
                    state_text = state_text[:max_details_length]

                    current_generated_state = state_text
                    current_generated_details = details_message
                else:
                    # pick a friendly playlist name; if a virtual playlist is loaded, use its name
                    try:
                        if current_virtual_playlist and os.path.exists(current_virtual_playlist):
                            vp_data = load_vp_json(current_virtual_playlist)
                            vp_name = vp_data.get('name') or os.path.splitext(os.path.basename(current_virtual_playlist))[0]
                            playlist_label = f"{vp_name} (virtual playlist)"
                        else:
                            playlist_label = os.path.basename(os.path.dirname(playlist[current_index]))
                    except Exception:
                        playlist_label = os.path.basename(os.path.dirname(playlist[current_index]))
                    state_text = f"Playlist: {playlist_label} // Volume: {vol_pct}%"
                    state_text = state_text[:max_details_length]

                # Always update presence while playing. Use the session start as
                # the `start` timestamp so Discord's elapsed timer continues
                # across song changes, pauses and skips. Do not send `end` so
                # Discord won't reset to a per-song progress bar.
                if error_message == True:
                    print(f"Generated message: {details_message} {state_text}")
                if _presence_changed(details_message, state_text, "play.png"):
                    rpc_ts = discord_session_start if discord_session_start is not None else rpc_start
                    _safe_rpc_update(
                        force=True,
                        details=details_message,
                        state=state_text,
                        start=rpc_ts,
                        buttons=[
                            {"label": "Get App", "url": "https://github.com/Tamino1230/BabTomaMusic"},
                            {"label": "Discord", "url": "https://discord.gg/8b8R9qCBF8"}
                        ],
                        large_image="play.png",
                        large_text="babTomaMusic - tamino1230"
                    )
            elif song_name and not is_playing:
                # paused
                mode = []
                if show_repeat_shuffle:
                    if repeat_mode:
                        mode.append("Repeat")
                    if shuffle_mode:
                        mode.append("Shuffle")
                    mode_str = " & ".join(mode) if mode else ""
                else:
                    if repeat_mode:
                        mode.append("")
                    if shuffle_mode:
                        mode.append("")
                    mode_str = "".join(mode) if mode else ""
                if not only_custom_rpc:
                    if use_old_rpc_settings:
                        details_message = f"{paused_presence}{song_name[:64]}{hardcoded_presence}{paused_custom_text_behind}"
                    else:
                        if mode_str == "":
                            details_message = f"Paused: {song_name[:64].replace('.mp3', '')}"
                        else:
                            details_message = f"Paused: {song_name[:64].replace('.mp3', '')} ({mode_str})"
                        details_message = details_message[:max_details_length]
                else:
                    if use_old_rpc_settings:
                        details_message = f"{custom_rpc_text}{hardcoded_presence}"
                    else:
                        details_message = f"{custom_rpc_text}"
                        details_message = details_message[:max_details_length]

                #* for debugchecking
                current_generated_details = details_message

                if error_message == True:
                    print(f"Generated message: {details_message}")
                if _presence_changed(details_message, None, "paused.png"):
                    _safe_rpc_update(
                        force=True,
                        buttons=[
                            {"label": "Get App", "url": "https://github.com/Tamino1230/BabTomaMusic"},
                            {"label": "Discord", "url": "https://discord.gg/8b8R9qCBF8"}
                        ],
                        details=details_message,
                        large_image="paused.png",
                        large_text="babTomaMusic - tamino1230"
                    )
            elif (time.time() - last_activity_time) >= 900:
                if use_old_rpc_settings:
                    details_message = f"{idle_presence} {idle_custom_text_behind}"
                    details_message = details_message[:max_details_length]
                else:
                    details_message = f"Idling"
                if error_message == True:
                    print(f"Generated message: {details_message}")
                idle_state = f"on {max(0, min(100, int((volume if isinstance(volume, (int, float)) else 0.5) * 100)))}% Volume" + hardcoded_presence + idle_custom_text_behind
                if _presence_changed(details_message, idle_state, "musi_ez_large_image"):
                    _safe_rpc_update(
                        force=True,
                        # idling
                        details=details_message,
                        state=idle_state,
                        buttons=[
                            {"label": "Get App", "url": "https://github.com/Tamino1230/BabTomaMusic"},
                            {"label": "Discord", "url": "https://discord.gg/8b8R9qCBF8"}
                        ],
                        large_image="musi_ez_large_image",
                        large_text="babTomaMusic - tamino1230"
                    )
            else:
                _safe_rpc_clear()
                if error_message:
                    print("rpc cleared")
        except Exception as e:
            # Swallow errors to keep UI responsive; backoff handled by safe helpers
            if error_message:
                print(f"RPC Error: {e}")
    else:
        _safe_rpc_clear()
        if error_message:
            print("rpc cleared")


#? plays songs
def play_sound():
    global is_playing, start_time, last_activity_time
    last_activity_time = time.time()
    if playlist:
        pygame.mixer.music.load(playlist[current_index])
        pygame.mixer.music.play(loops=0)
        song_length = get_song_length(playlist[current_index])
        time_slider.config(to=song_length)
        is_playing = True
        update_song_info()

        song_name = os.path.basename(playlist[current_index])
    start_time = int(time.time())
    # initialize ticker
    global last_tick_time
    last_tick_time = int(time.time())

    # ensure discord session start exists so presence elapsed time persists
    global discord_session_start
    if discord_session_start is None:
        discord_session_start = start_time

    update_presence(song_name, discord_session_start, song_length)

    # loads playtimes and start tracker
    load_playtimes()
    root.after(1000, track_playtime)


#? plays the song you have selected
def play_selected_song(event):
    global current_index, is_playing, start_time, last_activity_time
    last_activity_time = time.time()
    if playlist:
        current_selection = song_list.curselection()
        if current_selection:
            current_index = current_selection[0]
            play_sound()


#? pauses the playing song
def pause_sound():
    try:
        global is_playing, start_time, last_activity_time
        last_activity_time = time.time()
        if is_playing:
            # flush any pending seconds from the ticker
            now = int(time.time())
            global last_tick_time
            if last_tick_time is not None and playlist:
                current_song = os.path.basename(playlist[current_index])
                delta = now - last_tick_time
                if delta > 0:
                    song_playtimes[current_song] += delta
                    save_playtimes()
            last_tick_time = None
            pygame.mixer.music.pause()
            is_playing = False
            # preserve discord_session_start so elapsed timer continues when unpaused
            # include timestamps so Discord keeps showing elapsed time while paused
            try:
                song_length = get_song_length(playlist[current_index])
            except Exception:
                song_length = 0
            update_presence(os.path.basename(playlist[current_index]), discord_session_start, song_length)
            try:
                update_pause_button()
            except Exception:
                pass
    except Exception as e:
        pass


#? if song is paused it will be unpaused
def unpause_sound():
    try:
        global is_playing, start_time, last_activity_time
        last_activity_time = time.time()
        if not is_playing:
            pygame.mixer.music.unpause()
            is_playing = True
            song_name = os.path.basename(playlist[current_index])
            song_length = get_song_length(playlist[current_index])
            elapsed_time = int(time.time()) - start_time
            start_time = int(time.time()) - elapsed_time
            # pass the full song length as duration so update_presence can
            # correctly compute elapsed vs total duration
            global discord_session_start
            if discord_session_start is None:
                discord_session_start = start_time
            update_presence(song_name, discord_session_start, song_length)
            try:
                update_pause_button()
            except Exception:
                pass
    except Exception as e:
        pass


#? stops all sound playing
def stop_sound():
    global is_playing, last_activity_time
    last_activity_time = time.time()
    # flush any pending seconds and stop
    if is_playing and playlist:
        now = int(time.time())
        global last_tick_time
        if last_tick_time is not None:
            try:
                current_song = os.path.basename(playlist[current_index])
                delta = now - last_tick_time
                if delta > 0:
                    song_playtimes[current_song] += delta
                    save_playtimes()
            except Exception:
                pass
        last_tick_time = None
    is_playing = False
    time_slider.set(0)
    # stopping should clear the discord session start so next play begins fresh
    # global discord_session_start
    # discord_session_start = None
    # update_presence()
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    try:
        update_pause_button()
    except Exception:
        pass


#? toggles pause and unpause
def toggle_sound():
    try:
        global is_playing, start_time, last_activity_time, discord_session_start
        last_activity_time = time.time()
        global last_tick_time
        if is_playing:
            # pause: flush ticker
            now = int(time.time())
            if last_tick_time is not None and playlist:
                current_song = os.path.basename(playlist[current_index])
                delta = now - last_tick_time
                if delta > 0:
                    song_playtimes[current_song] += delta
                    save_playtimes()
            last_tick_time = None
            pygame.mixer.music.pause()
            is_playing = False
            try:
                song_length = get_song_length(playlist[current_index])
            except Exception:
                song_length = 0
            update_presence(os.path.basename(playlist[current_index]), discord_session_start, song_length)
            try:
                update_pause_button()
            except Exception:
                pass
        else:
            # unpause: resume ticker
            pygame.mixer.music.unpause()
            is_playing = True
            last_tick_time = int(time.time())
            song_name = os.path.basename(playlist[current_index])
            song_length = get_song_length(playlist[current_index])
            # ensure discord session start exists
            if discord_session_start is None:
                discord_session_start = int(time.time())
            update_presence(song_name, discord_session_start, song_length)
            try:
                update_pause_button()
            except Exception:
                pass
    except Exception:
        pass


#? plays the next song in the list
def skip_forward():
    global current_index, last_activity_time
    last_activity_time = time.time()
    if playlist:
        current_index = (current_index + 1) % len(playlist)
        play_sound()


#? plays the last played song
def skip_backwards():
    global current_index, last_activity_time
    last_activity_time = time.time()
    if playlist:
        current_index = (current_index - 1) % len(playlist)
        if current_index < 0:
            current_index = len(playlist) - 1
        play_sound()


#? changes your song through the slider
def set_volume(val, test=False):
    global volume
    global last_activity_time
    global max_volume
    last_activity_time = time.time()
    volume = float(val) / 1000
    if volume > max_volume / 1000:  # Adjusted to ensure it respects max_volume
        volume = max_volume / 1000
    elif volume < 0:
        volume = 0
    pygame.mixer.music.set_volume(volume)

    if test:
        if deactivate_add_remove_volume == False:
            volume_slider.set(volume * 100) #- i think this is causing the crashes


#? toggle repeat mode
def toggle_repeat():
    global repeat_mode, last_activity_time
    last_activity_time = time.time()
    repeat_mode = not repeat_mode
    repeat_button.config(text="Repeat: ON" if repeat_mode else "Repeat: OFF")


#? toggle shuffle mode
def toggle_shuffle():
    global shuffle_mode, playlist, original_playlist, last_activity_time
    last_activity_time = time.time()
    shuffle_mode = not shuffle_mode
    shuffle_button.config(text="Shuffle: ON" if shuffle_mode else "Shuffle: OFF")
    # Preserve currently-playing file when toggling shuffle so current_index remains correct
    try:
        if playlist and 0 <= current_index < len(playlist):
            current_song_path = playlist[current_index]
        else:
            current_song_path = None
    except Exception:
        current_song_path = None

    if shuffle_mode:
        random.shuffle(playlist)
        # restore index to current song if possible
        if current_song_path and current_song_path in playlist:
            try:
                current_index = playlist.index(current_song_path)
            except Exception:
                pass
    else:
        playlist = list(original_playlist)
        # restore index to current song in the restored playlist
        if current_song_path and current_song_path in playlist:
            try:
                current_index = playlist.index(current_song_path)
            except Exception:
                pass
        song_list.delete(0, tk.END)
        for file in playlist:
            song_list.insert(tk.END, os.path.basename(file))


#? toggle discord rich presence
def toggle_rich_presence():
    global rich_presence_enabled, last_activity_time
    last_activity_time = time.time()
    rich_presence_enabled = not rich_presence_enabled
    rich_presence_button.config(text="Rich Presence: ON" if rich_presence_enabled else "Rich Presence: OFF")
    if not rich_presence_enabled:
        _safe_rpc_clear()


#? plays the next song in list
def play_next_song():
    global current_index, is_playing, start_time, last_activity_time
    last_activity_time = time.time()
    is_playing = False
    if playlist:
        if repeat_mode:
            # Crossfade 3 Sekunden
            pygame.mixer.music.fadeout(3000)
            # time.sleep(3)  # Warte auf den Crossfade
            play_sound()
        else:
            # Crossfade 3 Sekunden
            pygame.mixer.music.fadeout(3000)
            # time.sleep(3)  # Warte auf den Crossfade
            current_index = (current_index + 1) % len(playlist)
            play_sound()


#? jump to a different second of the song
def jump_to_position(val):
    global last_activity_time
    last_activity_time = time.time()
    if playlist:
        new_time = int(val)
        pygame.mixer.music.rewind()
        try:
            pygame.mixer.music.set_pos(new_time)
        except Exception as e:
            pass
        if new_time >= time_slider.cget("to"):
            play_next_song()


#? updates the name in menue
def update_song_info():
    if playlist:
        current_file = os.path.basename(playlist[current_index])
        song_name_label.config(text=current_file)


#? gets the length of the song which is playing
def get_song_length(song_path):
    try:
        audio = MP3(song_path)
        return int(audio.info.length)
    except Exception as e:
        print(f"Error retrieving song length: {e}")
        return 0


#? if the playing song ends it will play the next song
def check_song_end():
    global is_playing, start_time
    if is_playing and not pygame.mixer.music.get_busy():
        play_next_song()
    else:
        if is_playing:
            # only update presence if we have a valid playlist and index
            if playlist and 0 <= current_index < len(playlist):
                current_song = os.path.basename(playlist[current_index])
                song_length = get_song_length(playlist[current_index])
                elapsed_time = int(time.time()) - start_time
                # pass full song length (duration) instead of remaining time
                global discord_session_start
                if discord_session_start is None:
                    discord_session_start = start_time
                update_presence(current_song, discord_session_start, song_length)
            else:
                # no valid playlist anymore
                is_playing = False
        elif (time.time() - last_activity_time) >= 900:
            update_presence()
    root.after(1000, check_song_end)


#? updates periodic (gui)
def periodic_update():
    global start_time
    if is_playing and playlist and 0 <= current_index < len(playlist):
        current_song = os.path.basename(playlist[current_index])
        song_length = get_song_length(playlist[current_index])
        elapsed_time = int(time.time()) - start_time
        global discord_session_start
        if discord_session_start is None:
            discord_session_start = start_time
        update_presence(current_song, discord_session_start, song_length)
    root.after(15000, periodic_update)


#? errorpatching
def error(check, text, custom_error_message, is_path_file):
    
    if is_path_file == True:
        if not os.path.exists(check):
            if error_message == True:
                erroradd()
                print("config.py doesnt exists.")
                print(f"Exited with \"{errorcounter}\" Errors.")
                time.sleep(5)
            
        else:
            if error_message == True:
                print("Successfully")
            else:
                pass
              

    if not check == text:
        if error_message == True:
            print(f"Not Sucessfull: {custom_error_message}")
        erroradd()
        
    else:
        if error_message == True:
            print("Successfull")
        else:
            pass


#? used to open the browser and show discord profile
def contact_me():
    try:
        webbrowser.open(hardcoded_contact_url)
    except:
        if error_message == True:
            print("Error while opening discord profile link.")


#? used to open the browser and joins the discord server
def join_discord():
    try:
        webbrowser.open(hardcoded_join_url)
    except:
        if error_message == True:
            print("Error while opening discord server link.")


#? used to open the browser and opens the feedback page
def feedback_send():
    try:
        webbrowser.open(hardcoded_feedback_url)
    except:
        if error_message == True:
            print("Error while opening feedback link.")


#? used to open the browser and opens the idea page
def idea_send():
    try:
        webbrowser.open(hardcoded_idea_url)
    except:
        if error_message == True:
            print("Error while opening idea link.")


#? for cancling the sleep function
def cancel_sleep():
    if not sleeptimer:
        messagebox.showinfo("Function disabled", "The variable \"sleeptimer\" is on False. Put it on True to use it")
    else:
        global cancel_flag
        cancel_flag = True
        messagebox.showinfo("Canceled", "Cancel has been requested. The program will not switch to sleep mode.")


#? sleeps
def sleep_function():
    global cancel_flag
    messagebox.showinfo("Started", f"In {original_time_input} {time_format} switches the program to Sleepmode")
    for _ in range(sleeplength):
        if cancel_flag:
            return
        time.sleep(1)
    stop_sound()
    messagebox.showinfo("Now in Sleepmode", f"Programm is now in Sleepmode! After {original_time_input} {time_format}!")


#? starts the counting until sleep mode
def start_sleep():

    if not sleeptimer:
        messagebox.showinfo("Function disabled", "The variable \"sleeptimer\" is on False. Put it on True to use it")
    else:
        global cancel_flag
        cancel_flag = False  #- resets flag
        threading.Thread(target=sleep_function).start()


#? sharing on twitter
def share_on_twitter():
    try:
        current_song = os.path.basename(playlist[current_index])

        tweet_text = f"Listening to {current_song} with the MusiEz App! Check it out on: {hardcoded_github_url} <3"
        tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text}"
        webbrowser.open(tweet_url)
    except Exception as e:
        messagebox.showerror("Error", "You can't share while no Song is Playing")

#? gets the current volume
def get_current_volume():
    return pygame.mixer.music.get_volume() * 100

#? creating hotkeys
def create_hotkeys():
    if not hotkeys_active:
        pass
    else:
        keyboard.add_hotkey(repeat_toggle_hotkey, toggle_repeat, timeout=None)
        if deactivate_add_remove_volume == False:
            keyboard.add_hotkey(add_volume_hotkey, lambda: set_volume(get_current_volume() + volume_onhotkey, True), timeout=None)
            keyboard.add_hotkey(remove_volume_hotkey, lambda: set_volume(get_current_volume() - volume_onhotkey, True), timeout=None)
        keyboard.add_hotkey(pause_unpause_hotkey, toggle_sound, timeout=None)
        keyboard.add_hotkey(next_song_hotkey, skip_forward, timeout=None)
        keyboard.add_hotkey(last_song_hotkey, skip_backwards, timeout=None)
        keyboard.add_hotkey(sleep_mode_start_hotkey, sleep_function, timeout=None)


#? searches for song information
def search_song_info(song_name):
    try:
        # URL encode the song name to prevent issues with special characters
        encoded_name = quote_plus(song_name)
        url = f"https://musicbrainz.org/ws/2/recording/?query={encoded_name}&fmt=json"
        
        # Make the request
        headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the response JSON
        data = response.json()
        
        # Check if any recordings exist
        if data.get('recordings'):
            recording = data['recordings'][0]
            artist = recording['artist-credit'][0]['artist']['name']
            title = recording['title']
            return artist, title
        
        # Handle the case where no recordings are found
        print("No recordings found for the given song.")
        return None, None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as e:
        print(f"Error fetching song info: {e}")
    return None, None



#? search for song lyrics
def search_song_lyrics(artist, title):
    try:
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('lyrics', "Lyrics not found.")
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
    return "Lyrics not found."


#? creates info window
def show_song_info_window(artist, title, lyrics):
    info_window = Toplevel(root)
    info_window.title("Song Information")
    info_window.geometry("400x600")
    try:
        info_window.iconbitmap(hardcoded_icon_path)
    except Exception:
        pass
    
    # Frame for song info
    song_info_frame = tk.Frame(info_window)
    song_info_frame.pack(pady=10)

    # Artist and Title
    song_info_label = tk.Label(song_info_frame, text=f"Artist: {artist}\nTitle: {title}", font=("Helvetica", 14))
    song_info_label.pack(pady=10)

    # Frame and scrollbar for lyrics
    lyrics_frame = tk.Frame(info_window)
    lyrics_frame.pack(fill=tk.BOTH, expand=True)

    lyrics_scrollbar = tk.Scrollbar(lyrics_frame)
    lyrics_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    lyrics_text = tk.Text(lyrics_frame, wrap=tk.WORD, yscrollcommand=lyrics_scrollbar.set, font=("Helvetica", 12))
    lyrics_text.pack(fill=tk.BOTH, expand=True)
    lyrics_scrollbar.config(command=lyrics_text.yview)

    # Insert lyrics
    lyrics_text.insert(tk.END, lyrics)
    lyrics_text.config(state=tk.DISABLED)


#? sort song info/lyrics
def fetch_and_show_song_info():
    if playlist:
        try:
            current_song_name = os.path.basename(playlist[current_index])
            artist, title = search_song_info(current_song_name)
            if artist and title:
                lyrics = search_song_lyrics(artist, title)
                root.after(0, show_song_info_window, artist, title, lyrics)
            else:
                root.after(0, show_song_info_window, "Song information not found", "", "Lyrics not found.")
        except IndexError:
            messagebox.showerror("Error", "No song selected or invalid song index.")
    else:
        messagebox.showerror("Error", "Playlist is empty.")


#? on open
def on_search_song_click():
    threading.Thread(target=fetch_and_show_song_info).start()


# =====================
# Virtual Playlists
# ---------------------
# Structure and behavior (MVP):
# - Stored in folder "_virtual_playlists" next to main.py
# - Each playlist is a JSON file: {"name":..., "thumbnail": "thumb.png"|null, "items": [{"path": "C:\\\...\\file.mp3", "title": "Optional title"}, ...]}
# - Missing files are silently skipped when loading into the app


# Virtual playlist runtime state
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VP_DIR = os.path.join(BASE_DIR, "_virtual_playlists")
current_virtual_playlist = None  # path to currently loaded virtual playlist JSON


def ensure_vp_dir():
    if not os.path.exists(VP_DIR):
        try:
            os.makedirs(VP_DIR, exist_ok=True)
        except Exception as e:
            if error_message:
                print(f"Could not create virtual playlist dir: {e}")


def list_virtual_playlist_files():
    ensure_vp_dir()
    files = []
    try:
        for f in os.listdir(VP_DIR):
            if f.lower().endswith('.json'):
                files.append(os.path.join(VP_DIR, f))
    except Exception as e:
        if error_message:
            print(f"Error listing virtual playlists: {e}")
    return files


def load_vp_json(path: str) -> dict:
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception as e:
        if error_message:
            print(f"Error loading virtual playlist {path}: {e}")
    return {}


def save_vp_json(path: str, data: dict):
    try:
        _atomic_write(path, data)
    except Exception as e:
        if error_message:
            print(f"Error saving virtual playlist {path}: {e}")


def sanitize_name_for_filename(name: str) -> str:
    safe = ''.join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
    if not safe:
        safe = 'virtual_playlist'
    return safe.replace(' ', '_')


def create_new_virtual_playlist_interactive(initial_name: str = None):
    # Show dialog for new virtual playlist name, not resizeable
    dialog = tk.Toplevel()
    dialog.title('New Virtual Playlist')
    dialog.geometry('350x120')
    dialog.resizable(False, False)
    try:
        dialog.iconbitmap(hardcoded_icon_path)
    except:
        pass
    tk.Label(dialog, text='Enter name for the new virtual playlist:').pack(pady=10)
    entry = tk.Entry(dialog)
    entry.pack(pady=5)
    entry.insert(0, initial_name or "")
    result = {'name': None}
    def on_ok():
        result['name'] = entry.get().strip()
        dialog.destroy()
    def on_cancel():
        dialog.destroy()
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=8)
    tk.Button(btn_frame, text='OK', command=on_ok).pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text='Cancel', command=on_cancel).pack(side=tk.LEFT, padx=8)
    dialog.grab_set()
    dialog.wait_window()
    name = result['name']
    if not name:
        return None
    filename = sanitize_name_for_filename(name) + '.json'
    path = os.path.join(VP_DIR, filename)
    # if exists, ask to overwrite or choose a different name
    if os.path.exists(path):
        if not messagebox.askyesno('Overwrite', f'Playlist "{name}" already exists. Overwrite?'):
            return None
    data = {"name": name, "thumbnail": None, "items": []}
    save_vp_json(path, data)
    refresh_virtual_playlists_menu()
    return path


def choose_thumbnail_and_copy(target_name: str) -> str | None:
    fp = filedialog.askopenfilename(title='Choose thumbnail', filetypes=[('Image files', '*.png;*.gif;*.jpg;*.jpeg')])
    if not fp:
        return None
    try:
        ext = os.path.splitext(fp)[1]
        dest_name = sanitize_name_for_filename(target_name) + '_thumb' + ext
        dest = os.path.join(VP_DIR, dest_name)
        shutil.copy(fp, dest)
        return dest_name
    except Exception as e:
        if error_message:
            print(f"Failed to copy thumbnail: {e}")
    return None


def refresh_virtual_playlists_menu():
    # Rebuild the Virtual Playlists menu in the menubar (if present)
    global virtual_menu
    vpm = virtual_menu
    # If the menu widget doesn't exist we do nothing here; UI setup will call this after creating menu
    if vpm is None:
        return
    # Clear existing entries
    vpm.delete(0, tk.END)
    # Add create / manage
    vpm.add_command(label='Create New Virtual Playlist...', command=lambda: create_new_virtual_playlist_via_dialog())
    vpm.add_command(label='Manage Virtual Playlists...', command=manage_virtual_playlists)
    vpm.add_separator()
    # Add each VP
    for path in list_virtual_playlist_files():
        try:
            data = load_vp_json(path)
            name = data.get('name') or os.path.splitext(os.path.basename(path))[0]
            vpm.add_command(label=name, command=lambda p=path: load_virtual_playlist_into_app(p))
        except Exception:
            continue


def create_new_virtual_playlist_via_dialog():
    ensure_vp_dir()
    path = create_new_virtual_playlist_interactive()
    if not path:
        return
    # optional thumbnail
    if messagebox.askyesno('Thumbnail', 'Would you like to add a thumbnail for this playlist?'):
        thumb = choose_thumbnail_and_copy(os.path.splitext(os.path.basename(path))[0])
        if thumb:
            data = load_vp_json(path)
            data['thumbnail'] = thumb
            save_vp_json(path, data)
    refresh_virtual_playlists_menu()


def load_virtual_playlist_into_app(path: str):
    global playlist, original_playlist, current_virtual_playlist
    on_switching_playlist()
    data = load_vp_json(path)
    items = data.get('items', []) if isinstance(data, dict) else []
    loaded = []
    song_list.delete(0, tk.END)
    for it in items:
        p = it.get('path') if isinstance(it, dict) else None
        if p and os.path.exists(p):
            loaded.append(p)
            song_list.insert(tk.END, it.get('title') or os.path.basename(p))
        else:
            # silently skip missing files (policy: a)
            continue
    playlist = loaded
    original_playlist = list(playlist)
    current_virtual_playlist = path
    #* maybe dont show
    # if playlist:
    #     messagebox.showinfo('Virtual Playlist Loaded', f'Loaded {len(playlist)} existing tracks from "{data.get("name", os.path.basename(path))}"')
    # else:
    #     messagebox.showinfo('Virtual Playlist Loaded', f'No existing files were found in "{data.get("name", os.path.basename(path))}"')


def add_tracks_to_virtual_playlist(vp_path: str, tracks: list[str]):
    if not vp_path or not os.path.exists(vp_path):
        messagebox.showerror('Error', 'Invalid virtual playlist selected.')
        return
    data = load_vp_json(vp_path)
    if not isinstance(data, dict):
        data = {"name": os.path.splitext(os.path.basename(vp_path))[0], "thumbnail": None, "items": []}
    for t in tracks:
        entry = {"path": t, "title": os.path.basename(t)}
        # avoid duplicates by path
        if not any(e.get('path') == t for e in data.get('items', [])):
            data.setdefault('items', []).append(entry)
    save_vp_json(vp_path, data)
    refresh_virtual_playlists_menu()
    if len(tracks) != 1:
        messagebox.showinfo('Added', f'Added {len(tracks)} tracks to "{data.get("name")}"')


def on_song_list_context(event):
    # show popup menu
    # enable/disable 'Remove from virtual playlist' depending on whether a VP is active
    try:
        if current_virtual_playlist and os.path.exists(current_virtual_playlist):
            try:
                song_context_menu.entryconfig('Remove from virtual playlist...', state='normal')
            except Exception:
                pass
        else:
            try:
                song_context_menu.entryconfig('Remove from virtual playlist...', state='disabled')
            except Exception:
                pass
        song_context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        song_context_menu.grab_release()


def context_add_to_virtual_playlist():
    # gather selected indices and corresponding absolute paths from current playlist
    sel = song_list.curselection()
    if not sel:
        messagebox.showinfo('No selection', 'No songs selected to add.')
        return
    tracks = []
    for idx in sel:
        try:
            tracks.append(playlist[int(idx)])
        except Exception:
            continue
    # Choose VP
    vps = list_virtual_playlist_files()
    chooser = Toplevel(root)
    chooser.title(hardcoded_root_title)
    chooser.geometry("400x400")
    chooser.resizable(False, False)
    lb = Listbox(chooser)
    lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for p in vps:
        d = load_vp_json(p)
        lb.insert(tk.END, d.get('name') or os.path.splitext(os.path.basename(p))[0])
    def on_choose():
        sel2 = lb.curselection()
        if not sel2:
            messagebox.showinfo('Choose', 'Choose a virtual playlist or create a new one.')
            return
        vp_path = vps[sel2[0]]
        add_tracks_to_virtual_playlist(vp_path, tracks)
        chooser.destroy()
    def on_create():
        chooser.destroy()
        new_vp = create_new_virtual_playlist_interactive()
        if new_vp:
            add_tracks_to_virtual_playlist(new_vp, tracks)
    tk.Button(chooser, text='Choose', command=on_choose).pack(side=tk.LEFT, padx=10, pady=8)
    tk.Button(chooser, text='Create New', command=on_create).pack(side=tk.LEFT, padx=10, pady=8)
    tk.Button(chooser, text='Cancel', command=chooser.destroy).pack(side=tk.RIGHT, padx=10, pady=8)


def manage_virtual_playlists():
    ensure_vp_dir()
    vps = list_virtual_playlist_files()
    win = tk.Toplevel(root)
    win.title('Manage Virtual Playlists')
    win.geometry('700x450')
    win.resizable(False, False)
    try:
        win.iconbitmap(hardcoded_icon_path)
    except Exception:
        pass

    left_frame = tk.Frame(win)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
    right_frame = tk.Frame(win)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

    # left list + scrollbar
    vp_listbox_frame = tk.Frame(left_frame)
    vp_listbox_frame.pack(fill=tk.BOTH, expand=True)
    vp_listbox = Listbox(vp_listbox_frame)
    vp_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vp_scroll = tk.Scrollbar(vp_listbox_frame, orient=tk.VERTICAL, command=vp_listbox.yview)
    vp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    vp_listbox.config(yscrollcommand=vp_scroll.set)
    for p in vps:
        d = load_vp_json(p)
        vp_listbox.insert(tk.END, d.get('name') or os.path.splitext(os.path.basename(p))[0])

    # right side: left column contains buttons (stacked) and the thumbnail below them; items list is on the right
    items_btn_bar = tk.Frame(right_frame)
    items_btn_bar.pack(side=tk.LEFT, anchor='n', padx=(0,8))

    items_listbox_frame = tk.Frame(right_frame)
    items_listbox_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    items_listbox = Listbox(items_listbox_frame)
    items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    items_scroll = tk.Scrollbar(items_listbox_frame, orient=tk.VERTICAL, command=items_listbox.yview)
    items_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    items_listbox.config(yscrollcommand=items_scroll.set)

    current_editing = {'path': None, 'data': None}

    # thumbnail will be created inside the button column after the buttons are packed
    # (placeholder variables; actual widget created after buttons so it appears under them)
    thumb_frame = None
    thumb_label = None

    def load_selected_vp(evt=None):
        sel = vp_listbox.curselection()
        if not sel:
            return
        p = vps[sel[0]]
        data = load_vp_json(p)
        current_editing['path'] = p
        current_editing['data'] = data
        items_listbox.delete(0, tk.END)
        for it in data.get('items', []):
            title = it.get('title') or os.path.basename(it.get('path', ''))
            path_val = it.get('path', '')
            if not os.path.exists(path_val):
                title = f"{title} [missing]"
            items_listbox.insert(tk.END, title)
        # ensure selection in vp_listbox stays on the same index
        try:
            vp_listbox.selection_clear(0, tk.END)
            vp_listbox.selection_set(vps.index(p))
        except Exception:
            pass
    

    def save_changes():
        p = current_editing.get('path')
        d = current_editing.get('data')
        if not p or not d:
            messagebox.showinfo('Save', 'No playlist selected.')
            return
        save_vp_json(p, d)
        messagebox.showinfo('Saved', 'Changes saved.')
        refresh_virtual_playlists_menu()

    def refresh_vp_listbox():
        # refresh local vps list and the visible vp_listbox
        nonlocal vps
        vps = list_virtual_playlist_files()
        vp_listbox.delete(0, tk.END)
        for p in vps:
            d = load_vp_json(p)
            vp_listbox.insert(tk.END, d.get('name') or os.path.splitext(os.path.basename(p))[0])

    def remove_selected_item():
        sel = items_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        d = current_editing.get('data')
        if d and 'items' in d and 0 <= idx < len(d['items']):
            d['items'].pop(idx)
            items_listbox.delete(idx)

    def rename_selected_item():
        sel = items_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        d = current_editing.get('data')
        if not d:
            return
        new = simpledialog.askstring('Rename', 'New display title:')
        if not new:
            return
        d['items'][idx]['title'] = new
        items_listbox.delete(idx)
        items_listbox.insert(idx, new)

    def add_files_to_vp():
        files = filedialog.askopenfilenames(title='Add files to virtual playlist', filetypes=[('Audio files', '*.mp3;*.wav;*.flac;*.m4a'), ('All files','*.*')])
        if not files:
            return
        d = current_editing.get('data')
        if not d:
            return
        for f in files:
            entry = {"path": f, "title": os.path.basename(f)}
            if not any(e.get('path') == f for e in d.get('items', [])):
                d.setdefault('items', []).append(entry)
                items_listbox.insert(tk.END, entry['title'])

    def rename_selected_playlist():
        sel = vp_listbox.curselection()
        if not sel:
            messagebox.showinfo('Rename', 'No playlist selected.')
            return
        idx = sel[0]
        old_path = vps[idx]
        data = load_vp_json(old_path)
        old_name = data.get('name') or os.path.splitext(os.path.basename(old_path))[0]
        # show custom dialog so we can set icon and offer checkbox
        def rename_playlist_dialog(initial_name: str):
            dlg = tk.Toplevel(win)
            dlg.title('Rename Playlist')
            dlg.geometry('400x140')
            dlg.resizable(False, False)
            try:
                dlg.iconbitmap(hardcoded_icon_path)
            except Exception:
                pass
            tk.Label(dlg, text='New playlist name:').pack(padx=10, pady=(10,0), anchor='w')
            name_var = tk.StringVar(value=initial_name)
            entry = tk.Entry(dlg, textvariable=name_var, width=50)
            entry.pack(padx=10, pady=6)
            rename_file_var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(dlg, text='Also rename the underlying JSON file', variable=rename_file_var)
            cb.pack(padx=10, anchor='w')
            result = {'name': None, 'rename_file': False}

            def on_ok():
                val = name_var.get().strip()
                if not val:
                    messagebox.showinfo('Rename', 'Please enter a name.')
                    return
                result['name'] = val
                result['rename_file'] = bool(rename_file_var.get())
                dlg.destroy()

            def on_cancel():
                dlg.destroy()

            btn_frame = tk.Frame(dlg)
            btn_frame.pack(pady=8)
            tk.Button(btn_frame, text='OK', width=10, command=on_ok).pack(side=tk.LEFT, padx=8)
            tk.Button(btn_frame, text='Cancel', width=10, command=on_cancel).pack(side=tk.LEFT)
            entry.focus_set()
            dlg.transient(win)
            dlg.grab_set()
            win.wait_window(dlg)
            return result['name'], result['rename_file']

        new_name, do_rename_file = rename_playlist_dialog(old_name)
        if not new_name:
            return
        # update JSON name and persist
        data['name'] = new_name
        save_vp_json(old_path, data)
        # optionally rename underlying file
        if do_rename_file:
            new_filename = sanitize_name_for_filename(new_name) + '.json'
            new_path = os.path.join(VP_DIR, new_filename)
            if os.path.abspath(new_path) != os.path.abspath(old_path):
                if os.path.exists(new_path):
                    if not messagebox.askyesno('Overwrite', f'File {new_filename} already exists. Overwrite?'):
                        refresh_vp_listbox()
                        refresh_virtual_playlists_menu()
                        return
                    try:
                        os.remove(new_path)
                    except Exception:
                        pass
                try:
                    os.rename(old_path, new_path)
                    if current_editing.get('path') and os.path.abspath(current_editing.get('path')) == os.path.abspath(old_path):
                        current_editing['path'] = new_path
                    old_path = new_path
                except Exception as e:
                    messagebox.showerror('Rename failed', f'Failed to rename file: {e}')
        # refresh listbox and menu
        refresh_vp_listbox()
        refresh_virtual_playlists_menu()
        messagebox.showinfo('Renamed', f'Playlist renamed to "{new_name}"')

    def remove_missing_items():
        d = current_editing.get('data')
        if not d:
            return
        before = len(d.get('items', []))
        d['items'] = [it for it in d.get('items', []) if os.path.exists(it.get('path', ''))]
        after = len(d.get('items', []))
        items_listbox.delete(0, tk.END)
        for it in d.get('items', []):
            items_listbox.insert(tk.END, it.get('title') or os.path.basename(it.get('path', '')))
        if before != after:
            messagebox.showinfo('Removed', f'Removed {before-after} missing item(s).')
        else:
            messagebox.showinfo('No Changes', 'No missing items were found.')

    def set_thumbnail_for_current():
        p = current_editing.get('path')
        d = current_editing.get('data')
        if not p or not d:
            return
        new_thumb = choose_thumbnail_and_copy(os.path.splitext(os.path.basename(p))[0])
        if new_thumb:
            d['thumbnail'] = new_thumb
            try:
                save_vp_json(p, d)
            except Exception:
                pass
            refresh_virtual_playlists_menu()
            show_thumbnail_for_current()

    def delete_selected_playlist():
        p = current_editing.get('path')
        if not p:
            return
        if messagebox.askyesno('Confirm Delete', 'Are you sure you want to delete this playlist?'):
            try:
                os.remove(p)
                current_editing.clear()
                refresh_vp_listbox()
                refresh_virtual_playlists_menu()
                song_list.delete(0, tk.END)
                on_switching_playlist()
            except Exception as e:
                messagebox.showerror('Delete failed', f'Failed to delete playlist: {e}')

    # helper: show the thumbnail for the currently-selected virtual playlist in the single thumb_label
    def show_thumbnail_for_current():
        p = current_editing.get('path')
        d = current_editing.get('data')
        # reset
        thumb_label.config(image='', text='No thumbnail')
        if not p or not d:
            return
        th = d.get('thumbnail')
        if not th:
            return
        fp = os.path.join(VP_DIR, th)
        if not os.path.exists(fp):
            thumb_label.config(text='Missing thumbnail')
            return
        if PIL_AVAILABLE:
            try:
                img = Image.open(fp)
                img.thumbnail((150,150))
                photo = ImageTk.PhotoImage(img)
                # store reference so it doesn't get GC'd
                thumb_label.image = photo
                thumb_label.config(image=photo, text='')
            except Exception:
                thumb_label.config(text=os.path.basename(fp))
        else:
            thumb_label.config(text=os.path.basename(fp))

    # buttons stacked vertically in the left button column
    tk.Button(items_btn_bar, text='Save', command=save_changes).pack(fill=tk.X, padx=6, pady=3)
    tk.Button(items_btn_bar, text='Remove Selected Song', command=remove_selected_item).pack(fill=tk.X, padx=6, pady=3)
    # tk.Button(items_btn_bar, text='Rename Selected', command=rename_selected_item).pack(fill=tk.X, padx=6, pady=3)
    tk.Button(items_btn_bar, text='Add Files', command=add_files_to_vp).pack(fill=tk.X, padx=6, pady=3)
    tk.Button(items_btn_bar, text='Remove Missing Items', command=remove_missing_items).pack(fill=tk.X, padx=6, pady=3)
    tk.Button(items_btn_bar, text='Set Thumbnail', command=set_thumbnail_for_current).pack(fill=tk.X, padx=6, pady=3)
    tk.Button(items_btn_bar, text='Create New Virtual Playlist', command=create_new_virtual_playlist_via_dialog).pack(fill=tk.X, padx=6, pady=3)
    tk.Button(items_btn_bar, text='Rename Playlist', command=rename_selected_playlist).pack(fill=tk.X, padx=6, pady=3)
    tk.Button(items_btn_bar, text='Delete Playlist', command=delete_selected_playlist).pack(fill=tk.X, padx=6, pady=3)

    # create the thumbnail widget as a child of the button column so it sits directly under the buttons
    thumb_frame = tk.Frame(items_btn_bar, width=150, height=150)
    # fill horizontally so the thumbnail sits directly under the full width of the buttons
    thumb_frame.pack(side=tk.TOP, pady=(10,0), fill=tk.X)
    thumb_frame.pack_propagate(False)
    thumb_label = tk.Label(thumb_frame, text='No thumbnail', anchor='center')
    thumb_label.pack(expand=True)

    vp_listbox.bind('<<ListboxSelect>>', lambda e: (load_selected_vp(), show_thumbnail_for_current()))


ensure_vp_dir()

# placeholder globals to be initialized after main window is created
song_context_menu = None
virtual_menu = None




#! checking for changes
#? main.py
error(hardcoded_config, "scripts/config.py", f"config.py doesnt exists", True)
error(hardcoded_resizeable, False, f"Wrong Resizeable is on {hardcoded_resizeable} and not on \"True\"", False)
error(hardcoded_geometry, "800x650", f"Wrong Geometry in {hardcoded_config}", False)
error(hardcoded_root_title, "BabTomaMusic - @tamino1230", f"Wrong RootTitle in {hardcoded_config}", False)
error(hardcoded_icon_path, "icon/babToma.ico", f"Wrong Icon Path in {hardcoded_config}", False)
error(sjksaahd, "Tamino1230", f"Wrong Owner in config.py File", False)
error(hardcoded_presence, f" | made by tamino1230 on GitHub <3", f"Wrong hardcoded Presence in {hardcoded_config}", False)
error(CLIENT_ID, "1309941984407977996", f"Wrong client-id in {hardcoded_config}", False)
error(hardcoded_contact_url, "https://discord.com/users/702893526303637604", f"Wrong hardcoded url in {hardcoded_config}", False)
error(hardcoded_join_url, "https://discord.gg/vpApZSjh3H", f"Wrong Discord Join Url in {hardcoded_config}", False)
error(hardcoded_feedback_url, "https://discord.com/channels/1308085385351397427/1321532070144774215", f"Wrong Discord Feedback Url in {hardcoded_config}", False)
error(hardcoded_idea_url, "https://discord.com/channels/1308085385351397427/1321532085957165138", f"Wrong Discord Idea Url in {hardcoded_config}", False)
error(hardcoded_github_url, "https://github.com/Tamino1230/babTomaMusic", f"Wrong hardcoded Github url in {hardcoded_config}", False)
#? helping window
error(hardcoded_resizeable_hp, False, f"Wrong helping resizeable in {hardcoded_config}", False)
error(hardcoded_geometry_hp, "800x600", f"Wrong helping geometry in {hardcoded_config}", False)
error(hardcoded_root_title_hp, "Helping Window - @tamino1230", f"Wrong helping root title in {hardcoded_config}", False)


#? sets the maximum volume to under 500 and over 1
if max_volume > 500 or max_volume < 1:
    print(f"Volume cant be \"{max_volume}\". It need to be under 500 and over 0!")
    time.sleep(5)
    exit()
else:
    pass


exiterror = f"Exited with \"{errorcounter}\" Errors."


#? errorhandling
def close_error():
    global exiterror
    
    if errorcounter > 0:
        print(exiterror)
        time.sleep(5)
        exit()
    else:
        print("No Errors")
        pass


#? closes if any errors accure
close_error()

def reload_config_settings():
    #! restarting the program
    python = sys.executable
    os.execl(python, python, *sys.argv)


#! Main window
root = tk.Tk()
root.title(hardcoded_root_title)
root.geometry(hardcoded_geometry)
root.configure(bg=bgcolor)
try:
    root.iconbitmap(hardcoded_icon_path)
except:
    pass
root.resizable(hardcoded_resizeable, hardcoded_resizeable)

button_frame = tk.Frame(root)
button_frame.pack(anchor="nw", pady=10)

# Search box (top-right) — searches the main song list for matching text
search_frame = tk.Frame(root)
search_frame.pack(anchor='ne', pady=6, padx=8)
search_entry = tk.Entry(search_frame, width=30)
search_entry.pack(side=tk.LEFT, padx=(0,6))

def search_in_song_list(event=None):
    q = search_entry.get().strip().lower()
    if not q:
        return
    try:
        items = song_list.get(0, tk.END)
    except Exception:
        messagebox.showinfo('Search', 'No songs to search.')
        return
    matches = [i for i, it in enumerate(items) if q in (it or '').lower()]
    if not matches:
        messagebox.showinfo('Search', 'No match found.')
        return
    # select first match and scroll to it
    idx = matches[0]
    song_list.selection_clear(0, tk.END)
    song_list.selection_set(idx)
    song_list.see(idx)

def clear_search():
    search_entry.delete(0, tk.END)
    try:
        song_list.selection_clear(0, tk.END)
    except Exception:
        pass

def on_switching_playlist():
    clear_search()
    stop_sound()

search_button = tk.Button(search_frame, text='Search', command=search_in_song_list)
search_button.pack(side=tk.LEFT)
clear_button = tk.Button(search_frame, text='Clear', command=clear_search)
clear_button.pack(side=tk.LEFT, padx=(6,0))
search_entry.bind('<Return>', search_in_song_list)


#! Discord RPC
#! RPC toggle button
rich_presence_button = tk.Button(button_frame, text=f"Rich Presence: {at_start_rich_button}", command=toggle_rich_presence)
rich_presence_button.pack(side=tk.LEFT, padx=5)

# Debug-only: show a small RPC status indicator
if error_message:
    rpc_status_var = tk.StringVar(value="RPC: ready")
    rpc_status_label = tk.Label(button_frame, textvariable=rpc_status_var, fg="#888")
    rpc_status_label.pack(side=tk.LEFT, padx=8)

#. RPC reconnect button
#// reconnect_button = tk.Button(button_frame, text="Reconnect", command=reconnect_rpc)
#// reconnect_button.pack(side=tk.LEFT, padx=5)


#! Load Songs Button
#// load_button = tk.Button(root, text="Load Songs", command=load_songs)
#// load_button.pack(pady=10)


# Song List (allow multi-selection)
song_list = Listbox(root, selectmode=tk.EXTENDED)
song_list.pack(pady=10, fill=tk.BOTH, expand=True)
# Double-click should play the item under the cursor (nearest) so multi-select doesn't change behavior
def play_selected_song(event):
    global current_index, is_playing, start_time, last_activity_time
    last_activity_time = time.time()
    if playlist:
        # choose the item that was double-clicked
        try:
            idx = song_list.nearest(event.y)
            if idx is not None:
                current_index = idx
                play_sound()
        except Exception:
            pass

song_list.bind("<Double-1>", play_selected_song)
song_list.bind('<Button-3>', lambda e: on_song_list_context(e))


#! controls Frame
controls_frame = tk.Frame(root)
controls_frame.pack(pady=10)

#. pause button

pause_button = tk.Button(controls_frame, text="Pause", command=toggle_sound)
pause_button.grid(row=0, column=1, padx=5)


def update_pause_button():
    """Update the pause/unpause button text to match the current playback state.

    This is safe to call from anywhere; it silently no-ops if the button
    or the tkinter module isn't available yet.
    """
    try:
        # is_playing is a global boolean set by play/pause/stop routines
        if 'pause_button' in globals() and pause_button is not None:
            pause_button.config(text=("Pause" if is_playing else "Unpause"))
    except Exception:
        # Keep UI calls resilient during startup/shutdown
        pass

# Call update_pause_button whenever play/pause state changes
# Add to play_sound, pause_sound, unpause_sound, toggle_sound
def play_sound():
    global is_playing, start_time, last_activity_time
    last_activity_time = time.time()
    if playlist:
        pygame.mixer.music.load(playlist[current_index])
        pygame.mixer.music.play(loops=0)
        song_length = get_song_length(playlist[current_index])
        time_slider.config(to=song_length)
        is_playing = True
        update_song_info()
        song_name = os.path.basename(playlist[current_index])
    start_time = int(time.time())
    global last_tick_time
    last_tick_time = int(time.time())
    global discord_session_start
    if discord_session_start is None:
        discord_session_start = start_time
    update_presence(song_name, discord_session_start, song_length)
    load_playtimes()
    root.after(1000, track_playtime)

def pause_sound():
    try:
        global is_playing, start_time, last_activity_time
        last_activity_time = time.time()
        if is_playing:
            now = int(time.time())
            global last_tick_time
            if last_tick_time is not None and playlist:
                current_song = os.path.basename(playlist[current_index])
                delta = now - last_tick_time
                if delta > 0:
                    song_playtimes[current_song] += delta
                    save_playtimes()
            last_tick_time = None
            pygame.mixer.music.pause()
            is_playing = False
            try:
                song_length = get_song_length(playlist[current_index])
            except Exception:
                song_length = 0
            update_presence(os.path.basename(playlist[current_index]), discord_session_start, song_length)
    except Exception as e:
        pass

def unpause_sound():
    try:
        global is_playing, start_time, last_activity_time
        last_activity_time = time.time()
        if not is_playing:
            pygame.mixer.music.unpause()
            is_playing = True
            song_name = os.path.basename(playlist[current_index])
            song_length = get_song_length(playlist[current_index])
            elapsed_time = int(time.time()) - start_time
            start_time = int(time.time()) - elapsed_time
            global discord_session_start
            if discord_session_start is None:
                discord_session_start = start_time
            update_presence(song_name, discord_session_start, song_length)
    except Exception as e:
        pass

def toggle_sound():
    try:
        global is_playing, start_time, last_activity_time, discord_session_start
        last_activity_time = time.time()
        global last_tick_time
        if is_playing:
            now = int(time.time())
            if last_tick_time is not None and playlist:
                current_song = os.path.basename(playlist[current_index])
                delta = now - last_tick_time
                if delta > 0:
                    song_playtimes[current_song] += delta
                    save_playtimes()
            last_tick_time = None
            pygame.mixer.music.pause()
            is_playing = False
            try:
                song_length = get_song_length(playlist[current_index])
            except Exception:
                song_length = 0
            update_presence(os.path.basename(playlist[current_index]), discord_session_start, song_length)
        else:
            pygame.mixer.music.unpause()
            is_playing = True
            last_tick_time = int(time.time())
            song_name = os.path.basename(playlist[current_index])
            song_length = get_song_length(playlist[current_index])
            if discord_session_start is None:
                discord_session_start = int(time.time())
            update_presence(song_name, discord_session_start, song_length)
    except Exception:
        pass


#. pause button
# pause_button = tk.Button(controls_frame, text="Pause", command=pause_sound)
# pause_button.grid(row=0, column=1, padx=5)

#. unpause button
# unpause_button = tk.Button(controls_frame, text="Unpause", command=unpause_sound)
# unpause_button.grid(row=0, column=2, padx=5)

#. stop button
stop_button = tk.Button(controls_frame, text="Stop", command=stop_sound)
stop_button.grid(row=0, column=3, padx=5)

#. skip back button
skip_backwards_button = tk.Button(controls_frame, text="Back", command=skip_backwards)
skip_backwards_button.grid(row=0, column=4, padx=5)

#. skip next button
skip_forward_button = tk.Button(controls_frame, text="Next", command=skip_forward)
skip_forward_button.grid(row=0, column=5, padx=5)

#. toggle repeat
repeat_button = tk.Button(controls_frame, text="Repeat: OFF", command=toggle_repeat)
repeat_button.grid(row=0, column=6, padx=5)

#. toggle shuffel
shuffle_button = tk.Button(controls_frame, text="Shuffle: OFF", command=toggle_shuffle)
shuffle_button.grid(row=0, column=7, padx=5)


#! Volume Frame
volume_frame = tk.Frame(root)
volume_frame.pack(pady=10, anchor="w")

volume_label = tk.Label(volume_frame, text="Volume")
volume_label.pack(side=tk.LEFT, padx=5)

#. Volume slider
volume_slider = tk.Scale(volume_frame, from_=0, to=max_volume, orient=tk.HORIZONTAL, command=set_volume)
volume_slider.set(50)

volume_slider.pack(side=tk.LEFT, padx=5)


#! Time Slider
time_frame = tk.Frame(root)
time_frame.pack(pady=10)

time_slider = tk.Scale(time_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=jump_to_position)
time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)


#! Song Name Label
song_name_label = tk.Label(root, text="No Song Loaded", font=("Helvetica", 14))
song_name_label.pack(pady=10)


#! URL Entry
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=10)

#. Download Button
download_button = tk.Button(root, text="Download MP3", command=download_youtube_mp3)
download_button.pack(pady=10)




#! HELP
#// help_button = tk.Button(root, text="Show Help!", command=show_help)
#// help_button.pack(pady=10)

#! Creates Menubar
menubar = tk.Menu(root)
root.config(menu=menubar)

#? filemenu
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Files", menu=file_menu)
file_menu.add_command(label="Load Songs", command=load_songs)
file_menu.add_command(label="Reload Config Settings", command=reload_config_settings)
file_menu.add_separator()
file_menu.add_command(label="End Program", command=root.quit)


# Virtual Playlists menu (created separately so we can refresh contents)
virtual_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='Virtual Playlists', menu=virtual_menu)
refresh_virtual_playlists_menu()

# create a minimal popup menu for the song list (Add to virtual playlist)
song_context_menu = tk.Menu(root, tearoff=0)
song_context_menu.add_command(label='Add to virtual playlist...', command=context_add_to_virtual_playlist)
song_context_menu.add_command(label='Remove from virtual playlist...', command=lambda: context_remove_from_virtual_playlist())


def context_remove_from_virtual_playlist():
    global playlist, original_playlist
    # remove selected songs from the currently loaded virtual playlist JSON (does not delete files)
    if not current_virtual_playlist or not os.path.exists(current_virtual_playlist):
        messagebox.showinfo('Remove', 'No virtual playlist is currently loaded.')
        return
    sel = song_list.curselection()
    if not sel:
        messagebox.showinfo('Remove', 'No song(s) selected.')
        return
    data = load_vp_json(current_virtual_playlist)
    if not isinstance(data, dict):
        messagebox.showerror('Error', 'Invalid virtual playlist data.')
        return
    paths_to_remove = set()
    for i in sel:
        try:
            p = playlist[int(i)]
            paths_to_remove.add(os.path.abspath(p))
        except Exception:
            continue
    if not paths_to_remove:
        messagebox.showinfo('Remove', 'No valid files selected.')
        return
    # remove matching entries from data['items'] by absolute path
    before = len(data.get('items', []))
    new_items = []
    for it in data.get('items', []):
        ip = os.path.abspath(it.get('path', '')) if isinstance(it.get('path', ''), str) else ''
        if ip in paths_to_remove:
            continue
        new_items.append(it)
    data['items'] = new_items
    save_vp_json(current_virtual_playlist, data)
    # also remove from in-memory playlist if we are currently viewing it
    try:
        # rebuild playlist and song_list from remaining items
        loaded = []
        song_list.delete(0, tk.END)
        for it in data.get('items', []):
            pth = it.get('path')
            if pth and os.path.exists(pth):
                loaded.append(pth)
                song_list.insert(tk.END, it.get('title') or os.path.basename(pth))
        playlist = loaded
        original_playlist = list(playlist)
    except Exception:
        pass
    refresh_virtual_playlists_menu()
    if len(data.get("items", [])) != 1:
        messagebox.showinfo('Removed', f'Removed {before - len(data.get("items", []))} tracks from the virtual playlist.')


#? discord menu
discord_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Discord", menu=discord_menu)
discord_menu.add_command(label="Reconnect RPC", command=reconnect_rpc)
discord_menu.add_command(label="Contact Me", command=contact_me)
discord_menu.add_command(label="Join Discord", command=join_discord)


#? feedback menu
feedback_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Feedback", menu=feedback_menu)
feedback_menu.add_command(label="Give Feedback", command=feedback_send)
feedback_menu.add_command(label="Give Ideas", command=idea_send)


#? feedback menu
feedback_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Share", menu=feedback_menu)
feedback_menu.add_command(label="Share on Twitter", command=share_on_twitter)
feedback_menu.add_command(label="Share on ...", command="in progress")


#? extra func menu
extra_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Extra Functions", menu=extra_menu)
extra_menu.add_command(label="Sleep Mode Start", command=start_sleep)
extra_menu.add_command(label="Sleep Mode Cancel", command=cancel_sleep)
extra_menu.add_command(label="Info and Lyrics (beta)", command=on_search_song_click)
# extra_menu.add_command(label="Mikrofonwiedergabe umschalten (working on)", command="toggle_virtual_mic_playback")


#? help menu
help_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="Show Help", command=show_help)
# help_menu.add_command(label="Settings (Not working)", command=print("not used"))


#! Message when programm starts
print("YOU CAN HIDE THIS WINDOW.") 

#! Creates Hotkeys if want to be used
create_hotkeys()

#! Check if song ends
check_song_end()

#! Start periodic update
periodic_update()

#! load times when started
load_playtimes()

#! Mainloop
root.mainloop()


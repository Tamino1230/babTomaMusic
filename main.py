
# todo playing soundboard on your microphone


# import online
import sys
from urllib.parse import quote_plus
import tkinter as tk
from tkinter import filedialog, Listbox, ttk, messagebox
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


#! saves
song_playtimes = defaultdict(int)


if record_actions == True: #- if on false it will not record any actions of what your listening to.
    if error_message == True:
        print("Actions are getting Recorded!")

    def load_playtimes():
        global song_playtimes
        if os.path.exists("song_playtimes.json"):
            with open("song_playtimes.json", "r") as f:
                try:
                    content = f.read().strip()
                    if content:  # Check if the file is not empty
                        song_playtimes = defaultdict(int, json.loads(content))
                    else:
                        song_playtimes = defaultdict(int)  # Initialize as empty
                except json.JSONDecodeError:
                    print("Error: song_playtimes.json contains invalid JSON. Initializing as empty.")
                    song_playtimes = defaultdict(int)

    def save_playtimes():
        with open("song_playtimes.json", "w") as f:
            json.dump(song_playtimes, f)
else:
    print("Actions are NOT getting Recorded!")

    def load_playtimes():
        pass

    def save_playtimes():
        pass


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
    global playlist, original_playlist, last_activity_time
    last_activity_time = time.time()
    folder_path = filedialog.askdirectory(initialdir=default_folder)
    if folder_path:
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
        'ffmpeg_location': 'ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe'
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error during download or processing: {e}")
    messagebox.showinfo("Downloaded.", f"Downloaded in {default_folder} (to change where its getting downloaded go into config.py)")


#? tracks your playtime of songs (if enabled)
def track_playtime():
    global start_time
    if is_playing:
        current_song = os.path.basename(playlist[current_index])
        current_song = f"{current_song}"
        elapsed_time = int(time.time()) - start_time
        song_playtimes[current_song] += elapsed_time
        save_playtimes()
        start_time = int(time.time())
    root.after(1000, track_playtime)


#? updates your discord rich presence
def update_presence(song_name=None, start_time=0, duration=0):
    global last_activity_time
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
                        details_message = f"{playing_presence} {song_name[:64].replace('.mp3', '')}"
                    else:
                        details_message = f"{playing_presence} {song_name[:64].replace('.mp3', '')} ({mode_str})"
                    details_message = details_message[:max_details_length]
                else:
                    details_message = f"{custom_rpc_text}{hardcoded_presence}"
                    details_message = details_message[:max_details_length]
                elapsed_time = int(time.time()) - start_time

                state_text =  f"on {int(volume*1000)}% Volume" + hardcoded_presence + playing_custom_text_behind
                state_text = state_text[:max_details_length]

                if elapsed_time < duration:
                    if error_message == True:
                        print(f"Generated message: {details_message}")
                        if details_message == None:
                            print("Error: details_message is None")
                        if details_message > 128:
                            print(f"Error: details_message is too long: {len(details_message)} characters: {details_message}")
                    RPC.update(
                        details=details_message,
                        state=state_text,
                        # start=start_time,
                        # end=start_time + duration,
                        large_image="play.png",
                        large_text="babTomaMusic - tamino1230"
                    )
                else:
                    RPC.clear()
            elif song_name and not is_playing:
                # paused
                if not only_custom_rpc:
                    details_message = f"{paused_presence}{song_name[:64]}{hardcoded_presence}{paused_custom_text_behind}"
                else:
                    details_message = f"{custom_rpc_text}{hardcoded_presence}"
                if error_message == True:
                    print(f"Generated message: {details_message}")
                RPC.update(
                    details=details_message,
                    large_image="paused.png",
                    large_text="babTomaMusic - tamino1230"
                )
            elif (time.time() - last_activity_time) >= 900:
                details_message = f"{idle_presence} {idle_custom_text_behind}"
                if error_message == True:
                    print(f"Generated message: {details_message}")
                RPC.update(
                    # idling
                    details=details_message,
                    state=f"on {int(volume*100)}% Volume" + hardcoded_presence + idle_custom_text_behind,
                    large_image="musi_ez_large_image",
                    large_text="babTomaMusic - tamino1230"
                )
            else:
                RPC.clear()
                if error_message:
                    print("rpc cleared")
        except Exception as e:
            if error_message:
                print(f"RPC Error: {e}")
            else:
                print("An error occurred while updating the RPC.")
    else:
        RPC.clear()
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

        update_presence(song_name, start_time, song_length)

        # loads spy
        load_playtimes()

        # starts spy
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
            current_song = os.path.basename(playlist[current_index])
            elapsed_time = int(time.time()) - start_time
            song_playtimes[current_song] += elapsed_time
            save_playtimes()
            
        pygame.mixer.music.pause()
        is_playing = False
        update_presence(os.path.basename(playlist[current_index]))
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
            update_presence(song_name, start_time, song_length - elapsed_time)
    except Exception as e:
        pass


#? stops all sound playing
def stop_sound():
    global is_playing, last_activity_time
    last_activity_time = time.time()
    is_playing = False
    time_slider.set(0)
    update_presence()
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        pass


#? toggles pause and unpause
def toggle_sound():
    try:
        global is_playing, start_time, last_activity_time
        last_activity_time = time.time()
        if is_playing:
            current_song = os.path.basename(playlist[current_index])
            elapsed_time = int(time.time()) - start_time
            song_playtimes[current_song] += elapsed_time
            save_playtimes()
            
            pygame.mixer.music.pause()
            is_playing = False
            update_presence(os.path.basename(playlist[current_index]))
        else:
            pygame.mixer.music.unpause()
            is_playing = True
            song_name = os.path.basename(playlist[current_index])
            song_length = get_song_length(playlist[current_index])
            elapsed_time = int(time.time()) - start_time
            start_time = int(time.time()) - elapsed_time
            update_presence(song_name, start_time, song_length - elapsed_time)
    except Exception as e:
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
            volume_slider.set(volume * 1000) #- i think this is causing the crashes


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
    if shuffle_mode:
        random.shuffle(playlist)
    else:
        playlist = list(original_playlist)
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
        RPC.clear()


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
            current_song = os.path.basename(playlist[current_index])
            song_length = get_song_length(playlist[current_index])
            elapsed_time = int(time.time()) - start_time
            update_presence(current_song, start_time, song_length - elapsed_time)
        elif (time.time() - last_activity_time) >= 900:
            update_presence()
    root.after(1000, check_song_end)


#? updates periodic (gui)
def periodic_update():
    global start_time
    if is_playing:
        current_song = os.path.basename(playlist[current_index])
        song_length = get_song_length(playlist[current_index])
        elapsed_time = int(time.time()) - start_time
        update_presence(current_song, start_time, song_length - elapsed_time)
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
    return pygame.mixer.music.get_volume() * 1000

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


#! checking for changes
#? main.py
error(hardcoded_config, "config.py", f"config.py doesnt exists", True)
error(hardcoded_resizeable, False, f"Wrong Resizeable is on {hardcoded_resizeable} and not on \"True\"", False)
error(hardcoded_geometry, "800x650", f"Wrong Geometry in {hardcoded_config}", False)
error(hardcoded_root_title, "MusiEz - @tamino1230", f"Wrong RootTitle in {hardcoded_config}", False)
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
root.iconbitmap(hardcoded_icon_path)
root.resizable(hardcoded_resizeable, hardcoded_resizeable)

button_frame = tk.Frame(root)
button_frame.pack(anchor="nw", pady=10)


#! Discord RPC
#! RPC toggle button
rich_presence_button = tk.Button(button_frame, text=f"Rich Presence: {at_start_rich_button}", command=toggle_rich_presence)
rich_presence_button.pack(side=tk.LEFT, padx=5)

#. RPC reconnect button
#// reconnect_button = tk.Button(button_frame, text="Reconnect", command=reconnect_rpc)
#// reconnect_button.pack(side=tk.LEFT, padx=5)


#! Load Songs Button
#// load_button = tk.Button(root, text="Load Songs", command=load_songs)
#// load_button.pack(pady=10)


#! Song List
song_list = Listbox(root)
song_list.pack(pady=10, fill=tk.BOTH, expand=True)
song_list.bind("<Double-1>", play_selected_song)


#! controls Frame
controls_frame = tk.Frame(root)
controls_frame.pack(pady=10)

#. pause button
pause_button = tk.Button(controls_frame, text="Pause/Unpause", command=toggle_sound)
pause_button.grid(row=0, column=1, padx=5)

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

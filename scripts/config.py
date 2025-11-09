
#* Programmer
by = "Tamino1230" #- maker of this program / Programm will not work if changed
# custom_discord_user_id = "702893526303637604"

#* Quality of Life
bgcolor = "purple" #- background-color | #F791C1 is a hex color
default_folder = "downloaded_music" #- where the downloaded files are getting added to. (which folder)


#* Recording Settings
record_actions = True #- If you want to record all your actions / False = no / True = yes


#* Debug Settings
error_message = True #- Debugging tool./ Info tool
#! Put on True if you programm is not starting/crashing or when problems appear (most errors in console can be ignored)


#* Discord RPC Settings
default_discord_rich_presence = True #- default True
show_repeat_shuffle = True #- If False it will not show (Repeat & Shuffle) on Discord
use_old_rpc_settings = False #- If True it will use the old RPC settings (not recommended)


#* Audio Settings
max_volume = 500 #- needs to be under 500 and over 0

sleeplength = 1 #- After how many minutes the program will end itself 
time_format = "h" #- Avaible time formats: s; m; h; second; minute; hour;
sleeptimer = True #- Music Automaticly Stops after how many minutes you put on sleeplength


#* Hotkey Settings
hotkeys_active = True #- On True your HotKeys will be used
 
pause_unpause_hotkey = 'ctrl+f6' #- HotKey for Pausing/Unpausing Songs
next_song_hotkey = 'ctrl+f7' #- HotKey next Songs
last_song_hotkey = 'ctrl+f5' #- HotKey for last Songs
sleep_mode_start_hotkey = 'shift+ctrl+9' #- HotKey for sleepmode / stop songs in time
repeat_toggle_hotkey = 'ctrl+f4' #- HotKey for repeat toggle

deactivate_add_remove_volume = True #- If True the add/remove volume hotkeys will not be used due to the Program crashing

add_volume_hotkey = 'ctrl+f3' #- HotKey for adding volume
remove_volume_hotkey = 'ctrl+f2' #- HotKey for removing volume

volume_onhotkey = 10 #- (Default: 10) Volume that gets added on hotkey 'add/remove_volume_hotkey'


# todo soundboard
#! NOT USED
#* Microphone Settings
mic = "Mikrofon (USB 2.0 Camera Audio)" #- if you wanna use the soundboard you need to input your microphone


#! do not change
#* Hardcoded Stuff
#? main.py
hardcoded_config = "scripts/config.py" #- Programm will not work if changed
hardcoded_resizeable = False #- Programm will not work if changed
hardcoded_geometry = "800x650" #- Programm will not work if changed
hardcoded_root_title = "BabTomaMusic - @tamino1230" #- Programm will not work if changed
hardcoded_presence = " | made by tamino1230 on GitHub <3" #- Programm will not work if changed
hardcoded_client_id = '1309941984407977996' #- Programm will not work if changed
hardcoded_icon_path = "icon/babToma.ico" #- Programm will not work if changed
hardcoded_contact_url = "https://discord.com/users/702893526303637604" #- Programm will not work if changed
hardcoded_join_url = "https://discord.gg/vpApZSjh3H" #- Programm will not work if changed
hardcoded_feedback_url = "https://discord.com/channels/1308085385351397427/1321532070144774215" #- Programm will not work if changed
hardcoded_idea_url = "https://discord.com/channels/1308085385351397427/1321532085957165138" #- Programm will not work if changed
#? helping window
hardcoded_resizeable_hp = False #- Programm will not work if changed
hardcoded_geometry_hp = "800x600" #- Programm will not work if changed
hardcoded_root_title_hp = "Helping Window - @tamino1230" #- Programm will not work if changed
#? Sharing
hardcoded_github_url = "https://github.com/Tamino1230/babTomaMusic" #- Programm will not work if changed

#! if any problems happen text me on discord: @tamino1230

#. other custom rich presence settings:
#* playing:
playing_presence = f"Listening to "
playing_custom_text_behind = f""

#* paused:
paused_presence = f"Paused "
paused_custom_text_behind = ""

#* idling:
idle_presence = f"Idling "
idle_custom_text_behind = ""

#. only custom rich presence
only_custom_rpc = False #- False on default
custom_rpc_text = "Exampletext!!!!" #- this text will show if you have 'only_custom_rpc' on 'True'

#! have fun with this "music app"

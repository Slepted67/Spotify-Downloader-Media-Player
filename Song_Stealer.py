# === Imports and Initial Setup ===
import os, sys
from mutagen.mp3 import MP3
from mutagen import File as MutagenFile
import pygame
import threading
import pandas as pd
import spotipy
import yt_dlp
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch
import tkinter as tk
from tkinter import simpledialog, ttk

# Determine base directory depending on whether running as a script or bundled exe
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

# Setup FFmpeg path and song download folder
ffmpeg_path = os.path.join(script_dir, 'ffmpeg', 'bin')
os.makedirs(os.path.join(script_dir, "StolenSongs"), exist_ok=True)

# Initialize the Pygame mixer for music playback
pygame.mixer.init()

music_player_window = None  # Tracks if the player window is open
currently_playing_path = None  # Stores currently playing file path


# === Spotify API Setup ===
client_id = '6ca2183c12fa4746af83cb9b63696b02'
client_secret = '41c2b23c8a4543e886c0ab04c5dd1c75'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))


# === Step 1: Fetch song data from Spotify track/album/playlist URL ===
def get_spotify_data(url):
    try:
        song_data = []
        if "track" in url:
            # Single track
            track = sp.track(url)
            song_data.append({
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "album": track['album']['name'],
                "release_year": track['album']['release_date'][:4]
            })

        elif "album" in url:
            # Full album
            album_tracks = sp.album_tracks(url)
            for track in album_tracks['items']:
                song_data.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": sp.album(url)['name'],
                    "release_year": sp.album(url)['release_date'][:4]
                })

        elif "playlist" in url:
            # Playlist
            playlist_tracks = sp.playlist_tracks(url)
            for item in playlist_tracks['items']:
                track = item['track']
                song_data.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "release_year": track['album']['release_date'][:4]
                })

        else:
            print("Invalid Spotify URL.")
            return []

        return song_data

    except Exception as e:
        print(f"Error fetching data from Spotify: {e}")
        return []


# === Step 2: Save song data as CSV for recordkeeping ===
def save_to_csv(song_data, filename='songs.csv'):
    csv_path = os.path.join(script_dir, filename)
    pd.DataFrame(song_data).to_csv(csv_path, index=False)
    print(f"Data saved to {csv_path}")


# === Step 3: Search for song on YouTube ===
def search_youtube(song):
    query = f"{song['name']}, {song['artist']}"
    result = VideosSearch(query, limit=1).result()
    return result['result'][0]['link'] if result['result'] else None


# === Step 4: Download audio from YouTube ===
def download_song(youtube_url, song=None, album_or_playlist_name=None, output_base_path='StolenSongs'):
    output_path = os.path.join(script_dir, output_base_path, album_or_playlist_name) if album_or_playlist_name else os.path.join(script_dir, output_base_path)
    os.makedirs(output_path, exist_ok=True)

    # Format filename safely
    base_name = f"{song['name']} - {song['artist']}" + (f" - {album_or_playlist_name}" if album_or_playlist_name else "")
    safe_name = "".join(c for c in base_name if c not in r'\/:*?"<>|')

    # yt-dlp config
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, f"{safe_name}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'prefer_ffmpeg': True,
        'ffmpeg_location': ffmpeg_path,
        'retries': 10,
        'overwrites': True,
        'nocheckcertificate': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"Downloading to: {output_path}")
        ydl.download([youtube_url])
    print("Download complete.")


# === GUI: Input, Buttons, Progress, Music Launch ===
def get_spotify_url():
    root = tk.Tk()
    root.title("Spotify Rhythm Thief")
    root.geometry("450x300")
    root.resizable(False, False)

    def clear_entry(): url_entry.delete(0, tk.END)

    def process_download():
        spotify_url = url_entry.get()
        if not spotify_url:
            clear_entry(); return

        songs = get_spotify_data(spotify_url)
        if not songs:
            clear_entry(); return

        save_to_csv(songs)

        album_or_playlist_name = sp.album(spotify_url)['name'] if "album" in spotify_url else sp.playlist(spotify_url)['name'] if "playlist" in spotify_url else None

        progress["maximum"], progress["value"] = len(songs), 0

        for song in songs:
            youtube_url = search_youtube(song)
            if youtube_url:
                print(f"Downloading: {song['name']} by {song['artist']}")
                download_song(youtube_url, song=song, album_or_playlist_name=album_or_playlist_name)
            else:
                print(f"Could not find YouTube link for {song['name']} by {song['artist']}")
            progress["value"] += 1
            root.update_idletasks()

        clear_entry()
        progress["value"] = 0

    def on_submit(): threading.Thread(target=process_download).start()

    # GUI Elements
    label = tk.Label(root, text="Enter Spotify URL:"); label.pack(pady=10)
    entry_frame = tk.Frame(root); entry_frame.pack(pady=5)
    url_entry = tk.Entry(entry_frame, width=40); url_entry.pack(side="left")
    tk.Button(entry_frame, text="❌", command=clear_entry).pack(side="left", padx=5)
    progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate"); progress.pack(pady=10)
    tk.Button(root, text="Submit", command=on_submit).pack(pady=20)
    tk.Button(root, text="View Song Hoard", command=lambda: show_downloaded_songs()).pack(pady=5)
    tk.Button(root, text="Launch Music Player", command=show_music_player).pack(pady=5)
    root.mainloop()


# === Song List Viewer GUI ===
def show_downloaded_songs(show_tracks_in_folders=False):
    window = tk.Toplevel()
    window.title("Stolen Song Hoard")
    window.geometry("500x500")
    window.resizable(True, True)

    show_tracks_var = tk.BooleanVar(value=show_tracks_in_folders)
    download_path = os.path.join(script_dir, "StolenSongs")

    def refresh_view(show_tracks):
        output.config(state="normal")
        output.delete("1.0", tk.END)

        if not os.path.exists(download_path):
            output.insert("end", "No songs downloaded yet.\n")
        else:
            output.insert("end", "── Singles ──\n")
            for item in os.listdir(download_path):
                if os.path.isfile(os.path.join(download_path, item)) and item.lower().endswith((".mp3", ".webm", ".m4a", ".opus")):
                    output.insert("end", f"• {item}\n")
            output.insert("end", "\n── Albums/Playlists ──\n")
            for folder in os.listdir(download_path):
                folder_path = os.path.join(download_path, folder)
                if os.path.isdir(folder_path):
                    output.insert("end", f"📁 {folder}\n")
                    if show_tracks:
                        for track in os.listdir(folder_path):
                            if track.lower().endswith((".mp3", ".webm", ".m4a", ".opus")):
                                output.insert("end", f"   • {track}\n")

        output.config(state="disabled")

    tk.Checkbutton(window, text="Show tracks inside albums/playlists", variable=show_tracks_var, command=lambda: refresh_view(show_tracks_var.get())).pack(pady=5)
    output = tk.Text(window, wrap="word", state="normal"); output.pack(expand=True, fill="both", padx=10, pady=10)
    refresh_view(show_tracks_var.get())


# === Update Music Progress Bar Based on Playback ===
def update_progress(window, progress_var, currently_playing_path):
    try:
        if pygame.mixer.music.get_busy() and currently_playing_path:
            audio = MP3(currently_playing_path) if currently_playing_path.lower().endswith(".mp3") else MutagenFile(currently_playing_path)
            if audio and hasattr(audio, "info") and hasattr(audio.info, "length"):
                length = audio.info.length
                pos_ms = pygame.mixer.music.get_pos()
                if length > 0 and pos_ms > 0:
                    progress_var.set((pos_ms / 1000) / length * 100)
                else:
                    progress_var.set(0)
            else:
                progress_var.set(0)
        else:
            progress_var.set(0)
    except Exception as e:
        print(f"[Progress Error] {e}")
        progress_var.set(0)
    window.after(500, lambda: update_progress(window, progress_var, currently_playing_path))


# === Music Player GUI with Play Controls, Volume, and Progress Bar ===
def show_music_player():
    global music_player_window, currently_playing_path

    if music_player_window and music_player_window.winfo_exists():
        music_player_window.lift(); return

    window = tk.Toplevel()
    music_player_window = window
    window.title("Rhythm Thief: Showcase")
    window.geometry("500x350")
    window.resizable(False, False)

    continue_var = tk.BooleanVar(value=False)

    def get_all_tracks():
        tracks = []
        for root, _, files in os.walk(os.path.join(script_dir, "StolenSongs")):
            for file in files:
                if file.lower().endswith((".mp3", ".webm", ".m4a", ".opus")):
                    tracks.append(os.path.join(root, file))
        return tracks

    playlist = get_all_tracks()
    if not playlist:
        print("No songs found in StolenSongs."); return

    current_index = 0
    last_index = None
    is_paused = False

    song_label_var = StringVar()
    tk.Label(window, textvariable=song_label_var, wraplength=480).pack(pady=20)

    progress_var = tk.DoubleVar()
    ttk.Progressbar(window, variable=progress_var, maximum=100, length=400).pack(pady=(0, 10))

    def play_song(index):
        nonlocal current_index, last_index, is_paused
        if 0 <= index < len(playlist):
            current_index = index
            pygame.mixer.music.load(playlist[current_index])
            pygame.mixer.music.play()
            song_label_var.set(f"Now Playing:\n{os.path.basename(playlist[current_index])}")
            globals()['currently_playing_path'] = playlist[current_index]
            is_paused = False

    def pause_song():
        nonlocal is_paused
        if pygame.mixer.music.get_busy(): pygame.mixer.music.pause(); is_paused = True

    def resume_song():
        nonlocal is_paused
        if is_paused: pygame.mixer.music.unpause(); is_paused = False

    def next_song():
        nonlocal current_index
        if current_index + 1 < len(playlist): play_song(current_index + 1)

    def previous_song():
        nonlocal current_index
        if pygame.mixer.music.get_pos() > 10000: play_song(current_index)
        elif current_index > 0: play_song(current_index - 1)

    # Control Buttons
    control_frame = tk.Frame(window); control_frame.pack()
    tk.Button(control_frame, text="⏮️", width=5, command=previous_song).grid(row=0, column=0, padx=5)
    tk.Button(control_frame, text="▶️", width=5, command=resume_song).grid(row=0, column=1, padx=5)
    tk.Button(control_frame, text="⏸️", width=5, command=pause_song).grid(row=0, column=2, padx=5)
    tk.Button(control_frame, text="⏭️", width=5, command=next_song).grid(row=0, column=3, padx=5)

    # Volume Slider
    volume_frame = tk.Frame(window); volume_frame.pack(pady=(0, 10))
    tk.Label(volume_frame, text="Volume").pack(side="left", padx=(10, 5))
    volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient="horizontal", command=lambda val: pygame.mixer.music.set_volume(float(val)/100))
    volume_slider.set(100); volume_slider.pack(side="left")

    # Continue playback toggle
    tk.Checkbutton(window, text="Continue playback after closing", variable=continue_var).pack(pady=5)

    if not pygame.mixer.music.get_busy():
        play_song(current_index)

    update_progress(window, progress_var, currently_playing_path)

    def on_close():
        if not continue_var.get(): pygame.mixer.music.stop()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)


# === Entry Point ===
def main():
    spotify_url = get_spotify_url()
    if spotify_url:
        songs = get_spotify_data(spotify_url)
        if not songs:
            print("No songs found.")
            return
        save_to_csv(songs)
        album_or_playlist_name = sp.album(spotify_url)['name'] if "album" in spotify_url else sp.playlist(spotify_url)['name'] if "playlist" in spotify_url else None
        for song in songs:
            youtube_url = search_youtube(song)
            if youtube_url:
                print(f"Downloading: {song['name']} by {song['artist']}")
                download_song(youtube_url, song=song, album_or_playlist_name=album_or_playlist_name)
            else:
                print(f"Could not find YouTube link for {song['name']} by {song['artist']}.")
    else:
        print("Exiting Program")


if __name__ == "__main__":
    main()

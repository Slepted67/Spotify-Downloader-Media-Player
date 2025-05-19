import tkinter as tk
from tkinter import simpledialog
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch
import yt_dlp
import pandas as pd
import os

# Set up Spotify API
client_id = '6ca2183c12fa4746af83cb9b63696b02'
client_secret = '41c2b23c8a4543e886c0ab04c5dd1c75'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Step 1: Get song data from Spotify
def get_spotify_data(url):
    try:
        # Identify if URL is for a track, album, or playlist
        song_data = []
        if "track" in url:
            track = sp.track(url)
            name = track['name']
            artist = track['artists'][0]['name']
            album = track['album']['name']
            release_year = track['album']['release_date'][:4]
            song_data.append({
                "name": name,
                "artist": artist,
                "album": album,
                "release_year": release_year
            })
        
        elif "album" in url:
            album_tracks = sp.album_tracks(url)
            for track in album_tracks['items']:
                name = track['name']
                artist = track['artists'][0]['name']
                album = sp.album(url)['name']
                release_year = sp.album(url)['release_date'][:4]
                song_data.append({
                    "name": name,
                    "artist": artist,
                    "album": album,
                    "release_year": release_year
                })
        
        elif "playlist" in url:
            playlist_tracks = sp.playlist_tracks(url)
            for item in playlist_tracks['items']:
                track = item['track']
                name = track['name']
                artist = track['artists'][0]['name']
                album = track['album']['name']
                release_year = track['album']['release_date'][:4]
                song_data.append({
                    "name": name,
                    "artist": artist,
                    "album": album,
                    "release_year": release_year
                })
        else:
            print("Invalid Spotify URL.")
            return []

        return song_data

    except Exception as e:
        print(f"Error fetching data from Spotify: {e}")
        return []


# Step 2: Save song data to CSV
def save_to_csv(song_data, filename='songs.csv'):
    df = pd.DataFrame(song_data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

# Step 3: Search for YouTube URL
def search_youtube(song):
    query = f"{song['name']}, {song['artist']}"
    video_search = VideosSearch(query, limit=1)
    result = video_search.result()
    if result['result']:
        return result['result'][0]['link']
    return None

# Step 4: Download song from YouTube
def download_song(youtube_url, album_or_playlist_name=None, output_base_path='downloads'):
    # If the album or playlist name is provided, create a folder based on it
    if album_or_playlist_name:
        output_path = os.path.join(output_base_path, album_or_playlist_name)
    else:
        output_path = output_base_path

    os.makedirs(output_path, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',  # best audio quality
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),  # output file template
        'ffmpeg-location': r'C:\Users\Justin Wilkins\Desktop\ffmpeg-7.1-essentials_build\bin',  # Specify the location of ffmpeg if necessary
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    print("Download complete.")

# Function to get Spotify URL from user with tkinter
import tkinter as tk
from tkinter import simpledialog

def get_spotify_url():
    # Create the main GUI window
    root = tk.Tk()
    root.title("Spotify Rhythm Thief")  # Set the window title
    root.geometry("300x150")
    root.resizable(False, False)

    # Add Label and Entry widgets for URL input
    label = tk.Label(root, text="Enter Spotify URL:")
    label.pack(pady=10)
    url_entry = tk.Entry(root, width=50)
    url_entry.pack()

    # This will store the entered URL to return it later
    spotify_url = None

    # Function to capture URL on button click
    def on_submit():
        nonlocal spotify_url
        spotify_url = url_entry.get()  # Get the URL from the entry widget
        root.quit()  # Close the GUI window

    # Add Submit button
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=20)

    # Run the Tkinter event loop
    root.mainloop()
    root.destroy()  # Ensure the Tk window is destroyed after it closes

    # Return the captured Spotify URL
    return spotify_url


# Main function
def main():
    spotify_url = get_spotify_url()
    if spotify_url:  # Only proceed if a URL was entered
        songs = get_spotify_data(spotify_url)
        if not songs:
            print("No songs found.")
            return

        album_or_playlist_name = None
        if "album" in spotify_url:
            album_or_playlist_name = sp.album(spotify_url)['name']
        elif "playlist" in spotify_url:
            album_or_playlist_name = sp.playlist(spotify_url)['name']

        save_to_csv(songs)

        for song in songs:
            youtube_url = search_youtube(song)
            if youtube_url:
                print(f"Downloading: {song['name']} by {song['artist']}")
                download_song(youtube_url, album_or_playlist_name=album_or_playlist_name)
            else:
                print(f"Could not find YouTube link for {song['name']} by {song['artist']}.")
    else:
        print("No URL entered. Exiting program.")

if __name__ == "__main__":
    main()

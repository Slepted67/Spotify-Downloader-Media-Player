# Spotify Downloader and Media Player

Really wanted to find a way to stop paying for Spotify Premium after my student discount dies.  
This project creates a Spotify URL downloader with a built-in GUI music player and playlist management features.

## Features
- Download songs from Spotify track, album, or playlist URLs
- Searches YouTube for the best audio match
- Converts audio to `.mp3` using FFmpeg
- Saves files into a clean "StolenSongs" folder
- Custom GUI music player with:
  - Play, pause, skip, and previous controls
  - Volume slider
  - Playback progress bar
  - Optional "continue playing when window closes" toggle
- Dynamic display of downloaded songs by folder or single file

## Technologies
- Python
- Tkinter
- Spotipy (Spotify Web API)
- youtube-search-python
- yt-dlp (YouTube downloader)
- pygame (audio playback)
- mutagen (track length detection for progress bar)
- FFmpeg (for audio conversion)

## FFmpeg Disclaimer
This tool uses [FFmpeg](https://ffmpeg.org/) for audio conversion. FFmpeg is an open-source project under the LGPL/GPL license.  
I do not claim ownership of FFmpeg, nor have I modified its binaries. This project simply uses FFmpeg to convert downloaded YouTube audio into MP3 format.

## What I Learned
- API authentication and integration (Spotify Web API)
- YouTube content scraping via search
- Event-driven GUI design with Tkinter
- Real-time progress tracking and multithreading
- Media playback and audio control via `pygame`

## Planned Features
- Playlist folder switching from the GUI
- Playback history and shuffle mode
- Keyboard hotkey support for player control

## Notes
This tool is for educational and personal use only. Respect copyright laws in your country.

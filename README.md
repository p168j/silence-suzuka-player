# Silence Suzuka Player

🤖 This app was written almost entirely by AI 🤖

A media player that automatically plays your content when it detects system-wide silence, and pauses when you're away from your computer.



## Features

* **Auto-Play on Silence:** Monitors your system's audio and automatically starts playing from your playlist when no other sound is active.
* **AFK Detection:** Pauses playback automatically when you're inactive and away from your computer.
* **Advanced Playlist Management:** Save, load, and manage multiple playlists.
* **Unified Library:** Add videos from YouTube, Bilibili, and local files all in one place.
* **Resume Playback:** Remembers your position in every video.
* **Background Duration Fetching:** Automatically fetches video durations in the background with intelligent caching to eliminate manual fetching delays.

## Requirements

1.  **Python 3.9+**
2.  **VoiceMeeter:** For audio routing on Windows. ([Download here](https://vb-audio.com/Voicemeeter/))
3.  All Python packages listed in `requirements.txt`.

## ⚙️ Setup Instructions

### 1. Audio Rerouting with VoiceMeeter (The Important Part!)

To detect system-wide silence, the app needs to be able to "hear" what your speakers are playing. Windows doesn't allow this by default, so we use a free tool called VoiceMeeter to create a virtual audio device.

**Setup Steps:**

1.  **Install VoiceMeeter:** Download and install it from the link above. **A restart is required after installation.**
2.  **Set VoiceMeeter as Default:**
    * Right-click the speaker icon in your Windows taskbar and select **"Sounds"**.
    * Go to the **"Playback"** tab.
    * Find **"VoiceMeeter Input"** in the list, click on it, and then click **"Set Default"**.
3.  **Configure VoiceMeeter:**
    * Open the VoiceMeeter application.
    * On the far right, under **HARDWARE OUT**, click on **A1**.
    * Select your actual speakers or headphones from the list (usually a WDM option).

### 2. Application Installation

1.  **Download/Clone:** Get the project files from GitHub.
2.  **Install Dependencies:** Open a terminal in the project folder and run:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure the Player:**
    * Run the player for the first time: `python silence_suzuka_player.py`
    * Click the **Settings** (⚙️) icon.
    * Go to the **"Audio Monitor"** tab.
    * From the **"Input device"** dropdown, select the device that says **"VoiceMeeter Output"** (or similar).

## 🚀 Usage

To run the application, open your terminal in the project folder and run:
```bash
python silence_suzuka_player.py
```
You can then add media via the "Add Media" button, copy-paste or drag-and-drop files/links, or load a saved playlist.

## ⚠️ Important Notes & Troubleshooting
* "mpv not found" Error: This application requires the official mpv player library to be installed on your system.

   * Solution: Install the official mpv player for your OS. On Windows, ensure the folder containing mpv-2.dll is in your system's PATH.

* Online Videos Suddenly Stop Working: YouTube and other sites frequently change their websites, which can break video downloading.

   * Solution: This is almost always fixed by updating yt-dlp. Run this command: pip install --upgrade yt-dlp.

* Audio Monitor Doesn't Work on First Run: The silence detection will not work out of the box.

   * Solution: You must follow the setup instructions to install and configure VoiceMeeter, then select the correct "VoiceMeeter Output" device in this app's Settings > Audio Monitor tab.

* **Automatic Duration Fetching**: Durations for both local files and online videos (YouTube/Bilibili) are now fetched automatically in the background with intelligent caching. The system prioritizes visible items and uses multiple worker threads for optimal performance. You can configure or disable this feature in Settings > Duration Fetching.

* Bilibili Login & Cookies: To access members-only Bilibili content, you need a cookies.txt file in the app's folder. Be aware that this file contains sensitive login information.

* Platform Support: This application and its audio monitoring features were developed and tested on Windows. Core functionality may work on macOS and Linux, but system-level features like audio and AFK monitoring will likely not work without changes.

## Known Limitations & Design Choices
This application was designed to be a fast, responsive personal tool. Some features were intentionally implemented in a manual way to prioritize performance over full automation.

* **Background Duration Fetching**: Duration information for local files is fetched automatically in the background when you add them. For online videos (YouTube/Bilibili), durations are now also fetched automatically in the background with intelligent caching to avoid repeated requests. You can also manually trigger duration fetching for all items by clicking the "Fetch all durations" button (⏱️) if needed.

* No Real-time Playlist Syncing: If you modify the playlists_v2.json file outside of the app while it's running, you will need to restart the application to see your changes.

* Limited Undo History: The Undo feature (Ctrl+Z) is intentionally limited to the last 10 actions to conserve memory.

* Simple Search Functionality: The search bar filters based on the visible text in the playlist (mostly titles). It does not search through deeper metadata.

* Potential Audio Monitoring Setup: The System Audio Monitor relies on a "loopback" device to hear what your speakers are playing, which may require manual setup using a tool like VoiceMeeter.

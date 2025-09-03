# Silence Suzuka Player

🤖 This app was written almost entirely by AI 🤖

A smart media player that automatically plays your content when it detects system-wide silence, and pauses when you're away from your computer.



## Features

* **Auto-Play on Silence:** Monitors your system's audio and automatically starts playing from your playlist when no other sound is active.
* **AFK Detection:** Pauses playback automatically when you're inactive and away from your computer.
* **Advanced Playlist Management:** Save, load, and manage multiple playlists.
* **Unified Library:** Add videos from YouTube, Bilibili, and local files all in one place.
* **Resume Playback:** Remembers your position in every video.

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
    * Run the player for the first time: `python silence-suzuka-player.py`
    * Click the **Settings** (⚙️) icon.
    * Go to the **"Audio Monitor"** tab.
    * From the **"Input device"** dropdown, select the device that says **"VoiceMeeter Output"** (or similar).

## 🚀 Usage

To run the application, open your terminal in the project folder and run:
```bash
python silence-suzuka-player.py
```
You can then add media via the "Add Media" button, copy-paste or drag-and-drop files/links, or load a saved playlist.

## Known Limitations & Design Choices
This application was designed to be a fast, responsive personal tool. Some features were intentionally implemented in a manual way to prioritize performance over full automation.

* Manual Duration Fetching for Online Videos: Fetching durations for local files happens automatically in the background when you add them. However, getting this information for online videos (YouTube/Bilibili) is a much slower process.

   * Solution: To prevent lag, you must manually trigger duration fetching for online content by clicking the "Fetch all durations" button (⏱️).

* No Real-time Playlist Syncing: If you modify the playlists_v2.json file outside of the app while it's running, you will need to restart the application to see your changes.

* Limited Undo History: The Undo feature (Ctrl+Z) is intentionally limited to the last 10 actions to conserve memory.

* Simple Search Functionality: The search bar filters based on the visible text in the playlist (mostly titles). It does not search through deeper metadata.

* Potential Audio Monitoring Setup: The System Audio Monitor relies on a "loopback" device to hear what your speakers are playing, which may require manual setup using a tool like VoiceMeeter.

# Silence-Suzuka-Player

🤖 This app was written almost entirely by AI 🤖

A media player that automatically plays your content when it detects system-wide silence, and pauses when you're away from your computer.



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

**Why?** Think of it like this: All the sound from your PC (games, browser, etc.) normally goes straight to your speakers. We need to route it through a "checkpoint" where our app can listen in. VoiceMeeter is that checkpoint.

**Setup Steps:**

1.  **Install VoiceMeeter:** Download and install it from the link above. **A restart is required after installation.**

2.  **Set VoiceMeeter as Default:**
    * Right-click the speaker icon in your Windows taskbar and select **"Sounds"**.
    * Go to the **"Playback"** tab.
    * Find **"VoiceMeeter Input"** in the list, click on it, and then click **"Set Default"**. A green checkmark will appear.
    * 

3.  **Configure VoiceMeeter:**
    * Open the VoiceMeeter application.
    * On the far right, under **HARDWARE OUT**, click on **A1**.
    * Select your actual speakers or headphones from the list (usually a WDM option).
    * 

    That's it for VoiceMeeter! All your computer's audio is now passing through it before going to your speakers.

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
    * From the **"Input device"** dropdown, select the device that says **"VoiceMeeter Output"** (or similar). This tells the app to listen to the checkpoint we just set up.

## 🚀 Usage

To run the application, open your terminal in the project folder and run:
```bash
python silence-suzuka-player.py
```
You can then add media via the "Add Media" button, drag-and-drop files/links, or load a saved playlist.
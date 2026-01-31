# Gemini YouTube Downloader

A modern, robust, and user-friendly YouTube Video Downloader built with Python and CustomTkinter.

## Features
- **Modern UI**: Dark mode, clean layout, and responsive design.
- **Format Support**: Download Video (MP4) or Audio Only (MP3/M4A).
- **Quality Control**: Select from available resolutions (720p, 360p, etc.).
- **Reliability**: Validates URLs, handles network errors, and prevents freezing during downloads.
- **Logging**: detailed logs in `logs/` directory for debugging.

## Installation

1.  **Clone/Download** this repository.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you encounter issues with `pytube`, consider installing `pytubefix` instead and updating the import in `core/downloader.py`.*

## Running the App
```bash
python main.py
```

## Packaging (Build .exe)
To build a standalone executable:
1.  Install PyInstaller: `pip install pyinstaller`
2.  Run the build command:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --name "GeminiDownloader" --icon="icon.ico" main.py
    ```
    *(Note: You can remove `--icon="icon.ico"` if you don't have an icon file yet)*

## Architecture
- **`core/`**: Contains the business logic (`downloader.py`). Separated from UI to allow for easy testing or CLI implementation in the future.
- **`ui/`**: Contains the GUI code (`app.py`). Handles user interaction and updates the display based on events.
- **`utils/`**: Helper functions for logging and validation.

## Troubleshooting
**"RegexMatchError" or "Video Unavailable"?**
YouTube frequently updates their player logic. If the downloader stops working:
1.  Try updating pytube: `pip install --upgrade pytube`
2.  Or switch to `pytubefix`: `pip install pytubefix` and change `from pytube import YouTube` to `from pytubefix import YouTube` in `core/downloader.py`.

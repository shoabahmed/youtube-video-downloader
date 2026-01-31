# Universal Downloader

A clean, modern, and powerful media downloader built with Python and CustomTkinter. Supports downloading video and audio from multiple social platforms.

## ✨ Features

- **Multi-Platform Support**: Download from YouTube (including Shorts), TikTok, Instagram (Reels), X (Twitter), Reddit, LinkedIn, and Facebook.
- **High Quality**: Automatically merges best video and audio streams for the highest possible resolution.
- **Audio Extraction**: Easily download any video as a high-quality MP3.
- **Modern UI**: Sleek, dark-themed interface built with CustomTkinter.
- **Safe & Clean**: Sanitizes filenames and manages temporary files automatically.

## 🛠️ Prerequisites

- **Python 3.8+**
- **FFmpeg**: Required for merging video and audio tracks (especially for 1080p+).
  - [Download FFmpeg](https://ffmpeg.org/download.html) and ensure it's in your system PATH.

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/shoabahmed/youtube-video-downloader.git
   cd youtube-downloader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

1. Run the application:
   ```bash
   python main.py
   ```
   *Or use the provided `run.bat` on Windows.*

2. Paste a URL from a supported platform.
3. Click **Fetch Info**.
4. Select your preferred format (Video/Audio) and quality.
5. Click **Download**.

## 📦 Dependencies

- `yt-dlp`: The core engine for media extraction.
- `customtkinter`: For the modern user interface.
- `Pillow`: For image/thumbnail processing.
- `packaging`: For version management.

## 📝 License

MIT License - feel free to use and modify!

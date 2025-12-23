import os
import subprocess
import shutil
from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError, VideoUnavailable
from utils.logger import setup_logger

logger = setup_logger()

class VideoInfo:
    def __init__(self, title, thumbnail_url, length, author, streams_mp4, streams_mp3):
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.length = length
        self.author = author
        self.streams_mp4 = streams_mp4 # List of (resolution, filesize_mb, itag, is_progressive)
        self.streams_mp3 = streams_mp3 # List of (abr, filesize_mb, itag)

class YouTubeHandler:
    def __init__(self):
        self.yt = None
        self.on_progress_callback = None
        self.on_complete_callback = None
        self.ffmpeg_available = shutil.which("ffmpeg") is not None

    def fetch_metadata(self, url):
        logger.info(f"Fetching metadata for URL: {url}")
        try:
            self.yt = YouTube(
                url, 
                on_progress_callback=self._on_progress,
                on_complete_callback=self._on_complete
            )
            
            # Force pre-fetch to validate
            self.yt.check_availability()
            
            title = self.yt.title
            thumbnail = self.yt.thumbnail_url
            length = self.yt.length
            author = self.yt.author

            mp4_options = []
            seen_resolutions = set()

            # 1. Get Progressive Streams (Audio + Video, usually max 720p)
            prog_streams = self.yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            
            for s in prog_streams:
                if s.resolution not in seen_resolutions:
                    filesize = s.filesize_mb
                    mp4_options.append({
                        "resolution": s.resolution,
                        "filesize": f"{filesize:.1f} MB",
                        "itag": s.itag,
                        "type": "video",
                        "is_progressive": True
                    })
                    seen_resolutions.add(s.resolution)

            # 2. Get Adaptive Streams (Video Only, 1080p, 4K, etc.)
            # Only if ffmpeg is available, otherwise we can't merge cleanly (or we warn user)
            # For now, we list them but if downloaded without ffmpeg, we might just save video.
            # But let's be robust: List them.
            adapt_streams = self.yt.streams.filter(only_video=True, adaptive=True, file_extension='mp4').order_by('resolution').desc()
            
            for s in adapt_streams:
                if s.resolution not in seen_resolutions and s.resolution:
                    # Filter out low quality adaptive if we already have progressive? 
                    # Usually we want to keep 1080p, 1440p, 2160p
                    # Simple logic: If not seen, add it.
                    filesize = s.filesize_mb
                    mp4_options.append({
                        "resolution": s.resolution,
                        "filesize": f"{filesize:.1f} MB (Video Only)" if not self.ffmpeg_available else f"{filesize:.1f} MB",
                        "itag": s.itag,
                        "type": "video",
                        "is_progressive": False
                    })
                    seen_resolutions.add(s.resolution)

            # Sort by resolution (numeric value) to ensure 1080p is top
            def res_sort_key(item):
                res_str = item['resolution']
                if not res_str: return 0
                return int(res_str.replace('p', ''))
            
            mp4_options.sort(key=res_sort_key, reverse=True)

            # MP3: Audio only
            audio_streams = self.yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc()
            
            mp3_options = []
            for s in audio_streams:
                filesize = s.filesize_mb
                mp3_options.append({
                    "resolution": s.abr, # e.g., 128kbps
                    "filesize": f"{filesize:.1f} MB",
                    "itag": s.itag,
                    "type": "audio"
                })

            logger.info("Metadata fetched successfully.")
            return VideoInfo(title, thumbnail, length, author, mp4_options, mp3_options)

        except VideoUnavailable:
            logger.error("Video unavailable.")
            raise Exception("Video is unavailable or private.")
        except RegexMatchError:
            logger.error("Invalid URL format.")
            raise Exception("Invalid YouTube URL.")
        except Exception as e:
            logger.error(f"Error fetching metadata: {str(e)}")
            raise Exception(f"Failed to fetch video info: {str(e)}")

    def download_stream(self, itag, download_path, progress_callback, complete_callback):
        """
        Blocking download function. Handles both progressive and adaptive (merge) downloads.
        """
        self.on_progress_callback = progress_callback
        self.on_complete_callback = complete_callback
        
        try:
            stream = self.yt.streams.get_by_itag(itag)
            if not stream:
                raise Exception("Stream not found.")
            
            logger.info(f"Starting download: {stream.title} ({stream.resolution or stream.abr})")
            
            filename = stream.default_filename
            is_audio_mode = stream.includes_audio_track and not stream.includes_video_track
            
            # Check if we need to do adaptive merge
            # It's adaptive if it's video-only (and we are in video mode)
            is_adaptive_video = stream.includes_video_track and not stream.includes_audio_track
            
            if is_adaptive_video:
                return self._download_adaptive(stream, download_path, filename)
            
            # Progressive or Audio-only download
            if is_audio_mode:
                 base, _ = os.path.splitext(filename)
                 filename = f"{base}.mp3"

            stream.download(output_path=download_path, filename=filename)
            logger.info("Download completed.")
            return os.path.join(download_path, filename)

        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise e

    def _download_adaptive(self, video_stream, download_path, filename):
        """
        Downloads video and audio separately, then merges with ffmpeg.
        """
        if not self.ffmpeg_available:
            logger.warning("FFmpeg not found. Downloading video only.")
            # Fallback: just download video, maybe rename to indicate no audio
            base, ext = os.path.splitext(filename)
            filename = f"{base}_no_audio{ext}"
            video_stream.download(output_path=download_path, filename=filename)
            return os.path.join(download_path, filename)

        # 1. Download Video
        logger.info("Downloading Video Track...")
        video_filename = f"temp_video_{video_stream.itag}.mp4"
        video_path = os.path.join(download_path, video_filename)
        video_stream.download(output_path=download_path, filename=video_filename)

        # 2. Download Best Audio
        logger.info("Downloading Audio Track...")
        audio_stream = self.yt.streams.get_audio_only()
        if not audio_stream:
             # Fallback if no audio found (rare)
             os.rename(video_path, os.path.join(download_path, filename))
             return os.path.join(download_path, filename)

        audio_filename = f"temp_audio_{audio_stream.itag}.mp4"
        audio_path = os.path.join(download_path, audio_filename)
        audio_stream.download(output_path=download_path, filename=audio_filename)

        # 3. Merge
        logger.info("Merging Video and Audio...")
        output_path = os.path.join(download_path, filename)
        
        # Clean up existing output if exists
        if os.path.exists(output_path):
            os.remove(output_path)

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ]
        
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            logger.info("Merge successful.")
            
            # Cleanup temps
            os.remove(video_path)
            os.remove(audio_path)
            
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg merge failed: {e}")
            # Don't delete temps so user can manually recover
            raise Exception("Failed to merge video and audio (FFmpeg error).")

    def _on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        
        if self.on_progress_callback:
            self.on_progress_callback(percentage, bytes_downloaded, total_size)

    def _on_complete(self, stream, file_path):
        if self.on_complete_callback:
            # For adaptive, this is called for EACH stream (video/audio)
            # We ignore it for the intermediate steps and handle final completion in _download_adaptive
            pass

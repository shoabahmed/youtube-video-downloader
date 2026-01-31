import os
import re
import yt_dlp
from utils.logger import setup_logger

logger = setup_logger()

class VideoInfo:
    def __init__(self, title, thumbnail_url, length, author, streams_mp4, streams_mp3):
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.length = length
        self.author = author
        self.streams_mp4 = streams_mp4 # List of dicts
        self.streams_mp3 = streams_mp3 # List of dicts

class DownloaderHandler:
    def __init__(self):
        self.on_progress_callback = None
        self.on_complete_callback = None
        self.url = None # Cached URL

    def fetch_metadata(self, url):
        logger.info(f"Fetching metadata for URL: {url}")
        self.url = url
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail', '')
            length = info.get('duration', 0)
            author = info.get('uploader', 'Unknown Author')
            
            formats = info.get('formats', [])
            
            mp4_options = []
            mp3_options = []
            seen_res = set()

            for f in formats:
                format_id = f.get('format_id')
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                if filesize:
                    filesize_mb = filesize / (1024 * 1024)
                    filesize_str = f"{filesize_mb:.1f} MB"
                else:
                    filesize_str = "Unknown Size"

                # Audio Options: vcodec='none' means audio only
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    abr = f.get('abr')
                    if abr:
                        mp3_options.append({
                            "resolution": f"{int(abr)}kbps",
                            "filesize": filesize_str,
                            "itag": format_id,
                            "type": "audio",
                        })

                # Video Options: vcodec!='none'
                elif f.get('vcodec') != 'none':
                    height = f.get('height')
                    if not height: continue
                    
                    res_str = f"{height}p"
                    
                    # Deduplicate by resolution (prefering better container/bitrate implicitly by order)
                    if res_str not in seen_res:
                        mp4_options.append({
                            "resolution": res_str,
                            "filesize": filesize_str,
                            "itag": format_id,
                            "type": "video",
                        })
                        seen_res.add(res_str)

            # Sort MP4 by resolution descending
            def res_sort_key(item):
                r = item['resolution'].replace('p', '')
                return int(r) if r.isdigit() else 0
            
            mp4_options.sort(key=res_sort_key, reverse=False)
            
            # Sort MP3 by bitrate descending
            def audio_sort_key(item):
                r = item['resolution'].replace('kbps', '')
                return int(r) if r.isdigit() else 0
            mp3_options.sort(key=audio_sort_key, reverse=False)

            logger.info("Metadata fetched successfully.")
            return VideoInfo(title, thumbnail, length, author, mp4_options, mp3_options)

        except Exception as e:
            logger.error(f"Error fetching metadata: {str(e)}")
            raise Exception(f"Failed to fetch video info: {str(e)}")

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            
            if total:
                percentage = (downloaded / total) * 100
                if self.on_progress_callback:
                    self.on_progress_callback(percentage, downloaded, total)
        
        elif d['status'] == 'finished':
            if self.on_progress_callback:
                self.on_progress_callback(100, 100, 100)

    def download_stream(self, format_id, download_path, progress_callback, complete_callback, is_audio=False):
        """
        Downloads the specified stream using yt-dlp.
        """
        self.on_progress_callback = progress_callback
        self.on_complete_callback = complete_callback
        
        try:
            logger.info(f"Starting download: {format_id} (Audio: {is_audio})")
            
            # Format Selection Strategy
            if is_audio:
                # Download specific audio format (or best audio) and convert to mp3
                format_str = f"{format_id}" 
            else:
                # Download video, merge with best audio if needed
                format_str = f"{format_id}+bestaudio/best"

            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
                'overwrites': True,
                'restrictfilenames': True, # Sanitize filenames
            }

            if is_audio:
                # Convert to MP3
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                # Ensure output is MP4 (merge compatible)
                ydl_opts['merge_output_format'] = 'mp4'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # We need to re-pass the URL. self.url should be set from fetch_metadata
                if not self.url:
                    raise Exception("URL not set. Fetch metadata first.")

                # download returns status code, not info. 
                # To get filename, we need info.
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Adjust filename extension if post-processing changed it
                if is_audio:
                    base, _ = os.path.splitext(filename)
                    filename = f"{base}.mp3"
                elif ydl_opts.get('merge_output_format') == 'mp4':
                     base, _ = os.path.splitext(filename)
                     filename = f"{base}.mp4"

            logger.info("Download completed.")
            if self.on_complete_callback:
                self.on_complete_callback(filename)
            
            return filename

        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise e

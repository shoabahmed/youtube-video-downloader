import re

def validate_youtube_url(url):
    """
    Validates if the provided URL is a valid YouTube URL.
    """
    if not url:
        return False
    
    # Common YouTube URL patterns
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    match = re.match(youtube_regex, url)
    return bool(match)

import re

def validate_url(url):
    """
    Validates if the provided URL is from a supported platform
    (YouTube, TikTok, Instagram, X/Twitter, Reddit, LinkedIn, Facebook).
    """
    if not url:
        return False
    
    # Simple domain check is often more robust than complex regexes for this purpose
    # as platforms have many URL variations (shortlinks, mobile subs, etc.)
    supported_domains = [
        "youtube.com", "youtu.be",
        "tiktok.com",
        "instagram.com",
        "twitter.com", "x.com",
        "reddit.com",
        "linkedin.com",
        "facebook.com", "fb.watch"
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in supported_domains)

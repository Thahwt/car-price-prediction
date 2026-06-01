HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36 "
        "Edg/136.0.0.0"
    ),

    # Accept
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",

    # Edge fingerprint
    "Sec-Ch-Ua": (
        '"Chromium";v="136", '
        '"Microsoft Edge";v="136", '
        '"Not.A/Brand";v="99"'
    ),
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',

    # Fetch
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",

    # Navigation
    "Upgrade-Insecure-Requests": "1",

    # Cache
    "Cache-Control": "max-age=0",
    "Pragma": "no-cache",

    # Connection
    "Connection": "keep-alive",

    # Privacy
    "DNT": "1",

    # Important
    "Referer": "https://www.google.com/",

    # Edge/Chrome priority
    "Priority": "u=0, i"
}
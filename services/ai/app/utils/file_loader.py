import httpx

def download_file(url: str) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url, headers=headers)

    content = response.content

    if not content.startswith(b"%PDF"):
        raise Exception("Downloaded content is not a valid PDF")

    return content
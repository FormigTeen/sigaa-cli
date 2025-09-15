from bs4 import BeautifulSoup

def strip_html_bs4(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style"]):
        s.decompose()
    return soup.get_text(separator="\n", strip=True)

# -*- coding: utf-8 -*-
import urllib.request, re, os

BASE = "https://facioergosum.com"
OUT = os.path.dirname(os.path.abspath(__file__))
BRAND = "\U0001f6e0️  Facio Ergo Sum"  # wrench emoji + double space + name, no slashes
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}

PAGES = ["/"] + [
 "/blog","/blog/failure-is-the-best-option","/blog/the-book-that-started-it-all",
 "/blog/pet-firefly-pcb-design","/blog/first","/blog/project-three-8h3m7",
 "/contact","/about","/work","/projects",
 "/projects/openheg-diy-brainreading-headband","/projects/electric-minibike-build",
 "/projects/lightning-bug-pcb","/projects/create-48","/projects/green-thumb-project",
 "/projects/tin-can-telephone","/projects/big-mouth-billy-bass-alexa","/projects/camp-cupid",
 "/projects/alien-spaceship-learn2solder","/projects/plonty","/projects/apex",
 "/projects/plant-emotion-monitor","/projects/agtag","/projects/industrial-demagnetizer",
 "/projects/nasa-watts-on-the-moon-challenge-finalist",
]

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8","replace")

def strip_slashes(s):
    # defensively remove a slash immediately before the wrench and after the name
    s = re.sub(r'/(\s*\U0001f6e0)', r'\1', s)
    s = re.sub(r'(Facio Ergo Sum)\s*/', r'\1', s)
    return s.strip()

def sub_attr(html, tag_regex, value):
    return re.sub(tag_regex, lambda m: m.group(1) + '"' + value + '"', html, count=1)

n = 0
for path in PAGES:
    url = BASE + ("" if path == "/" else path)
    live = fetch(url)
    m = re.search(r'<title>(.*?)</title>', live, re.S | re.I)
    title = strip_slashes(m.group(1).strip()) if m else BRAND

    local_path = os.path.join(OUT, "index.html") if path == "/" else \
        os.path.join(OUT, path.strip("/").replace("/", os.sep), "index.html")
    with open(local_path, encoding="utf-8") as f:
        html = f.read()

    html = re.sub(r'<title>.*?</title>', '<title>' + title.replace('\\', r'\\') + '</title>',
                  html, count=1, flags=re.S | re.I)
    # visible header brand
    html = re.sub(r'(id="site-title"[^>]*>)[^<]*(</a>)',
                  lambda m: m.group(1) + BRAND + m.group(2), html)
    # share/meta tags
    html = sub_attr(html, r'(<meta property="og:title" content=)"[^"]*"', title)
    html = sub_attr(html, r'(<meta name="twitter:title" content=)"[^"]*"', title)
    html = sub_attr(html, r'(<meta property="og:site_name" content=)"[^"]*"', BRAND)
    html = sub_attr(html, r'(<meta itemprop="name" content=)"[^"]*"', BRAND)

    with open(local_path, "w", encoding="utf-8") as f:
        f.write(html)
    n += 1
    print("FIXED", path, "->", title)
print(f"\nUpdated {n} pages")

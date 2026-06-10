import urllib.request, re, os, hashlib
from urllib.parse import urljoin, urlparse, unquote

BASE = "https://facioergosum.com"
OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT, "assets")
os.makedirs(ASSETS, exist_ok=True)

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

UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}

# CSS injected into every page: undo Squarespace's JS-dependent lazy-load hiding
FIX_CSS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
 '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap" rel="stylesheet">'
 '<style id="font-override">'
 "body, body *:not(i):not([class*='icon']):not([class*='Icon']):not([class*='fa-'])"
 "{font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important}"
 '</style>'
 "<style id='selfhost-fix'>"
 "img{opacity:1 !important;visibility:visible !important;filter:none !important}"
 ".sqs-image,.image-block-wrapper,.intrinsic,.summary-thumbnail-container,"
 ".sqs-image-content,[data-load]{opacity:1 !important;visibility:visible !important}"
 "</style>")

def fetch(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8","replace")

RASTER = (".jpg",".jpeg",".png",".webp")
def canon(url):
    """Collapse every srcset width-variant of a Squarespace image to one 1500px copy."""
    pu = urlparse(url)
    if pu.netloc == "images.squarespace-cdn.com" and pu.path.lower().endswith(RASTER):
        return url.split("?")[0] + "?format=1500w"
    return url

asset_map = {}
def asset_local(url):
    cu = canon(url)
    if cu in asset_map:
        return asset_map[cu]
    p = urlparse(cu)
    base = unquote(os.path.basename(p.path)) or "index"
    h = hashlib.md5((p.path + "?" + p.query).encode()).hexdigest()[:8]
    root, ext = os.path.splitext(base)
    if not ext: ext = ".bin"
    fname = re.sub(r"[^A-Za-z0-9._-]", "_", root)[:60] + "_" + h + ext
    dest = os.path.join(ASSETS, fname)
    local = "/assets/" + fname
    asset_map[cu] = local
    if not os.path.exists(dest):
        try:
            with open(dest, "wb") as f:
                f.write(fetch(cu, binary=True))
        except Exception as e:
            print("  ASSET FAIL", cu, e)
            asset_map[cu] = url
            return url
    return local

ASSET_HOSTS = ("images.squarespace-cdn.com","static1.squarespace.com","static.squarespace.com")
def is_asset_url(u):
    pu = urlparse(u)
    return pu.netloc in ASSET_HOSTS or pu.path.lower().endswith(
        (".css",".js",".png",".jpg",".jpeg",".gif",".webp",".svg",".ico",".woff",".woff2",".ttf",".mp4",".avif",".jfif"))

url_re   = re.compile(r'(?:src|href|data-src|data-image|content)\s*=\s*["\']([^"\']+)["\']', re.I)
srcset_re= re.compile(r'srcset\s*=\s*["\']([^"\']+)["\']', re.I)
css_url_re=re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', re.I)
img_tag_re=re.compile(r'<img\b[^>]*>', re.I)

def fix_img_tag(tag):
    """Ensure src points at the (now local) image and drop responsive/lazy attrs."""
    m = re.search(r'data-src\s*=\s*"([^"]+)"', tag, re.I)
    if m:
        local = m.group(1)
        if re.search(r'\bsrc\s*=\s*"[^"]*"', tag, re.I):
            tag = re.sub(r'\bsrc\s*=\s*"[^"]*"', 'src="%s"' % local, tag, count=1, flags=re.I)
        else:
            tag = re.sub(r'<img\b', '<img src="%s"' % local, tag, count=1, flags=re.I)
    tag = re.sub(r'\ssrcset\s*=\s*"[^"]*"', '', tag, flags=re.I)
    tag = re.sub(r'\ssizes\s*=\s*"[^"]*"', '', tag, flags=re.I)
    tag = re.sub(r'\sdata-load\s*=\s*"[^"]*"', ' data-load="true"', tag, flags=re.I)
    return tag

def process_html(html, page_url):
    found = set()
    for m in url_re.finditer(html): found.add(m.group(1))
    for m in srcset_re.finditer(html):
        for part in m.group(1).split(","):
            u = part.strip().split(" ")[0]
            if u: found.add(u)
    for m in css_url_re.finditer(html): found.add(m.group(1))

    replacements = {}
    for raw in found:
        if raw[:5] in ("data:","#mail") or raw.startswith(("#","mailto:","tel:","javascript:")):
            continue
        absu = urljoin(page_url, raw)
        pu = urlparse(absu)
        if pu.netloc in ("facioergosum.com","www.facioergosum.com") and not is_asset_url(absu):
            path = pu.path
            replacements[raw] = "/" if path in ("","/") else path.rstrip("/") + "/"
        elif is_asset_url(absu) and (pu.netloc in ASSET_HOSTS or pu.netloc in ("facioergosum.com","www.facioergosum.com","")):
            replacements[raw] = asset_local(absu)

    for raw in sorted(replacements, key=len, reverse=True):
        html = html.replace(raw, replacements[raw])

    html = img_tag_re.sub(lambda m: fix_img_tag(m.group(0)), html)
    html = re.sub(r'\ssrcset\s*=\s*"[^"]*"', '', html, flags=re.I)  # kill <source> srcset too
    if "</head>" in html:
        html = html.replace("</head>", FIX_CSS + "</head>", 1)
    return html

count = 0
for path in PAGES:
    url = BASE + ("" if path == "/" else path)
    try:
        html = process_html(fetch(url), url + "/")
    except Exception as e:
        print("PAGE FAIL", url, e); continue
    if path == "/":
        dest = os.path.join(OUT, "index.html")
    else:
        d = os.path.join(OUT, path.strip("/").replace("/", os.sep))
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, "index.html")
    with open(dest, "w", encoding="utf-8") as f: f.write(html)
    count += 1
    print("PAGE", path)
print(f"\nDONE: {count} pages, {len(asset_map)} unique assets")

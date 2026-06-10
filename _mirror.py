import urllib.request, urllib.error, re, os, hashlib
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

def fetch(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8","replace")

asset_map = {}   # original absolute url -> local /assets/<name>
def asset_local(url):
    """download an asset, return root-relative local path, cached."""
    if url in asset_map:
        return asset_map[url]
    p = urlparse(url)
    base = os.path.basename(p.path) or "index"
    base = unquote(base)
    # build a stable, unique filename
    h = hashlib.md5((p.path + "?" + p.query).encode()).hexdigest()[:8]
    root, ext = os.path.splitext(base)
    if not ext:
        ext = ".bin"
    fname = re.sub(r"[^A-Za-z0-9._-]", "_", root)[:60] + "_" + h + ext
    dest = os.path.join(ASSETS, fname)
    local = "/assets/" + fname
    asset_map[url] = local
    if not os.path.exists(dest):
        try:
            data = fetch(url, binary=True)
            with open(dest, "wb") as f:
                f.write(data)
        except Exception as e:
            print("  ASSET FAIL", url, e)
            asset_map[url] = url  # leave original on failure
            return url
    return local

ASSET_HOSTS = ("images.squarespace-cdn.com","static1.squarespace.com","static.squarespace.com")

def is_asset_url(u):
    pu = urlparse(u)
    return pu.netloc in ASSET_HOSTS or pu.path.lower().endswith(
        (".css",".js",".png",".jpg",".jpeg",".gif",".webp",".svg",".ico",".woff",".woff2",".ttf",".mp4",".avif"))

url_re = re.compile(r'(?:src|href|data-src|data-image|content)\s*=\s*["\']([^"\']+)["\']', re.I)
srcset_re = re.compile(r'srcset\s*=\s*["\']([^"\']+)["\']', re.I)
css_url_re = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', re.I)

def process_html(html, page_url):
    found = set()
    # collect single-url attributes
    for m in url_re.finditer(html):
        found.add(m.group(1))
    # srcset (comma separated "url w")
    srcsets = []
    for m in srcset_re.finditer(html):
        srcsets.append(m.group(1))
        for part in m.group(1).split(","):
            u = part.strip().split(" ")[0]
            if u: found.add(u)
    # css url() inside <style> blocks
    for m in css_url_re.finditer(html):
        found.add(m.group(1))

    replacements = {}
    for raw in found:
        if raw.startswith("data:") or raw.startswith("#") or raw.startswith("mailto:") or raw.startswith("tel:"):
            continue
        absu = urljoin(page_url, raw)
        pu = urlparse(absu)
        if pu.netloc in ("facioergosum.com","www.facioergosum.com") and not is_asset_url(absu):
            # internal page link -> root-relative trailing slash
            path = pu.path
            if path in ("","/"):
                new = "/"
            else:
                new = path.rstrip("/") + "/"
            replacements[raw] = new
        elif is_asset_url(absu) and (pu.netloc in ASSET_HOSTS or pu.netloc in ("facioergosum.com","www.facioergosum.com","")):
            local = asset_local(absu)
            replacements[raw] = local

    # apply replacements (longest first to avoid partial overlap)
    for raw in sorted(replacements, key=len, reverse=True):
        html = html.replace(raw, replacements[raw])
    # rewrite srcset entries
    for ss in srcsets:
        new_ss = ss
        for part in ss.split(","):
            u = part.strip().split(" ")[0]
            absu = urljoin(page_url, u)
            if is_asset_url(absu):
                local = asset_local(absu)
                new_ss = new_ss.replace(u, local)
        html = html.replace(ss, new_ss)
    return html

count_pages = 0
for path in PAGES:
    url = BASE + ("" if path == "/" else path)
    try:
        html = fetch(url)
    except Exception as e:
        print("PAGE FAIL", url, e)
        continue
    html = process_html(html, url + "/")
    if path == "/":
        dest = os.path.join(OUT, "index.html")
    else:
        d = os.path.join(OUT, path.strip("/").replace("/", os.sep))
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, "index.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    count_pages += 1
    print("PAGE", path, "->", os.path.relpath(dest, OUT))

print(f"\nDONE: {count_pages} pages, {len(asset_map)} assets downloaded")

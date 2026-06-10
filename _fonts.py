import os, glob

OUT = os.path.dirname(os.path.abspath(__file__))

BLOCK = (
 '<link rel="preconnect" href="https://fonts.googleapis.com">'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
 '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap" rel="stylesheet">'
 '<style id="font-override">'
 "body, body *:not(i):not([class*='icon']):not([class*='Icon']):not([class*='fa-'])"
 "{font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important}"
 '</style>'
)

n = 0
for path in glob.glob(os.path.join(OUT, "**", "index.html"), recursive=True) + [os.path.join(OUT, "index.html")]:
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as f:
        html = f.read()
    if 'id="font-override"' in html:
        continue  # already done
    if "</head>" in html:
        html = html.replace("</head>", BLOCK + "</head>", 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        n += 1
        print("FONT", os.path.relpath(path, OUT))
print(f"\nUpdated {n} pages")

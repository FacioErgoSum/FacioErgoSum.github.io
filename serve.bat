@echo off
echo Opening browser to localhost:8000...
start "" "http://localhost:8000/index.html"

echo Starting Python HTTP server on port 8000...
:: Navigate to a specific folder if you want, e.g., cd C:\Users\Name\Desktop
python -m http.server 8000
pause
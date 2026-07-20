# linkshort

A tiny URL shortener I made for myself and a few friends. Flask + SQLite, one process, runs on a small VM. Not a business, no revenue, no on-call, no Kubernetes.

## Run

```
pip install -r requirements.txt
python app.py
```

## Endpoints

- `POST /shorten` with `{"url": "..."}` returns a short code
- `GET /<code>` redirects to the original URL

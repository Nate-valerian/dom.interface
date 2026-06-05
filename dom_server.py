from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error as urlerror, request
from urllib.parse import quote, unquote, urlsplit, urlunsplit
import json
import os
import socket
import time


HOST = os.environ.get("DOM_HOST", "0.0.0.0")
PORT = int(os.environ.get("DOM_PORT", "8000"))
RESOLUME_IP = os.environ.get("RESOLUME_IP", "127.0.0.1")
RESOLUME_API = os.environ.get("RESOLUME_API", f"http://{RESOLUME_IP}:8080/api/v1")
ROOT = Path(__file__).resolve().parent
MANUAL_COMPOSITIONS = ROOT / "compositions.json"
MANUAL_FOLDERS = ROOT / "composition_folders.json"
WORKING_RESOLUME_API = ""


def lan_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return ""


def resolume_api_bases():
    candidates = [
        WORKING_RESOLUME_API,
        RESOLUME_API,
        "http://127.0.0.1:8080/api/v1",
    ]

    current_lan_ip = lan_ip()
    if current_lan_ip:
        candidates.append(f"http://{current_lan_ip}:8080/api/v1")

    candidates.append("http://localhost:8080/api/v1")

    seen = set()
    bases = []
    for candidate in candidates:
        normalized = candidate.rstrip("/")
        if normalized and normalized not in seen:
            seen.add(normalized)
            bases.append(normalized)
    return bases


def remember_resolume_api(base_url):
    global WORKING_RESOLUME_API
    WORKING_RESOLUME_API = base_url.rstrip("/")


def path_exists(path):
    try:
        return path.exists()
    except OSError:
        return False


def documents_roots():
    home = Path.home()
    candidates = [
        home / "Documents",
        home / "OneDrive" / "Documents",
        Path(os.environ.get("USERPROFILE", "")) / "Documents",
    ]

    return [path for path in candidates if path_exists(path)]


def local_composition_dirs():
    home = Path.home()
    user_profile = Path(os.environ.get("USERPROFILE", ""))
    candidates = []

    for base in [ROOT, ROOT.parent, home / "Downloads", home / "Desktop", user_profile / "Downloads", user_profile / "Desktop"]:
        if not path_exists(base):
            continue
        candidates.extend([
            base / "Compositions",
            base / "dom-pro" / "Compositions",
        ])

    users_root = Path(os.environ.get("SYSTEMDRIVE", "C:")) / "Users"
    if path_exists(users_root):
        for profile in users_root.glob("*"):
            candidates.append(profile / "Downloads" / "dom-pro" / "Compositions")
            candidates.append(profile / "Desktop" / "dom-pro" / "Compositions")

    return [path for path in candidates if path_exists(path)]


def composition_dirs():
    names = [
        "Resolume Arena",
        "Resolume Avenue",
        "Resolume Arena 7",
        "Resolume Avenue 7",
        "Resolume Arena 6",
        "Resolume Avenue 6",
        "Resolume",
    ]

    found = []
    for root in documents_roots():
        for name in names:
            path = root / name / "Compositions"
            if path_exists(path):
                found.append(path)

        for path in root.glob("Resolume*/Compositions"):
            if path_exists(path):
                found.append(path)

    program_roots = [
        Path(os.environ.get("PROGRAMFILES", "")),
        Path(os.environ.get("PROGRAMFILES(X86)", "")),
        Path(os.environ.get("PROGRAMDATA", "")),
    ]
    for root in program_roots:
        if not path_exists(root):
            continue
        for app_dir in root.glob("Resolume*"):
            for folder_name in ["Compositions", "Samples", "Examples", "Example Compositions"]:
                path = app_dir / folder_name
                if path_exists(path):
                    found.append(path)

    found.extend(local_composition_dirs())

    for path in manual_composition_dirs():
        if path_exists(path):
            found.append(path)

    unique = []
    seen = set()
    for path in found:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)

    return unique


def collection(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ["compositions", "files", "recent", "items"]:
            if isinstance(value.get(key), list):
                return value[key]
        for key in ["folders", "dirs", "directories", "paths"]:
            if isinstance(value.get(key), list):
                return value[key]
        return list(value.values())
    return []


def manual_composition_dirs():
    folders = []

    raw_env = os.environ.get("RESOLUME_COMPOSITION_DIRS", "")
    for value in raw_env.split(";"):
        value = value.strip()
        if value:
            folders.append(Path(value))

    if MANUAL_FOLDERS.exists():
        try:
            data = json.loads(MANUAL_FOLDERS.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            data = []

        for item in collection(data):
            if isinstance(item, str):
                path = os.path.expandvars(os.path.expanduser(item.strip()))
            elif isinstance(item, dict):
                path = os.path.expandvars(os.path.expanduser(str(item.get("path") or item.get("folder") or "").strip()))
            else:
                path = ""

            if path:
                folders.append(Path(path))

    return folders


def manual_compositions():
    if not MANUAL_COMPOSITIONS.exists():
        return []

    try:
        data = json.loads(MANUAL_COMPOSITIONS.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []

    compositions = []
    for index, item in enumerate(collection(data)):
        if isinstance(item, str):
            path = item.strip()
            name = Path(path).stem or f"Composition {index + 1}"
        elif isinstance(item, dict):
            path = str(item.get("path") or item.get("file") or item.get("url") or "").strip()
            name = str(item.get("name") or Path(path).stem or f"Composition {index + 1}").strip()
        else:
            continue

        if path:
            compositions.append({
                "name": name,
                "path": path,
                "folder": str(Path(path).parent),
                "modified": 0,
                "modifiedText": "manual",
                "size": 0,
                "manual": True,
            })

    return compositions


def scan_compositions():
    compositions = manual_compositions()
    seen_paths = {item["path"] for item in compositions}
    seen_stems = {Path(item["path"]).stem.lower() for item in compositions}

    for directory in composition_dirs():
        for file_path in directory.rglob("*.avc*"):
            if file_path.is_dir():
                continue
            path_text = str(file_path)
            if path_text in seen_paths:
                continue
            stem = file_path.stem.lower()
            if stem in seen_stems:
                continue
            try:
                stat = file_path.stat()
            except OSError:
                continue

            compositions.append({
                "name": file_path.stem,
                "path": path_text,
                "folder": str(file_path.parent),
                "modified": int(stat.st_mtime),
                "modifiedText": time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)),
                "size": stat.st_size,
            })
            seen_paths.add(path_text)
            seen_stems.add(stem)

    compositions.sort(key=lambda item: item["modified"], reverse=True)
    return compositions


def composition_file_url(path):
    text = str(path).strip()
    if text.lower().startswith("file:"):
        parts = urlsplit(text.replace("\\", "/"))
        encoded_path = quote(unquote(parts.path), safe="/:")
        return urlunsplit((parts.scheme, parts.netloc, encoded_path, parts.query, parts.fragment))

    return Path(text).resolve().as_uri()


def post_resolume_open(path):
    file_url = composition_file_url(path)
    body = file_url.encode("utf-8")
    errors = []

    for base_url in resolume_api_bases():
        url = f"{base_url}/composition/open"
        req = request.Request(url, data=body, headers={"Content-Type": "text/plain"}, method="POST")

        try:
            with request.urlopen(req, timeout=8) as response:
                if 200 <= response.status < 300:
                    remember_resolume_api(base_url)
                    return True, response.read().decode("utf-8", errors="replace"), response.status
                return False, f"Resolume returned {response.status}", response.status
        except urlerror.HTTPError as http_err:
            try:
                resp_body = http_err.read().decode("utf-8", errors="replace")
            except Exception:
                resp_body = ""
            detail = resp_body or http_err.reason
            print(f"[open] POST {url} body={body!r} -> HTTP {http_err.code}: {detail}")
            return False, f"HTTP {http_err.code}: {detail}", http_err.code
        except Exception as error:
            detail = str(error)
            errors.append(f"{url}: {detail}")

    for detail in errors:
        print(f"[open] {detail}")
    return False, "Could not reach Resolume API. Tried " + "; ".join(errors), 502


def resolume_proxy_targets(path):
    prefix = "/dom/resolume"
    if not path.startswith(prefix):
        return []

    suffix = path[len(prefix):] or "/"
    return [(base, f"{base}{suffix}") for base in resolume_api_bases()]


class DomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def json_response(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        request_path = self.path.split("?", 1)[0]

        if request_path.startswith("/dom/resolume/"):
            self.proxy_resolume()
            return

        if request_path == "/dom/compositions":
            self.json_response(200, {
                "compositions": scan_compositions(),
                "folders": [str(path) for path in composition_dirs()],
            })
            return

        super().do_GET()

    def do_POST(self):
        request_path = self.path.split("?", 1)[0]

        if request_path.startswith("/dom/resolume/"):
            self.proxy_resolume()
            return

        if request_path != "/dom/compositions/open":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")

        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"path": raw}

        path = str(payload.get("path", "")).strip()
        known_paths = {item["path"] for item in scan_compositions()}

        if not path or path not in known_paths:
            self.json_response(400, {"ok": False, "error": "Unknown composition path"})
            return

        ok, detail, status = post_resolume_open(path)
        if ok:
            self.json_response(200, {"ok": True})
        else:
            self.json_response(status, {"ok": False, "error": detail})

    def proxy_resolume(self):
        targets = resolume_proxy_targets(self.path)
        if not targets:
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        headers = {}
        content_type = self.headers.get("Content-Type")
        if content_type:
            headers["Content-Type"] = content_type

        errors = []

        for base_url, url in targets:
            req = request.Request(url, data=body, headers=headers, method=self.command)

            try:
                with request.urlopen(req, timeout=8) as response:
                    payload = response.read()
                    remember_resolume_api(base_url)
                    self.send_response(response.status)
                    self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
            except urlerror.HTTPError as http_err:
                payload = http_err.read()
                self.send_response(http_err.code)
                self.send_header("Content-Type", http_err.headers.get("Content-Type", "text/plain"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            except Exception as error:
                detail = str(error)
                errors.append(f"{url}: {detail}")

        for detail in errors:
            print(f"[proxy] {self.command} {detail}")
        self.json_response(502, {"ok": False, "error": "Could not reach Resolume API. Tried " + "; ".join(errors)})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), DomHandler)
    current_lan_ip = lan_ip()
    print(f"DOM control server local: http://127.0.0.1:{PORT}/dom_pro2.html")
    print(f"DOM control server iPad:  http://{current_lan_ip}:{PORT}/dom_pro2.html")
    print(f"Resolume API candidates:  {', '.join(resolume_api_bases())}")
    server.serve_forever()

#!/usr/bin/env python3
"""决断助手(Jev Playground 本地版)- 本地服务器。

作用:
  1. 在 http://localhost:8735 提供助手页面(浏览器不允许 file:// 页面
     直接调用 api.typesafe.ai,CORS 会拦截,所以经本地服务器代理);
  2. 代理 API:
     POST /api/systemone -> https://api.typesafe.ai/v1/systemone
     GET  /api/models    -> https://api.typesafe.ai/v1/models
  API key 只存在本机,不会发进浏览器页面。

key 读取顺序:环境变量 TYPESAFE_API_KEY -> ~/.pi/agent/typesafe.json
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def say(msg: str):
    """pythonw(无窗口模式)下没有 stdout,print 会直接报错,这里做保护。"""
    if sys.stdout:
        print(msg)

PORT = 8735
HERE = Path(__file__).resolve().parent
BASE = "https://api.typesafe.ai"


def api_key() -> str:
    env = os.environ.get("TYPESAFE_API_KEY")
    if env:
        return env
    return json.loads((Path.home() / ".pi" / "agent" / "typesafe.json")
                      .read_text(encoding="utf-8"))["apiKey"]


KEY = api_key()

# 直连 opener:无视环境变量里的 HTTP(S)_PROXY。
# 实测直连 api.typesafe.ai 稳定可用,而本机代理工具(如 7892)未运行时会把
# TLS 连接掐断(SSL: UNEXPECTED_EOF_WHILE_READING),导致所有判断请求失败。
DIRECT_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/assistant.html"
        elif self.path == "/api/models":
            self._proxy("GET", BASE + "/v1/models", None)
            return
        elif self.path == "/api/info":
            data = json.dumps({
                "upstream": BASE,
                "keyMasked": KEY[:10] + "…" + KEY[-6:],
                "keySource": "env TYPESAFE_API_KEY" if os.environ.get("TYPESAFE_API_KEY")
                             else "~/.pi/agent/typesafe.json",
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/systemone":
            length = int(self.headers.get("Content-Length", 0))
            self._proxy("POST", BASE + "/v1/systemone", self.rfile.read(length))
            return
        self.send_error(404)

    def _proxy(self, method: str, url: str, body: bytes | None):
        headers = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
        data, status = b"{}", 502
        for attempt in range(3):
            req = urllib.request.Request(url, data=body, method=method, headers=headers)
            try:
                with DIRECT_OPENER.open(req, timeout=45) as resp:
                    data, status = resp.read(), resp.status
                break
            except urllib.error.HTTPError as e:
                # HTTP 错误码(4xx/5xx)原样透传,页面端会按状态码决定是否重试
                data, status = e.read(), e.code
                break
            except Exception as e:
                # 网络层抖动(SSL EOF、超时、连接重置):退避后重试
                if attempt < 2:
                    time.sleep(0.6 * (attempt + 1))
                    continue
                data = json.dumps({"detail": f"本地代理无法连接 typesafe.ai(已重试 3 次): {e}"}).encode("utf-8")
                status = 502
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # 安静模式
        pass


def main():
    url = f"http://localhost:{PORT}"
    server = None
    for attempt in range(3):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
            break
        except OSError:
            if attempt == 2:
                say(f"端口 {PORT} 被占用。如果助手已在运行,直接打开 {url} 即可。")
                webbrowser.open(url)
                return
            time.sleep(1)
    say(f"决断助手已启动:{url}  (可用 停止助手.bat 关闭)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        say("\n已退出。")


if __name__ == "__main__":
    main()

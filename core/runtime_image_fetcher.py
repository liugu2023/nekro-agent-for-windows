import os
from urllib.request import Request, urlopen


class RuntimeImageFetcher:
    def __init__(self, urls, log=None, progress=None):
        self.urls = urls
        self.log = log or (lambda message, level="info": None)
        self.progress = progress or (lambda message: None)

    def download(self, dest_path):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        for url in self.urls:
            try:
                self.log(f"[镜像下载] 尝试下载: {url}", "info")
                self.progress("正在下载基础镜像...")
                request = Request(url, headers={"User-Agent": "NekroAgent/1.0"})
                with urlopen(request, timeout=60) as resp, open(dest_path, "wb") as fh:
                    total = resp.headers.get("Content-Length")
                    total = int(total) if total else None
                    downloaded = 0
                    while True:
                        chunk = resp.read(1024 * 1024)
                        if not chunk:
                            break
                        fh.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = int(downloaded * 100 / total)
                            self.progress(f"正在下载基础镜像... {pct}%")
                self.progress("基础镜像下载完成")
                return True
            except Exception as exc:
                self.log(f"[镜像下载] 下载失败: {exc}", "warning")

        self.progress("基础镜像下载失败")
        return False

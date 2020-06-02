import requests
import urllib
from filehandling import join_path
from omnitools import p
import mfd
import os
import shutil


class IA_Broker(object):
    def __init__(self, access: str = None, secret: str = None, identifier: str = None) -> None:
        self.access = access
        self.secret = secret
        self.identifier = identifier

    def upload(self, root: str, path: str, filename: str):
        remote_filename = filename.replace(".", "_,_")
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "multipart/form-data; charset=UTF-8",
            "Origin": "https://archive.org",
            "Referer": f"https://archive.org/upload/?identifier={self.identifier}",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "x-amz-acl": "bucket-owner-full-control",
            "x-amz-auto-make-bucket": "1",
            "x-archive-interactive-priority": "1",
            "x-archive-size-hint": "2",
            "X-File-Name": f"uri({remote_filename})",
            "X-Requested-With": "XMLHttpRequest"
        }
        url = f"https://s3.us.archive.org/"
        url_path = self.identifier+"/"+path.replace("\\", "/")+"/"+remote_filename
        url_path = url_path.replace("//", "/")
        uri = url+urllib.parse.quote(url_path, safe="")
        file = join_path(root, path, filename)
        p(f"[Uploading] {file} => {uri}", end="")
        r = requests.put(uri, data=open(file, "rb"), headers=headers)
        p(f"\r[Uploaded] {file} => https://archive.org/download/{url_path}")
        return r

    def download(self, save_dir: str, url: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> dict:
        try:
            os.makedirs(save_dir)
        except:
            pass
        p(f"[Downloading] {url} => {save_dir}", end="")
        _mfd = mfd.MFD(save_dir, piece_size=piece_size)
        _f = _mfd.download(url, connections=connections, cal_hash=cal_hash, quiet=True)
        _mfd.stop()
        _ffp = _f["file_path"]
        _f["file_path"] = _f["file_path"].replace("_,_", ".").replace("_%2C_", ".")
        if _ffp != _f["file_path"]:
            shutil.move(_ffp, _f["file_path"])
        p(f"\r[Downloaded] {url} => "+_f["file_path"])
        return _f

    def rename(self, session: requests.Session, identifier: str, old_item: str, new_item: str):
        p(f"[Renaming] <{identifier}> {old_item} => {new_item}", end="")
        r = session.post("https://archive.org/edit.php", data={
            "cmd": "rename",
            "oldname": "root/foo3.txt4",
            "newname": "root/foo3.txt"
        }, cookies={
            "http-editor-v3": identifier
        })
        p(f"[Renamed] <{identifier}> {old_item} => {new_item}", end="")
        return r


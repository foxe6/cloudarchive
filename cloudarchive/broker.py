import text2png
from filehandling import join_path
from omnitools import p
import mfd
import requests
import urllib
import os
import hashlib
import random


__ALL__ = ["IA_Broker"]


class IA_Broker(object):
    def __init__(self, access: str = None, secret: str = None, identifier: str = None) -> None:
        self.access = access
        self.secret = secret
        self.identifier = identifier
        self.types = {
            b"\x37\x7a\xbc\xaf": b"7z",
            b"\x52\x61\x72\x21": b"rar",
            b"\x50\x4b\x03\x04": b"zip",
            b"7z": b"\x37\x7a\xbc\xaf",
            b"rar": b"\x52\x61\x72\x21",
            b"zip": b"\x50\x4b\x03\x04",
            "types": [b"7z", b"rar", b"zip"]
        }

    def check_file_type(self, file_path: str) -> bool:
        file_type = os.path.basename(file_path).split(".")[-1]
        if file_type in self.types["types"]:
            return True
        return False

    def cloak_file_type(self, file_path: str) -> None:
        if not self.check_file_type(file_path):
            return
        with open(file_path, "r+b") as f:
            f.seek(0)
            file_header = f.read(4)
            if file_header not in self.types:
                return
            type = self.types[file_header]
            key = bytes([random.randint(0, 255)])
            session = hashlib.sha3_512(type+key).digest()[:3]+key
            f.seek(0)
            f.write(session)
            f.close()

    def uncloak_file_type(self, file_path: str) -> None:
        if not self.check_file_type(file_path):
            return
        with open(file_path, "r+b") as f:
            f.seek(0)
            session = f.read(4)
            key = bytes([session[-1]])
            for type in self.types["types"]:
                if hashlib.sha3_512(type+key).digest()[:3] == session[:-1]:
                    f.seek(0)
                    f.write(self.types[type])
                    f.close()
                    return

    def upload(self, root: str, path: str, filename: str):
        file = join_path(root, path, filename)
        self.cloak_file_type(file)
        remote_filename = filename
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
        self.uncloak_file_type(_f["file_path"])
        p(f"\r[Downloaded] {url} => "+_f["file_path"])
        return _f

    def rename(self, identifier: str, old_item: str, new_item: str):
        p(f"[Renaming] <{identifier}> {old_item} => {new_item}")
        p(f"[Copying] <{identifier}> {old_item} => {new_item}", end="")
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "x-amz-copy-source": "/"+identifier+"/"+old_item,
            "x-amz-metadata-directive": "COPY",
            "x-archive-keep-old-version": "0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"
        }
        url = "https://s3.us.archive.org"
        url += "/"+identifier+"/"+new_item
        r = requests.put(url, headers=headers)
        p(f"\r[Copied] <{identifier}> {old_item} => {new_item}")
        self.delete(identifier, old_item)
        p(f"\r[Renamed] <{identifier}> {old_item} => {new_item}")
        return r

    def delete(self, identifier: str, item: str):
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "x-archive-cascade-delete": "1"
        }
        p(f"[Deleting] {identifier}/{item}", end="")
        r = requests.delete(f"https://s3.us.archive.org/{identifier}/{item}", headers=headers)
        p(f"\r[Deleted] {identifier}/{item}")
        return r

    def new_identifier(self, identifier: str):
        p(f"[Identifier] Creating {identifier}", end="")
        thumbnail_path = text2png.TextToPng("C:\\Windows\\Fonts\\msgothic.ttc", 64).create(identifier)
        remote_filename = os.path.basename(thumbnail_path)
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "multipart/form-data; charset=UTF-8",
            "Origin": "https://archive.org",
            "Referer": f"https://archive.org/upload/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "x-amz-acl": "bucket-owner-full-control",
            "x-amz-auto-make-bucket": "1",
            "x-archive-interactive-priority": "1",
            "x-archive-meta-mediatype": "uri(data)",
            "x-archive-meta01-collection": "uri(opensource_media)",
            "x-archive-meta01-description": f"uri({identifier})",
            "x-archive-meta01-noindex": "uri(true)",
            "x-archive-meta01-private": "uri(true)",
            "x-archive-meta01-scanner": "uri(Internet%20Archive%20HTML5%20Uploader%201.6.4)",
            "x-archive-meta01-subject": f"uri({identifier})",
            "x-archive-meta01-title": f"uri({identifier})",
            "x-archive-size-hint": "2000",
            "X-File-Name": f"uri({remote_filename})",
            "X-Requested-With": "XMLHttpRequest"
        }
        url = f"https://s3.us.archive.org/"
        url_path = identifier+"/"+remote_filename
        url_path = url_path.replace("//", "/")
        uri = url+urllib.parse.quote(url_path, safe="")
        r = requests.put(uri, data=open(thumbnail_path, "rb"), headers=headers)
        p(f"\r[Identifier] Created {identifier} => https://archive.org/download/{identifier}")
        return r

    def metadata(self, identifier: str, data: dict):
        url = f"https://archive.org/metadata/{identifier}"
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}"
        }
        r = requests.post(url, headers=headers, data=data)
        return r


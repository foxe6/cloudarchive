import text2png
from filehandling import join_path, abs_dir, file_size
from omnitools import p, jd
import mfd
import requests
import urllib.parse
import os
import hashlib
import random
import platform
import sys
import shutil
from cloudarchive import __version__


__ALL__ = ["IA_Broker"]


USER_AGENT = lambda access: os.path.basename(os.path.dirname(abs_dir(__file__)))+\
             f"/{__version__} ("+platform.uname()[0]+"; "+platform.uname()[-1]+f"; {access}; Python "+\
             "{0}.{1}.{2}".format(*sys.version_info)+")"

class IA_Broker(object):
    def __init__(self, access: str = None, secret: str = None, identifier: str = None) -> None:
        self.__s = requests.Session()
        self.__s.headers.update({"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"})
        self.__s.get("https://archive.org/")
        self.__s.get("https://archive.org/create")
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

    def cloak_file_type(self, file_path: str) -> bool:
        if not self.check_file_type(file_path):
            return False
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
        return True

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

    def blur_file_ext(self, filename: str) -> str:
        return filename+".cloudarchive"

    def unblur_file_ext(self, filename: str) -> str:
        org_filename = filename.replace(".cloudarchive", "")
        shutil.move(filename, org_filename)
        return org_filename

    def upload(self, root: str, path: str, filename: str):
        file = join_path(root, path, filename)
        cloaked = self.cloak_file_type(file)
        remote_filename = self.blur_file_ext(filename)
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ru;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "multipart/form-data; charset=UTF-8",
            # "Referer": f"https://archive.org/upload/?identifier={self.identifier}",
            # "User-Agent": USER_AGENT(self.access),
            "x-amz-acl": "bucket-owner-full-control",
            "x-amz-auto-make-bucket": "1",
            # "x-archive-interactive-priority": "1",
            "x-archive-queue-derive": "0",
            "x-archive-size-hint": str(file_size(file)),
            "X-File-Size": str(file_size(file)),
            "Content-Length": str(file_size(file)),
            "X-File-Name": f"uri({remote_filename})",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        url = f"https://s3.us.archive.org/"
        url_path = self.identifier+"/"+path.replace("\\", "/")+"/"+remote_filename
        url_path = url_path.replace("//", "/")
        uri = url+urllib.parse.quote(url_path, safe="")
        p(f"[Uploading] {file} => {uri}", end="")
        r = self.__s.put(uri, data=open(file, "rb"), headers=headers)
        if cloaked:
            self.uncloak_file_type(file)
        if r.status_code != 200:
            raise Exception(f"failed to upload {file} => {uri}", r.status_code, r.content)
        p(f"\r[Uploaded] {file} => https://archive.org/download/{url_path}")

    def download(self, save_dir: str, identifier: str, path: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> dict:
        try:
            os.makedirs(save_dir)
        except:
            pass
        url = f"https://archive.org/download/{identifier}/{path}"
        p(f"[Downloading] <{identifier}> {path} => {save_dir}", end="")
        _mfd = mfd.MFD(save_dir, piece_size=piece_size)
        _f = _mfd.download(url, connections=connections, cal_hash=cal_hash, quiet=True)
        _mfd.stop()
        self.uncloak_file_type(_f["file_path"])
        _f["file_path"] = self.unblur_file_ext(_f["file_path"])
        p(f"\r[Downloaded] {identifier} "+_f["file_path"]+" <= {path}")
        return _f

    def rename(self, identifier: str, old_item: str, new_item: str):
        p(f"[Renaming] {identifier} {old_item} => {new_item}", end="")
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "x-amz-copy-source": "/"+identifier+"/"+old_item,
            "x-amz-metadata-directive": "COPY",
            "x-archive-keep-old-version": "0",
            "User-Agent": USER_AGENT(self.access)
        }
        url = "https://s3.us.archive.org"
        url += "/"+identifier+"/"+new_item
        r = self.__s.put(url, headers=headers)
        if r.status_code != 200:
            raise Exception(f"failed to copy {identifier} {old_item} => {new_item}", r.status_code, r.content)
        p(f"\r[Renamed] {identifier} {old_item} => {new_item}")
        r = self.delete(identifier, old_item)
        if r.status_code != 200:
            raise Exception(f"failed to delete old item {identifier} {old_item}", r.status_code, r.content)

    def delete(self, identifier: str, path: str):
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "User-Agent": USER_AGENT(self.access),
            "x-archive-cascade-delete": "1"
        }
        p(f"[Deleting] {identifier} {path}", end="")
        r = self.__s.delete(f"https://s3.us.archive.org/{identifier}/{path}", headers=headers)
        if r.status_code != 200:
            raise Exception(f"failed to delete {identifier} {path}", r.status_code, r.content)
        p(f"\r[Deleted] {identifier} {path}")

    def new_identifier(self, identifier: str, title: str = None, description: str = None):
        p(f"[Identifier] Creating new {identifier}", end="")
        thumbnail_path = text2png.TextToPng(64).create(title or identifier)
        remote_filename = os.path.basename(thumbnail_path)
        if description is None:
            description = identifier
        if title is None:
            title = identifier
        org_title = title
        title = urllib.parse.quote(title)
        description = urllib.parse.quote(description)
        headers = {
            "authorization": f"LOW {self.access}:{self.secret}",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ru;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "multipart/form-data; charset=UTF-8",
            # "Referer": f"https://archive.org/upload/",
            # "User-Agent": USER_AGENT(self.access),
            "x-amz-acl": "bucket-owner-full-control",
            "x-amz-auto-make-bucket": "1",
            # "x-archive-interactive-priority": "1",
            "x-archive-queue-derive": "0",
            "x-archive-meta-mediatype": "uri(data)",
            "x-archive-meta01-collection": "uri(opensource_media)",
            # "x-archive-meta01-description": f"uri({description})",
            "x-archive-meta01-description": f"uri(video%20software%20data)",
            "x-archive-meta01-noindex": "uri(true)",
            "x-archive-meta01-private": "uri(true)",
            "x-archive-meta01-scanner": "uri(Internet%20Archive%20HTML5%20Uploader%201.6.4)",
            # "x-archive-meta01-subject": f"uri({title})",
            "x-archive-meta01-subject": f"uri(video%3Bsoftware%3Bdata)",
            "x-archive-meta01-title": f"uri({title})",
            "x-archive-size-hint": str(file_size(thumbnail_path)),
            "X-File-Size": str(file_size(thumbnail_path)),
            "Content-Length": str(file_size(thumbnail_path)),
            "X-File-Name": f"uri({remote_filename})",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        url = f"https://s3.us.archive.org/"
        url_path = identifier+"/"+remote_filename
        url_path = url_path.replace("//", "/")
        uri = url+urllib.parse.quote(url_path, safe="")
        r = self.__s.put(uri, data=open(thumbnail_path, "rb"), headers=headers)
        if r.status_code != 200:
            raise Exception(f"failed to create {identifier}", r.status_code, r.content)
        p(f"\r[Identifier] Created {org_title} => https://archive.org/download/{identifier}")

    def metadata(self, identifier: str, op: str, k: str, v: str):
        url = f"https://archive.org/metadata/{identifier}"
        data = {
            "-patch": [
                {
                    "op": op,
                    "path": "/"+k
                }
            ],
            "-target": "metadata",
            "priority": -5,
            "access": self.access,
            "secret": self.secret
        }
        if op != "remove":
            data["-patch"][0]["value"] = v
        p(f"[Metadata] Pending {identifier} {op} {k}: {v}", end="")
        data["-patch"] = jd(data["-patch"])
        r = self.__s.post(url, data=data)
        if r.status_code != 200:
            raise Exception(f"failed metadata {identifier} {op} {k}: {v}", r.status_code, r.content)
        p(f"\r[Metadata] Done {identifier} {op} {k}: {v}")


import text2png
from filehandling import join_path, abs_dir, file_size
from omnitools import p, jd
import mfd
import requests
import urllib.parse
import os
import re
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
    def __init__(self, session: requests.Session = None) -> None:
        self.__session = session
        self.types = [
            ("7z", b"^\x37\x7a\xbc\xaf", 0, 4),
            ("rar", b"^\x52\x61\x72\x21", 0, 4),
            ("zip", b"^\x50\x4b\x03\x04", 0, 4),
            ("mp4", b"^(....)\x66\x74\x79\x70", 4, 4),
            ("mkv", b"^\x1a\x45\xdf\xa3", 0, 4),
            ("avi", b"^\x52\x49\x46\x46", 0, 4),
            ("wmv", b"^\x30\x26\xb2\x75\x8e\x66\xcf\x11\xa6\xd9\x00\xaa\x00\x62\xce\x6c", 0, 16),
            ("mpg", b"^\x00\x00\x01\xba", 0, 4),
            ("mpeg", b"^\x00\x00\x01\xba", 0, 4),
            ("ogm", b"^\x4f\x67\x67\x53", 0, 4),
            ("flv", b"^\x46\x4c\x56", 0, 3),
            ("m2ts", b"^(....)\x47", 4, 1),
            ("rmvb", b"^\x2e\x52\x4d\x46", 0, 4),
        ]
        self.other_types = [
            "swf",
            "mov",
            "asf",
            "sub",
            "idx",
            "rm",
            "png",
            "jpg",
            "jpeg",
            "bmp",
            "gif",
            "tif",
            "svg",
            "mka",
            "mp3",
            "flac",
            "aac",
            "m3u",
            "m3u8",
        ]

    def obfuscate_file_type(self, file_path: str) -> None:
        fo = open(file_path, "r+b")
        fo.seek(0)
        obfuscated = bytes([(_+128)%256 for _ in fo.read(1024*1024*1)])
        fo.seek(0)
        fo.write(obfuscated)
        fo.close()

    def cloak_file_ext(self, file_path: str) -> str:
        fo = open(file_path, "r+b")
        sig = None
        for ext, regex, seek_len, length in self.types:
            fo.seek(0)
            file_header = fo.read(seek_len+length)
            if re.search(regex, file_header):
                sig = ext
                break
        fo.close()
        if sig is None:
            ext = os.path.basename(file_path).split(".")[-1]
            if ext.lower() not in self.other_types:
                shutil.move(file_path, file_path+".cloudarchive_")
                return file_path+".cloudarchive_"
        shutil.move(file_path, file_path+".cloudarchive_"+ext)
        file_path += ".cloudarchive_"+ext
        self.obfuscate_file_type(file_path)
        return file_path

    def uncloak_file_ext(self, file_path: str) -> str:
        filename = os.path.basename(file_path)
        org_filename, ext = filename.split(".cloudarchive_")
        org_file_path = os.path.join(os.path.dirname(file_path), org_filename)
        if ext != "":
            self.obfuscate_file_type(file_path)
        shutil.move(file_path, org_file_path)
        return org_file_path

    def upload(self, identifier: str, root: str, path: str, check_overwrite, check_skip_same_size):
        path_prefix = identifier.split("/")[1:]
        identifier = identifier.split("/")[0]
        file = join_path(root, path)
        file = self.cloak_file_ext(file)
        remote_filename = os.path.basename(file)
        _path = "/".join(path_prefix+file.replace(root, "")[1:].split(os.path.sep))
        if not check_overwrite(_path) and check_skip_same_size(_path):
            p("[Upload] [Warning] File {} is skipped due to existing remote file".format(join_path(root, path)))
            self.uncloak_file_ext(file)
            return
        fs = str(file_size(file))
        headers = {
            # "authorization": f"LOW {self.access}:{self.secret}",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "multipart/form-data; charset=UTF-8",
            "Referer": f"https://archive.org/upload/?identifier={identifier}",
            # "User-Agent": USER_AGENT(self.access),
            "x-amz-acl": "bucket-owner-full-control",
            "x-amz-auto-make-bucket": "1",
            # "x-archive-interactive-priority": "1",
            "x-archive-queue-derive": "0",
            "x-archive-size-hint": fs,
            "X-File-Size": fs,
            "Content-Length": fs,
            "X-File-Name": f"uri({remote_filename})",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "X-Requested-With": "XMLHttpRequest"
        }
        url = f"https://s3.us.archive.org/"
        # url_path = identifier+"/"+path.replace("\\", "/")+"/"+remote_filename
        url_path = identifier+"/"+_path
        url_path = url_path.replace("//", "/")
        uri = url+urllib.parse.quote(url_path, safe="")
        p(f"[Uploading] {file} => {uri}", end="")
        fo = open(file, "rb")
        while True:
            try:
                fo.seek(0)
                r = self.__session.put(uri, data=fo, headers=headers)
                break
            except requests.exceptions.RequestException as ex:
                import time
                print(ex)
                for i in range(0, 10):
                    time.sleep(1)
                    print("\rretry in", i, end="", flush=True)
                print(flush=True)
            except KeyboardInterrupt as e:
                fo.close()
                self.uncloak_file_ext(file)
                raise e
        fo.close()
        self.uncloak_file_ext(file)
        if r.status_code != 200:
            raise Exception(f"failed to upload {file} => {uri}", r.status_code, r.request.headers, r.content)
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
        _f["file_path"] = self.uncloak_file_ext(_f["file_path"])
        p(f"\r[Downloaded] {identifier} {path} => "+_f["file_path"])
        return _f

    def rename(self, identifier: str, old_item: str, new_item: str):
        p(f"[Renaming] {identifier} {old_item} => {new_item}", end="")
        headers = {
            # "authorization": f"LOW {self.access}:{self.secret}",
            "x-amz-copy-source": "/"+urllib.parse.quote(identifier+"/"+old_item),
            "x-amz-metadata-directive": "COPY",
            "x-archive-keep-old-version": "0",
            "x-archive-queue-derive": "0",
            # "User-Agent": USER_AGENT(self.access)
        }
        url = "https://s3.us.archive.org"
        url += "/"+urllib.parse.quote(identifier+"/"+new_item)
        r = self.__session.put(url, headers=headers)
        if r.status_code != 200:
            raise Exception(f"failed to copy {identifier} {old_item} => {new_item}", r.status_code, r.content)
        p(f"\r[Renamed] {identifier} {old_item} => {new_item}")
        self.delete(identifier, old_item)
        # if r.status_code != 200:
        #     raise Exception(f"failed to delete old item {identifier} {old_item}", r.status_code, r.content)

    def delete(self, identifier: str, path: str):
        headers = {
            # "authorization": f"LOW {self.access}:{self.secret}",
            # "User-Agent": USER_AGENT(self.access),
            "x-archive-queue-derive": "0",
            "x-archive-cascade-delete": "1"
        }
        p(f"[Deleting] {identifier} {path}", end="")
        r = self.__session.delete(f"https://s3.us.archive.org/{identifier}/{path}", headers=headers)
        if r.status_code not in [200, 204]:
            raise Exception(f"failed to delete {identifier} {path}", r.status_code, r.content)
        p(f"\r[Deleted] {identifier} {path}")

    def new_identifier(self, identifier: str, title: str = None, description: str = None):
        p(f"[Identifier] Creating new {identifier}", end="")
        thumbnail_path = text2png.TextToPng(64).create(title or identifier)
        remote_filename = os.path.basename(thumbnail_path)
        org_title = title
        title = urllib.parse.quote(title) if title else identifier
        description = urllib.parse.quote(description) if description else ""
        headers = {
            # "authorization": f"LOW {self.access}:{self.secret}",
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
            "x-archive-meta01-description": f"uri(video%20software%20data%20{description})",
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
        r = self.__session.put(uri, data=open(thumbnail_path, "rb"), headers=headers)
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
            "access": self.__session.headers["authorization"][4:].split(":")[0],
            "secret": self.__session.headers["authorization"][4:].split(":")[1]
        }
        if op != "remove":
            data["-patch"][0]["value"] = v
        p(f"[Metadata] Pending {identifier} {op} {k}: {v}", end="")
        data["-patch"] = jd(data["-patch"])
        r = self.__session.post(url, data=data)
        if r.status_code != 200:
            raise Exception(f"failed metadata {identifier} {op} {k}: {v}", r.status_code, r.content)
        p(f"\r[Metadata] Done {identifier} {op} {k}: {v}")


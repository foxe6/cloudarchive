from .broker import *
import requests
import re
import text2png
import os
import time


class IA_Agent(object):
    def __init__(self, access: str = None, secret: str = None) -> None:
        self.s = requests.Session()
        self.access = access
        self.secret = secret

    def upload(self, identifier: str, root: str, path: str) -> None:
        if not self.check_identifier_created(identifier):
            raise Exception(f"identifier {identifier} does not exist")
        if os.path.isdir(join_path(root, path)):
            for file_dir, _, files in os.walk(join_path(root, path)):
                for file in files:
                    IA_Agent(self.access, self.secret).upload(
                        identifier,
                        root,
                        join_path(file_dir.replace(root, "")[1:], file)
                    )
        else:
            file = ""
            try:
                paths = path.split(os.path.sep)
                file = paths[-1]
                path = os.path.sep.join(paths[:-1])
                IA_Broker(self.access, self.secret, identifier).upload(root, path, file)
            except Exception as e:
                raise Exception(
                    f"failed to upload {root} > {path} > {file} to {identifier}",
                    e
                )

    def download(self, save_dir: str, url: str, identifier: str, path: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> None:
        # url = url.replace("https://archive.org/download/", "")
        # identifier = url.split("/")[0]
        self.check_identifier_created(identifier)
        # path = "/".join(url.split("/")[1:])
        files = self.find_matching_files(self.get_identifier_metadata(identifier), path)
        for file in files:
            try:
                while True:
                    hashes = IA_Broker().download(
                        join_path(save_dir, identifier, *(file["name"].split("/")[:-1])),
                        f"https://archive.org/download/{identifier}/"+file["name"],
                        piece_size=piece_size, connections=connections, cal_hash=cal_hash
                    )
                    if not cal_hash or hashes["sha1"] == file["sha1"]:
                        if cal_hash:
                            p(f"[Verified]", hashes["file_path"], hashes["sha1"])
                        break
            except:
                raise Exception(f"failed to download {identifier} > {path} to {save_dir}")

    def get_identifier_metadata(self, identifier: str) -> list:
        metadata = f"https://archive.org/metadata/{identifier}"
        metadata = requests.get(metadata).json()
        return metadata["files"]

    def find_matching_files(self, files: list, path: str) -> list:
        is_file = False
        if len([file for file in files if file["name"] == path]) == 1:
            is_file = True
        else:
            if path != "":
                path = (path+"/").replace("//", "/")
        files = [
            file for file in files if
            (
                (file["name"] == path and is_file) or
                (file["name"].startswith(path) and not is_file)
            ) and
            re.search(r"(_(files|meta)\.xml|_(archive\.torrent|meta\.sqlite))$", file["name"]) is None
        ]
        return files

    def check_identifier_available(self, identifier: str) -> bool:
        r_identifier = requests.post("https://archive.org/upload/app/upload_api.php", {
            "name": "identifierAvailable",
            "identifier": identifier,
            "findUnique": True
        }).json()["identifier"]
        return True if identifier == r_identifier else False

    def check_identifier_created(self, identifier: str) -> None:
        r = requests.get("https://archive.org/details/"+identifier)
        if r.status_code != 200:
            raise Exception(f"identifier {identifier} is not created yet")

    def wait_until_identifier_created(self, identifier: str) -> None:
        while True:
            try:
                self.check_identifier_created(identifier)
                return
            except:
                time.sleep(1)

    def new_identifier(self, identifier: str):
        if not self.check_identifier_available(identifier):
            raise Exception(f"identifier {identifier} already exists")
        p(f"[Identifier] Creating {identifier}", end="")
        thumbnail_path = text2png.TextToPng("C:\\Windows\\Fonts\\msgothic.ttc", 64).create(self.identifier)
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

    def login(self, credentials: tuple) -> None:
        self.s.get("https://archive.org/account/login")
        self.s.post("https://archive.org/account/login", {
            "username": credentials[0],
            "password": credentials[1],
            "remember": "undefined",
            "referer": "https://archive.org",
            "login": "true",
            "submit_by_js": "true"
        })

    def rename(self, credentials: tuple, identifier: str, old_item: str, new_item: str):
        self.check_identifier_created(identifier)
        if old_item == "" or new_item == "":
            raise Exception("rename name cannot be empty")
        self.login(credentials)
        files = self.get_identifier_metadata(identifier)
        old_files = self.find_matching_files(files, old_item)
        for i, old_file in enumerate(old_files):
            new_file = old_file["name"].replace(old_item, new_item, 1)
            collision = self.find_matching_files(files, new_file)
            if len(collision) == 1:
                raise Exception(
                    f"cannot rename {old_item} to {new_item}\n"+
                    f"because {new_item} already exists or\n"+
                    f"a file from {old_item} already exists in {new_item}"
                )
        for old_file in old_files:
            new_file = old_file["name"].replace(old_item, new_item, 1)
            IA_Broker().rename(self.s, identifier, old_file["name"], new_file)

    def delete(self, identifier: str, item: str):
        self.check_identifier_created(identifier)
        files = self.find_matching_files(self.get_identifier_metadata(identifier), item)
        for file in files:
            IA_Broker(self.access, self.secret).delete(identifier, file["name"])

    def list(self, identifier: str, item: str) -> list:
        files = self.find_matching_files(self.get_identifier_metadata(identifier), item)
        tree = {}
        for file in files:
            paths = file["name"].split("/")
            if len(paths) == 1:
                dir = ""
                item = (paths[0], file)
            else:
                dir = "/".join(paths[:-1])
                item = (paths[-1], file)
            if dir not in tree:
                if dir == "":
                    tree[""] = []
                else:
                    tree[dir] = {"": []}
            if dir == "":
                tree[dir].append(item)
            else:
                tree[dir][""].append(item)
        while any(["/" in k for k, v in tree.items()]):
            for k, v in tree.copy().items():
                if "/" in k:
                    ks = k.split("/")
                    new_k = "/".join(ks[:-1])
                    sub_k = ks[-1]
                    if new_k not in tree:
                        tree[new_k] = {}
                    tree[new_k][sub_k] = v
                    tree.pop(k)

        def dump_tree(d, depth=1) -> list:
            d = sorted(d.copy().items(), key=lambda x: x[0])
            cascade = []
            for k, v in d:
                if k == "":
                    v = sorted(v, key=lambda x: x[0])
                    for _k, _v in v:
                        cascade.append((depth, _k, _v))
                    continue
                elif isinstance(v, dict):
                    cascade.append((depth, k))
                    cascade += dump_tree(v, depth + 1)
            return cascade

        cascade = [(0, identifier)]+dump_tree(tree)
        return cascade

    def view(self, identifier: str, item: str) -> None:
        for _ in self.list(identifier, item):
            p("    "*_[0]+_[1])



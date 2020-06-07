from .broker import *
import text2png
from filehandling import create_cascade, create_tree, format_cascade
from lxml import html
import requests
import re
import os
import time


__ALL__ = ["IA_Agent"]


class IA_Agent(object):
    def __init__(self, access: str = None, secret: str = None) -> None:
        self.access = access
        self.secret = secret

    def upload(self, identifier: str, root: str, path: str) -> None:
        self.check_identifier_created(identifier)
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

    def download(self, save_dir: str, identifier: str, path: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> None:
        self.check_identifier_created(identifier)
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

    def __login(self, credentials: tuple) -> requests.Session:
        s = requests.Session()
        s.get("https://archive.org/account/login")
        s.post("https://archive.org/account/login", {
            "username": credentials[0],
            "password": credentials[1],
            "remember": "undefined",
            "referer": "https://archive.org",
            "login": "true",
            "submit_by_js": "true"
        })
        return s

    def rename(self, credentials: tuple, identifier: str, old_path: str, new_path: str):
        self.check_identifier_created(identifier)
        if old_path == "" or new_path == "":
            raise Exception("rename name cannot be empty")
        s = self.__login(credentials)
        files = self.get_identifier_metadata(identifier)
        old_files = self.find_matching_files(files, old_path)
        for old_file in old_files:
            new_file = old_file["name"].replace(old_path, new_path, 1)
            collision = self.find_matching_files(files, new_file)
            if len(collision) == 1:
                raise Exception(
                    f"cannot rename {old_path} to {new_path}\n"+
                    f"because {new_path} already exists or\n"+
                    f"a file from {old_path} already exists in {new_path}"
                )
        for old_file in old_files:
            new_file = old_file["name"].replace(old_path, new_path, 1)
            IA_Broker().rename(s, identifier, old_file["name"], new_file)

    def delete(self, identifier: str, path: str):
        self.check_identifier_created(identifier)
        files = self.find_matching_files(self.get_identifier_metadata(identifier), path)
        for file in files:
            IA_Broker(self.access, self.secret).delete(identifier, file["name"])

    def list_content(self, identifier: str, path: str) -> None:
        files = self.find_matching_files(self.get_identifier_metadata(identifier), path)
        cascade = create_cascade(identifier, create_tree(identifier, files, "name", "/"))
        p(format_cascade(cascade))

    def list_items(self, credentials: tuple) -> list:
        s = self.__login(credentials)
        r = s.get("https://archive.org/").content.decode()
        username = re.search(r"https\:\/\/archive\.org\/details\/@(.*?)\"", r)[1]
        url = f"https://archive.org/details/@{username}?&sort=-addeddate&page=<page>&scroll=1"
        items = []
        for i in range(1, 9999):
            r = s.get(url.replace("<page>", str(i))).content.decode()
            if "No results" in r:
                break
            r = html.fromstring(r)
            _items = r.xpath("//div[@class='ttl']/../@title")
            items += _items
        return items


    # def view(self, identifier: str, path: str) -> None:
    #     for _ in self.list(identifier, path):
    #         p("    "*_[0]+_[1])



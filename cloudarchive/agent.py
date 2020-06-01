from .broker import *
import requests
import re


class IA_Agent(object):
    def __init__(self, access: str = None, secret: str = None, identifier: str = None) -> None:
        self.access = access
        self.secret = secret
        self.identifier = identifier

    def upload(self, root: str, item: str) -> None:
        if os.path.isdir(join_path(root, item)):
            for _, sub_dir, files in os.walk(os.path.join(root, item)):
                for file in files:
                    IA_Broker(self.access, self.secret, self.identifier).\
                        upload(root, os.path.sep.join([item]+sub_dir), file)
        else:
            paths = item.split(os.path.sep)
            file = paths[-1]
            path = os.path.sep.join(paths[:-1])
            IA_Broker(self.access, self.secret, self.identifier).upload(root, path, file)

    def download(self, save_dir: str, url: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> None:
        url = url.replace("https://archive.org/download/", "")
        identifier = url.split("/")[0]
        path = "/".join(url.split("/")[1:])
        if requests.get(f"https://archive.org/download/{url}/").status_code != 404:
            if path != "":
                path = (path+"/").replace("//", "/")
        metadata = f"https://archive.org/metadata/{identifier}"
        metadata = requests.get(metadata).json()
        files = metadata["files"]
        files = [file for file in files if file["name"].startswith(path) and
                 re.search(r"(_(files|meta)\.xml|_(archive\.torrent|meta\.sqlite))$", file["name"]) is None]
        for file in files:
            while True:
                hashes = IA_Broker().download(
                    join_path(save_dir, identifier, *(file["name"].split("/")[:-1])),
                    f"https://archive.org/download/{identifier}/"+file["name"],
                    piece_size=piece_size, connections=connections, cal_hash=cal_hash
                )
                p(cal_hash, hashes["sha1"], file["sha1"])
                if not cal_hash or hashes["sha1"] == file["sha1"]:
                    if cal_hash:
                        p(f"[Verified] {url} => " + hashes["file_path"])
                    break


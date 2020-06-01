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
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3) -> None:
        url = url.replace("https://archive.org/download/", "")
        identifier = url.split("/")[0]
        path = url.replace(identifier, "")[1:]
        if requests.get(f"https://archive.org/download/{url}/").status_code != 404:
            if path != "":
                path = (path+"/").replace("//", "/")
        metadata = f"https://archive.org/metadata/{identifier}"
        metadata = requests.get(metadata).json()
        files = metadata["files"]
        files = [file for file in files if file["name"].find(path) == 0 and
                 re.search(r"(_(files|meta)\.xml|_(archive\.torrent|meta\.sqlite))$", file["name"]) is None]
        p(files)


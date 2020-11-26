from .broker import *
from filehandling import create_cascade, create_tree, format_cascade
from lxml import html
import requests
import re
import os
import time


__ALL__ = ["IA_Agent"]


class IA_Agent(object):
    def __init__(self, access: str = None, secret: str = None) -> None:
        self.iaa_upload = lambda identifier, root, path: IA_Agent(access, secret).upload(identifier, root, path)
        self.iab_upload = lambda identifier, root, path, file: IA_Broker(access, secret, identifier).upload(root, path, file)
        self.iab_new_identifier = lambda identifier, title, description: IA_Broker(access, secret).new_identifier(identifier, title, description)
        self.iab_delete = lambda identifier, file_name: IA_Broker(access, secret).delete(identifier, file_name)
        self.iab_rename = lambda identifier, old_item, new_item: IA_Broker(access, secret).rename(identifier, old_item, new_item)
        self.iab_metadata = lambda identifier, op, k, v: IA_Broker(access, secret).metadata(identifier, op, k, v)

    def get_identifier_metadata(self, identifier: str) -> dict:
        metadata = f"https://archive.org/metadata/{identifier}"
        metadata = requests.get(metadata).json()
        return metadata

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
        r = requests.get("https://archive.org/download/"+identifier)
        if r.status_code != 200:
            raise Exception(f"identifier {identifier} is not created yet")

    def wait_until_identifier_created(self, identifier: str, func=lambda: None) -> None:
        while True:
            try:
                self.check_identifier_created(identifier)
                break
            except:
                time.sleep(1)
        func()

    def list_content(self, identifier: str, path: str) -> tuple:
        files = self.find_matching_files(self.get_identifier_metadata(identifier)["files"], path)
        cascade = create_cascade(identifier, create_tree(identifier, files, "name", "/"))
        return (cascade, format_cascade(cascade))

    def upload(self, identifier: str, root: str, path: str) -> None:
        self.check_identifier_created(identifier)
        if os.path.isdir(join_path(root, path)):
            for file_dir, _, files in os.walk(join_path(root, path)):
                for file in files:
                    self.iaa_upload(
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
                self.iab_upload(identifier, root, path, file)
            except Exception as e:
                raise Exception(
                    f"failed to upload {root} > {path} > {file} to {identifier}",
                    e
                )

    def download(self, save_dir: str, identifier: str, path: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> None:
        self.check_identifier_created(identifier)
        files = self.find_matching_files(self.get_identifier_metadata(identifier)["files"], path)
        try:
            for file in files:
                while True:
                    hashes = IA_Broker().download(
                        join_path(save_dir, identifier, *(file["name"].split("/")[:-1])),
                        identifier, file["name"],
                        piece_size=piece_size, connections=connections, cal_hash=cal_hash
                    )
                    if not cal_hash:
                        break
                    elif hashes["sha1"] == file["sha1"]:
                        p(f"[Verified]", hashes["file_path"], hashes["sha1"])
                        break
                    raise Exception(f"failed to download "+file["name"]+" or verify "+hashes["file_path"])
        except Exception as e:
            raise Exception(
                f"failed to download {identifier} > {path} to {save_dir}",
                e
            )

    def new_identifier(self, identifier: str, title: str = None, description: str = None):
        if not self.check_identifier_available(identifier):
            raise Exception(f"identifier {identifier} already exists")
        try:
            self.iab_new_identifier(identifier, title, description)
        except Exception as e:
            raise Exception(
                f"failed to create new identifier {identifier}",
                e
            )

    def rename(self, identifier: str, old_path: str, new_path: str):
        self.check_identifier_created(identifier)
        if old_path == "" or new_path == "":
            raise Exception("rename name cannot be empty")
        files = self.get_identifier_metadata(identifier)["files"]
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
        try:
            for old_file in old_files:
                new_file = old_file["name"].replace(old_path, new_path, 1)
                self.iab_rename(identifier, old_file["name"], new_file)
        except Exception as e:
            raise Exception(
                f"failed to rename {identifier} {old_path} to {new_path}",
                e
            )

    def delete(self, identifier: str, path: str):
        self.check_identifier_created(identifier)
        files = self.find_matching_files(self.get_identifier_metadata(identifier)["files"], path)
        try:
            for file in files:
                self.iab_delete(identifier, file["name"])
        except Exception as e:
            raise Exception(
                f"failed to delete {identifier} {path}",
                e
            )

    def metadata(self, identifier: str, k: str = None, v: str = None):
        self.check_identifier_created(identifier)
        metadata = self.get_identifier_metadata(identifier)["metadata"]
        if not k:
            return metadata
        if v == "REMOVE_TAG":
            op = "remove"
        else:
            if not k in metadata:
                op = "add"
            elif metadata[k] != v:
                op = "replace"
            else:
                p(f"failed to modify metadata <{identifier}> same k v {k}: {v}")
                return
        try:
            self.iab_metadata(identifier, op, k, v)
        except Exception as e:
            raise Exception(
                f"failed to fetch/modify metadata {identifier} {k} {v}",
                e
            )

    def delete_identifier(self, identifier: str):
        self.metadata(identifier, "collection", "test_collection")


    # def view(self, identifier: str, path: str) -> None:
    #     for _ in self.list(identifier, path):
    #         p("    "*_[0]+_[1])



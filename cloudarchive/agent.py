from .broker import *
from filehandling import create_cascade, create_tree, format_cascade
from lxml import html
import requests
import re
import os
import time
import traceback


__ALL__ = ["IA_Agent"]


class IA_Agent(object):
    def __init__(self, session: requests.Session = None) -> None:
        # self.iaa_upload = lambda identifier, root, path: IA_Agent(access, secret).upload(identifier, root, path)
        # self.iab_upload = lambda identifier, root, path, file: IA_Broker(access, secret, identifier).upload(root, path, file)
        # self.iab_new_identifier = lambda identifier, title, description: IA_Broker(access, secret).new_identifier(identifier, title, description)
        # self.iab_delete = lambda identifier, file_name: IA_Broker(access, secret).delete(identifier, file_name)
        # self.iab_rename = lambda identifier, old_item, new_item: IA_Broker(access, secret).rename(identifier, old_item, new_item)
        # self.iab_metadata = lambda identifier, op, k, v: IA_Broker(access, secret).metadata(identifier, op, k, v)
        self.__session = session

    def get_identifier_metadata(self, identifier: str) -> dict:
        metadata = f"https://archive.org/metadata/{identifier}"
        metadata = self.__session.get(metadata).json()
        return metadata

    def find_matching_files(self, files: list, path) -> list:
        # if path.startswith("^") and path.endswith("$"):
        #     path = re.compile(path)
        is_file = False
        if not isinstance(path, re.Pattern):
            if len([file for file in files if file["name"] == path]) == 1:
                is_file = True
            else:
                if path != "":
                    path = (path+"/").replace("//", "/")
        files = [
            file for file in files if
            (
                (
                    path.search(file["name"]) is not None
                ) if isinstance(path, re.Pattern) else
                (
                    (file["name"] == path and is_file) or
                    (file["name"].startswith(path) and not is_file)
                )
            ) and
            re.search(
                r"(_(files|meta)\.xml|_(archive\.torrent|meta\.sqlite))$",
                file["name"]
            ) is None
        ]
        return files

    def check_identifier_available(self, identifier: str) -> bool:
        r_identifier = self.__session.post("https://archive.org/upload/app/upload_api.php", {
            "name": "identifierAvailable",
            "identifier": identifier,
            "findUnique": True
        }).json()["identifier"]
        return True if identifier == r_identifier else False

    def check_identifier_created(self, identifier: str) -> None:
        r = self.__session.get("https://archive.org/download/"+identifier)
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

    def list_content(self, identifier: str, path) -> tuple:
        files = self.find_matching_files(self.get_identifier_metadata(identifier)["files"], path)
        cascade = create_cascade(identifier, create_tree(identifier, files, "name", "/"))
        return (files, format_cascade(cascade))

    def upload(self, identifier: str, root: str, path: str,
               overwrite: bool = True, replace_same_size: bool = False, exist_files: list = None,
               check_identifier_created: bool = True) -> None:
        _identifier = identifier.split("/")[0]
        if check_identifier_created:
            self.check_identifier_created(_identifier)
        if exist_files is None:
            exist_files = self.get_identifier_metadata(_identifier)["files"]
            if identifier != _identifier:
                exist_files = self.find_matching_files(exist_files, identifier.replace(_identifier, "")[1:])
        is_pattern = path.startswith("^") and path.endswith("$")
        walk_path = root if is_pattern else join_path(root, path)
        path_pattern = re.compile(path) if is_pattern else None
        if os.path.isdir(walk_path):
            for file_dir, _, files in os.walk(walk_path):
                for file in files:
                    _path = join_path(file_dir.replace(root, "")[1:], file)
                    if is_pattern and path_pattern.search(_path) is None:
                        p("[Upload] [Warning] File {} is skipped due to mismatched regex".format(join_path(root, _path)))
                        continue
                    IA_Agent(self.__session).upload(
                        identifier,
                        root,
                        _path,
                        overwrite,
                        replace_same_size,
                        exist_files,
                        False
                    )
        else:
            file = ""
            try:
                fs = file_size(join_path(root, path))
                if fs == 0:
                    p("[Upload] [Warning] File {} is skipped due to 0 file size".format(join_path(root, path)))
                    return
                def check_overwrite(_path):
                    matches = self.find_matching_files(exist_files, _path)
                    if len(matches) != 1:
                        return True
                    return overwrite
                def check_replace_same_size(_path):
                    matches = self.find_matching_files(exist_files, _path)
                    if len(matches) != 1:
                        return True
                    return replace_same_size and int(matches[0]["size"]) == fs
                IA_Broker(self.__session).upload(
                    identifier, root, path, check_overwrite, check_replace_same_size
                )
            except:
                raise Exception(
                    f"failed to upload {root} > {path} > {file} to {identifier}",
                    traceback.format_exc()
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
        except:
            raise Exception(
                f"failed to download {identifier} > {path} to {save_dir}",
                traceback.format_exc()
            )

    def new_identifier(self, identifier: str, title: str = None, description: str = None):
        if not self.check_identifier_available(identifier):
            raise Exception(f"identifier {identifier} already exists")
        try:
            IA_Broker(self.__session).new_identifier(identifier, title, description)
        except:
            raise Exception(
                f"failed to create new identifier {identifier}",
                traceback.format_exc()
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
                IA_Broker(self.__session).rename(identifier, old_file["name"], new_file)
        except:
            raise Exception(
                f"failed to rename {identifier} {old_path} to {new_path}",
                traceback.format_exc()
            )

    def delete(self, identifier: str, path: str):
        self.check_identifier_created(identifier)
        files = self.find_matching_files(self.get_identifier_metadata(identifier)["files"], path)
        try:
            for file in files:
                IA_Broker(self.__session).delete(identifier, file["name"])
        except:
            raise Exception(
                f"failed to delete {identifier} {path}",
                traceback.format_exc()
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
            IA_Broker(self.__session).metadata(identifier, op, k, v)
        except:
            raise Exception(
                f"failed to fetch/modify metadata {identifier} {k} {v}",
                traceback.format_exc()
            )

    def delete_identifier(self, identifier: str):
        self.metadata(identifier, "collection", "test_collection")


    # def view(self, identifier: str, path: str) -> None:
    #     for _ in self.list(identifier, path):
    #         p("    "*_[0]+_[1])



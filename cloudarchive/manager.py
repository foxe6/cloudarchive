from .agent import *
from omnitools import randstr


__ALL__ = ["IA_MGR"]


class IA_MGR(object):
    def __init__(self, credentials: tuple):
        self.email_prefix = credentials[0].split("@")[0]
        self.__s = requests.Session()
        self.__s.get("https://archive.org/account/login")
        self.__s.post("https://archive.org/account/login", {
            "username": credentials[0],
            "password": credentials[1],
            "remember": "undefined",
            "referer": "https://archive.org",
            "login": "true",
            "submit_by_js": "true"
        })
        r = self.__s.get("https://archive.org/account/s3.php")
        a, s = re.findall(r">Your S3 (?:access|secret) key: ([A-Za-z0-9]{16})<", r.content.decode())
        self.__iaa = IA_Agent(a, s)

    def get_items(self) -> dict:
        item_username = "https://archive.org/details/{}".format(self.email_prefix)
        r = self.__s.get(item_username)
        if r.status_code == 404:
            raise Exception('''
failed to fetch username for profile page. please create a new identifier with the following code:
IA_Agent("access", "secret").new_identifier("{}", "metadata_username")'''.format(self.email_prefix))
        username = re.search(r"\"\/details\/@(.*?)\"", r.content.decode())[1]
        url = f"https://archive.org/details/@{username}?&sort=-addeddate&page=<page>&scroll=1"
        items = {}
        for i in range(1, 9999):
            r = self.__s.get(url.replace("<page>", str(i))).content.decode()
            if "No results" in r:
                break
            r = html.fromstring(r)
            vs = r.xpath("//div[@class='ttl']/../@title")
            ks = r.xpath("//div[@class='ttl']/../@href")
            for i in range(0, len(ks)):
                items[ks[i].replace("/details/", "")] = vs[i]
        return items

    def get_identifier_by_title(self, regex: str) -> str:
        org_regex = regex
        regex = re.compile(regex)
        matches = []
        for k, v in self.get_items().items():
            if regex.search(v):
                matches.append(k)
        if len(matches) > 1:
            raise Exception("multiple title matches against {}".format(org_regex), matches)
        elif len(matches) == 0:
            raise Exception("zero title match against {}".format(org_regex), matches)
        return matches[0]

    def new_item(self, title: str, description: str = None, identifier: str = None) -> str:
        if identifier is None:
            identifier = randstr(100, "-_.")
        self.__iaa.new_identifier(identifier, title, description)
        self.__iaa.wait_until_identifier_created(identifier)
        return identifier

    def delete_item(self, identifier: str):
        self.__iaa.metadata(identifier, "collection", "test_collection")

    def get_item_content(self, identifier: str, path: str) -> tuple:
        if identifier == self.email_prefix:
            raise Exception("failed to fetch/modify because {} is a metadata item".format(identifier))
        return self.__iaa.list_content(identifier, path)

    def upload(self, identifier: str, root: str, path: str) -> None:
        if identifier == self.email_prefix:
            raise Exception("failed to fetch/modify because {} is a metadata item".format(identifier))
        self.__iaa.upload(identifier, root, path)

    def download(self, save_dir: str, identifier: str, path: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> None:
        if identifier == self.email_prefix:
            raise Exception("failed to fetch/modify because {} is a metadata item".format(identifier))
        self.__iaa.download(save_dir, identifier, path, piece_size, connections, cal_hash)

    def rename(self, identifier: str, old_path: str, new_path: str) -> None:
        if identifier == self.email_prefix:
            raise Exception("failed to fetch/modify because {} is a metadata item".format(identifier))
        self.__iaa.rename(identifier, old_path, new_path)

    def delete(self, identifier: str, path: str) -> None:
        if identifier == self.email_prefix:
            raise Exception("failed to fetch/modify because {} is a metadata item".format(identifier))
        self.__iaa.delete(identifier, path)

    def metadata(self, identifier: str, k: str = None, v: str = None) -> None:
        if identifier == self.email_prefix:
            raise Exception("failed to fetch/modify because {} is a metadata item".format(identifier))
        self.__iaa.metadata(identifier, k, v)



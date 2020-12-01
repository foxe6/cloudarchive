from .agent import *
from omnitools import randstr


__ALL__ = ["IA_Manager"]


class IA_Manager(object):
    def __init__(self, credentials: tuple):
        if credentials:
            self.email_prefix = credentials[0].split("@")[0]
            s = self.init_session(credentials)
            self.__iaa = IA_Agent(s)
            def get_items() -> dict:
                item_username = "https://archive.org/details/{}".format(self.email_prefix)
                r = s.get(item_username)
                if r.status_code == 404:
                    raise Exception('''
failed to fetch username for profile page. please create a new identifier with the following code:
IA_Agent("access", "secret").new_identifier("{}", "metadata_username")'''.format(self.email_prefix))
                username = re.search(r"\"\/details\/@(.*?)\"", r.content.decode())[1]
                url = f"https://archive.org/details/@{username}?&sort=-addeddate&page=<page>&scroll=1"
                items = {}
                for i in range(1, 9999):
                    r = s.get(url.replace("<page>", str(i))).content.decode()
                    if "No results" in r:
                        break
                    r = html.fromstring(r)
                    vs = r.xpath("//div[@class='ttl']/../@title")
                    ks = r.xpath("//div[@class='ttl']/../@href")
                    for i in range(0, len(ks)):
                        items[ks[i].replace("/details/", "")] = vs[i]
                return items
            self.get_items = get_items
        else:
            self.__iaa = IA_Agent()

    def init_session(self, credentials: tuple) -> requests.Session:
        s = requests.Session()
        s.headers.update({
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
        })
        s.get("https://archive.org/account/login")
        s.post("https://archive.org/account/login", {
            "username": credentials[0],
            "password": credentials[1],
            "remember": "undefined",
            "referer": "https://archive.org",
            "login": "true",
            "submit_by_js": "true"
        })
        r = s.get("https://archive.org/account/s3.php")
        _a, _s = re.findall(r">Your S3 (?:access|secret) key: ([A-Za-z0-9]{16})<", r.content.decode())
        s.headers.update({
            "authorization": "LOW {}:{}".format(_a, _s),
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9"
        })
        # s.get("https://archive.org/upload/")
        return s

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

    def _check_op(self, identifier: str) -> None:
        if identifier.split("/")[0] == self.email_prefix:
            raise Exception("failed to fetch/modify because {} is a metadata item".format(identifier))

    def delete_item(self, identifier: str):
        self._check_op(identifier)
        self.__iaa.metadata(identifier, "collection", "test_collection")

    def get_item_content(self, identifier: str, path: str) -> tuple:
        self._check_op(identifier)
        return self.__iaa.list_content(identifier, path)

    def upload(self, identifier: str, root: str, path: str,
               overwrite: bool = True, replace_same_size: bool = False) -> None:
        self._check_op(identifier)
        self.__iaa.upload(identifier, root, path, overwrite, replace_same_size)

    def download(self, save_dir: str, identifier: str, path: str,
                 piece_size: int = 1024*1024*(2**4), connections: int = 2**3,
                 cal_hash: bool = False) -> None:
        self._check_op(identifier)
        self.__iaa.download(save_dir, identifier, path, piece_size, connections, cal_hash)

    def rename(self, identifier: str, old_path: str, new_path: str) -> None:
        self._check_op(identifier)
        self.__iaa.rename(identifier, old_path, new_path)

    def delete(self, identifier: str, path: str) -> None:
        self._check_op(identifier)
        self.__iaa.delete(identifier, path)

    def metadata(self, identifier: str, k: str = None, v: str = None) -> None:
        self._check_op(identifier)
        self.__iaa.metadata(identifier, k, v)



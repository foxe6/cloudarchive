from .broker import *


class IA_Agent(object):
    def __init__(self, access: str = None, secret: str = None, identifier: str = None) -> None:
        self.access = access
        self.secret = secret
        self.identifier = identifier

    def upload(self, root: str, item: str) -> None:
        for _, sub_dir, files in os.walk(os.path.join(root, item)):
            for file in files:
                print(root, os.path.sep.join([item]+sub_dir), file)
                IA_Broker(self.access, self.secret, self.identifier)



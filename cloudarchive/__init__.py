__version__ = "0.8.0"
__keywords__ = ["internetarchive cloud archive storage archive.org"]


if not __version__.endswith(".0"):
    import re
    print(f"version {__version__} is deployed for automatic commitments only", flush=True)
    print("install version " + re.sub(r"([0-9]+\.[0-9]+\.)[0-9]+", r"\g<1>0", __version__) + " instead")
    import os
    os._exit(1)


from .agent import *
from .broker import *
from .manager import *

# Internet Archive (archive.org) Python Frontend

<badges>[![version](https://img.shields.io/pypi/v/cloudarchive.svg)](https://pypi.org/project/cloudarchive/)
[![license](https://img.shields.io/pypi/l/cloudarchive.svg)](https://pypi.org/project/cloudarchive/)
[![pyversions](https://img.shields.io/pypi/pyversions/cloudarchive.svg)](https://pypi.org/project/cloudarchive/)  
[![donate](https://img.shields.io/badge/Donate-Paypal-0070ba.svg)](https://paypal.me/foxe6)
[![powered](https://img.shields.io/badge/Powered%20by-UTF8-red.svg)](https://paypal.me/foxe6)
[![made](https://img.shields.io/badge/Made%20with-PyCharm-red.svg)](https://paypal.me/foxe6)
</badges>

<i>Unlimited cloud storage. Best for archiving.</i>

# Hierarchy

```
cloudarchive
'---- IA_Agent()
    |---- check_identifier_available()
    |---- check_identifier_created()
    |---- delete()
    |---- download()
    |---- find_matching_files()
    |---- get_identifier_metadata()
    |---- list_content()
    |---- list_items()
    |---- metadata()
    |---- new_identifier()
    |---- rename()
    |---- upload()
    '---- wait_until_identifier_created()
```

# Example

## python
```python
from cloudarchive import IA_Agent
iaa = IA_Agent(
    # Retrieve at https://archive.org/account/s3.php
    access="Your S3 access key",
    secret="Your S3 secret key"
)

# check if the identifier is unused
# thus usable for uploading new items
# used in new_identifier()
iaa.check_identifier_available(
    identifier="identifier"
)

# check if the identifier is created
# please use wait_until_identifier_created() instead
iaa.check_identifier_created(
    identifier="identifier"
)

# consider the following identifier (footest) tree:
# footest
# â”œâ”€â”€â”€ footest3.7z
# â””â”€â”€â”¬ footest2
#    â”œâ”€â”€â”€ somefile
#    â”œâ”€â”€â”€ somefile.txt
#    â”œâ”€â”€â”€ testfile
#    â”œâ”€â”€â”¬ footest3
#    â”‚  â”œâ”€â”€â”€ somefile
#    â”‚  â”œâ”€â”€â”€ somefile.txt
#    â”‚  â”œâ”€â”€â”€ testfile
#    â”‚  â””â”€â”€â”€ testfile.zip
#    â””â”€â”€â”¬ footest7
#       â”œâ”€â”€â”€ somefile
#       â”œâ”€â”€â”€ somefile.txt
#       â”œâ”€â”€â”€ testfile
#       â””â”€â”€â”€ testfile.zip

# delete a folder or a file
iaa.delete(
    identifier="footest",
    path="footest2/footest3" or "footest2/footest7/somefile"
)
# result:
# footest
# â”œâ”€â”€â”€ footest3.7z
# â””â”€â”€â”¬ footest2
#    â”œâ”€â”€â”€ somefile
#    â”œâ”€â”€â”€ somefile.txt
#    â”œâ”€â”€â”€ testfile
#    â””â”€â”€â”¬ footest7
#       â”œâ”€â”€â”€ somefile
#       â”œâ”€â”€â”€ somefile.txt
#       â”œâ”€â”€â”€ testfile
#       â””â”€â”€â”€ testfile.zip

# download a folder or a file
iaa.download(
    # save directory
    save_dir=r"D:\testing",
    identifier="footest",
    path="footest2/footest3" or "",
    # refer to mfd readme 
    piece_size=1024*1024*(2**4),
    connections=2**3,
    cal_hash=False
)
# result:
# D:\testing # save directory
# â””â”€â”€â”¬ footest # identifier
#    â””â”€â”€â”¬ footest2
#       â””â”€â”€â”¬ footest3 # selected path
#          â”œâ”€â”€â”€ somefile
#          â”œâ”€â”€â”€ somefile.txt
#          â”œâ”€â”€â”€ testfile
#          â””â”€â”€â”€ testfile.zip

# search for matching file names
# used in other methods
iaa.find_matching_files(
    files=iaa.get_identifier_metadata(
        identifier="footest"
    )["files"],
    path="footest2/footest3" or ""
)
# result:
# [
#     {'name': 'footest2/footest3/somefile', 'source': 'original', 'mtime': '1591130223', 'size': '11', 'md5': 'c8dd6a11b9613d3ff04240fffa3e3c30', 'crc32': 'e99e8fda', 'sha1': '63f4001c22fbc493ec8294452a5e1566d0f2d5ab', 'format': 'Unknown'},
#     {'name': 'footest2/footest3/somefile.txt', 'source': 'original', 'mtime': '1591130231', 'size': '11', 'md5': 'c8dd6a11b9613d3ff04240fffa3e3c30', 'crc32': 'e99e8fda', 'sha1': '63f4001c22fbc493ec8294452a5e1566d0f2d5ab', 'format': 'Unknown'},
#     {'name': 'footest2/footest3/testfile', 'source': 'original', 'mtime': '1591130241', 'size': '520477', 'md5': '59fe680036dfc2cddf64865687fbb180', 'crc32': '5f138f18', 'sha1': 'b250a8c48ebdfbb349cc47e66f115db3a8fd3b85', 'format': 'Unknown'},
#     {'name': 'footest2/footest3/testfile.zip', 'source': 'original', 'mtime': '1591130250', 'size': '520477', 'md5': '59fe680036dfc2cddf64865687fbb180', 'crc32': '5f138f18', 'sha1': 'b250a8c48ebdfbb349cc47e66f115db3a8fd3b85', 'format': 'Unknown'}
# ]

# get metadata of the identifier
# same as json of
# https://archive.org/metadata/footest
# used in other methods
iaa.get_identifier_metadata(
    identifier="test2"
)
# result:
# {"created":1592630409,"d1":"ia600300.us.archive.org","d2":"ia800300.us.archive.org","dir":"/10/items/test2","files":[{"name":"AudacityTest003.mp3","source":"original","track":"0","creator":"Norbert Davis","album":"norbtek.info Podcast Test","title":"Audacity Test #3","format":"VBR MP3","license":"Licensed to the public under http:\/\/creativecommons.org\/licenses\/by\/2.0\/ verify at http:\/\/www.archive.org\/audio\/audio-details-db.php?collection=opensource_audio&collectionid=test2","md5":"cd05915b7bbbb1c33640dabada46136e","mtime":"1114404446","size":"1042766","crc32":"693ce006","sha1":"3bbff980b4972afe22170e331cc72921a2424217","length":"148.97","height":"0","width":"0","genre":"Blues","artist":"Norbert Davis","external-identifier-match-date":"acoustid:2019-04-10T19:13:13Z","external-identifier":"urn:acoustid:b786fe51-bc80-4c1c-9f47-f27ffc199529"},{"name":"AudacityTest003.ogg","source":"derivative","track":"0","creator":"Norbert Davis","album":"norbtek.info Podcast Test","title":"Audacity Test #3","original":"AudacityTest003.mp3","format":"Ogg Vorbis","license":"Licensed to the public under http:\/\/creativecommons.org\/licenses\/by\/2.0\/ verify at http:\/\/www.archive.org\/audio\/audio-details-db.php?collection=opensource_audio&collectionid=test2","md5":"7d1dc6f6c21536361e9eae4690d7c68d","mtime":"1114405262","size":"1396309","crc32":"78e47871","sha1":"a12f14359b52d941f0150924bb86155edf4e73b5","length":"148.68","height":"0","width":"0"},{"name":"AudacityTest003.png","source":"derivative","format":"PNG","original":"AudacityTest003.mp3","mtime":"1415084219","size":"11087","md5":"0b568e36ef70ec779da8f1871b7376da","crc32":"77d6be09","sha1":"146e7d453ccc993f11d809bb1e8ab164ed9f975c"},{"name":"AudacityTest003_64kb.mp3","source":"derivative","track":"0","creator":"Norbert Davis","length":"02:28","album":"norbtek.info Podcast Test","title":"Audacity Test #3","original":"AudacityTest003.mp3","bitrate":"64","format":"64Kbps MP3","license":"Licensed to the public under http:\/\/creativecommons.org\/licenses\/by\/2.0\/ verify at http:\/\/www.archive.org\/audio\/audio-details-db.php?collection=opensource_audio&collectionid=test2","md5":"2b7b0d62ca4f7e9fa17145b24cb4a993","mtime":"1114405274","size":"1191422","crc32":"e693d9fd","sha1":"8e3ec130a75fc4d887503862bef9da50201efef9","height":"0","width":"0"},{"name":"__ia_thumb.jpg","source":"original","mtime":"1541667227","size":"3244","md5":"10305bc8fdceb781e6679218503ddefe","crc32":"14f1d725","sha1":"077e6d956ed9a6b8bcaa82ecf53e1ae0aa1c6d52","format":"Item Tile","rotation":"0"},{"name":"test2_64kb.m3u","source":"derivative","format":"64Kbps M3U","original":"AudacityTest003_64kb.mp3","md5":"28e3ea1c0122f11480af93ec6ecdf316","mtime":"1114405274","size":"63","crc32":"d7627d9f","sha1":"937dce166ffef1041923755adc67a36335c3bea5"},{"name":"test2_64kb_mp3.zip","source":"derivative","format":"64Kbps MP3 ZIP","original":"AudacityTest003_64kb.mp3","md5":"998f4428c784edeaf2dc4ccfcc5cad7e","mtime":"1114405274","size":"1191602","crc32":"60aa2975","sha1":"0e6dcd1d09af7663477a35f60fb55d530e467bf8","length":"148.95","height":"0","width":"0"},{"name":"test2_archive.torrent","source":"metadata","btih":"831a37df4512a48de8d639931115ee4bf56495df","mtime":"1554923602","size":"2534","md5":"d963969703e2a1930a9df914be46b7e0","crc32":"1fb2cf58","sha1":"4022c5d15ca7bd7fa16c4edc5d9c2d32d0cbeb27","format":"Archive BitTorrent"},{"name":"test2_files.xml","source":"metadata","md5":"8614a21f83170527d91977a587c464fa","format":"Metadata"},{"name":"test2_meta.xml","source":"metadata","mtime":"1554923602","size":"1043","format":"Metadata","md5":"732a634d8c1fa0bd1b9dc8870c96029c","crc32":"c51b206b","sha1":"002043be7521fb73853638b14f31372ac00d6816"},{"name":"test2_reviews.xml","source":"metadata","md5":"593627c08e4a510883e184763f0aaf09","mtime":"1133929214","size":"166","crc32":"2a102c41","sha1":"178a63b93b48a990c94409ed07bff1e1bf9eacee","format":"Metadata"},{"name":"test2_vbr.m3u","source":"derivative","format":"VBR M3U","original":"AudacityTest003.mp3","md5":"1fc0c95f758effd8a7d471b01500c3c4","mtime":"1114405244","size":"58","crc32":"164617d2","sha1":"dba018c18a3ba792fdfb7fcef82bf6eafeca448b"},{"name":"test2_vbr_mp3.zip","source":"derivative","format":"VBR ZIP","original":"AudacityTest003.mp3","md5":"c07f58b5bd0578ec2d4378bd7b83b195","mtime":"1114405244","size":"1042936","crc32":"e3da3c99","sha1":"892c37cbd6044412b8433fbb00b39ff44104b58e","length":"148.99","height":"0","width":"0"}],"files_count":13,"item_last_updated":1554923602,"item_size":5883230,"metadata":{"mediatype":"audio","identifier":"test2","type":"sound","publicdate":"2005-04-25 20:52:48","creator":"Norbert Davis","description":"norbtek podcast test 002","licenseurl":"http://creativecommons.org/licenses/by/2.0/","date":"0000-00-00 00:00:00","collection":"podcasts","title":"Norbtek test 002","uploader":"norbtek.info@gmail.com","addeddate":"2005-04-24 21:50:39","adder":"Norbert Davis","pick":"0","runtime":"2:28","taper":"Norbert Davis","subject":"Podcasts","publisher":"Norbert Davis","source":"folio","updater":"unix:etree","curation":"[curator]malware@archive.org[/curator][date]20140318060035[/date][comment]checked for malware[/comment]","backup_location":"ia903600_8","external_metadata_update":"2019-04-10T19:13:13Z","notes":""},"reviews":[],"server":"ia800300.us.archive.org","uniq":496844391,"workable_servers":["ia800300.us.archive.org","ia600300.us.archive.org"]}

# list content of the identifier
iaa.list_content(
    identifier="footest",
    path="footest2/footest3" or ""
)
# (
#     [
#         (0, 'footest2'),
#         (1, 'footest2'),
#         (2, 'footest3'),
#         (3, 'somefile', {'name': 'footest2/footest3/somefile', 'source': 'original', 'mtime': '1591130223', 'size': '11', 'md5': 'c8dd6a11b9613d3ff04240fffa3e3c30', 'crc32': 'e99e8fda', 'sha1': '63f4001c22fbc493ec8294452a5e1566d0f2d5ab', 'format': 'Unknown'}),
#         (3, 'somefile.txt', {'name': 'footest2/footest3/somefile.txt', 'source': 'original', 'mtime': '1591130231', 'size': '11', 'md5': 'c8dd6a11b9613d3ff04240fffa3e3c30', 'crc32': 'e99e8fda', 'sha1': '63f4001c22fbc493ec8294452a5e1566d0f2d5ab', 'format': 'Unknown'}),
#         (3, 'testfile', {'name': 'footest2/footest3/testfile', 'source': 'original', 'mtime': '1591130241', 'size': '520477', 'md5': '59fe680036dfc2cddf64865687fbb180', 'crc32': '5f138f18', 'sha1': 'b250a8c48ebdfbb349cc47e66f115db3a8fd3b85', 'format': 'Unknown'}),
#         (3, 'testfile.zip', {'name': 'footest2/footest3/testfile.zip', 'source': 'original', 'mtime': '1591130250', 'size': '520477', 'md5': '59fe680036dfc2cddf64865687fbb180', 'crc32': '5f138f18', 'sha1': 'b250a8c48ebdfbb349cc47e66f115db3a8fd3b85', 'format': 'Unknown'})
#     ],
# '''footest2
# â””â”€â”€â”¬ footest2
#    â””â”€â”€â”¬ footest3
#       â”œâ”€â”€â”€ somefile
#       â”œâ”€â”€â”€ somefile.txt
#       â”œâ”€â”€â”€ testfile
#       â””â”€â”€â”€ testfile.zip
# '''
# )

# list all items/identifiers of an account
iaa.list_items(
    credentials=(
        "email",
        "password"   
    )
)
# ['footest', 'fsk8f', ...]

# list all metadata fields of the identifier
iaa.metadata(
    identifier="footest"
)
# {'identifier': 'footest', 'mediatype': 'data', 'collection': 'opensource_media', 'description': 'footest', 'scanner': 'Internet Archive HTML5 Uploader 1.6.4', 'subject': 'footest', 'title': 'footest', 'uploader': '...', 'publicdate': '2020-01-09 11:02:29', 'addeddate': '2020-01-09 11:02:29', 'curation': '[curator]validator@archive.org[/curator][date]20200109110239[/date][comment]checked for malware[/comment]', 'noindex': 'true', ...}

# modify metadata field data
# some fields cannot be modified
# https://archive.org/services/docs/api/metadata-schema/index.html
# https://archive.org/services/docs/api/internetarchive/cli.html#modifying-metadata
iaa.metadata(
    identifier="footest",
    k="ka",
    v="vasasd" or "REMOVE_TAG"
)
# [Metadata] <footest> add ka: vasasd

# create a new item/identifier
iaa.new_identifier(
    identifier="test_item_69"
)
# this process takes some time to complete
# result:
# [Identifier] Created test_item_69 => https://archive.org/download/test_item_69

# rename a folder or a file
iaa.rename(
    identifier="footest",
    old_path="footest2/footest7" or "footest3.7z",
    new_path="footest2/footest69" or "footest69.7z"
)
# result:
# footest
# â”œâ”€â”€â”€ footest3.7z
# â””â”€â”€â”¬ footest2
#    â”œâ”€â”€â”€ somefile
#    â”œâ”€â”€â”€ somefile.txt
#    â”œâ”€â”€â”€ testfile
#    â””â”€â”€â”¬ footest69
#       â”œâ”€â”€â”€ somefile
#       â”œâ”€â”€â”€ somefile.txt
#       â”œâ”€â”€â”€ testfile
#       â””â”€â”€â”€ testfile.zip

# consider the following directory (D:\testing\footest):
# D:\testing\footest
# â””â”€â”€â”¬ footest2
#    â””â”€â”€â”¬ footest69
#       â””â”€â”€â”¬ new
#          â””â”€â”€â”€ somefile

# upload a folder or a file
# preserve folder structure of specified path
iaa.upload(
    identifier="footest",
    root=r"D:\testing\footest",
    path=r"footest2\footest69\new" or r"footest2\footest69\new\somefile" or ""
)
# result:
# footest
# â”œâ”€â”€â”€ footest3.7z
# â””â”€â”€â”¬ footest2
#    â”œâ”€â”€â”€ somefile
#    â”œâ”€â”€â”€ somefile.txt
#    â”œâ”€â”€â”€ testfile
#    â””â”€â”€â”¬ footest69
#       â”œâ”€â”€â”€ somefile
#       â”œâ”€â”€â”€ somefile.txt
#       â”œâ”€â”€â”€ testfile
#       â”œâ”€â”€â”€ testfile.zip
#       â””â”€â”€â”¬ new
#          â””â”€â”€â”€ somefile

# wait until the identifier is created
iaa.wait_until_identifier_created(
    identifier="some_identifier"
)

# example of uploading files to a new item/identifier
iaa = IA_Agent("...", "...")
new_identifier = "SYSTEM_DUMP_20200620"
iaa.new_identifier(new_identifier)
iaa.wait_until_identifier_created(new_identifier)
iaa.upload(new_identifier, r"C:\SYSTEM_DUMP_20200620", "")
```

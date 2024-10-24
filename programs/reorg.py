from tf.core.helpers import console
from tf.core.files import (
    dirContents,
    expanduser as ex,
    initTree,
    splitExt,
    fileCopy,
)


REPO_DIR = ex("~/github/HuygensING/translatin")
TRANS_DIR = f"{REPO_DIR}/datasource/transcriptions"
ORIG_DIR = f"{TRANS_DIR}/orig"
DOCX_DIR = f"{TRANS_DIR}/docx"

DS_STORE = ".DS_Store"


def reorg():
    authors = [x for x in dirContents(ORIG_DIR)[1] if x != DS_STORE]

    nWorks = 0
    notOk = 0
    skipped = 0

    operations = []

    for author in authors:
        titles = [x for x in dirContents(f"{ORIG_DIR}/{author}")[0] if x != DS_STORE]

        for title in titles:
            (title, ext) = splitExt(title)
            titleOk = True
            msg = []

            if ext != ".docx":
                msg.append(f"!{ext}")
                notOk += 1
                titleOk = False

            if title.startswith("~"):
                skipped += 1
                titleOk = False
                continue

            if len(msg) == 0:
                msg = "OK"
            else:
                msg = ", ".join(msg)

            if titleOk:
                operations.append((f"{author}/{title}{ext}", f"{author} - {title}{ext}"))

            console(f"\t{msg:<5} {author} - {title}")
            nWorks += 1

    console(f"{nWorks} works of {len(authors)} authors")

    if skipped:
        console(f"skipped {skipped} tilde files")
    else:
        console("No tilde files")

    if notOk:
        console(f"{notOk} not OK", error=True)
    else:
        console("All OK")

    if not notOk:
        console(f"Copying {len(operations)} items from {ORIG_DIR} to {DOCX_DIR}")

        initTree(DOCX_DIR, fresh=False)

        for (src, dst) in operations:
            fileCopy(f"{ORIG_DIR}/{src}", f"{DOCX_DIR}/{dst}")

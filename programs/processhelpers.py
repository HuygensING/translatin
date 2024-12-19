import re

from tf.core.files import expanduser
from tf.ner.helpers import toAscii

from workspecific import WorkSpecific

ORG = "HuygensING"
REPO = "translatin"
BACKEND = "github"

_REPODIR = expanduser(f"~/{BACKEND}/{ORG}/{REPO}")
_PROGRAMDIR = f"{_REPODIR}/programs"
_REPORTDIR = f"{_REPODIR}/report"
_NERDIR = f"{_REPODIR}/ner/specs"
_DATADIR = f"{_REPODIR}/datasource"
_TRANSDIR = f"{_DATADIR}/transcriptions"
_METADIR = f"{_DATADIR}/metadata"

METACSS = "meta.css"
METAOUTDIR = f"{_REPODIR}/static/both/metadata"
DOCXDIR = f"{_TRANSDIR}/docx"
MD_RAWDIR = f"{_TRANSDIR}/mdRaw"
MD_PRISDIR = f"{_TRANSDIR}/mdPristine"
MDDIR = f"{_TRANSDIR}/md"
TRANS_TXT = f"{_TRANSDIR}/translation.txt"
SOURCEBASE = _DATADIR
TEIDIR = f"{SOURCEBASE}/tei"
METADATA_YML = f"{_PROGRAMDIR}/metadata.yml"
METADATA_FILE = f"{_METADIR}/work-author.xlsx"

REPORT_TRANSDIR = f"{_REPORTDIR}/trans"
REPORT_LETTER_META = f"{REPORT_TRANSDIR}/lettermeta.yml"
REPORT_SECTIONS = f"{REPORT_TRANSDIR}/sections.yml"
REPORT_NONSECTIONS = f"{REPORT_TRANSDIR}/sections-non.yml"
REPORT_WARNINGS = f"{REPORT_TRANSDIR}/warnings.txt"
REPORT_INFO = f"{REPORT_TRANSDIR}/info.txt"

REPORT_TEIDIR = f"{_REPORTDIR}/tei"


APOS_RE = re.compile(r"""['‘]""")


def normalizeChars(text):
    text = text.replace("\u00a0", " ").replace("\u00ad", " ").replace("\ufffc", " ")
    return APOS_RE.sub("’", text)


FILENAME_RE = re.compile(r"""^(.*?)\s*-\s*(.*)$""")


def sanitizeFileName(fName):
    match = FILENAME_RE.match(fName)

    if not match:
        return None

    (auth, work) = match.group(1, 2)
    return toAscii(f"{auth}-{work}")


SECTION_LINE_RE = re.compile(
    r"""
    ^
    \s*
    <p>
    \s*
    /
    \s*
    (
        [a-z]+
    )
    \s*
    /
    \s*
    </p>
    \s*
    $
    """,
    re.M | re.X,
)

PARTS = """
    front
    main
    back
""".strip().split()

PARTSET = set(PARTS)

LINENUMBER_RE = re.compile(
    r"""
    ^
    (
        (?:
            (?:
                \w+\.
                |
                ,,
                |
                \*
            )
            \s*
        )?
    )
    \\?\(
    (
        [0-9]+
        [A-Za-z]?
    )
    \\?\)
    \s*
    (?=\S)
    """,
    re.M | re.X,
)

LINENUMBER_AFTER_RE = re.compile(
    r"""
    ^
    (.*)
    \s+
    \(
    (
        [0-9]+
        [A-Za-z]?
    )
    \)
    \s*
    $
    """,
    re.M | re.X,
)

LINENUMBER_BARE_RE = re.compile(
    r"""
    ^
    (
        .*
        [a-z]
        .*
    )
    \s+
    (
        [0-9]+
    )
    $
    """,
    re.M | re.X,
)

LINENUMBER_BARE_BEFORE_RE = re.compile(
    r"""
    ^
    (
        [0-9]+
    )
    \s+
    (
        .*
        [a-z]
        .*
    )
    $
    """,
    re.M | re.X,
)

SMALLCAPS_RE = re.compile(
    r"""
    (?<!\\)
    \[
        (
            (?:
                (?:\\[\[\]])
                |
                [^\]]+
            )++
        )
    \]
    \{\.smallcaps\}
    """,
    re.X | re.S,
)


def msgLine(work, ln, line, heading):
    workRep = "" if work is None else f"{work:<30}"
    lnRep = "" if ln is None else f"{ln:>5}"
    lineRep = "" if line is None else f" :: {line}"
    sep1 = ":" if workRep else ""
    headingRep = "" if heading is None else f"{heading:<30}"
    sep2 = " " if (workRep or lnRep) and (headingRep or lineRep) else ""

    return f"{workRep}{sep1}{lnRep}{sep2}{headingRep}{lineRep}\n"


def cleanup(text, workName):
    text = normalizeChars(text)

    text = text.replace("\\\n", "\n\n")
    text = text.replace("\n> ", "\n")
    text = SMALLCAPS_RE.sub(r"\1", text)

    workMethod = workName.replace("-", "_")

    method = getattr(WorkSpecific, workMethod, None)
    msg = "specific"

    if method is None:
        msg = "handled in a generic way"
        method = WorkSpecific.identity

    text = method(text)

    (pre, rest) = text.split("/front/", 1)
    (front, rest) = rest.split("/main/", 1)
    (main, back) = rest.split("/back/", 1)

    main = LINENUMBER_RE.sub(r"\1«\2» ", main)
    main = LINENUMBER_AFTER_RE.sub(r"«\2» \1\n", main)
    main = LINENUMBER_BARE_RE.sub(r"«\2» \1\n", main)
    main = LINENUMBER_BARE_BEFORE_RE.sub(r"«\1» \2", main)
    return (msg, f"{pre}/front/{front}/main/{main}/back/{back}")

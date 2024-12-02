import re

from tf.core.files import expanduser

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
TEIXDIR = f"{_TRANSDIR}/teiSimple"
TRANS_TXT = f"{_TRANSDIR}/translation.txt"
SOURCEBASE = _DATADIR
TEIDIR = f"{SOURCEBASE}/tei"
METADATA_YML = f"{_PROGRAMDIR}/metadata.yml"
METADATA_FILE = f"{_METADIR}/work-author.xlsx"

REPORT_TRANSDIR = f"{_REPORTDIR}/trans"
REPORT_LETTER_META = f"{REPORT_TRANSDIR}/lettermeta.yml"
REPORT_WARNINGS = f"{REPORT_TRANSDIR}/warnings.txt"

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
    return f"{auth}-{work}"


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
    """, re.M | re.X
)

PARTS = """
    front
    main
    back
""".strip().split()

PARTSET = set(PARTS)


def warnLine(work, ln, line, heading):
    workRep = "" if work is None else f"{work:<30}"
    lnRep = "" if ln is None else f"{ln:>5}"
    lineRep = "" if line is None else f" :: {line}"
    sep1 = ":" if workRep else ""
    headingRep = "" if heading is None else f"{heading:<30}"
    sep2 = " " if (workRep or lnRep) and (headingRep or lineRep) else ""

    return f"{workRep}{sep1}{lnRep}{sep2}{headingRep}{lineRep}\n"

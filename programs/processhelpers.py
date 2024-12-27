import re
from textwrap import TextWrapper

from tf.core.files import expanduser
from tf.ner.helpers import toAscii

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
MD_ORIGDIR = f"{_TRANSDIR}/mdOrig"
MD_FINALDIR = f"{_TRANSDIR}/mdRefined"
TEIXDIR = f"{_TRANSDIR}/teiSimple"
TRANS_TXT = f"{_TRANSDIR}/translation.txt"
SOURCEBASE = _DATADIR
TEIDIR = f"{SOURCEBASE}/tei"
METADATA_YML = f"{_PROGRAMDIR}/metadata.yml"
METADATA_FILE = f"{_METADIR}/work-author.xlsx"

REPORT_TRANSDIR = f"{_REPORTDIR}/trans"
REPORT_LETTER_META = f"{REPORT_TRANSDIR}/lettermeta.yml"
REPORT_LINES = f"{REPORT_TRANSDIR}/lines.yml"
REPORT_PAGES = f"{REPORT_TRANSDIR}/pages.yml"
REPORT_SECTIONS = f"{REPORT_TRANSDIR}/sections.yml"
REPORT_LINES_RAW = f"{REPORT_TRANSDIR}/lines_raw.yml"
REPORT_LINENUMBERS_RAW = f"{REPORT_TRANSDIR}/linenumbers_raw.yml"
REPORT_PAGES_RAW = f"{REPORT_TRANSDIR}/pages_raw.yml"
REPORT_SECTIONS_RAW = f"{REPORT_TRANSDIR}/sections_raw.yml"
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


def msgLine(work, ln, line, heading):
    workRep = "" if work is None else f"{work:<30}"
    lnRep = "" if ln is None else f"{ln:>5}"
    lineRep = "" if line is None else f" :: {line}"
    sep1 = ":" if workRep else ""
    headingRep = "" if heading is None else f"{heading:<30}"
    sep2 = " " if (workRep or lnRep) and (headingRep or lineRep) else ""

    return f"{workRep}{sep1}{lnRep}{sep2}{headingRep}{lineRep}\n"


Wrapper = TextWrapper(
    width=72,
    expand_tabs=False,
    tabsize=4,
    replace_whitespace=False,
    drop_whitespace=True,
    initial_indent="",
    subsequent_indent="",
    fix_sentence_endings=False,
    break_long_words=False,
    break_on_hyphens=False,
    max_lines=None,
)


def wrapParas(text):
    wrap = Wrapper.wrap

    return "\n\n".join(
        "\n".join(wrap(" ".join(para.split("\n")))) for para in text.split("\n\n")
    )


def unwrapParas(text):
    return "\n\n".join(" ".join(para.split("\n")) for para in text.split("\n\n"))

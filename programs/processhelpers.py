import re

from tf.core.files import expanduser

ORG = "HuygensING"
REPO = "translatin"
BACKEND = "github"

TRANSCRIBERS = "Jan Bloemendal et al."

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
METADATA_FILE = f"{_METADIR}/work-author.xlsx"

REPORT_TRANSDIR = f"{_REPORTDIR}/trans"
REPORT_LETTER_META = f"{REPORT_TRANSDIR}/lettermeta.yml"
REPORT_WARNINGS = f"{REPORT_TRANSDIR}/warnings.txt"


APOS_RE = re.compile(r"""['‘]""")


def normalizeChars(text):
    text = text.replace("\u00a0", " ").replace("\u00ad", " ").replace("\ufffc", " ")
    return APOS_RE.sub("’", text)


SECTION_LINE_RE = re.compile(r"""^\s*/\s*(front|main|back)\s*/\s*$""", re.M)

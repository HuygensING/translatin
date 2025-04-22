import re
from textwrap import TextWrapper

from tf.core.files import expanduser
from tf.ner.helpers import toAscii


def setVars(test=False):
    org = "HuygensING"
    repo = "translatin"
    backend = "github"

    repoDir = expanduser(f"~/{backend}/{org}/{repo}")
    configDir = f"{repoDir}/config"
    reportDir = f"{repoDir}/report"

    if test:
        reportDir += "Test"

    dataDir = f"{repoDir}/datasource"
    metaDir = f"{dataDir}/metadata"

    if test:
        metaDir += "Test"

    transDir = f"{dataDir}/transcriptions"

    if test:
        transDir += "Test"

    sourceBase = repoDir
    docXDir = f"{transDir}/docx"
    mdOrigDir = f"{transDir}/mdOrig"
    mdFinalDir = f"{transDir}/mdRefined"
    teiXDir = f"{transDir}/teiSimple"
    teiDir = f"{repoDir}/tei"

    if test:
        teiDir += "Test"

    metadataYml = f"{configDir}/metadata.yml"
    metadataFile = f"{metaDir}/drama-author.xlsx"

    reportTeiDir = f"{reportDir}/tei"
    reportTransDir = f"{reportDir}/trans"
    reportLines = f"{reportTransDir}/lines.yml"
    reportPages = f"{reportTransDir}/pages.yml"
    reportSections = f"{reportTransDir}/sections.yml"
    reportLinesRaw = f"{reportTransDir}/lines_raw.yml"
    reportLinenumbersRaw = f"{reportTransDir}/linenumbers_raw.yml"
    reportPagesRaw = f"{reportTransDir}/pages_raw.yml"
    reportSectionsRaw = f"{reportTransDir}/sections_raw.yml"
    reportWarnings = f"{reportTransDir}/warnings.txt"
    reportInfo = f"{reportTransDir}/info.txt"

    return dict(
        docXDir=docXDir,
        mdOrigDir=mdOrigDir,
        mdFinalDir=mdFinalDir,
        teiXDir=teiXDir,
        teiDir=teiDir,
        sourceBase=sourceBase,
        metadataYml=metadataYml,
        metadataFile=metadataFile,
        reportInfo=reportInfo,
        reportWarnings=reportWarnings,
        reportTeiDir=reportTeiDir,
        reportTransDir=reportTransDir,
        reportLines=reportLines,
        reportLinesRaw=reportLinesRaw,
        reportLinenumbersRaw=reportLinenumbersRaw,
        reportPages=reportPages,
        reportPagesRaw=reportPagesRaw,
        reportSections=reportSections,
        reportSectionsRaw=reportSectionsRaw,
    )


APOS_RE = re.compile(r"""['‘]""")


def normalizeChars(text):
    text = text.replace("\u00a0", " ").replace("\u00ad", " ").replace("\ufffc", " ")
    return APOS_RE.sub("’", text)


FILENAME_RE = re.compile(r"""^(.*?)\s*-\s*(.*)$""")


def sanitizeFileName(fName):
    match = FILENAME_RE.match(fName)

    if not match:
        return None

    (auth, drama) = match.group(1, 2)
    return toAscii(f"{auth}-{drama}")


def msgLine(drama, ln, line, heading):
    dramaRep = "" if drama is None else f"{drama:<30}"
    lnRep = "" if ln is None else f"{ln:>5}"
    lineRep = "" if line is None else f" :: {line}"
    sep1 = ":" if dramaRep else ""
    headingRep = "" if heading is None else f"{heading:<30}"
    sep2 = " " if (dramaRep or lnRep) and (headingRep or lineRep) else ""

    return f"{dramaRep}{sep1}{lnRep}{sep2}{headingRep}{lineRep}\n"


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

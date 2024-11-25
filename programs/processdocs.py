"""Convert DOCX to TEI

USAGE

Program

    from processdocs import TeiFromDocx

    TFD = TeiFromDocx(silent)
    TFD.task(task, task, task, ...)

Where task is:

*   `pandoc`: convert docx files to tei simple files
*   `tei`: convert tei simple files to proper tei files
*   `all`: perform the previous steps in that order

"""

import collections
from subprocess import run

from openpyxl import load_workbook

from tf.core.files import (
    dirContents,
    initTree,
    mTime,
    fileExists,
)
from tf.core.helpers import console, htmlEsc
from processhelpers import (
    TRANSCRIBERS,
    DOCXDIR,
    TEIXDIR,
    TEIDIR,
    METADATA_FILE,
    REPORT_WARNINGS,
    SECTION_LINE_RE,
    normalizeChars,
)


TITLE_SHORT = "title (short)"
TITLE_EXPANDED = "title (expanded)"
TITLE_FULL = "title (full)"
AUTHOR_ACRO = "author (acro)"
SOURCE = "source"
SOURCE_LINK = "source link"
DICTION = "prose/verse"
GENRE = "genre"
N_OF_ACTS = "#acts"
CHORUS = "chorus"
PUB_YEAR = "year of publication"
PUB_PLACE = "place of publication"
IS_MS = "Ms."
FIRST_EDITION_YEAR = "Firs Edition"

# parameters:
#
# filza
# letterno
# normalizedDate
# date
# settlement
# biblScope
# respName
# doc2stringNotesDiv
# doc2stringSecretarial
# doc2stringOriginal
# letter.querySelector('p:nth-of-type(4)').textContent

TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<?xml-model href="https://xmlschema.huygens.knaw.nl/suriano.rng" type="application/xml"  schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="https://xmlschema.huygens.knaw.nl/suriano.rng" type="application/xml"  schematypens="http://purl.oclc.org/dsdl/schematron"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader>
<fileDesc>
    <titleStmt>
        <title>{title}</title>
        <author>{author}</author>
        <editor xml:id="nl">Jan Bloemendal</editor>
        <respStmt>
            <resp>transcription</resp>
            <name>{respName}</name>
        </respStmt>
    </titleStmt>
    <publicationStmt>
        <publisher>{publisher}</publisher>
        <pubPlace>{placeOfPublication}</pubPlace>
        <date>{yearOfPublication}</date>
    </publicationStmt>
    <sourceDesc>
        <p>{ms}</p>
    </sourceDesc>
</fileDesc>
</teiHeader>
<text>
<body>
{material}
<div type="notes">
    {notes}
</div>
</body>
</text>
</TEI>
"""


class TeiFromDocx:
    def __init__(self, silent=False):
        self.warnings = []
        self.rhw = None

    def warn(self, filza, letter, textNum, ln, line, heading, summarize=False):
        rhw = self.rhw
        warnings = self.warnings

        warnings.append((filza, letter, textNum, ln, line, heading, summarize))

        if rhw:
            msg = f"{filza}:{letter} n.{textNum} ln {ln:>5} {heading} :: {line}"
            rhw.write(f"{msg}\n")

    def showWarnings(self):
        silent = self.silent
        warnings = self.warnings

        nWarnings = len(warnings)
        limit = 100

        summarized = collections.Counter()
        ln = 0

        for filza, letter, textNum, ln, line, heading, summarize in warnings:
            if summarize:
                summarized[heading] += 1
            else:
                if ln >= limit:
                    continue

                msg = f"{filza}:{letter} n.{textNum} ln {ln:>5} " f"{heading} :: {line}"
                self.console(msg, error=True)
                ln += 1

        nSummarized = len(summarized)

        if nSummarized:
            self.console("", error=True)

        for heading, n in sorted(summarized.items(), key=lambda x: (-x[1], x[0])):
            self.console(f"{n:>5} {'x':<6} {heading}. See warnings.txt", error=True)

        if silent:
            if nWarnings:
                console(f"\tThere were {nWarnings} warnings.", error=True)
        else:
            if nWarnings:
                self.console("", error=nWarnings > 0)
            console(f"{nWarnings} warnings", error=nWarnings > 0)

        warnings.clear()

    def readMetadata(self):
        if self.error:
            return

        console("Collecting excel metadata ...")

        try:
            wb = load_workbook(METADATA_FILE, data_only=True)
            ws = wb.active
        except Exception as e:
            console(f"\t{str(e)}", error=True)
            self.error = True
            return

        (headRow, *rows) = list(ws.rows)

        fields = {head.value: i for (i, head) in enumerate(headRow)}

        titleShortI = fields[TITLE_SHORT]
        titleExpandedI = fields[TITLE_EXPANDED]
        titleFullI = fields[TITLE_FULL]
        authorAcroI = fields[AUTHOR_ACRO]
        sourceI = fields[SOURCE]
        sourceLinkI = fields[SOURCE_LINK]
        dictionI = fields[DICTION]
        genreI = fields[GENRE]
        nOfActsI = fields[N_OF_ACTS]
        chorusI = fields[CHORUS]
        pubYearI = fields[PUB_YEAR]
        pubPlaceI = fields[PUB_PLACE]
        isMsI = fields[IS_MS]
        firstEditionYearI = fields[FIRST_EDITION_YEAR]

        rows = [
            (r + 1, row) for (r, row) in enumerate(rows) if any(c.value for c in row)
        ]

        information = {}
        self.extraLetterData = information

        def findex(row):
            return normalizeChars(f"{row[authorAcroI]} - {row[titleShortI]}") or ""

        def fi(row, index):
            return row[index].value or 0

        def fs(row, index):
            return htmlEsc(normalizeChars(row[index].value or ""))

        for r, row in rows:
            work = findex(row)
            titleShort = fs(row, titleShortI)
            titleExpanded = fs(row, titleExpandedI)
            titleFull = fs(row, titleFullI)
            authorAcro = fs(row, authorAcroI)
            source = fs(row, sourceI)
            sourceLink = fs(row, sourceLinkI)
            diction = fs(row, dictionI)
            genre = fs(row, genreI)
            nOfActs = fs(row, nOfActsI)
            chorus = fs(row, chorusI)
            pubYear = fs(row, pubYearI)
            pubPlace = fs(row, pubPlaceI)
            isMs = fs(row, isMsI)
            firstEditionYear = fs(row, firstEditionYearI)

            information[work] = dict(
                work=work,
                titleShort=titleShort,
                titleExpanded=titleExpanded,
                titleFull=titleFull,
                authorAcro=authorAcro,
                source=source,
                sourceLink=sourceLink,
                diction=diction,
                genre=genre,
                nOfActs=nOfActs,
                chorus=chorus,
                pubYear=pubYear,
                pubPlace=pubPlace,
                isMs=isMs,
                firstEditionYear=firstEditionYear,
            )

    def transformWork(self, file, work):
        if self.error:
            return

        extraLetterData = self.extraLetterData

        with open(f"{TEIXDIR}/{file}") as f:
            text = f.read()

        textLines = text.split("\n")
        newTextLines = []

        for i, line in enumerate(textLines):
            ln = i + 1
            ln

            line = line.replace("""rendition=""", """rend=""")
            line = line.replace("""rend="simple:""", '''rend="''')
            line = line.replace("""<hi rend="italic"><lb /></hi>""", "")

            match = SECTION_LINE_RE.match(line)

            if match:
                kind = match.group(1, 2)
                kind

            newTextLines.append(line)

        extraData = extraLetterData.get(work, [])

        if extraData is None:
            work = ("",)
            titleShort = ("",)
            titleExpanded = ("",)
            titleFull = ("",)
            authorAcro = ("",)
            source = ("",)
            sourceLink = ("",)
            diction = ("",)
            genre = ("",)
            nOfActs = ("",)
            chorus = ("",)
            pubYear = ("",)
            pubPlace = ("",)
            shelfmark = ("",)
        else:
            work = extraData[work]
            titleShort = extraData[titleShort]
            titleExpanded = extraData[titleExpanded]
            titleFull = extraData[titleFull]
            authorAcro = extraData[authorAcro]
            source = extraData[source]
            sourceLink = extraData[sourceLink]
            diction = extraData[diction]
            genre = extraData[genre]
            nOfActs = extraData[nOfActs]
            chorus = extraData[chorus]
            pubYear = extraData[pubYear]
            pubPlace = extraData[pubPlace]
            shelfmark = extraData[shelfmark]

        return TEMPLATE.format(
            work=work,
            respName=TRANSCRIBERS,
            work=work,
            titleShort=titleShort,
            titleExpanded=titleExpanded,
            titleFull=titleFull,
            authorAcro=authorAcro,
            source=source,
            sourceLink=sourceLink,
            diction=diction,
            genre=genre,
            nOfActs=nOfActs,
            chorus=chorus,
            pubYear=pubYear,
            pubPlace=pubPlace,
            shelfmark=shelfmark,
        )

    def teiFromDocx(self):
        if self.error:
            return

        console("DOCX => simple TEI per filza ...")

        files = sorted(
            x
            for x in dirContents(DOCXDIR)[0]
            if x.endswith(".docx") and not x.startswith("~")
        )
        initTree(TEIXDIR, fresh=False)

        for file in files:
            self.console(f"\t{file} ... ", newline=False)

            inFile = f"{DOCXDIR}/{file}"
            outFile = f"{TEIXDIR}/{file}".removesuffix(".docx") + ".xml"

            if fileExists(outFile) and mTime(outFile) > mTime(inFile):
                self.console("uptodate")
                continue

            run(
                [
                    "pandoc",
                    inFile,
                    "-f",
                    "docx",
                    "-t",
                    "tei",
                    "-s",
                    "-o",
                    outFile,
                ]
            )
            with open(outFile) as fh:
                text = normalizeChars(fh.read())

            with open(outFile, mode="w") as fh:
                fh.write(text)

            self.console("converted")

    def teiFromTei(self):
        if self.error:
            return

        self.warnings = []

        extraLog = {}
        self.extraLog = extraLog

        self.rhw = open(REPORT_WARNINGS, mode="w")

        console("simple TEI => enriched TEI ...")

        files = dirContents(TEIXDIR)[0]
        initTree(TEIDIR, fresh=True, gentle=True)

        for file in sorted(files):
            if not file.endswith(".xml"):
                continue

            self.console(f"\t{file}")

            workFile = file.removesuffix(".xml")
            initTree(f"{TEIDIR}/{workFile}", fresh=True, gentle=True)
            workText = self.transformWork(file, workFile)

            with open(f"{TEIDIR}/{workFile}.xml", "w") as f:
                f.write(workText)

        self.showWarnings()

        self.rhw.close()
        self.rhw = None

    def task(self, *args):
        if self.error:
            return

        tasks = dict(
            pandoc=False,
            tei=False,
        )

        good = True

        for arg in args:
            if arg in tasks:
                tasks[arg] = True
            elif arg == "all":
                for arg in tasks:
                    tasks[arg] = True
            else:
                console(f"Unrecognized task: {arg}", error=True)
                good = False

        if not good:
            console(f"Valid tasks are {' '.join(tasks)}", error=True)
            return

        if all(not do for do in tasks.values()):
            console("Nothing to do", error=True)
            return

        for task, do in tasks.items():
            if not do:
                continue

            if task == "pandoc":
                self.teiFromDocx()
            elif task == "tei":
                self.readMetadata()
                self.teiFromTei()

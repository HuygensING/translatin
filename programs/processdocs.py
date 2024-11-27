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

from tf.core.files import (
    dirContents,
    initTree,
    mTime,
    fileExists,
)
from tf.core.helpers import console

from processmeta import Meta as MetaCls
from processhelpers import (
    DOCXDIR,
    TEIXDIR,
    TEIDIR,
    REPORT_TRANSDIR,
    REPORT_WARNINGS,
    SECTION_LINE_RE,
    PARTSET,
    normalizeChars,
)


class TeiFromDocx:
    def __init__(self, silent=False):
        self.silent = silent
        self.error = False

        initTree(REPORT_TRANSDIR, fresh=False)

        self.warnings = []
        self.rhw = None

    def console(self, *args, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        When the silent member of the object is True, the message will be suppressed.
        """
        silent = self.silent

        if not silent:
            console(*args, **kwargs)

    def warn(self, work, ln, line, heading, summarize=False):
        rhw = self.rhw
        warnings = self.warnings

        warnings.append((work, ln, line, heading, summarize))

        if rhw:
            msg = f"{work:<30}: ln {ln:>5} {heading:<30} :: {line}"
            rhw.write(f"{msg}\n")

    def showWarnings(self):
        silent = self.silent
        warnings = self.warnings

        nWarnings = len(warnings)
        limit = 100

        summarized = collections.Counter()
        i = 0

        for work, ln, line, heading, summarize in warnings:
            if summarize:
                summarized[heading] += 1
            else:
                if i >= limit:
                    continue

                msg = f"{work:<30}: ln {ln:>5} {heading:<30} :: {line}"
                self.console(msg, error=True)
                i += 1

        nSummarized = len(summarized)

        if nSummarized:
            self.console("", error=True)

            for heading, n in sorted(summarized.items(), key=lambda x: (-x[1], x[0])):
                self.console(f"{n:>5} {'x':<6} {heading}", error=True)

            self.console("See warnings.txt", error=True)

        if silent:
            if nWarnings:
                console(f"\tThere were {nWarnings} warnings.", error=True)
        else:
            if nWarnings:
                self.console("", error=nWarnings > 0)
            console(f"{nWarnings} warnings", error=nWarnings > 0)

        warnings.clear()

    def transformWork(self, file, workName):
        if self.error:
            return

        Meta = self.Meta

        if Meta.error:
            return

        with open(f"{TEIXDIR}/{file}") as f:
            text = f.read()

        textLines = text.split("\n")

        newTextLines = dict(
            front=[],
            main=[],
            back=[],
        )
        dest = None

        for i, line in enumerate(textLines):
            ln = i + 1

            match = SECTION_LINE_RE.match(line)

            if match:
                part = match.group(1)

                if part not in PARTSET:
                    self.warn(workName, ln, line, f"/{part}/ not recognized")
                    continue

                if dest is None:
                    if part != "front":
                        heading = "Missing /front/"

                        if part == "back":
                            heading += " and /main/"

                        self.warn(workName, ln, line, heading)

                elif (
                    (dest == "front" and part != "main")
                    or (dest == "main" and part != "back")
                    or dest == "back"
                ):
                    self.warn(workName, ln, line, f"{part} part after main part")

                dest = part
                continue

            line = line.replace("""rendition=""", """rend=""")
            line = line.replace("""rend="simple:""", '''rend="''')
            line = line.replace("""<hi rend="italic"><lb /></hi>""", "")

            if dest is not None:
                newTextLines[dest].append(line)

        material = {part: "\n".join(newTextLines[part]) for part in PARTSET}

        return Meta.fillTemplate(workName, **material)

    def teiFromDocx(self):
        if self.error:
            return

        console("DOCX => simple TEI per work ...")

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

        Meta = MetaCls()
        self.Meta = Meta
        Meta.readMetadata()

        files = dirContents(TEIXDIR)[0]
        initTree(TEIDIR, fresh=True, gentle=True)

        for file in sorted(files):
            if not file.endswith(".xml"):
                continue

            self.console(f"\t{file}")

            workName = file.removesuffix(".xml")
            workText = self.transformWork(file, workName)

            with open(f"{TEIDIR}/{workName}.xml", "w") as f:
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
                self.teiFromTei()

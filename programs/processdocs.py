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
    REPORT_INFO,
    SECTION_LINE_RE,
    PARTSET,
    normalizeChars,
    msgLine,
    sanitizeFileName,
)

SPECIAL_REPLACEMENTS = (
    ("""<formula notation="TeX">ë</formula>""", """ë"""),
    ("""<formula notation="TeX">î</formula>""", """î"""),
    ("""<formula notation="TeX">˂</formula>""", ""),
)


class TeiFromDocx:
    def __init__(self, silent=False):
        self.silent = silent
        self.error = False

        initTree(REPORT_TRANSDIR, fresh=False)

        self.warnings = []
        self.info = []
        self.rhw = None
        self.rhi = None

        self.Meta = MetaCls(self)

        self.getInventory()

    def console(self, *args, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        When the silent member of the object is True, the message will be suppressed.
        """
        silent = self.silent

        if not silent:
            console(*args, **kwargs)

    def warn(
        self, work=None, ln=None, line=None, heading=None, summarize=False, serious=True
    ):
        rh = self.rhw if serious else self.rhi
        warnings = self.warnings if serious else self.info

        warnings.append((work, ln, line, heading, summarize))

        if rh:
            rh.write(msgLine(work, ln, line, heading))

    def showWarnings(self, serious=True):
        silent = self.silent
        warnings = self.warnings if serious else self.info

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

                self.console(msgLine(work, ln, line, heading), error=serious)
                i += 1

        nSummarized = len(summarized)

        if nSummarized:
            self.console("", error=serious)

            for heading, n in sorted(summarized.items(), key=lambda x: (-x[1], x[0])):
                self.console(f"{n:>5} {'x':<6} {heading}", error=serious)

            wFile = REPORT_WARNINGS if serious else REPORT_INFO
            self.console(f"See {wFile}", error=serious)

        if silent:
            if nWarnings:
                console(f"\tThere were {nWarnings} warnings.", error=serious)
        else:
            if nWarnings:
                self.console("", error=serious)
            label = "warning" if serious else "informational message"
            plural = "" if nWarnings == 1 else "s"
            console(f"{nWarnings} {label}{plural}", error=serious and nWarnings > 0)

        warnings.clear()

    def getInventory(self):
        Meta = self.Meta

        workFiles = {}
        self.workFiles = workFiles

        console("GET docx files and their metadata from XLS ...")

        files = sorted(
            x
            for x in dirContents(DOCXDIR)[0]
            if x.endswith(".docx") and not x.startswith("~")
        )

        for file in files:
            workName = file.removesuffix(".docx")
            saneWorkName = sanitizeFileName(workName)

            if saneWorkName is None:
                self.warn(work=workName, heading="Not a valid work name")
                continue

            workFiles[saneWorkName] = workName

        console("")

        goodWorkFiles = Meta.readMetadata(workFiles)
        console(
            f"Continuing with {len(goodWorkFiles)} good files "
            f"among {len(workFiles)} in total"
        )
        self.workFiles = goodWorkFiles

    def transformWork(self, workName):
        if self.error:
            return (False, None, None)

        Meta = self.Meta

        if Meta.error:
            return (False, None, None)

        with open(f"{TEIXDIR}/{workName}.xml") as f:
            text = f.read()

        replacementLog = self.replacementLog

        for orig, repl in SPECIAL_REPLACEMENTS:
            n = text.count(orig)

            replRep = f"«{orig} → {repl}»"

            if n != 0:
                text = text.replace(orig, repl)

            replacementLog[replRep] += n

        textLines = text.split("\n")

        newTextLines = dict(
            front=[],
            main=[],
            back=[],
        )
        dest = None
        skipping = True

        partsEncountered = []
        mainEncountered = False
        partsError = False

        for i, line in enumerate(textLines):
            if skipping:
                if line.startswith("<body>"):
                    skipping = False

                continue
            else:
                if line.startswith("</body>"):
                    skipping = True
                    continue

            match = SECTION_LINE_RE.match(line)

            if match:
                part = match.group(1)
                partsEncountered.append(part)

                if part not in PARTSET:
                    partsError = True
                    continue

                if (dest is not None) and (
                    (dest == "front" and part != "main")
                    or (dest == "main" and part != "back")
                    or dest == "back"
                ):
                    partsError = True

                if part == "main":
                    mainEncountered = True

                dest = part
                continue

            line = line.replace("""rendition=""", """rend=""")
            line = line.replace("""rend="simple:""", '''rend="''')
            line = line.replace("""<hi rend="italic"><lb /></hi>""", "")

            if dest is not None:
                newTextLines[dest].append(line)

        material = {
            part: "\n".join(newTextLines[part]) or "<p></p>" for part in PARTSET
        }

        text = Meta.fillTemplate(workName, **material)

        partsMsg = f"{'-'.join(partsEncountered)}"

        if not mainEncountered:
            partsError = True
            sep = " " if partsMsg else ""
            partsMsg = f"NO main PART{sep}{partsMsg}"

        if partsError:
            self.warn(work=workName, heading=partsMsg)

        return (not partsError, partsMsg, text)

    def teiFromDocx(self):
        if self.error:
            return

        console("DOCX => simple TEI per work ...")

        workFiles = self.workFiles

        initTree(TEIXDIR, fresh=False)

        for file in sorted(workFiles):
            realFile = workFiles[file]

            inFile = f"{DOCXDIR}/{realFile}.docx"
            outFile = f"{TEIXDIR}/{file}.xml"

            if fileExists(outFile) and mTime(outFile) > mTime(inFile):
                # self.console(f"\t{file} :  uptodate")
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

            self.console(f"\t{file} : converted")

        self.console(f"{len(workFiles)} files done.")

    def teiFromTei(self):
        if self.error:
            return

        self.warnings = []

        extraLog = {}
        self.extraLog = extraLog

        replacementLog = collections.Counter()
        self.replacementLog = replacementLog

        self.rhw = open(REPORT_WARNINGS, mode="w")
        self.rhi = open(REPORT_INFO, mode="w")

        console("simple TEI => enriched TEI ...")

        initTree(TEIDIR, fresh=True, gentle=True)
        workFiles = self.workFiles

        for workName in sorted(workFiles):
            (workStatus, workMsg, workText) = self.transformWork(workName)

            with open(f"{TEIDIR}/{workName}.xml", "w") as f:
                f.write(workText)

            console(f"\t{workName:<30} ... {workMsg}", error=not workStatus)

        for replRep, n in sorted(replacementLog.items()):
            self.warn(
                line=f"{replRep} {n} x applied",
                heading="special replacement",
                summarize=True,
                serious=n == 0,
            )

        self.showWarnings(serious=False)
        self.showWarnings()

        self.rhw.close()
        self.rhw = None
        self.rhi.close()
        self.rhi = None

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

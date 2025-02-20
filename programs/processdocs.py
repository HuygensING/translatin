"""Convert DOCX to TEI

USAGE

Program

    from processdocs import TeiFromDocx

    TFD = TeiFromDocx(silent)
    TFD.task(task, task, task, ...)

Where task is:

*   `convert`: convert docx files to tei files
*   `all`: perform the previous steps in that order

"""

import re
import collections
from subprocess import run

from tf.core.files import (
    dirContents,
    initTree,
    mTime,
    fileExists,
    readYaml,
    writeYaml,
)
from tf.core.helpers import console

from processmeta import Meta as MetaCls
from processhelpers import (
    DOCXDIR,
    MD_ORIGDIR,
    MD_FINALDIR,
    TEIXDIR,
    TEIDIR,
    REPORT_TRANSDIR,
    REPORT_WARNINGS,
    REPORT_INFO,
    REPORT_LINES,
    REPORT_PAGES,
    REPORT_SECTIONS,
    REPORT_LINES_RAW,
    REPORT_LINENUMBERS_RAW,
    REPORT_PAGES_RAW,
    REPORT_SECTIONS_RAW,
    msgLine,
    sanitizeFileName,
    normalizeChars,
    wrapParas,
)

from dramaspecific import DramaSpecific

SECTIONTRIGGER_RE = re.compile(
    r"""
    (?<=\n\n)
    (?:
        \\<
        |
        \*\*
    )?
    [\ ]?
    (
        (?:
            (?:
                ≤
                (?: page | folio | line )
                =
                [^≥]+
                ≥
                [\ ]?
            )
            |
            (?:
                \[\^
                [0-9]+
                \]
            )
        )*+
    )
    \**
    (\w+)
    \**
    (
        [.,:]?
        (?:
            [\ ]?
            [.,:]?
            (\w+)
        )?
        [.,:]?
        ([^\n]*?)
    )
    (?:
        \\>
        |
        \*\*
    )?
    (?=\n\n)
""",
    re.S | re.X,
)

SECTIONTRIGGER_SND_RE = re.compile(
    r"""
    ^
    [.,;]?
    [\ ]?
    [.,;]?
    \**
    (\w+)
    \**
    [.,;]?
    [\ ]
    [.,;]?
    (\w+)
    [.,;]?
    [^\n]*
    $
""",
    re.X,
)

SNUM_RE = re.compile(
    r"""
    ^
    (?:
        [ivxvl0-9]+
        | prim[a-z]+
        | sec[uv]nd[a-z]+
        | tert(?:i[a-z]+)?
        | q[uv]art(?:[a-z]+)?
        | q[uv]int[a-z]+
        | sext[a-z]+
        | septim[a-z]+
        | octav[a-z]+
        | non[a-z]+
        | decim[a-z]+
        | [uv]ndecim[a-z]+
        | d[uv]odecim[a-z]+
        | decima\ terti[a-z]+
        | decima\ quart[a-z]+
        | decima\ q[uv]int[a-z]+
    )
    $
    """,
    re.X | re.I,
)


# 1: is section (or caption)
# 2: needs a number indication
# 3: needs a trigger as next word

SECTION_TRIGGERS_DEF = dict(
    actores=(True, False, False, "actores"),
    actorum=(True, False, False, "actorum"),
    actus=(True, True, False, "actus"),
    act=(True, True, False, "actus"),
    argumentum=(True, False, False, "argumentum"),
    chori=(False, False, False, "chorus"),
    chorus=(False, False, False, "chorus"),
    chor=(False, False, False, "chorus"),
    ch=(False, False, False, "chorus"),
    codices=(False, False, False, "codices"),
    comoedia=(False, False, False, "comoedia"),
    comoediae=(True, False, True, "$1"),
    conclusio=(True, False, False, "conclusio"),
    dramatis=(True, False, False, "dramatis"),
    epitasis=(False, False, False, "epitasis"),
    epilogus=(True, False, False, "epilogus"),
    errata=(True, False, False, "errata"),
    finis=(False, False, False, "finis"),
    incipit=(True, False, False, "incipit"),
    interlocutores=(True, False, False, "interlocutores"),
    interloquutores=(True, False, False, "interlocutores"),
    ludionum=(False, False, False, "ludionum"),
    pars=(True, True, False, "pars"),
    peroratio=(True, False, False, "peroratio"),
    personae=(True, False, False, "personae"),
    periocha=(True, False, False, "periocha"),
    prologus=(True, False, False, "prologus"),
    protasis=(False, False, False, "protasis"),
    scaena=(True, True, False, "scena"),
    scaenae=(True, True, False, "scena"),
    scena=(True, True, False, "scena"),
    strophe=(False, False, False, "strophe"),
    tragoediae=(True, False, True, "$1"),
    tragoidia=(False, False, False, "tragoedia"),
    prima=(True, False, True, "prima"),
    secunda=(True, False, True, "secunda"),
    tertia=(True, False, True, "tertia"),
    quarta=(True, False, True, "quarta"),
    quinta=(True, False, True, "quinta"),
    sexta=(True, False, True, "sexta"),
)

SECTION_NEEDS_UPPER = {"errata"}

SECTION_TRIGGERS_PROTO = SECTION_TRIGGERS_DEF | {
    k.replace("u", "v"): v for (k, v) in SECTION_TRIGGERS_DEF.items()
}

SECTION_TRIGGERS = {k: v[-1] for (k, v) in SECTION_TRIGGERS_PROTO.items()}
SECTION_TRIGGERS_SEC = {k: v[0] for (k, v) in SECTION_TRIGGERS_PROTO.items()}
SECTION_TRIGGERS_NUM = {k: v[1] for (k, v) in SECTION_TRIGGERS_PROTO.items()}
SECTION_TRIGGERS_TRIG = {k: v[2] for (k, v) in SECTION_TRIGGERS_PROTO.items()}

LINENUMBER_ALONE_RE = re.compile(
    r"""
    (?<=\n\n)
    ([0-9]+)
    (?=\n\n)
    """,
    re.X
)
LINENUMBER_BEFORE_RE = re.compile(
    r"""
    ^
    (
        (?:
            (?:
                \w+[.,;]
                |
                ,,
                |
                \*
            )
            [\ ]?
        )?
    )
    \\?[(\[]
    (
        [0-9]+
        [A-Za-z]?
    )
    \\?[)\]]
    [\ ]?
    (?=
        .*
        [A-Za-z]
        .*
    )
    """,
    re.M | re.X,
)

LINENUMBER_AFTER_RE = re.compile(
    r"""
    ^
    (
        .*
        [a-z]
        .*
    )
    [\ ]
    \(
    (
        [0-9]+
        [A-Za-z]?
    )
    \)
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
    [\ ]
    (
        .*
        [a-z]
        .*
    )
    $
    """,
    re.M | re.X,
)

LINENUMBER_DASH_BEFORE_RE = re.compile(
    r"""
    ^
    (
        [0-9]+
    )
    -
    [\ ]
    (
        .*
        [a-z]
        .*
    )
    $
    """,
    re.M | re.X,
)

LINENUMBER_BARE_AFTER_RE = re.compile(
    r"""
    ^
    (
        .*
        [a-z]
        .*
    )
    [\ ]
    (
        [0-9]+
    )
    $
    """,
    re.M | re.X,
)

NUM_RE = re.compile(r"[≤≥]")
LNUM_RE = re.compile(r"""≤line=([^≥]+)≥""")
FNUM_RE = re.compile(r"""≤folio=([^≥]+)≥""")
PNUM_RE = re.compile(
    r"""
    ≤page=
    (
        [^|≥]+?
    )
    (?:
        \|
        (
            [^≥]*
        )
    )?
    ≥
    """,
    re.X,
)


def pNumRepl(match):
    (num, src) = match.group(1, 2)

    sourceAtt = f''' source="{src}"''' if src else ""
    return f"""<milestone unit="page" facs="{num}"{sourceAtt}/>"""


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

NOTE_RE = re.compile(
    r"""
    <note>(.*?)</note>
    """,
    re.X | re.S,
)

FIX_ITALIC_RE = re.compile(
    r"""
    \n
    \*
    ([^\n]+?)
    (\\?)
    \n
    \*
    """,
    re.X | re.S,
)

SPLIT_PARA_RE = re.compile(r"(?<=[^\n\\])\n(?=[^\n])")


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

        self.showWarnings(serious=False)
        self.showWarnings()

    def console(self, *args, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        When the silent member of the object is True, the message will be suppressed.
        """
        silent = self.silent

        if not silent:
            console(*args, **kwargs)

    def warn(
        self, drama=None, ln=None, line=None, heading=None, summarize=False, serious=True
    ):
        rh = self.rhw if serious else self.rhi
        warnings = self.warnings if serious else self.info

        warnings.append((drama, ln, line, heading, summarize))

        if rh:
            rh.write(msgLine(drama, ln, line, heading))

    def showWarnings(self, serious=True):
        silent = self.silent
        warnings = self.warnings if serious else self.info

        nWarnings = len(warnings)
        limit = 100

        summarized = collections.Counter()
        i = 0

        for drama, ln, line, heading, summarize in warnings:
            if summarize:
                summarized[heading] += 1
            else:
                if i >= limit:
                    continue

                self.console(msgLine(drama, ln, line, heading), error=serious)
                i += 1

        nSummarized = len(summarized)

        if nSummarized:
            self.console("", error=serious)

            for heading, n in sorted(summarized.items(), key=lambda x: (-x[1], x[0])):
                self.console(f"{n:>5} {'x':<6} {heading}", error=serious)

            if hasattr(self, "rhw"):
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

        dramaFiles = {}
        self.dramaFiles = dramaFiles

        console("GET docx files and their metadata from XLS ...")

        files = sorted(
            x
            for x in dirContents(DOCXDIR)[0]
            if x.endswith(".docx") and not x.startswith("~")
        )

        for file in files:
            dramaName = file.removesuffix(".docx")
            saneDramaName = sanitizeFileName(dramaName)

            if saneDramaName is None:
                self.warn(drama=dramaName, heading="Not a valid drama name")
                continue

            dramaFiles[saneDramaName] = dramaName

        console("")

        goodDramaFiles = Meta.readMetadata(dramaFiles)
        console(
            f"Continuing with {len(goodDramaFiles)} good files "
            f"among {len(dramaFiles)} in total"
        )
        self.dramaFiles = goodDramaFiles

    def makeLineNumRepl(self, dramaName):
        lineNumbers = []
        self.lineNumbers[dramaName] = lineNumbers

        def replAlone(match):
            lNum = match.group(1)
            start = match.start()
            lineNumbers.append([start, lNum])
            return f"≤line={lNum}≥"

        def replGeneric(pos, result):
            def repl(match):
                lNum = match.group(pos)
                start = match.start()
                lineNumbers.append([start, lNum])
                return result.format(a=match.group(1), b=match.group(2))

            return repl

        self.lnumReplAlone = replAlone
        self.lnumReplBefore = replGeneric(2, "{a}≤line={b}≥ ")
        self.lnumReplAfter = replGeneric(2, "≤line={b}≥ {a}")
        self.lnumReplBareAfter = replGeneric(2, "≤line={b}≥ {a}")
        self.lnumReplBareBefore = replGeneric(1, "≤line={a}≥ {b}")

    def makeSectionTriggerRepl(self, dramaName):
        sections = self.sections[dramaName]

        def repl(match):
            (pre, trigger, post, number, after) = match.group(1, 2, 3, 4, 5)
            start = match.start()
            triggerL = trigger.lower()
            triggerN = None
            number = number or ""

            if triggerL in SECTION_TRIGGERS:
                if trigger in SECTION_NEEDS_UPPER and trigger == triggerL:
                    makeSection = False
                elif len(post.replace(".", "").split()) > 6:
                    makeSection = False
                elif SECTION_TRIGGERS_TRIG[triggerL]:
                    nextWord = post.split()[0].rstrip(".") if post else ""
                    nextWordL = nextWord.lower()
                    triggerN = SECTION_TRIGGERS.get(nextWordL, None)
                    number = ""
                    makeSection = triggerN is not None
                elif SECTION_TRIGGERS_NUM[triggerL]:
                    makeSection = SNUM_RE.match(number)
                else:
                    makeSection = True
            else:
                makeSection = False

            if makeSection:
                isSection = SECTION_TRIGGERS_SEC[triggerN or triggerL]
                sigil = "§" if isSection else "±"

                extraTerm = "Residuum "
                hasExtraTerm = False

                if extraTerm in after:
                    after = after.replace(extraTerm, "")
                    hasExtraTerm = True

                matchSub = SECTIONTRIGGER_SND_RE.match(after)

                triggerSub = ""
                numberSub = ""

                if matchSub:
                    (tSub, nSub) = matchSub.group(1, 2)
                    triggerSubL = tSub.lower()

                    if triggerSubL in SECTION_TRIGGERS:
                        triggerSub = f"-{SECTION_TRIGGERS[triggerSubL]}"

                        numberSub = f"-{nSub.lower()}"

                        if hasExtraTerm:
                            numberSub += f"({extraTerm.strip()})"

                if triggerN is None:
                    triggerN = f"{sigil}{SECTION_TRIGGERS[triggerL]}{triggerSub}"

                number = f"{number.lower()}{numberSub}"
                sections.append([start, triggerN, number])
                secNum = len(sections)
                secHead = f"{pre}{trigger}{post}".strip()
                replacement = (
                    f"# {secNum}. {secHead}"
                    if isSection
                    else f"**{secHead}**"
                )
            else:
                replacement = match.group(0)

            return replacement

        self.sectionRepl = repl

    def makeNoteRepl(self, dramaName):
        notes = []
        self.notes = notes
        self.noteMark = 0

        def repl(match):
            self.noteMark += 1
            noteMark = self.noteMark
            note = (
                match.group(1).strip().removeprefix("<p>").removesuffix("</p>").strip()
            )

            footNote = (
                f"""<note xml:id="tn{noteMark}">"""
                f"""<p><hi rend="footnote">{noteMark}</hi> """
                f"""{note}</p></note>"""
            )
            notes.append(footNote)
            return f"""<ptr target="#tn{noteMark}" n="{noteMark}"/>"""

        return repl

    def cleanup(self, text, dramaName):
        lines = self.lines
        specific = self.specific

        self.sections[dramaName] = []

        specific.makePageRepl(dramaName)

        # only to check whether there are unwrapped paragraphs
        # n = len(SPLIT_PARA_RE.findall(text))
        # return (f"{n}", text)

        text = normalizeChars(text)

        text = FIX_ITALIC_RE.sub(r"\n*\1*\2\n", text)
        text = text.replace("\\\n", "\n\n")
        text = text.replace("\n> ", "\n")
        text = text.replace("\n>\n", "\n\n")
        text = text.replace("$", "")
        text = SMALLCAPS_RE.sub(r"\1", text)

        dramaMethod = dramaName.replace("-", "_")

        method = getattr(specific, dramaMethod, None)
        msg = "special  "

        if method is None:
            msg = "         "
            method = getattr(specific, "identity")
        elif method == "generic":
            msg = "generic  "
            method = getattr(specific, "identity")

        text = method(text)
        rest = text
        textParts = {}

        kinds = ("/front/", "/main/", "/back/")

        for i, kind in enumerate(kinds):
            parts = rest.split(kind, 1)

            if len(parts) == 1:
                self.warn(drama=dramaName, heading=f"No {kind}")
                pre = ""
                rest = parts[0]
            else:
                pre, rest = parts

            if i > 0:
                textParts[kinds[i - 1]] = pre

        textParts[kinds[-1]] = parts[1]

        front = textParts["/front/"]
        main = textParts["/main/"]
        back = textParts["/back/"]

        self.makeLineNumRepl(dramaName)
        main = LINENUMBER_ALONE_RE.sub(self.lnumReplAlone, main)
        main = LINENUMBER_BEFORE_RE.sub(self.lnumReplBefore, main)
        main = LINENUMBER_AFTER_RE.sub(self.lnumReplAfter, main)
        main = LINENUMBER_BARE_AFTER_RE.sub(self.lnumReplBareAfter, main)
        main = LINENUMBER_BARE_BEFORE_RE.sub(self.lnumReplBareBefore, main)
        main = LINENUMBER_DASH_BEFORE_RE.sub(self.lnumReplBareBefore, main)

        self.makeSectionTriggerRepl(dramaName)
        main = SECTIONTRIGGER_RE.sub(self.sectionRepl, main)
        main = main.replace("qqq", "")

        lines[dramaName] = int(
            round(front.count("\n") + main.count("\n") + back.count("\n"))
        )

        text = f"# Front\n\n/{front}\n\n# Main\n\n{main}\n\n# Back\n\n{back}\n"
        text = wrapParas(text)
        return (msg, text)

    def transformDrama(self, dramaName):
        if self.error:
            return (False, None, None)

        Meta = self.Meta

        if Meta.error:
            return (False, None, None)

        with open(f"{TEIXDIR}/{dramaName}.xml") as f:
            text = f.read()

        textLines = text.split("\n")
        newTextLines = []

        skipping = True

        for i, line in enumerate(textLines):
            if skipping:
                if line.startswith("<body>"):
                    skipping = False

                continue
            else:
                if line.startswith("</body>"):
                    skipping = True
                    continue

            line = line.replace("""rendition=""", """rend=""")
            line = line.replace("""rend="simple:""", '''rend="''')
            line = LNUM_RE.sub(r"(\1)", line)
            line = PNUM_RE.sub(pNumRepl, line)
            line = FNUM_RE.sub(r"""<milestone unit="folio" facs="\1"/>""", line)

            newTextLines.append(line)

        material = "\n".join(newTextLines)

        leftovers = NUM_RE.findall(material)
        n = len(leftovers)

        if n:
            self.warn(drama=dramaName, heading=f"number leftovers: {n} x")

        repl = self.makeNoteRepl(dramaName)
        material = NOTE_RE.sub(repl, material)

        notes = "\n".join(self.notes)
        notes = f"""\n<div type="notes">{notes}</div>\n""" if notes.strip() else ""
        text = Meta.fillTemplate(dramaName, text=material, notes=notes)

        return (True, "", text)

    def convert(
        self,
        forceDocx=False,
        forceClean=False,
        forceTeix=False,
        forceTei=False,
        skipDocx=False,
        skipClean=False,
        skipTeix=False,
        skipTei=False,
        dramaName=None,
    ):
        if self.error:
            return

        self.warnings = []
        extraLog = {}
        self.extraLog = extraLog
        self.specific = DramaSpecific(self)

        self.rhw = open(REPORT_WARNINGS, mode="w")
        self.rhi = open(REPORT_INFO, mode="w")

        cleanDone = False

        console("DOCX => Markdown per drama ...")
        console(
            f"\t   {'drama':30} | "
            f"{'lines':>7} | {'lnums':>5} | {'pages':>5} | {'folios':>5}| "
            f"{'sect':>4} | "
            f"conversion steps"
        )

        dramaFiles = self.dramaFiles

        initTree(MD_ORIGDIR, fresh=False)
        initTree(MD_FINALDIR, fresh=False)
        initTree(TEIXDIR, fresh=False)
        initTree(TEIDIR, fresh=True, gentle=True)

        lines = readYaml(asFile=REPORT_LINES_RAW, plain=True)
        lineNumbers = readYaml(asFile=REPORT_LINENUMBERS_RAW, plain=True)
        pages = readYaml(asFile=REPORT_PAGES_RAW, plain=True)
        sections = readYaml(asFile=REPORT_SECTIONS_RAW, plain=True)

        self.lines = lines
        self.lineNumbers = lineNumbers
        self.pages = pages
        self.sections = sections

        nDramas = 0
        allOK = True
        someOK = False
        specNone = 0
        totLines = 0
        totLineNumbers = 0
        totPages = 0
        totFolios = 0
        totSections = 0

        for file in sorted(dramaFiles):
            if dramaName is not None and file != dramaName:
                continue

            nDramas += 1
            realFile = dramaFiles[file]

            inFile = f"{DOCXDIR}/{realFile}.docx"
            rawFile = f"{MD_ORIGDIR}/{file}.md"
            cleanFile = f"{MD_FINALDIR}/{file}.md"
            teixFile = f"{TEIXDIR}/{file}.xml"
            teiFile = f"{TEIDIR}/{file}.xml"

            rawUptodate = fileExists(rawFile) and mTime(rawFile) > mTime(inFile)

            convMessage = []
            thisOK = True
            extraMsg = ""

            if not skipDocx and (forceDocx or not rawUptodate):
                run(
                    [
                        "pandoc",
                        inFile,
                        "--from=docx",
                        "--to=markdown",
                        "--wrap=none",
                        "--standalone",
                        f"--output={rawFile}",
                    ]
                )
                convMessage.append("docx")

            cleanUptodate = fileExists(cleanFile) and mTime(cleanFile) > mTime(rawFile)

            if not skipClean and (forceClean or not cleanUptodate):
                with open(rawFile) as fh:
                    msg, text = self.cleanup(fh.read(), file)

                    if not msg.strip():
                        specNone += 1

                with open(cleanFile, mode="w") as fh:
                    fh.write(text)

                convMessage.extend(["clean", msg])
                cleanDone = True
            else:
                cleanDone = False

            teixUptodate = fileExists(teixFile) and mTime(teixFile) > mTime(cleanFile)

            if not skipTeix and (forceTeix or not teixUptodate):
                run(
                    [
                        "pandoc",
                        cleanFile,
                        "--from=markdown",
                        "--to=tei",
                        "--standalone",
                        f"--output={teixFile}",
                    ]
                )
                convMessage.append("teisimple")

            teiUptodate = fileExists(teiFile) and mTime(teiFile) > mTime(teixFile)

            if not skipTei and (forceTei or not teiUptodate):
                (dramaStatus, dramaMsg, dramaText) = self.transformDrama(file)

                if not dramaStatus:
                    thisOK = False

                if dramaMsg:
                    extraMsg = dramaMsg

                with open(teiFile, "w") as f:
                    f.write(dramaText)

                convMessage.append("tei")

            nLines = lines.get(file, 0)
            nLineNumbers = len(lineNumbers.get(file, 0))
            nPages = sum(1 for x in pages.get(file, []) if x[0] == "p")
            nFolios = sum(1 for x in pages.get(file, []) if x[0] == "f")
            nSections = len(sections.get(file, []))

            if thisOK:
                someOK = True
            else:
                allOK = False

            status = "OK" if thisOK else "!!"
            totLines += nLines
            totLineNumbers += nLineNumbers
            totPages += nPages
            totFolios += nFolios
            totSections += nSections

            if len(convMessage):
                self.console(
                    f"\t{status} {file:30} | "
                    f"{nLines:>7} | {nLineNumbers:>5} | {nPages:>5} | {nFolios:>5} | "
                    f"{nSections:>4} | "
                    f"{' '.join(convMessage)} {extraMsg or ''}"
                )

        totStatus = "OK" if allOK else "+-" if someOK else "!!"
        msg = f"All dramas ({nDramas})"
        self.console(
            f"\t{totStatus} {msg:30} | "
            f"{totLines:>7} | {totLineNumbers:>5} | {totPages:>5} | {totFolios:>5} | "
            f"{totSections:>4} | done"
        )
        self.console(f"Dramas without specifics defined: {specNone}")

        if cleanDone:
            writeYaml(lines, asFile=REPORT_LINES_RAW)
            writeYaml(lineNumbers, asFile=REPORT_LINENUMBERS_RAW)
            writeYaml(pages, asFile=REPORT_PAGES_RAW)
            writeYaml(sections, asFile=REPORT_SECTIONS_RAW)

        lineInfo = {}
        pageInfo = {}
        sectionInfo = {}

        if cleanDone:
            for file in sorted(dramaFiles):
                if dramaName is not None and file != dramaName:
                    continue

                wLines = sorted(lineNumbers.get(file, []), key=lambda x: x[0])
                lineInfo[file] = [x[1] for x in wLines]

                wPages = sorted(pages.get(file, []), key=lambda x: x[1])
                pageInfo[file] = [f"{x[0]}. {x[-1]}" for x in wPages]

                wSections = sections.get(file, ())

                items = []

                for s in sorted(wSections, key=lambda x: x[0]):
                    (kind, number) = s[1:]
                    items.append(f"{kind} {number or ''}".rstrip())

                sectionInfo[file] = items

            writeYaml(lineInfo, asFile=REPORT_LINES)
            self.console(f"See for pages: {REPORT_LINES}")

            writeYaml(pageInfo, asFile=REPORT_PAGES)
            self.console(f"See for pages: {REPORT_PAGES}")

            writeYaml(sectionInfo, asFile=REPORT_SECTIONS)
            self.console(f"See for sections: {REPORT_SECTIONS}")

        self.showWarnings(serious=False)
        self.showWarnings()

        self.rhw.close()
        self.rhw = None
        self.rhi.close()
        self.rhi = None

    def task(self, *args, **kwargs):
        if self.error:
            return

        tasks = dict(
            convert=False,
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

            if task == "convert":
                mykwargs = {
                    k: v
                    for (k, v) in kwargs.items()
                    if k
                    in {
                        "forceDocx",
                        "forceClean",
                        "forceTei",
                        "forceTeix",
                        "skipDocx",
                        "skipClean",
                        "skipTeix",
                        "skipTei",
                        "dramaName",
                    }
                }
                self.convert(**mykwargs)

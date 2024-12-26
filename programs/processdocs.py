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
    REPORT_NONSECTIONS,
    REPORT_LINES_RAW,
    REPORT_LINENUMBERS_RAW,
    REPORT_PAGES_RAW,
    REPORT_SECTIONS_RAW,
    REPORT_NONSECTIONS_RAW,
    REPORT_SECTION_COUNT_RAW,
    msgLine,
    sanitizeFileName,
    normalizeChars,
    wrapParas,
)

from workspecific import WorkSpecific

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
    (\w+)
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
    (\w+)
    [.,;]?
    [\ ]
    [.,;]?
    (\w+)
    [.,;]?
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
        | terti[a-z]+
        | q[uv]art[a-z]+
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
    actores=(False, False, False, "actores"),
    actorum=(False, False, False, "actorum"),
    actus=(True, True, False, "actus"),
    argumentum=(True, False, False, "argumentum"),
    chori=(False, False, False, "chorus"),
    chorus=(False, False, False, "chorus"),
    chor=(False, False, False, "chorus"),
    ch=(False, False, False, "chorus"),
    codices=(False, False, False, "codices"),
    comoedia=(False, False, False, "comoedia"),
    comoediae=(False, False, False, "comoediae"),
    conclusio=(True, False, False, "conclusio"),
    dramatis=(True, False, False, "dramatis"),
    epitasis=(False, False, False, "epitasis"),
    epilogus=(True, False, False, "epilogus"),
    finis=(False, False, False, "finis"),
    incipit=(True, False, False, "incipit"),
    interlocutores=(True, False, False, "interlocutores"),
    interloquutores=(True, False, False, "interlocutores"),
    ludionum=(False, False, False, "ludionum"),
    pars=(True, True, False, "pars"),
    peroratio=(True, False, False, "peroratio"),
    personae=(True, False, False, "personae"),
    prologus=(True, False, False, "prologus"),
    protasis=(False, False, False, "protasis"),
    scaena=(True, True, False, "scena"),
    scena=(True, True, False, "scena"),
    strophe=(False, False, False, "strophe"),
    tragoidia=(False, False, False, "tragoedia"),
    prima=(True, False, True, "prima"),
    secunda=(True, False, True, "secunda"),
    tertia=(True, False, True, "tertia"),
    quarta=(True, False, True, "quarta"),
    quinta=(True, False, True, "quinta"),
    sexta=(True, False, True, "sexta"),
)

SECTION_TRIGGERS_PROTO = SECTION_TRIGGERS_DEF | {
    k.replace("u", "v"): v for (k, v) in SECTION_TRIGGERS_DEF.items()
}

SECTION_TRIGGERS = {k: v[-1] for (k, v) in SECTION_TRIGGERS_PROTO.items()}
SECTION_TRIGGERS_SEC = {k: v[0] for (k, v) in SECTION_TRIGGERS_PROTO.items()}
SECTION_TRIGGERS_NUM = {k: v[1] for (k, v) in SECTION_TRIGGERS_PROTO.items()}
SECTION_TRIGGERS_TRIG = {k: v[2] for (k, v) in SECTION_TRIGGERS_PROTO.items()}

NAMES_DEF = set(
    r"""
    acolastus
    aluta
    amor
    andrisca
    anna
    anima
    angeli
    angelus
    asmodaeus
    buccartius
    byrsocopus
    christus
    cognitio
    colax
    cometa
    cupido
    dudelaeus
    ecclesia
    euripus
    explorator
    fides
    genovefam
    georgus
    gustavus
    hecastus
    henricus
    herodes
    homulus
    iesuah
    ioseph
    iosephus
    luce
    magi
    maria
    matres
    megadorus
    miles
    mors
    morosophus
    nauta
    nehemias
    nomocrates
    numina
    nuncius
    nuntius
    octonarii
    pedantius
    pestis
    ponus
    primus
    princeps
    puella
    raphael
    religio
    sanguine
    sara
    sathanas
    secundus
    senarii
    senarij
    senex
    simus
    tempus
    tertia
    tertius
    timor
    tobias
    tristia
    venus
    virginum
    """.strip().split()
)

NAMES = NAMES_DEF | {k.replace("u", "v") for k in NAMES_DEF}

NONSECTION_WORDS_DEF = set(
    r"""
    a
    aa
    ab
    abite
    ad
    age
    apostolorum
    at
    b
    bene
    c
    capta
    carmine
    consuetudine
    credere
    cum
    cuncta
    d
    de
    destrues
    desydero
    dilectionis
    dimetri
    duo
    effare
    e
    eiusdem
    en
    equidem
    ergo
    esse
    est
    et
    etiam
    ex
    exhauriendus
    f
    fac
    fortiter
    g
    gaudia
    h
    hei
    hoc
    iambici
    iambico
    iambicum
    imò
    in
    ita
    itáne
    k
    l
    laudate
    laus
    licet
    m
    me
    mea
    mihi
    miserare
    more
    mortis
    n
    ne
    nell
    nihil
    nobis
    nomen
    non
    nos
    nunc
    nunquid
    o
    omnes
    omnia
    omnibus
    ordine
    p
    pectora
    pectore
    proh
    puer
    pulvere
    q
    quando
    quem
    qui
    quid
    quis
    quî
    quod
    r
    regemque
    s
    satis
    sed
    serenitate
    sic
    sine
    solus
    sunt
    t
    tantisper
    ubi
    ut
    te
    tetrametri
    trimetri
    trochaici
    tum
    v
    vel
    vere
    versu
    versus
    vis
    x
    y
    z
    """.strip().split()
)

NONSECTION_WORDS = NONSECTION_WORDS_DEF | {
    k.replace("u", "v") for k in NONSECTION_WORDS_DEF
}

NONSECTION = NAMES | NONSECTION_WORDS

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
    \\?\(
    (
        [0-9]+
        [A-Za-z]?
    )
    \\?\)
    [\ ]?
    (?=
        .*
        [a-z]
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

LNUM_RE = re.compile(r"""≤line=([^≥]+)≥""")
PNUM_RE = re.compile(r"""≤page=([^≥]+)≥""")
FNUM_RE = re.compile(r"""≤folio=([^≥]+)≥""")

NUM_RE = re.compile(r"[≤≥]")

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

    def makeLineNumRepl(self, workName):
        lineNumbers = []
        self.lineNumbers[workName] = lineNumbers

        def replGeneric(pos, result):
            def repl(match):
                lNum = match.group(pos)
                start = match.start()
                lineNumbers.append([start, lNum])
                return result.format(a=match.group(1), b=match.group(2))

            return repl

        self.lnumReplBefore = replGeneric(2, "{a}≤line={b}≥ ")
        self.lnumReplAfter = replGeneric(2, "≤line={b}≥ {a}\n")
        self.lnumReplBareAfter = replGeneric(2, "≤line={b}≥ {a}\n")
        self.lnumReplBareBefore = replGeneric(1, "≤line={a}≥ {b}\n")

    def makeSectionTriggerRepl(self, workName):
        sectionCount = self.sectionCount
        sections = []
        pseudoSections = []
        self.sections[workName] = sections
        self.pseudoSections[workName] = pseudoSections

        def repl(match):
            (pre, trigger, post, number, after) = match.group(1, 2, 3, 4, 5)
            triggerL = trigger.lower()
            number = number or ""

            if triggerL in SECTION_TRIGGERS:
                if len(post.replace(".", "").split()) > 3:
                    makeSection = False
                elif SECTION_TRIGGERS_TRIG[triggerL]:
                    nextWord = post.split()[0].rstrip(".") if post else ""
                    makeSection = nextWord.lower() in SECTION_TRIGGERS
                elif SECTION_TRIGGERS_NUM[triggerL]:
                    makeSection = SNUM_RE.match(number)
                else:
                    makeSection = True
            else:
                makeSection = False

            if makeSection:
                isSection = SECTION_TRIGGERS_SEC[triggerL]
                sigil = "§" if isSection else "*"

                matchSub = SECTIONTRIGGER_SND_RE.match(after)

                triggerSub = ""
                numberSub = ""

                if matchSub:
                    (tSub, nSub) = matchSub.group(1, 2)
                    triggerSubL = tSub.lower()

                    if triggerSubL in SECTION_TRIGGERS:
                        triggerSub = f"-{SECTION_TRIGGERS[triggerSubL]}"
                        numberSub = f"-{nSub.lower()}"

                triggerN = f"{sigil}{SECTION_TRIGGERS[triggerL]}{triggerSub}"
                number = f"{number.lower()}{numberSub}"
                sections.append([triggerN, number])
                sectionCount[triggerN] += 1
                replacement = (
                    f"# {pre}{trigger}{post}"
                    if isSection
                    else f"**{pre}{trigger}{post}**"
                )
            else:
                pseudoSections.append([trigger, number])
                replacement = match.group(0)

            return replacement

        return repl

    def makeNoteRepl(self, workName):
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

    def cleanup(self, text, workName):
        lines = self.lines
        specific = self.specific
        specific.makePageRepl(workName)

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

        workMethod = workName.replace("-", "_")

        method = getattr(specific, workMethod, None)
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
                self.warn(work=workName, heading=f"No {kind}")
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

        repl = self.makeLineNumRepl(workName)
        main = LINENUMBER_BEFORE_RE.sub(self.lnumReplBefore, main)
        main = LINENUMBER_AFTER_RE.sub(self.lnumReplAfter, main)
        main = LINENUMBER_BARE_AFTER_RE.sub(self.lnumReplBareAfter, main)
        main = LINENUMBER_BARE_BEFORE_RE.sub(self.lnumReplBareBefore, main)

        repl = self.makeSectionTriggerRepl(workName)
        main = SECTIONTRIGGER_RE.sub(repl, main)
        main = main.replace("qqq", "")

        lines[workName] = int(
            round(front.count("\n") + main.count("\n") + back.count("\n"))
        )

        text = f"# Front\n\n/{front}\n\n# Main\n\n{main}\n\n# Back\n\n{back}\n"
        text = wrapParas(text)
        return (msg, text)

    def transformWork(self, workName):
        if self.error:
            return (False, None, None)

        Meta = self.Meta

        if Meta.error:
            return (False, None, None)

        with open(f"{TEIXDIR}/{workName}.xml") as f:
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
            line = PNUM_RE.sub(r"""<pb n="\1"/>""", line)
            line = FNUM_RE.sub(r"""<milestone unit="folio" n="\1"/>""", line)

            newTextLines.append(line)

        material = "\n".join(newTextLines)

        leftovers = NUM_RE.findall(material)
        n = len(leftovers)

        if n:
            self.warn(work=workName, heading=f"number leftovers: {n} x")

        repl = self.makeNoteRepl(workName)
        material = NOTE_RE.sub(repl, material)

        notes = "\n".join(self.notes)
        text = Meta.fillTemplate(workName, text=material, notes=notes)

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
        workName=None,
    ):
        if self.error:
            return

        self.warnings = []
        extraLog = {}
        self.extraLog = extraLog
        self.specific = WorkSpecific(self)

        self.rhw = open(REPORT_WARNINGS, mode="w")
        self.rhi = open(REPORT_INFO, mode="w")

        console("DOCX => Markdown per work ...")
        console(
            f"\t   {'work':30} | "
            f"{'lines':>7} | {'lnums':>5} | {'pages':>5} | {'folios':>5}| "
            f"{'sect':>4} | "
            f"conversion steps"
        )

        workFiles = self.workFiles

        initTree(MD_ORIGDIR, fresh=False)
        initTree(MD_FINALDIR, fresh=False)
        initTree(TEIXDIR, fresh=False)
        initTree(TEIDIR, fresh=True, gentle=True)

        lines = readYaml(asFile=REPORT_LINES_RAW, plain=True)
        lineNumbers = readYaml(asFile=REPORT_LINENUMBERS_RAW, plain=True)
        pages = readYaml(asFile=REPORT_PAGES_RAW, plain=True)
        sections = readYaml(asFile=REPORT_SECTIONS_RAW, plain=True)
        pseudoSections = {}  # only do pseudoSections if clean is performed
        sectionCount = readYaml(asFile=REPORT_SECTION_COUNT_RAW, plain=True)
        sectionCount = collections.Counter(sectionCount)

        self.lines = lines
        self.lineNumbers = lineNumbers
        self.pages = pages
        self.sections = sections
        self.pseudoSections = pseudoSections
        self.sectionCount = sectionCount

        totLines = 0
        totLineNumbers = 0
        totPages = 0
        totFolios = 0
        totSections = 0

        for file in sorted(workFiles):
            if workName is not None and file != workName:
                continue

            realFile = workFiles[file]

            inFile = f"{DOCXDIR}/{realFile}.docx"
            rawFile = f"{MD_ORIGDIR}/{file}.md"
            cleanFile = f"{MD_FINALDIR}/{file}.md"
            teixFile = f"{TEIXDIR}/{file}.xml"
            teiFile = f"{TEIDIR}/{file}.xml"

            rawUptodate = fileExists(rawFile) and mTime(rawFile) > mTime(inFile)

            convMessage = []
            status = "OK"
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
                (workStatus, workMsg, workText) = self.transformWork(file)

                if not workStatus:
                    status = "!!"

                if workMsg:
                    extraMsg = workMsg

                with open(teiFile, "w") as f:
                    f.write(workText)

                convMessage.append("tei")

            nLines = lines.get(file, 0)
            nLineNumbers = len(lineNumbers.get(file, 0))
            nPages = sum(1 for x in pages.get(file, []) if x[0] == "p")
            nFolios = sum(1 for x in pages.get(file, []) if x[0] == "f")
            nSections = len(sections.get(file, []))

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

        msg = f"All works ({len(workFiles)})"
        self.console(
            f"\t{msg:30} | "
            f"{totLines:>7} | {totLineNumbers:>5} | {totPages:>5} | {totFolios:>5} | "
            f"{totSections:>4} | done"
        )

        if cleanDone:
            writeYaml(lines, asFile=REPORT_LINES_RAW)
            writeYaml(lineNumbers, asFile=REPORT_LINENUMBERS_RAW)
            writeYaml(pages, asFile=REPORT_PAGES_RAW)
            writeYaml(sections, asFile=REPORT_SECTIONS_RAW)
            writeYaml(pseudoSections, asFile=REPORT_NONSECTIONS_RAW)
            writeYaml(dict(sectionCount), asFile=REPORT_SECTION_COUNT_RAW)

        lineInfo = {}
        pageInfo = {}
        sectionInfo = {}
        pseudoSectionInfo = {}

        if cleanDone:
            for file in sorted(workFiles):
                if workName is not None and file != workName:
                    continue

                wLines = sorted(lineNumbers.get(file, []), key=lambda x: x[0])
                lineInfo[file] = [x[1] for x in wLines]

                wPages = sorted(pages.get(file, []), key=lambda x: x[1])
                pageInfo[file] = [f"{x[0]}. {x[-1]}" for x in wPages]

                wSections = sections.get(file, ())

                items = []

                for kind, number in wSections:
                    cnt = sectionCount[kind]
                    items.append(f"x {cnt:>4} {kind} {number or ''}".rstrip())

                sectionInfo[file] = items

                wpSections = pseudoSections.get(file, ())

                if len(wpSections):
                    items = []

                    for kind, number in wpSections:
                        cnt = sectionCount[kind]

                        if kind.isdigit() or kind.lower() in NONSECTION or cnt == 1:
                            continue

                        items.append(f"x {cnt:>4} {kind} {number or ''}".rstrip())

                    pseudoSectionInfo[file] = items

            writeYaml(lineInfo, asFile=REPORT_LINES)
            self.console(f"See for pages: {REPORT_LINES}")

            writeYaml(pageInfo, asFile=REPORT_PAGES)
            self.console(f"See for pages: {REPORT_PAGES}")

            writeYaml(sectionInfo, asFile=REPORT_SECTIONS)
            self.console(f"See for sections: {REPORT_SECTIONS}")

            writeYaml(pseudoSectionInfo, asFile=REPORT_NONSECTIONS)
            self.console(f"See for non-sections: {REPORT_NONSECTIONS}")

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
                        "workName",
                    }
                }
                self.convert(**mykwargs)

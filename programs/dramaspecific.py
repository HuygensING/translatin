import re
import inspect


HEAD_PAGENUM_RE = re.compile(
    r"""
    ^
    [A-Z]+
    \.
    \s+
    (
        [0-9]+
    )
    $
    """,
    re.M | re.X,
)

ROMAN_PAGENUM_SQ_RE = re.compile(
    r"""
    \\\[
    [\ ]?
    ([ijvxlc]+)
    [\ ]?
    \\\]
    """,
    re.X,
)

ARABIC_PAGENUM_SQ_RE = re.compile(
    r"""
    \\\[
    (?:p\.)?
    [\ ]?
    ([0-9]+)
    [\ ]?
    \\\]
    """,
    re.X,
)

ARABIC_PAGENUM_SQ_FACS_RE = re.compile(
    r"""
    \\\[
    (?:p\.)?
    [\ ]?
    ([0-9]+)
    (?:
        :
        [\ ]+
        ([^\\]*)
    )?
    \\\]
    """,
    re.X,
)

ARABIC_PAGENUM_RND_RE = re.compile(
    r"""
    (?:
        \\?\( | \)\(
    )
    [\ ]?
    ([0-9]+)
    [\ ]?
    (?:
        \\?\) | \)\(
    )
    """,
    re.X,
)

ARABIC_PAGENUM_DASH_RE = re.compile(
    r"""
    ^
    -
    (
        [0-9]+
    )
    -
    [\ ]?
    $
    """,
    re.M | re.X,
)

ARABIC_PAGENUM_BARE_RE = re.compile(
    r"""
    ^
    (
        [0-9]+
    )
    [\ ]?
    $
    """,
    re.M | re.X,
)

PAGE_FACS_RE = re.compile(
    r"""
    \[
    Page
    [\ \xa0\n]+
    (
        [^\]]+
    )
    \]
    \(
    (
        [^)]+
    )
    \)
    """,
    re.X | re.S,
)

PAGE_FACS_IMAGE_RE = re.compile(
    r"""
    image:
    [\ \n]
    \[
    [a-z]0*
    (
        [0-9]+
    )
    \]
    \(
    (
        [^)]+
    )
    \)
    """,
    re.X | re.S,
)

FOLIO_ALPHA_ROMAN_ALONE_RE = re.compile(
    r"""
    ^
    (
        [A-Z]
        [\ ]?
        [ijxvcl]*
        [ab]?
    )
    $
    """,
    re.X | re.M,
)

FOLIO_ALPHA_ARABIC_ALONE_RE = re.compile(
    r"""
    ^
    (
        [A-Z]
        (?:
            [\ ]?
            [0-9]+
        )?
    )
    $
    """,
    re.X | re.M,
)

FOLIO_ALPHA_ARABIC_BARE_RE = re.compile(
    r"""
    (
        [A-Z]
        [0-9]+
    )
    """,
    re.X,
)

FOLIO_ALPHA_ROMAN_SQ_RE = re.compile(
    r"""
    \\\[
    (
        [A-Z]
        [\ ]?
        [ijxvcl]*
        [\ ]?
        [ab]?
    )
    \\\]
    """,
    re.X,
)

FOLIO_ALPHA_ARABIC_SQ_RE = re.compile(
    r"""
    \\\[
    (
        [A-Z]
        [\ ]?
        [0-9]*
        [\ ]?
        [ab]?
    )
    \\\]
    """,
    re.X,
)

FOLIO_SLASH_RE = re.compile(
    r"""
    (?:\\\[)?
    /
    ([A-Za-z]?[0-9]*[rv]?)
    /
    (?:\\\])?
    """,
    re.X,
)

FOLIO_MARK_RE = re.compile(
    r"""
    \\\[
    fol\.
    [\ ]?
    (.*?)
    \\\]
    """,
    re.X,
)

NUMERALS_NL = dict(
    eerste="i",
    tweede="ii",
    derde="iii",
)


class DramaSpecific:
    def __init__(self, converter):
        self.converter = converter
        self.pageRepl = None
        self.folioRepl = None

    def identity(self, text):
        return text

    def makePageRepl(self, dramaName):
        converter = self.converter

        pages = []
        converter.pages[dramaName] = pages

        def pageRepl(match):
            page = match.group(1)
            start = match.start()
            pages.append(["p", start, page])
            return f"≤page={page}≥"

        self.pageRepl = pageRepl

        def pageFacsRepl(match):
            page = match.group(1)
            facs = match.group(2) or ""

            if facs:
                facs = f"|{facs}"

            start = match.start()
            pages.append(["p", start, f"{page}{facs}"])
            return f"≤page={page}{facs}≥"

        self.pageFacsRepl = pageFacsRepl

        def folioRepl(match):
            folio = match.group(1).replace(" ", "").replace("\n", "")
            start = match.start()
            pages.append(["f", start, folio])
            return f"≤folio={folio}≥"

        self.folioRepl = folioRepl

        def folioFacsRepl(match):
            folio = match.group(1).replace(" ", "").replace("\n", "")
            facs = (match.group(2) or "").replace(" ", "").replace("\n", "")

            if facs:
                facs = f"|{facs}"

            start = match.start()
            pages.append(["f", start, f"{folio}{facs}"])
            return f"≤folio={folio}{facs}≥"

        self.folioFacsRepl = folioFacsRepl

    def Alberti_Philodoxus(self, text):
        text = ROMAN_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Aler_Innocentia(self, text):
        text = ARABIC_PAGENUM_RND_RE.sub(self.pageRepl, text)
        return text

    Balde_Iephtias = "generic"
    Barlandus_Dialogus = "generic"

    def Beza_Abrahamus(self, text):
        headLeftRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\\.,]*
            [\ ]?
            (?:ABRAHAMUS|TRAGOEDIA)
            \.?[\ ]
            (?:SACRIFICANS|SACRA)
            [\\.,]*
            $
            """,
            re.M | re.X,
        )
        headRightRe = re.compile(
            r"""
            ^
            (?:ABRAHAMUS|TRAGOEDIA)
            \.?[\ ]
            (?:SACRIFICANS|SACRA)
            [\\.,]+
            [\ ]?
            ([0-9]+)
            [\\.,]*
            $
            """,
            re.M | re.X,
        )
        text = headLeftRe.sub(self.pageRepl, text)
        text = headRightRe.sub(self.pageRepl, text)
        return text

    def Brechtus_Euripus(self, text):
        headRe = re.compile(
            r"""
            ^
            Levin.*
            \n\n
            """,
            re.X | re.M,
        )
        text = headRe.sub("", text)
        folioRe = re.compile(
            r"""
            \\<
            (
                [A-Z]
                [\ ]?
                [0-9]*
                [rv]?
            )
            \\>
            """,
            re.X,
        )
        text = folioRe.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_BARE_RE.sub(self.pageRepl, text)
        return text

    Caussin_Felicitas = "generic"

    def Caussin_Hermenigildus(self, text):
        text = ROMAN_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    Caussin_Nabuchodonosor = "generic"
    Caussin_Solyma = "generic"
    Caussin_Theodoricus = "generic"

    def Cellotius_Adrianus(self, text):
        text = ROMAN_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Cellotius_Chosroes(self, text):
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Cellotius_Reviviscentes(self, text):
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Cellotius_Sapor(self, text):
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    Celtis_Ludus = "generic"
    Claus_Vulpanser = "generic"
    Crocus_Ioseph = "generic"
    Cunaeus_Dido = "generic"

    def Dalanthus_Dido(self, text):
        headRe = re.compile(
            r"""
            ^
            (
                \\\[
                [0-9]+
                \\\]
            )
            [\ ]
            [A-Z]+
            .*
            $
            """,
            re.X | re.M,
        )
        text = headRe.sub(r"\1", text)
        text = FOLIO_ALPHA_ROMAN_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    Diether_Ioseph = "generic"

    def Enden_Philedonius(self, text):
        dramaName = (inspect.stack()[0][3]).replace("_", "-")
        converter = self.converter
        text = FOLIO_MARK_RE.sub(self.folioRepl, text)
        sections = []
        sectionRe = re.compile(
            r"""
            ^
            (
                (?:
                    (?:DE)?|HET
                )
                [\ ]?
            )
            (
                \w+
                \\?\.?
            )
            (
                [\ ]?
            )
            (
                BEDRYF|UITKOMSTE
            )
            .*
            $
            """,
            re.M | re.X,
        )

        def repl(match):
            (pre, number, space, trigger) = match.group(1, 2, 3, 4)
            start = match.start()
            triggerL = trigger.lower()
            triggerN = f"§{triggerL}"
            numberL = number.lower()
            numberN = (NUMERALS_NL[numberL] if trigger == "BEDRYF" else numberL).strip(
                "\\."
            )
            sections.append([start, triggerN, numberN])
            return f"## {pre}{number}{space}{trigger}"

        text = sectionRe.sub(repl, text)
        ssections = sorted(sections, key=lambda x: x[0])
        converter.sections[dramaName] = ssections
        return text

    Ens_Auriacus = "generic"

    def Forsett_Pedantius(self, text):
        text = PAGE_FACS_RE.sub(self.pageFacsRepl, text)
        return text

    def Foxe_Christus(self, text):
        pageRemoveRe = re.compile(
            r"""
            [\ ]
            Page
            [\ ]
            \[
            unnumbered
            \]
            [\ ]
            """,
            re.X | re.S,
        )
        text = pageRemoveRe.sub(" ", text)
        text = PAGE_FACS_RE.sub(self.pageFacsRepl, text)
        noteRe = re.compile(
            r"""
            \[
            \\
            \*
            \]
            \(
            (
                [^)]+
            )
            \)
            """,
            re.X | re.S
        )

        def noteRepl(match):
            url = match.group(1)
            ref = url.split("DLPS", 1)[-1].split(";", 1)[0]
            return f"""[note {ref}]({url})"""

        text = noteRe.sub(noteRepl, text)
        return text

    Gnapheus_Acolastus = "generic"
    Gnapheus_Morosophus = "generic"

    def Goethals_Soter(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    Gretser_Timon = "generic"
    Gretser_Underwaldius = "generic"
    Grimald_Christus = "generic"
    Grotius_Adamus = "generic"
    Grotius_Christus = "generic"

    def Grotius_Phoenissae(self, text):
        folioRe = re.compile(
            r"""
            \\\[
            fol\.
            [\ ]
            (\w+)
            (?:
                :
                [\ ]?
                (
                    [^\\]*
                )
            )?
            \\\]
            """,
            re.X | re.S,
        )
        text = folioRe.sub(self.folioFacsRepl, text)
        text = ARABIC_PAGENUM_SQ_FACS_RE.sub(self.pageFacsRepl, text)
        return text

    Gwalther_Nabal = "generic"
    Heinsius_Auriacus = "generic"

    def Heinsius_Herodes(self, text):
        # there is wrongly coded greek at the end, past Back
        text = FOLIO_SLASH_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            /
            p\.
            [\ ]
            ([0-9]+)
            /
            [\ ]?
            """,
            re.X
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Holonius_Catharina(self, text):
        headRe = re.compile(
            r"""
            ^
            (
                \\\[
                [0-9]+
                \\\]
            )
            [\ ]
            [A-Z]
            .*
            $
            """,
            re.X | re.M
        )
        text = headRe.sub(r"\1", text)
        text = FOLIO_ALPHA_ROMAN_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Holonius_Laurentias(self, text):
        headRe = re.compile(
            r"""
            ^
            [A-Z]
            .*?
            [\ ]
            (
                \\\[
                [0-9]+
                \\\]
            )
            $
            """,
            re.X | re.M
        )
        text = headRe.sub(r"\1", text)
        text = FOLIO_ALPHA_ROMAN_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Honerdus_Thamara(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                THAMARA
                |
                TRA[GC]OEDIA
                |
                TRAGOAEDIA
            )
            \.?
            [\ ]?
            ([0-9]+)
            .*
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Houcharius_Grisellis(self, text):
        converter = self.converter
        dramaName = (inspect.stack()[0][3]).replace("_", "-")
        text = FOLIO_ALPHA_ROMAN_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        sections = []
        sectionRe = re.compile(
            r"""
            ^
            (Tertius)
            [\ ]
            (actus)
            \.
            [\ ]
            (.*)
            $
            """,
            re.M | re.X,
        )

        def repl(match):
            (number, trigger, rest) = match.group(1, 2, 3)
            start = match.start()
            triggerL = trigger.lower()
            triggerN = f"§{triggerL}"
            numberN = number.lower()
            sections.append([start, triggerN, numberN])
            return f"## {number} {trigger}\n\n{rest}"

        text = sectionRe.sub(repl, text)
        ssections = sorted(sections, key=lambda x: x[0])
        converter.sections[dramaName] = ssections
        return text

    def Houthem_Gedeon(self, text):
        text = FOLIO_ALPHA_ROMAN_ALONE_RE.sub(self.folioRepl, text)
        return text

    def Ischyrius_Homulus(self, text):
        text = FOLIO_ALPHA_ROMAN_SQ_RE.sub(self.folioRepl, text)
        return text

    Kerckmeister_Codrus = "generic"

    def Knuyt_Scornetta(self, text):
        text = FOLIO_ALPHA_ROMAN_SQ_RE.sub(self.folioRepl, text)
        return text

    def Laurimanus_Exodus(self, text):
        headRe = re.compile(
            r"""
            ^
            [A-Z]
            \s+
            [a-z]+
            \n\n
            [A-Z]+
            \n\n
            """,
            re.M | re.X,
        )
        text = headRe.sub("", text)
        text = HEAD_PAGENUM_RE.sub(self.pageRepl, text)
        return text

    def Laurimanus_Miles(self, text):
        headRe = re.compile(
            r"""
            ^
            MILES
            \.?
            \n\n
            """,
            re.M | re.X,
        )
        text = headRe.sub("", text)
        markRe = re.compile(
            r"""
            ^
            [A-Z]
            \s
            [0-9]+
            \n\n
            """,
            re.X | re.M,
        )
        text = markRe.sub("", text)
        text = HEAD_PAGENUM_RE.sub(self.pageRepl, text)
        return text

    def Locher_Iudicium(self, text):
        converter = self.converter
        dramaName = (inspect.stack()[0][3]).replace("_", "-")
        text = FOLIO_ALPHA_ROMAN_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        sections = []
        sectionRe = re.compile(
            r"""
            ^
            (TERTIVS)
            [\ ]
            (ACTVS)
            \.
            $
            """,
            re.M | re.X,
        )

        def repl(match):
            (number, trigger) = match.group(1, 2)
            start = match.start()
            triggerL = trigger.lower()
            triggerN = f"§{triggerL}"
            numberN = number.lower()
            sections.append([start, triggerN, numberN])
            return f"## {number} {trigger}"

        text = sectionRe.sub(repl, text)
        ssections = sorted(sections, key=lambda x: x[0])
        converter.sections[dramaName] = ssections
        return text

    def Lummenaeus_Abimelech(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                ABIMELECH
                \.
                [\ ]
            )?
            ([0-9]+)
            (?:
                [\ ]
                IACOBI
                .*
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Lummenaeus_Amnon(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            TRAGOEDIA
            [\ ]
            SACRA
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        pageSecRe = re.compile(
            r"""
            ^
            ACTVS
            \.?
            [\ ]
            [IVX]+
            \.?
            [\ ]
            ([0-9]+)
            $
            """,
            re.X | re.M
        )
        text = pageSecRe.sub(self.pageRepl, text)
        return text

    def Lummenaeus_Bustum(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                BVSTVM
                [\ ]
                SODOMAE
                \.
                [\ ]
            )?
            ([0-9]+)
            (?:
                [\ ]
                IACOBI
                .*
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Lummenaeus_Carcer(self, text):
        text = FOLIO_ALPHA_ROMAN_SQ_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Lummenaeus_Iephte(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    IEPHTE
                    |
                    (?:
                        REVERENDO[\ ]VIRO
                    )
                )
                \.?
                [\ ]
            )?
            ([0-9]+)
            (?:
                [\ ]
                (?:
                    IACOBI
                    |
                    ARGVMENTVM
                    |
                    (?:
                        REVERENDO[\ ]VIRO
                    )
                )
                .*
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Lummenaeus_Sampson(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                SAMPSON
                \.
                [\ ]
            )?
            ([0-9]+)
            (?:
                [\ ]
                (?:
                    IACOBI
                    |
                    SAMPSON
                )
                .*
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Lummenaeus_Saul(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                SAVL
                \.+
                [\ ]
            )?
            ([0-9]+)
            (?:
                [\ ]
                (?:
                    IACOBI
                    |
                    SAVL
                )
                .*
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    Macropedius_Adamus = "generic"
    Macropedius_Aluta = "generic"

    def Macropedius_Andrisca(self, text):
        text = FOLIO_MARK_RE.sub(self.folioRepl, text)
        return text

    Macropedius_Asotus = "generic"
    Macropedius_Bassarus = "generic"
    Macropedius_Hecastus = "generic"
    Macropedius_Hypomone = "generic"
    Macropedius_Iesus = "generic"
    Macropedius_Iosephus = "generic"
    Macropedius_Lazarus = "generic"
    Macropedius_Petriscus = "generic"
    Macropedius_Rebelles = "generic"
    Malapertius_Sedecias = "generic"
    Muretus_Caesar = "generic"
    Mussato_Ecerinis = "generic"

    def Narssius_Gustavus(self, text):
        text = FOLIO_ALPHA_ARABIC_SQ_RE.sub(self.folioRepl, text)
        # there is an extra arabic numbering between [], looks like page numbering
        # I treat it as an extra folio numbering
        text = ARABIC_PAGENUM_SQ_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_BARE_RE.sub(self.pageRepl, text)
        return text

    Papaeus_Samarites = "generic"
    Philicinus_Esther = "generic"

    def Philicinus_Magdalena(self, text):
        text = ARABIC_PAGENUM_DASH_RE.sub(self.pageRepl, text)
        return text

    def Placentius_Clericus(self, text):
        folioRe = re.compile(
            r"""
            ^
            \**
            p
            \\?
            \.?
            [\ ]?
            (
                [a-z]+
            )
            \**
            $
            """,
            re.X | re.M
        )
        text = folioRe.sub(self.folioRepl, text)
        return text

    def Placentius_Plausus(self, text):
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Placentius_Susanna(self, text):
        text = FOLIO_ALPHA_ARABIC_BARE_RE.sub(self.folioRepl, text)
        return text

    Reuchlin_Henno = "generic"
    Reuchlin_Sergius = "generic"

    def Rosefeldus_Moschus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        return text

    Roulerius_Stuarta = "generic"
    Ruggle_Ignoramus = "generic"
    Salius_Nassovius = "generic"

    def Schonaeus_Ananias(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                (?:
                    TERENT
                    \.
                    [\ ]
                    CHRIST
                )
                |
                ANANIAS
            )
            \.
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Baptistes(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                TRAGICOCOMOEDIA
                |
                BAPTISTES
            )
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Cunae(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                FABVLA
                |
                CVNAE
            )
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Daniel(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                (?:
                    TERENT
                    \.
                    [\ ]
                    CHRIST
                )
                |
                DANIEL
            )
            \.
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Dyscoli(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                COMOEDIA
                |
                DYSCOLI
            )
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Fabula(self, text):
        text = FOLIO_SLASH_RE.sub(self.folioRepl, text)
        return text

    def Schonaeus_Iosephus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    TERENTII
                    [\ ]
                    CHRIST
                )
                |
                IOSEPHVS
            )
            \.
            [\ ]
            ([0-9]+)
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Iuditha(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    TEREN[TR]II?
                    [\ ]
                    CHRIST
                )
                |
                IVDITHA
            )
            \.
            [\ ]
            ([0-9]+)
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Naaman(self, text):
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Schonaeus_Nehemias(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    TEREN[TR]II?
                    [\ ]
                    CHRIST
                )
                |
                NEHEMIAS
            )
            \.?
            [\ ]
            ([0-9]+)
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Pentecoste(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                (?:
                    TERENT
                    \.
                    [\ ]
                    CHR[IY]ST
                )
                |
                PROLOGVS
                |
                PENTECOSTE
            )
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Pseudostratiotae(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            \\?\.?
            [\ ]
            (?:
                FABVLA
                |
                PSEVDO[A-Z]*
            )
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Saulus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    TERENTII
                    [\ ]
                    CHRIST
                )
                |
                SAVLVS
            )
            \.?
            [\ ]
            ([0-9]+)
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Susanna(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    TERENT
                    \.
                    [\ ]
                    CHRIST
                )
                |
                SVSANNA
            )
            \.?
            [\ ]
            ([0-9]+)
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                (?:
                    TERENT
                    \.
                    [\ ]
                    CHRIST
                )
                |
                SVSANNA
            )
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Tobaeus(self, text):
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Schonaeus_Triumphus(self, text):
        # N.B. the order of tha last two pages is inverted: 129, 128
        # Also: the header/footer of these pages is consistent with their numbering.
        # So I leave it as is.
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                (?:
                    TERENT
                    \.
                    [\ ]
                    CHRIST
                )
                |
                (?:
                    TRIVMPHVS
                    [\ ]
                    CHRISTI
                )
            )
            [.:]?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Typhlus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                (?:
                    TERENT
                    \.
                    [\ ]
                    CHRIST
                )
                |
                TYPHLVS
            )
            [.:]?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schonaeus_Vitulus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            \\?\.?
            [\ ]
            (?:
                FABVLA
                |
                VITVLVS
            )
            \.?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Schopper_Ectrachelistes(self, text):
        text = PAGE_FACS_IMAGE_RE.sub(self.pageFacsRepl, text)
        return text

    def Simonides_Castus(self, text):
        folioRe = re.compile(
            r"""
            ^
            (
                [A-K]
                (?:
                    [\ ]?
                    [0-9]+
                )?
            )
            [\ ]
            [A-Z]
            .*
            $
            """,
            re.X | re.M,
        )
        text = folioRe.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Stymmelius_Isaac(self, text):
        headRe = re.compile(
            r"""
            ^
            (?:
                EPISTOLA
                |
                DEDICATORIA\.
                |
                (?:
                    EPISTO\.
                    [\ ]
                    DEDICA\.
                )
            )
            $
            """,
            re.X | re.M
        )
        text = headRe.sub("", text)
        return text

    Stymmelius_Studentes = "generic"

    def Susius_Pendularia(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                PENDVLARIA\.[\ ]
            )?
            ([0-9]+)
            (?:
                [\ ]
                (?:
                    DRAMA.*
                    |
                    PENDVLARIA\.
                )
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Telesio_Imber(self, text):
        headRe = re.compile(
            r"""
            ^
            (?:
                ANTONII[\ ]THYLESII
                |
                IMBER[\ ]AVREVS
            )
            \.?
            [\ ]
            (?=\\\[)
            """,
            re.X | re.M
        )
        text = headRe.sub("", text)
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Vernulaeus_Conradinus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    CONRADINVS
                    |
                    NICOLA[IT][\ ]VERNVLAEI
                )
                \.?[\ ]
            )?
            ([0-9]+)
            (?:
                [\ ]
                (?:
                    CONRADINVS
                    |
                    NICOLA[IT][\ ]VERNVLAEI
                )
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Vernulaeus_Crispus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    CRISPVS
                    |
                    NICOLA[IT][\ ]VERNVLAEI
                )
                \.?[\ ]?
            )?
            ([0-9]+)
            (?:
                [\ ]?
                (?:
                    CRISPVS
                    |
                    NICOLA[IT][\ ]VERNVLAEI
                )
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    def Vernulaeus_Gorcomienses(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    Vernulaeus_Henricus = "generic"

    def Vernulaeus_Theodoricus(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        pageRe = re.compile(
            r"""
            ^
            (?:
                (?:
                    THEODORIC[UV]S
                    |
                    NICOLA[IT][\ ]VERNVLAEI
                )
                \.?[\ ]?
            )?
            ([0-9]+)
            (?:
                [\ ]?
                (?:
                    THEODORIC[UV]S
                    |
                    NICOLA[IT][\ ]VERNVLAEI
                )
            )?
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    Vladeraccus_Tobias = "generic"
    Weitenauer_Annibal = "generic"

    def Wimpheling_Stylpho(self, text):
        dramaName = (inspect.stack()[0][3]).replace("_", "-")
        converter = self.converter
        text = FOLIO_MARK_RE.sub(self.folioRepl, text)
        sections = []
        sectionRe = re.compile(
            r"""
            ^
            \\?<?
            (
                prima
                | secunda
                | tertia
                | quarta
                | quinta
                | sexta
            )
            [\ ]
            (
                scena
            )
            \\?>?
            $
            """,
            re.M | re.X | re.I,
        )

        def repl(match):
            (number, trigger) = match.group(1, 2)
            start = match.start()
            triggerL = trigger.lower()
            triggerN = f"§{triggerL}"
            numberN = number.lower()
            sections.append([start, triggerN, numberN])
            return f"## {number} {trigger}"

        text = sectionRe.sub(repl, text)
        ssections = sorted(sections, key=lambda x: x[0])
        converter.sections[dramaName] = ssections
        return text

    def Zevecotius_Rosimunda(self, text):
        text = FOLIO_ALPHA_ARABIC_ALONE_RE.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        pageRe = re.compile(
            r"""
            ^
            ([0-9]+)
            [\ ]
            (?:
                I\.[ ]ZEVECOTII
                |
                ROSIM[UV]NDA
            )
            [\\.]*
            $
            """,
            re.X | re.M
        )
        text = pageRe.sub(self.pageRepl, text)
        return text

    Zovitius_Didascalus = "generic"
    Zovitius_Ruth = "generic"

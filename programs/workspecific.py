import re


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
    ([ivxlc]+)
    [\ ]?
    \\\]
    """,
    re.X,
)

ARABIC_PAGENUM_SQ_RE = re.compile(
    r"""
    \\\[
    [\ ]?
    ([0-9]+)
    [\ ]?
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


class WorkSpecific:
    def __init__(self, converter):
        self.converter = converter
        self.pageRepl = None
        self.folioRepl = None

    def identity(self, text):
        return text

    def makePageRepl(self, workName):
        converter = self.converter

        pages = []
        converter.pages[workName] = pages

        def pageRepl(match):
            page = match.group(1)
            start = match.start()
            pages.append(("p", start, page))
            return f"≤page {page}≥"

        self.pageRepl = pageRepl

        def folioRepl(match):
            folio = match.group(1)
            start = match.start()
            pages.append(("f", start, folio))
            return f"≤folio {folio}≥"

        self.folioRepl = folioRepl

    def Alberti_Philodoxus(self, text):
        text = ROMAN_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    def Aler_Innocentia(self, text):
        text = ARABIC_PAGENUM_RND_RE.sub(self.pageRepl, text)
        return text

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

    def Caussin_Hermenigildus(self, text):
        text = ROMAN_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

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

    # Cunaeus_Dido is done, start with Dalanthus Dido

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

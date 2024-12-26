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
    ([ijvxlc]+)
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
            pages.append(["p", start, page])
            return f"≤page={page}≥"

        self.pageRepl = pageRepl

        def folioRepl(match):
            folio = match.group(1).replace(" ", "")
            start = match.start()
            pages.append(["f", start, folio])
            return f"≤folio={folio}≥"

        self.folioRepl = folioRepl

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
            re.X | re.M
        )
        text = headRe.sub(r"\1", text)
        folioRe = re.compile(
            r"""
            ^
            (
                [A-Z]
                [\ ]?
                [ijxvcl]*
            )
            $
            """,
            re.X | re.M
        )
        text = folioRe.sub(self.folioRepl, text)
        text = ARABIC_PAGENUM_SQ_RE.sub(self.pageRepl, text)
        return text

    Diether_Ioseph = "generic"

    Enden_Philedonius = "generic"
    Ens_Auriacus = "generic"
    Forsett_Pedantius = "generic"
    Foxe_Christus = "generic"
    Gnapheus_Acolastus = "generic"
    Gnapheus_Morosophus = "generic"
    Goethals_Soter = "generic"
    Gretser_Timon = "generic"
    Gretser_Underwaldius = "generic"
    Grimald_Christus = "generic"
    Grotius_Adamus = "generic"
    Grotius_Christus = "generic"
    Grotius_Phoenissae = "generic"
    Gwalther_Nabal = "generic"
    Heinsius_Auriacus = "generic"
    Heinsius_Herodes = "generic"
    Holonius_Catharina = "generic"
    Holonius_Laurentias = "generic"
    Honerdus_Thamara = "generic"
    Houcharius_Grisellis = "generic"
    Houthem_Gedeon = "generic"
    Ischyrius_Homulus = "generic"
    Kerckmeister_Codrus = "generic"
    Knuyt_Scornetta = "generic"

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

    Locher_Iudicium = None
    Lummenaeus_Abimelech = None
    Lummenaeus_Amnon = None
    Lummenaeus_Bustum = None
    Lummenaeus_Carcer = None
    Lummenaeus_Iephte = None
    Lummenaeus_Sampson = None
    Lummenaeus_Saul = None
    Macropedius_Adamus = None
    Macropedius_Aluta = None
    Macropedius_Andrisca = None
    Macropedius_Asotus = None
    Macropedius_Bassarus = None
    Macropedius_Hecastus = None
    Macropedius_Hypomone = None
    Macropedius_Iesus = None
    Macropedius_Iosephus = None
    Macropedius_Lazarus = None
    Macropedius_Petriscus = None
    Macropedius_Rebelles = None
    Malapertius_Sedecias = None
    Muretus_Caesar = None
    Mussato_Ecerinis = None
    Narssius_Gustavus = None
    Papaeus_Samarites = None
    Philicinus_Esther = None
    Philicinus_Magdalena = None
    Placentius_Clericus = None
    Placentius_Plausus = None
    Placentius_Susanna = None
    Reuchlin_Henno = None
    Reuchlin_Sergius = None
    Rosefeldus_Moschus = None
    Roulerius_Stuarta = None
    Ruggle_Ignoramus = None
    Salius_Nassovius = None
    Schonaeus_Ananias = None
    Schonaeus_Baptistes = None
    Schonaeus_Cunae = None
    Schonaeus_Daniel = None
    Schonaeus_Dyscoli = None
    Schonaeus_Fabula = None
    Schonaeus_Iosephus = None
    Schonaeus_Iuditha = None
    Schonaeus_Naaman = None
    Schonaeus_Nehemias = None
    Schonaeus_Pentecoste = None
    Schonaeus_Pseudostratiotae = None
    Schonaeus_Saulus = None
    Schonaeus_Susanna = None
    Schonaeus_Tobaeus = None
    Schonaeus_Triumphus = None
    Schonaeus_Typhlus = None
    Schonaeus_Vitulus = None
    Schopper_Ectrachelistes = None
    Simonides_Castus = None
    Stymmelius_Isaac = None
    Stymmelius_Studentes = None
    Susius_Pendularia = None
    Telesio_Imber = None
    Vernulaeus_Conradinus = None
    Vernulaeus_Crispus = None
    Vernulaeus_Gorcomienses = None
    Vernulaeus_Henricus = None
    Vernulaeus_Theodoricus = None
    Vladeraccus_Tobias = None
    Weitenauer_Annibal = None
    Wimpheling_Stylpho = None
    Zevecotius_Rosimunda = None
    Zovitius_Didascalus = None
    Zovitius_Ruth = None

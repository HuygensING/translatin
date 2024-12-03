from openpyxl import load_workbook

from tf.core.helpers import console, htmlEsc
from tf.core.files import readYaml

from processhelpers import METADATA_YML, METADATA_FILE


TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<?xml-model
    href="https://xmlschema.huygens.knaw.nl/translatin.rng"
    type="application/xml"
    schematypens="http://relaxng.org/ns/structure/1.0"
?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="{workId}" xml:lang="lat">
<teiHeader>
<fileDesc>
    <titleStmt>
        <title type="main">{titleExpanded}</title>
        <title type="sub">{titleFull}</title>
        <author>{name}</author>
        <editor>{editor}</editor>
        <respStmt>
            <resp>transcription</resp>
            <name>{transcribers}</name>
        </respStmt>
    </titleStmt>
    <publicationStmt>
        <publisher>{publisher}</publisher>
        <pubPlace>{pubPlace}</pubPlace>
        <date>"{pubYear}"</date>
    </publicationStmt>
    <sourceDesc>
        <bibl>
            Identifier: <name>{work}</name><lb/>
            Short title: <title>{titleShort}</title><lb/>
            Year of first edition: <date>{firstEdition}</date><lb/>
            Author information:<lb/>
            Alias: {alias}<lb/>
            Birth: {birth}, {birthPlace}<lb/>
            Death: {death}, {deathPlace}<lb/>
            Floruit: {floruit}, {activity}<lb/>
            {linkRep}<lb/>
            <emph>{source}</emph><lb/>
            {sourceLinkRep}
        </bibl>
    </sourceDesc>
</fileDesc>
<profileDesc>
    <textClass>
        <keywords>
            <term type="diction">{diction}</term>
            <term type="genre">{genre}</term>
            <term type="acts">{acts}</term>
            <term type="chorus">{chorus}</term>
            <term type="medium">{medium}</term>
        </keywords>
    </textClass>
</profileDesc>
</teiHeader>
<text>
    <front>
        {front}
    </front>
    <body>
        {main}
    </body>
    <back>
        {back}
    </back>
</text>
</TEI>
"""


class Meta:
    def __init__(self, Process):
        self.template = TEMPLATE
        self.Process = Process
        self.metaFields = readYaml(asFile=METADATA_YML)
        self.error = False
        self.workById = {}
        self.workByName = {}

    def readMetadata(self, workFiles):
        if self.error:
            return

        console("Collecting excel metadata ...")

        Process = self.Process
        metaFields = self.metaFields

        workById = self.workById
        workByName = self.workByName

        goodWorkFiles = {}

        default = dict(author={}, work={})
        self.default = default

        metadata = dict(author={}, work={})
        self.metadata = metadata
        ws = {}

        try:
            wb = load_workbook(METADATA_FILE, data_only=True)
            ws["author"] = wb["author"]
            ws["work"] = wb["work"]
        except Exception as e:
            Process.warn(heading=f"\t{str(e)}")
            self.error = True
            return goodWorkFiles

        for kind in ("author", "work"):
            (headRow, *rows) = list(ws[kind].rows)

            fields = {i: head.value for (i, head) in enumerate(headRow)}
            fieldInvHead = {v: k for (k, v) in fields.items()}
            fieldInv = {}

            thisDefault = default[kind]

            for field, fieldInfo in metaFields[kind].items():
                column = fieldInfo.column

                if column not in fieldInvHead:
                    Process.warn(
                        work=f"Meta {kind}",
                        ln=0,
                        line=column,
                        heading="Extra column configured",
                    )
                    continue

                fieldInv[column] = field
                thisDefault[field] = fieldInfo.default

                if field in {"link", "sourceLink"}:
                    thisDefault[f"{field}Rep"] = ""

            for v, k in fieldInvHead.items():
                if v not in fieldInv:
                    Process.warn(
                        work=f"Meta {kind}",
                        ln=0,
                        line=v,
                        heading="Column not configured",
                    )
                    del fields[k]

            for r, row in enumerate(rows):
                if not any(c.value for c in row):
                    continue

                rp = r + 1

                thisMeta = {}

                for i, cell in enumerate(row):
                    fieldRep = fields.get(i, None)

                    if fieldRep is None:
                        continue

                    field = fieldInv.get(fieldRep, None)

                    if field is None:
                        Process.warn(
                            work=f"Meta {kind}",
                            ln=rp,
                            line=fieldRep,
                            heading="Column not configured",
                        )
                        continue

                    fieldInfo = metaFields[kind][field]
                    value = cell.value or thisDefault[field]

                    if fieldInfo.tp == "str":
                        value = htmlEsc(str(value).strip())

                    thisMeta[field] = value

                if kind == "author":
                    authorId = thisMeta["author"]

                    if authorId is None:
                        Process.warn(
                            work="author",
                            ln=rp,
                            line=thisMeta["name"],
                            heading="no acro",
                        )
                        continue
                    elif authorId in metadata[kind]:
                        Process.warn(
                            work="author",
                            ln=rp,
                            line=authorId,
                            heading="acro not unique",
                        )
                        continue

                    link = thisMeta.get("link", None)
                    linkRep = f"""<ref target="{link}">Link</ref>""" if link else ""
                    thisMeta["linkRep"] = linkRep

                    metadata[kind][authorId] = thisMeta

                elif kind == "work":
                    sourceLink = thisMeta.get("sourceLink", None)
                    sourceLinkRep = (
                        f"""<ref target="{sourceLink}">Source link</ref>"""
                        if sourceLink
                        else ""
                    )
                    thisMeta["sourceLinkRep"] = sourceLinkRep

                    author = thisMeta["author"] or "Unknown"
                    title = thisMeta["titleShort"]
                    work = f"{author}-{title}"

                    if author != "Unknown" and author not in metadata["author"]:
                        Process.warn(
                            work=work,
                            ln=rp,
                            line=author,
                            heading="author not found",
                        )

                    if work in workFiles:
                        realWork = workFiles[work]
                        goodWorkFiles[work] = realWork

                        thisMeta["work"] = work
                        workId = f"translatin{rp:>04}"
                        metadata[kind][workId] = thisMeta
                        workById[workId] = work
                        workByName[work] = workId

                    else:
                        Process.warn(work=work, ln=rp, heading="metadata but no data")

        for work in sorted(workFiles):
            if work not in workByName:
                Process.warn(work=work, heading="data but no metadata")

        console("Metadata collected.")
        Process.showWarnings()
        return goodWorkFiles

    def fillTemplate(self, workName, **data):
        if self.error:
            return None

        metaFields = self.metaFields
        template = self.template
        metadata = self.metadata
        workByName = self.workByName
        workDefault = self.default["work"]
        authorDefault = self.default["author"]

        workId = workByName.get(workName, None)

        if workId is None or workId not in metadata["work"]:
            thisMetadata = workDefault
        else:
            thisMetadata = metadata["work"][workId]

        author = thisMetadata["author"]

        if author is None or author == "Unknown" or author not in metadata["author"]:
            authorMetadata = authorDefault
        else:
            authorMetadata = metadata["author"][author]

        authorMetadata = {k: v for k, v in authorMetadata.items() if k != "author"}

        return template.format(
            workId=workId,
            **thisMetadata,
            **metaFields["corpus"],
            **authorMetadata,
            **data,
        )

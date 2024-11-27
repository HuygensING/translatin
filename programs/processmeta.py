from openpyxl import load_workbook

from tf.core.helpers import console
from tf.core.files import readYaml

from processhelpers import METADATA_YML, METADATA_FILE


TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<?xml-model
    href="https://dracor.org/schema.rng"
    type="application/xml"
    schematypens="http://relaxng.org/ns/structure/1.0"
?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="{workId}" xml:lang="lat">
<teiHeader>
<fileDesc>
    <titleStmt>
        <title type="main">{titleExpanded}</title>
        <title type="sub">{titleFull}</title>
        <author>{author}</author>
        <editor xml:id="nl">{editor}</editor>
        <respStmt>
            <resp>transcription</resp>
            <name>{transcribers}</name>
        </respStmt>
    </titleStmt>
    <publicationStmt>
        <publisher>{publisher}</publisher>
        <pubPlace>{pubPlace}</pubPlace>
        <date when="{pubYear}/>
    </publicationStmt>
    <sourceDesc>
        <bibl>
            Identifier: <name>{work}</name><lb/>
            Short title: <title>{titleShort}</title><lb/>
            Year of first edition: <date>{firstEdition}"</date><lb/>
            Source type: <emph xml:id="medium">{medium}</emph><lb/>
            Source description: <emph xml:id="source">{source}</emph><lb/>
            <ref target="{sourceLink}">See</ref>
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
        </keywords>
    </textClass>
</profileDesc>
</teiHeader>
<standOff>
</standOff>
Balde-Iephtias
Iephthias
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
    def __init__(self):
        self.template = TEMPLATE
        cfg = readYaml(asFile=METADATA_YML)
        self.cfg = cfg

        corpusMeta = {
            field: props.value for field, props in cfg.items() if "value" in props
        }
        self.corpusMeta = corpusMeta
        self.workFields = set(cfg) - set(corpusMeta)
        self.error = False
        self.workById = {}
        self.workByName = {}

    def readMetadata(self):
        if self.error:
            return

        cfg = self.cfg
        workFields = self.workFields
        workById = self.workById
        workByName = self.workByName

        console("Collecting excel metadata ...")

        default = {}
        self.default = default

        metadata = {}
        self.metadata = metadata

        try:
            wb = load_workbook(METADATA_FILE, data_only=True)
            ws = wb.active
        except Exception as e:
            console(f"\t{str(e)}", error=True)
            self.error = True
            return

        (headRow, *rows) = list(ws.rows)

        fields = {i: head.value for (i, head) in enumerate(headRow)}
        fieldInv = {}

        for field in workFields:
            fieldInfo = cfg[field]
            fieldInv[fieldInfo.column] = field
            default[field] = fieldInfo.default

        for r, row in enumerate(rows):
            if not any(c.value for c in row):
                continue

            thisMeta = {}

            for i, cell in enumerate(row):
                field = fieldInv[fields[i]]
                value = cell.value or default[field]
                thisMeta[field] = value

            work = f"{thisMeta['author']}-{thisMeta['titleShort']}"
            thisMeta["work"] = work
            workId = f"translatin{r + 1:>04}"
            metadata[workId] = thisMeta
            workById[workId] = work
            workByName[work] = workId

    def fillTemplate(self, workName, **data):
        if self.error:
            return None

        template = self.template
        metadata = self.metadata
        corpusMeta = self.corpusMeta
        workByName = self.workByName

        workId = workByName[workName]

        if workId not in metadata:
            return None

        return template.format(workId=workId, **metadata[workId], **corpusMeta, **data)

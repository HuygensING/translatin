[![Project Status: Inactive – The project has reached a stable, usable state but is no longer being actively developed; support/maintenance will be provided as time allows.](https://www.repostatus.org/badges/latest/inactive.svg)](https://www.repostatus.org/#inactive)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14859915.svg)](https://doi.org/10.5281/zenodo.14859915)

# TransLatin overview

There are three repositories in
[GitHub/HuygensING](https://github.com/HuygensING)
that contain data produced by the Translatin project:

*   [translatin-wemi](https://github.com/HuygensING/translatin-wemi)
    Metadata preparation and analysis to identify works, expressions, manifestations
    and items (wemi), in the
    [FRBR sense](https://en.wikipedia.org/wiki/Functional_Requirements_for_Bibliographic_Records)

*   [translatin-manif](https://github.com/HuygensING/translatin-manif)
    Publication of a selection of manifestations, as
    [text-fabric](https://github.com/annotation/text-fabric) files, with an
    [annotation](https://annotation.github.io/text-fabric/tf/convert/watm.html) export
    to the publishing pipeline of TeamText of HuC-DI.

*   [translatin](https://github.com/HuygensING/translatin)
    Data production for the final published result of the project: a collection
    of 100+ medieval, latin dramas.

The most comprehensive information on Translatin, the project, the people involved,
the data and the programs, is in
[translatin-manif](https://github.com/HuygensING/translatin-manif).

## About this repo

The final result of the Translatin project is a website with a selection of
100+ medieval, latin dramas.

The source data consists of word documents, collected by Jan Bloemendal, and
then curated with the help of Dirk Roorda.

The result has been sent through a pipeline of conversions into a stream of
annotations that can be presented by TAV (Text Annoviz), the Team Text front end by
which corpora can be published on the Web.

## Curation

We curated the source documents in a number of steps in order to arrive at a set of
well-defined and well-formed pieces of text with meaningful and handy file names.

The stages of this process can be inspected in the directory
[datasource/transcriptions](datasource/transcriptions).
Here are the successive steps:

1.  **docx** Every input Word document is a drama.
    We gave all documents a concise name, of the form `aaa - www.docx`
    We weeded out excessive formatting, which mostly derived from html origins.
    Jan went through every document and marked the front, main and back parts.

2.  **mdOrig** The result of a mechanical conversion from word to markdown, done by the
    [PanDoc program](https://pandoc.org).

3.  **mdRefined** The result of applying heuristics to the markdown of the
    previous steps. We detected sections haeadings and captions for acts,
    scenes, choruses, etc. We detected line numbers, page numbers and folio references,
    and wrapped them in special markers.
    During this process, Dirk has inspected every document and has written regular
    expressions tailored to each work to extract the numbers and headings.

4.  **teiSimple** The result of a mechanical conversion from markdown to
    [TEI](https://tei-c.org), done by the
    [PanDoc program](https://pandoc.org).

5.  **tei** The result of the curation is a set of TEI files in
    [tei](tei). The main purpose of this step is to add appropriate metadata to the
    teiHeader parts of the documents. This metadata comes from a
    [spreadsheet](datasource/work-author.xlsx) prepared by Jan, with metadata on works
    and authors.

Reports of what these steps encountered and did can be found in the
[report/trans](report/trans) directory.

Another part of the curation was to select/customize a TEI schema that is
geared to drama texts. We used the 
[Roma tool](https://roma.tei-c.org) to customize TEI's module
[performance texts](https://tei-c.org/release/doc/tei-p5-doc/en/html/DR.html).

However, although this schema contains sophisticated elements to encode all aspects
of drama texts that are worth marking up, we have not actually tried to use those
elements, because that was one step to far within the boundaries of the current
project. We used the schema, and all documents validate against it, but the documents
are all marked up using only the more generic elements of the TEI.

It is possible to gradually up-convert the current TEI to versions that make more use
of the dramatic markup, and it can be done with the present [schema](schema).

## Conversion

The curation results, the TEI documents with proper metadata, are then pushed through
a publishing pipeline. Here are the steps.

1.  **Validation** We validated each document against the schema. We also produced
    some reports on element usage, id-references etc. See the
    [report/tei](report/tei) directory.

2.  **Text-Fabric** We converted the TEI documents to a
    [Text-Fabric](https://github.com/annotation/text-fabric/tree/master) datasource.
    See the
    [TF docs](https://annotation.github.io/text-fabric/tf/about/install.html) on how to
    install and use Text-Fabric.
    For this project, Text-Fabric is mainly used as a swiss-army-knife to untangle
    the TEI markup from the content and produce a stream of (web) annotations
    with the same information content.

3.  **WATM** Web Annotation Text Model. This is a raw data format that encodes the
    information to be contained in web annotations. These annotations will be displayed
    on the web, and they constitute, together with the plain text, the documents
    as they can be browsed and searched on the web.

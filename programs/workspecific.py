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


class WorkSpecific:
    @staticmethod
    def identity(text):
        return text

    @staticmethod
    def Laurimanus_Exodus(text):
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

        text = HEAD_PAGENUM_RE.sub(r"«page \1»", text)

        return text

    @staticmethod
    def Laurimanus_Miles(text):
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
            re.X | re.M
        )
        text = markRe.sub("", text)

        text = HEAD_PAGENUM_RE.sub(r"«page \1»", text)

        return text

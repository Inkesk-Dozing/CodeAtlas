from parsers.base import BaseParser, ParseResult
from parsers.golang import GoParser
from parsers.javascript import JavaScriptParser
from parsers.python import PythonParser
from parsers.rust import RustParser

_parsers: dict[str, BaseParser] = {}


def get_parser(language: str) -> BaseParser | None:
    if language in _parsers:
        return _parsers[language]

    if language in ("typescript", "javascript"):
        parser = JavaScriptParser(language)
    elif language == "python":
        parser = PythonParser()
    elif language in ("go", "golang"):
        parser = GoParser()
    elif language in ("rust", "rs"):
        parser = RustParser()
    else:
        return None

    _parsers[language] = parser
    return parser


__all__ = ["BaseParser", "GoParser", "ParseResult", "RustParser", "get_parser"]

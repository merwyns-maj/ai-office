"""Parser for the small YAML subset the office files use (stdlib has no YAML).

Supported: block mappings and lists (spaces only), flow lists and maps (nested),
quoted and plain scalars, comments. Everything else raises YamlError.
"""
import re


class YamlError(ValueError):
    def __init__(self, source, line, msg):
        super().__init__(f"{source}:{line}: {msg}")
        self.source = source
        self.line = line
        self.msg = msg


_INT = re.compile(r"^[-+]?\d+$")
_FLOAT = re.compile(r"^[-+]?\d+\.\d+$")
_BLOCK_SCALAR = re.compile(r"^[|>][+-]?\d*$")
_QUOTE_PREV = " \t[{,"


def _strip_comment(s):
    """Drop a trailing comment ('#' at start or after whitespace, not in quotes)."""
    q = None
    i = 0
    while i < len(s):
        c = s[i]
        if q:
            if q == '"' and c == "\\":
                i += 2
                continue
            if c == q:
                if q == "'" and s[i + 1:i + 2] == "'":
                    i += 2
                    continue
                q = None
        elif c in "\"'" and (i == 0 or s[i - 1] in _QUOTE_PREV):
            q = c
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
        i += 1
    return s.rstrip()


def _unquote(tok, source, line):
    q = tok[0]
    out = []
    i = 1
    while i < len(tok):
        c = tok[i]
        if q == '"' and c == "\\":
            nxt = tok[i + 1:i + 2]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/"}.get(nxt, "\\" + nxt))
            i += 2
            continue
        if c == q:
            if q == "'" and tok[i + 1:i + 2] == "'":
                out.append("'")
                i += 2
                continue
            if tok[i + 1:].strip():
                raise YamlError(source, line, f"unexpected text after closing quote: {tok[i + 1:].strip()!r}")
            return "".join(out)
        out.append(c)
        i += 1
    raise YamlError(source, line, f"unterminated quoted string: {tok!r}")


def _scalar(tok, source, line):
    tok = tok.strip()
    if tok == "":
        return None
    if tok[0] in "\"'":
        return _unquote(tok, source, line)
    if tok[0] in "&*!":
        raise YamlError(source, line, f"unsupported YAML construct (anchor, alias or tag): {tok!r}")
    if _BLOCK_SCALAR.match(tok):
        raise YamlError(source, line, "unsupported YAML construct: block scalar")
    if tok in ("null", "~"):
        return None
    if tok == "true":
        return True
    if tok == "false":
        return False
    if _INT.match(tok):
        return int(tok)
    if _FLOAT.match(tok):
        return float(tok)
    return tok


class _Flow:
    """Recursive-descent parser for one flow collection on a single line."""

    def __init__(self, s, source, line):
        self.s, self.source, self.line, self.pos = s, source, line, 0

    def err(self, msg):
        return YamlError(self.source, self.line, msg)

    def ws(self):
        while self.pos < len(self.s) and self.s[self.pos] in " \t":
            self.pos += 1

    def peek(self):
        return self.s[self.pos] if self.pos < len(self.s) else ""

    def parse_top(self):
        v = self.value()
        self.ws()
        if self.pos != len(self.s):
            raise self.err(f"unexpected text after flow collection: {self.s[self.pos:]!r}")
        return v

    def value(self):
        self.ws()
        c = self.peek()
        if c == "[":
            return self.seq()
        if c == "{":
            return self.map()
        if c in ("\"", "'"):
            return _unquote(self.quoted(), self.source, self.line)
        start = self.pos
        while self.pos < len(self.s) and self.s[self.pos] not in ",]}":
            self.pos += 1
        return _scalar(self.s[start:self.pos], self.source, self.line)

    def quoted(self):
        q = self.s[self.pos]
        i = self.pos + 1
        while i < len(self.s):
            c = self.s[i]
            if q == '"' and c == "\\":
                i += 2
                continue
            if c == q:
                if q == "'" and self.s[i + 1:i + 2] == "'":
                    i += 2
                    continue
                tok = self.s[self.pos:i + 1]
                self.pos = i + 1
                return tok
            i += 1
        raise self.err("unterminated quoted string in flow collection")

    def seq(self):
        self.pos += 1
        out = []
        while True:
            self.ws()
            if self.peek() == "]":
                self.pos += 1
                return out
            if self.peek() == "":
                raise self.err("unterminated flow list")
            out.append(self.value())
            self.ws()
            if self.peek() == ",":
                self.pos += 1
            elif self.peek() != "]":
                raise self.err("expected ',' or ']' in flow list")

    def map(self):
        self.pos += 1
        out = {}
        while True:
            self.ws()
            if self.peek() == "}":
                self.pos += 1
                return out
            if self.peek() == "":
                raise self.err("unterminated flow map")
            if self.peek() in ("\"", "'"):
                key = _unquote(self.quoted(), self.source, self.line)
                self.ws()
                if self.peek() != ":":
                    raise self.err("expected ':' after key in flow map")
                self.pos += 1
            else:
                start = self.pos
                while True:
                    j = self.s.find(":", self.pos)
                    if j < 0 or self.s[j + 1:j + 2] not in (" ", "\t", ",", "}", ""):
                        if j < 0:
                            raise self.err("expected 'key: value' in flow map")
                        self.pos = j + 1
                        continue
                    key = self.s[start:j].strip()
                    self.pos = j + 1
                    break
                if not key or any(ch in key for ch in ",{}[]"):
                    raise self.err(f"bad key in flow map: {key!r}")
            if key in out:
                raise self.err(f"duplicate key {key!r}")
            out[key] = self.value()
            self.ws()
            if self.peek() == ",":
                self.pos += 1
            elif self.peek() != "}":
                raise self.err("expected ',' or '}' in flow map")


def _split_key(content):
    """Return (key, rest) for 'key: rest' / 'key:', or None if not a mapping line."""
    if content[0] in "\"'":
        q = content[0]
        i = 1
        while i < len(content):
            if q == '"' and content[i] == "\\":
                i += 2
                continue
            if content[i] == q:
                break
            i += 1
        else:
            return None
        after = content[i + 1:]
        if after.startswith(":") and (len(after) == 1 or after[1] in " \t"):
            return content[1:i], after[1:].strip()
        return None
    i = 0
    while True:
        j = content.find(":", i)
        if j < 0:
            return None
        if j + 1 == len(content) or content[j + 1] in " \t":
            return content[:j].strip(), content[j + 1:].strip()
        i = j + 1


class _Parser:
    def __init__(self, text, source, offset):
        self.source = source
        self.lines = []  # (indent, content, lineno)
        for n, raw in enumerate(text.split("\n"), 1 + offset):
            raw = raw.rstrip("\r")
            body = raw.lstrip(" ")
            indent = len(raw) - len(body)
            if body.startswith("\t") or (not body.strip() and "\t" in raw):
                if body.strip():
                    raise YamlError(source, n, "tabs are not allowed for indentation")
            content = _strip_comment(body)
            if not content:
                continue
            if "\t" in raw[:indent]:
                raise YamlError(source, n, "tabs are not allowed for indentation")
            if content in ("---", "..."):
                raise YamlError(source, n, "unsupported YAML construct: multi-document marker")
            self.lines.append((indent, content, n))

    def parse(self):
        if not self.lines:
            return None
        indent = self.lines[0][0]
        value, i = self.block(0, indent)
        if i < len(self.lines):
            raise YamlError(self.source, self.lines[i][2], "unexpected indentation")
        return value

    def block(self, i, indent):
        content = self.lines[i][1]
        if content == "-" or content.startswith("- "):
            return self.seq(i, indent)
        return self.map(i, indent)

    def inline(self, rest, line):
        if rest[0] in "[{":
            return _Flow(rest, self.source, line).parse_top()
        return _scalar(rest, self.source, line)

    def nested(self, i, indent, line):
        """Value of an empty-valued key / '-' item at lines[i-1]; returns (value, next_i)."""
        if i < len(self.lines):
            ni, nc, _ = self.lines[i]
            if ni > indent:
                return self.block(i, ni)
        return None, i

    def map(self, i, indent):
        out = {}
        while i < len(self.lines):
            ind, content, n = self.lines[i]
            if ind < indent:
                break
            if ind > indent:
                raise YamlError(self.source, n, "unexpected indentation")
            if content == "-" or content.startswith("- "):
                raise YamlError(self.source, n, "list item where a 'key: value' line was expected")
            kv = _split_key(content)
            if kv is None:
                raise YamlError(self.source, n, f"expected 'key: value', got {content!r}")
            key, rest = kv
            if key in out:
                raise YamlError(self.source, n, f"duplicate key {key!r}")
            if rest == "":
                i += 1
                if i < len(self.lines) and self.lines[i][0] == indent and (
                        self.lines[i][1] == "-" or self.lines[i][1].startswith("- ")):
                    out[key], i = self.seq(i, indent)
                else:
                    out[key], i = self.nested(i, indent, n)
            else:
                out[key] = self.inline(rest, n)
                i += 1
        return out, i

    def seq(self, i, indent):
        out = []
        while i < len(self.lines):
            ind, content, n = self.lines[i]
            if ind < indent:
                break
            if ind > indent:
                raise YamlError(self.source, n, "unexpected indentation")
            if not (content == "-" or content.startswith("- ")):
                break
            rest = content[1:].strip()
            if rest == "":
                v, i = self.nested(i + 1, indent, n)
                out.append(v)
                continue
            if rest[0] not in "\"'[{" and _split_key(rest) is not None:
                raise YamlError(self.source, n, "unsupported YAML construct: block mapping inside a list item (use a flow map { k: v })")
            out.append(self.inline(rest, n))
            i += 1
        return out, i


def _loads(text, source, offset):
    return _Parser(text, source, offset).parse()


def loads(text, source="<string>"):
    return _loads(text, source, 0)


def split_frontmatter(text, source):
    """Return (frontmatter dict, body) for a markdown file that starts with a '---' block."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        raise YamlError(source, 1, "no frontmatter: file must start with a '---' line")
    for k in range(1, len(lines)):
        if lines[k].rstrip("\r") == "---":
            meta = _loads("\n".join(lines[1:k]), source, 1)
            if meta is None:
                meta = {}
            if not isinstance(meta, dict):
                raise YamlError(source, 2, "frontmatter must be a mapping")
            return meta, "\n".join(lines[k + 1:])
    raise YamlError(source, 1, "frontmatter has no closing '---' line")

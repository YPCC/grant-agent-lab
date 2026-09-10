"""Tiny YAML subset used so the harness has no required third-party deps."""
from __future__ import annotations

from typing import Any


def parse_simple_yaml(text: str) -> Any:
    """Parse a restricted YAML subset: mappings, lists of mappings, scalars, inline lists."""
    lines = text.splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    i = 0

    def parent_at(indent: int) -> Any:
        while stack and stack[-1][0] >= indent:
            stack.pop()
        return stack[-1][1]

    def coerce(raw: str) -> Any:
        s = raw.strip()
        if s == "" or s in ("null", "~"):
            return None
        if s in ("true", "True", "yes") and raw.strip() in ("true", "True"):
            return True
        if s in ("false", "False") and raw.strip() in ("false", "False"):
            return False
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if not inner:
                return []
            return [coerce(p.strip()) for p in _split_csv(inner)]
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
        try:
            if "." in s:
                return float(s)
        except ValueError:
            pass
        return s

    def _split_csv(inner: str) -> list[str]:
        parts, buf, quote = [], [], None
        for ch in inner:
            if quote:
                if ch == quote:
                    quote = None
                buf.append(ch)
            elif ch in "\"'":
                quote = ch
                buf.append(ch)
            elif ch == ",":
                parts.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        if buf:
            parts.append("".join(buf))
        return parts

    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        parent = parent_at(indent)

        if stripped.startswith("- "):
            item_body = stripped[2:]
            if isinstance(parent, list):
                target_list = parent
            else:
                raise ValueError(f"list item without list parent: {stripped}")
            if ":" in item_body and not item_body.startswith("[") and not (
                item_body.startswith("'") or item_body.startswith('"')
            ):
                key, _, rest = item_body.partition(":")
                obj: dict[str, Any] = {}
                rest = rest.strip()
                if rest:
                    obj[key.strip()] = coerce(rest)
                target_list.append(obj)
                stack.append((indent, obj))
            else:
                target_list.append(coerce(item_body))
            continue

        if ":" in stripped:
            key, _, rest = stripped.partition(":")
            key = key.strip()
            rest = rest.strip()
            if not isinstance(parent, dict):
                raise ValueError(f"mapping entry under non-mapping: {stripped}")
            if rest == "" or rest == "|":
                # look ahead: list or nested mapping
                j = i
                child_indent = None
                is_list = False
                while j < len(lines):
                    peek = lines[j]
                    if not peek.strip() or peek.lstrip().startswith("#"):
                        j += 1
                        continue
                    child_indent = len(peek) - len(peek.lstrip(" "))
                    is_list = peek.lstrip().startswith("- ")
                    break
                if child_indent is not None and child_indent > indent:
                    child: Any = [] if is_list else {}
                    parent[key] = child
                    stack.append((indent, child))
                else:
                    parent[key] = "" if rest == "" else rest
            else:
                parent[key] = coerce(rest)
            continue
        raise ValueError(f"unparsed yaml line: {raw}")

    return root

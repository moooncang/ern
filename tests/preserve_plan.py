#!/usr/bin/env python3
"""Preserve the original story and interaction contracts during asset upgrades.

Baselines were captured from commit bceb51b. No Git history, packages, or server
are needed to run this check. New wrappers, layouts, classes, decorative images,
and SVG interiors are allowed across the site. Original body copy, link
destinations, form controls, and source facts remain protected.
The four explicitly approved lord's margin notes are validated separately;
only their exact text may be excluded from the original content digest.
"""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# User-authorized additions; the original page fingerprints remain unchanged.
LORD_NOTES = {
    "home.html": ("우물과 곳간부터 확인.", "세금을 올리면 촌락이 반발.", "가을 공납 몫은 따로."),
    "world.html": ("서쪽 통행세 확인.",),
}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

# Original bceb51b fingerprints; update only for an explicitly approved redesign.
BASELINE = {
    "pages": {
        "char/a.html": {
            "content": "922273842ea6cde5622cba38148aae5cb5a68d8194eec055037fd102e1639fe5",
            "semantic": "2a320700c0a029734493c31db458aa20dd591e9baf0966f3253095ac1e174265"
        },
        "char/b.html": {
            "content": "7ab1284c0b6885dadb42e927a5a5d99cd6154872ca0bad1037466853e0f7ebec",
            "semantic": "bcee647913a41f3504259874dcc07b150ad2d5a41ab735a09c121599e0c7fa5c"
        },
        "char/c.html": {
            "content": "09437fe835a46cca0b34c2a57c315b729323829815b32e37b902603167c64d13",
            "semantic": "07c18cc587efe0b2cd405f71d80e0a938d8172997fcfc119d905bbb5b93cebd8"
        },
        "char/d.html": {
            "content": "a82dbf638af25311ec91efe34adec1e1b9d1c0305ad29a691279e4812e66fb46",
            "semantic": "781758582609ff1078c8155af84a12fcb719e5079f7d3f6da5f8f0f5a550ad8c"
        },
        "char/e.html": {
            "content": "daa2ade9f24d09e5332a7a16f086fca0a604d1707241ba12fb3749de4d250e45",
            "semantic": "2767c07ce42712b2691852f99f7f7ebba59bedf5f98179986cebb589f0e0d5fd"
        },
        "char/f.html": {
            "content": "bdc5de22e3f205b19cb1f48c9ae5cb3a8cfa57ade5ce807975982616ec9137e2",
            "semantic": "6b7fa930422024b742d72f57d7e64eb9b46cf6e429ab8c7d2c36cdafbe85da54"
        },
        "char/g.html": {
            "content": "f9e015b6068b59601acd0a4593196ef5e9f7bd2d00f3f5932ab1fb4182a7e56e",
            "semantic": "bd707766343185315cf76d00034a25f628f2088eb798ac2ae34a5236b2e0015f"
        },
        "char/h.html": {
            "content": "d1d0ada2460bba9000685bb2c7201ecf2ed1ff5c18b440f01cddbc2a02fee407",
            "semantic": "d40e472a6f0ac7579cfde3e6431b4c4128dd2992ca4a42d07c72e79e69d2feb7"
        },
        "char/i.html": {
            "content": "80e2ec85b0a67431ad8ee219988606254e3f938402ef126935afbb39404a9d1d",
            "semantic": "5894a487d049b372023d2422a0694b11b08c16b9336362d09106554ad8820a4a"
        },
        "char/j.html": {
            "content": "27a1c3effa2ab6133bf9b99eb81ba1aec4bec044098b527356f45bb91ca0f4c4",
            "semantic": "5f2c6b1db81a15941cbcec136e7067a88b10c571040d55fceaf4f15b59267342"
        },
        "char/k.html": {
            "content": "45402383d7404e686ce8db69174880c44ff0454efb0b63b45f52a8b270c3e044",
            "semantic": "6d52f8c941c9ec57b39ba43fd77fa0e027a24e5187758f7f1dc366a68e371e3b"
        },
        "char/l.html": {
            "content": "180f619b1f4777a96c10185f8ca1e5b2d22943d623ec461cf304184c256fa620",
            "semantic": "4e8f9e3b45a78a5799d6939a14e5ab3c05913b444c5eacdb84068cbd7ae6cb1c"
        },
        "characters.html": {
            "content": "d41f29f78f119eba8057e3a95060e4fcb54ece4130f91f5839c41c20f4172d58",
            "semantic": "9d820925ffdcbe6a9410bebb9707a2ac83fa239146c94a65bef7ec4212336804"
        },
        "domain.html": {
            "content": "5c653461591722d1dbb08c824d644c1bd98b616fc71a1c56a3f4b8201fe09e53",
            "semantic": "dff333aabf034b3ac65981de818631919209b7b441be1ee9cafd5081e806cc6c"
        },
        "home.html": {
            "content": "243c76a8f0f1aca0d1c6bf7230b4270347c2cebe05b4090bd9fd04be29d3f508",
            "semantic": "044550dcbf96296665ba52330b3c5ffd6b5af00e3b2804941f45f8004dec7510"
        },
        "index.html": {
            "content": "ef4f7d94851a72f3e8fe8e1efb953c1f2301b61a4954a58cd0ebcef5d463bfda",
            "semantic": "a143516f2e6d0b985c271bf4af9992b5c543682be3f87061d88e78a13054c828"
        },
        "start.html": {
            "content": "4e2bc49d56098077be22ab5d38801f33ca3687d12396eb51812b09b78b8b1103",
            "semantic": "471d675ec078e84ba236f99d79f901d0d1e07ddc418f2bfa600597a74e077d22"
        },
        "world.html": {
            "content": "d38aa0ba52444f61b2ec6779eb83bcd0563ba1aa5da07961257ee4e6b271217a",
            "semantic": "38f2a7c4b67f816eb0374541d95360d7c4a6d1a2fa6fa5cb10ae8953151cb177"
        }
    },
    "protected": {
        "PLAN.md": "bb48ebb1385031da1f4b8872616ab1fd6b45fc41914b864bcc3198464e36e398",
        "_build/data.py": "47d73ca1d9efef99f3430033c5d6c5ea28221b426a0e3a98c66c9c89b2c00057"
    }
}


class BodySignature(HTMLParser):
    def __init__(self, exclude_lord_notes=False):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.svg_depth = 0
        self.script_depth = 0
        self.structure = []
        self.words = []
        self.elements = []
        self.exclude_lord_notes = exclude_lord_notes
        self.note_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs = [(key, value.split("?")[0] if key == "src" and value else value) for key, value in attrs]
        if tag == "body":
            self.in_body = True
        if not self.in_body:
            return
        if self.exclude_lord_notes:
            if self.note_depth and tag not in VOID_TAGS:
                self.note_depth += 1
            elif "data-lord-note" in dict(attrs):
                self.note_depth = 1
        if self.svg_depth:
            if tag == "svg":
                self.svg_depth += 1
            return
        self.elements.append((tag, dict(attrs)))
        self.structure.append(["start", tag, sorted(attrs)])
        if tag == "svg":
            self.svg_depth = 1
        if tag == "script":
            self.script_depth += 1

    def handle_endtag(self, tag):
        if not self.in_body:
            return
        if self.note_depth:
            self.note_depth -= 1
        if self.svg_depth:
            if tag == "svg":
                self.svg_depth -= 1
                if not self.svg_depth:
                    self.structure.append(["end", "svg"])
            return
        self.structure.append(["end", tag])
        if tag == "script":
            self.script_depth = max(0, self.script_depth - 1)
        if tag == "body":
            self.in_body = False

    def handle_startendtag(self, tag, attrs):
        if self.in_body and not self.svg_depth:
            self.elements.append((tag, dict(attrs)))
            self.structure.append(["empty", tag, sorted(attrs)])

    def handle_data(self, data):
        if self.in_body and not self.svg_depth and not self.script_depth and not self.note_depth:
            self.words.append(data)


class LordNoteAudit(HTMLParser):
    """Validate additions before the content parser is allowed to omit them."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.active = None
        self.open_tags = []
        self.notes = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "body":
            self.in_body = True
        if "data-lord-note" in attrs:
            if self.active is not None:
                self.errors.append("lord notes may not contain another lord note")
            else:
                self.active = []
                self.notes.append(self.active)
                if tag != "aside" or not self.in_body:
                    self.errors.append("lord notes must be aside elements inside the body")
        if self.active is None:
            return
        # Formatting spans are permitted, but these additions must not acquire
        # controls, hidden script/style text, or additional accessible labels.
        if tag not in ("aside", "span"):
            self.errors.append(f"lord note contains unexpected <{tag}>")
        forbidden = {"tabindex", "contenteditable", "accesskey", "autofocus", "href", "role",
                     "aria-label", "aria-labelledby", "aria-describedby", "title", "alt"}
        if forbidden.intersection(attrs) or any(key.startswith("on") for key in attrs):
            self.errors.append("lord notes must be noninteractive and contain no additional labels")
        if tag not in VOID_TAGS:
            self.open_tags.append(tag)

    def handle_endtag(self, tag):
        if self.active is not None:
            if not self.open_tags or self.open_tags[-1] != tag:
                self.errors.append("lord note markup must be properly closed")
            if self.open_tags:
                self.open_tags.pop()
            if not self.open_tags:
                self.active = None
        if tag == "body":
            self.in_body = False

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.active is not None:
            self.active.append(data)


def lord_note_contracts(html, page):
    parser = LordNoteAudit()
    parser.feed(html)
    if parser.active is not None:
        parser.errors.append("lord note is not closed")
    actual = ["".join(parts).strip() for parts in parser.notes]
    expected = LORD_NOTES.get(page, ())
    if sorted(actual) != sorted(expected):
        parser.errors.append(f"expected only the {len(expected)} exact authorized lord notes; found {actual!r}")
    return parser.errors


def signatures(html, exclude_lord_notes=False):
    parser = BodySignature(exclude_lord_notes=exclude_lord_notes)
    parser.feed(html)
    text = " ".join(" ".join(parser.words).split())
    control_keys = {
        "name", "min", "max", "step", "maxlength", "placeholder", "data-season",
        "data-g", "data-e", "data-d", "data-reset", "data-f", "data-m", "data-n",
        "data-domain-input", "data-copy",
    }
    links, controls = [], []
    for tag, attrs in parser.elements:
        # The entry seal may be either a named link or a button; entry_contracts
        # checks that separately. Artwork or wrappers do not enter this digest.
        if "data-seal" in attrs:
            continue
        if tag == "a" and "href" in attrs:
            links.append(attrs["href"])
        if tag in ("input", "button", "select", "textarea"):
            properties = {key: value for key, value in attrs.items() if key in control_keys}
            if tag == "input":
                properties["type"] = attrs.get("type", "text")
            controls.append([tag, sorted(properties.items())])
    semantic = json.dumps({"links": sorted(links), "controls": sorted(controls, key=repr)}, ensure_ascii=False)
    return {
        "content": sha256(json.dumps(sorted(re.findall(r"\S+", text)), ensure_ascii=False).encode()).hexdigest(),
        "semantic": sha256(semantic.encode()).hexdigest(),
    }


def entry_contracts(html):
    """Check the entry's user-facing contract without prescribing its geometry."""
    parser = BodySignature()
    parser.feed(html)
    errors = []
    elements = parser.elements

    def marked(attribute):
        return [(tag, attrs) for tag, attrs in elements if attribute in attrs]

    for attribute in ("data-writ", "data-seal", "data-domain-input", "data-enter"):
        if len(marked(attribute)) != 1:
            errors.append(f"entry requires exactly one [{attribute}]")
    if sum(tag == "main" for tag, _ in elements) != 1:
        errors.append("entry requires one main landmark")
    names = marked("data-domain-input")
    if len(names) == 1:
        tag, attrs = names[0]
        if tag != "input" or attrs.get("maxlength") != "12":
            errors.append("entry name must remain a 12-character input")
        if not attrs.get("id") or not any(t == "label" and a.get("for") == attrs["id"] for t, a in elements):
            errors.append("entry name input requires its visible label")
    enters = marked("data-enter")
    if len(enters) == 1 and (enters[0][0] != "a" or enters[0][1].get("href") != "home.html"):
        errors.append("entry CTA must retain its home.html destination")
    seals = marked("data-seal")
    if len(seals) == 1:
        tag, attrs = seals[0]
        if tag not in ("a", "button") or not attrs.get("aria-label"):
            errors.append("seal must remain a named keyboard-operable control")
    return errors


def main():
    failures = []
    for name, expected in BASELINE["pages"].items():
        path = ROOT / name
        if not path.is_file():
            failures.append(f"{name}: original page missing")
            continue
        html = path.read_text(encoding="utf-8")
        note_errors = lord_note_contracts(html, name)
        failures.extend(f"{name}: {message}" for message in note_errors)
        # Invalid notes are never granted an exclusion from the original hash.
        actual = signatures(html, exclude_lord_notes=not note_errors)
        for part in ("content", "semantic"):
            if actual[part] != expected[part]:
                failures.append(f"{name}: original body {part} changed")
        if name == "index.html":
            failures.extend(f"index.html: {message}" for message in entry_contracts(html))
    actual_pages = {p.relative_to(ROOT).as_posix() for p in ROOT.glob("*.html")} | {
        p.relative_to(ROOT).as_posix() for p in (ROOT / "char").glob("*.html")
    }
    unexpected = sorted(actual_pages - BASELINE["pages"].keys())
    if unexpected:
        failures.append(f"Unexpected pages: {', '.join(unexpected)}")
    for name, expected in BASELINE["protected"].items():
        path = ROOT / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(f"{name}: protected original file changed")
    if failures:
        print("Original-site preservation FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print("PASS: all 18 pages preserve original copy, semantic link destinations, and input/control contracts.")
    print("PASS: new layouts, wrappers, artwork, and SVG interiors are allowed; entry seal/name/home semantics remain intact.")
    print("PASS: original PLAN.md and _build/data.py source facts are byte-for-byte unchanged.")
    print("PASS: exactly three home and one world margin notes match the authorized text and are noninteractive.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

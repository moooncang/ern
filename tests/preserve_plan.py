#!/usr/bin/env python3
"""Preserve the original story/site while allowing the approved envelope design.

Baselines were captured from commit bceb51b. No Git history, packages, or server
are needed to run this check. The entry may change wrappers, classes and layout,
but keeps its original copy and seal/name/home semantics. The other 17 pages
keep their original body structure. SVG artwork and head wiring are excluded.
"""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# Original bceb51b fingerprints; update only for an explicitly approved redesign.
BASELINE = {
    "pages": {
        "char/a.html": {
            "structure": "51f632114305a77ea01c99bf7d11723499f9d306ee246a95230951a543caf7fd",
            "text": "4a46c00f33d83f814e78f0aff242e0bb2ca1ca8c7026edc54f42656c8465aff1"
        },
        "char/b.html": {
            "structure": "3cee240712aeccf8f78c8122008e59a91e0420a4eca0efdb65b9fc4bcb22520d",
            "text": "f26e2a66ea5214f4d3dcf5cee310925ea9592345b463c7370ba5bb51a3fb9114"
        },
        "char/c.html": {
            "structure": "c82426c3ebe0fcd166344f17d828f7759e9b0bd24c98bf0b4aeb49c188317fe1",
            "text": "bb26376cab1ee69650bd5cb5cb5f382f8a8901699ef45c239be4e46ea4301646"
        },
        "char/d.html": {
            "structure": "e72b49a03ec386f7ab6813ae77e1faa55ba2bf7d570875580bad9a4e32790371",
            "text": "3abc63341da24c8e3e4302fc13da97277cd51aefdccff49eb38974ab8cc8fb68"
        },
        "char/e.html": {
            "structure": "498ecfbae1becbd4ddfc0071321c558f0e88ea17e6a729c5fc4ec9533da5da58",
            "text": "8a6e264b993052dca1e9d6a3f57b5581722b88c9f6ce705f1b96c3ded4701e6a"
        },
        "char/f.html": {
            "structure": "d214dfc81710d1af7c791c81ef999446a6db231ed8b4084f875aa6a2020fee8c",
            "text": "5a5eb802e4ea33e0b3826df9ea77890ab0925ea81ca035a60fe2249b64573ee3"
        },
        "char/g.html": {
            "structure": "4c2535d2e6ed830ed2b341eacd22954ae0ad02b1661fea0573944a109e7228f6",
            "text": "bd6448e7854a90867d2aa85800f6c44cca92600e0f9a30a16ee173ca3cfb606b"
        },
        "char/h.html": {
            "structure": "14e658817ee1e16b55309dc06750fcf58bcce09867fa0a92470c4cdeafde348f",
            "text": "b7e874656ceeb4e4c3ceade80144993ad3700f1ecd86d9d6e31937f560cb4013"
        },
        "char/i.html": {
            "structure": "291a06618bbccb5f160ca9542dea6aac43f424ef013c60c61588b78e89487fbe",
            "text": "9d0ef0fe6ad88920d27951f38c9fc53486593dc931a0d0242c1e53f9bf2ab1a1"
        },
        "char/j.html": {
            "structure": "7ce00815535668c86b0d2b63cfde6416480a3fb572822ef186b2dcb5a2e82f21",
            "text": "23d8f8308337f10d2f8af6966dad1a654d8ac05e0c1e5ae89de714217bb6c8f2"
        },
        "char/k.html": {
            "structure": "680722a8e528a6af478d9d99d7090c5a4d745b8f99da88728fb39b273d602dcb",
            "text": "104808b5c66e994a146c74929a3e6d066fe5ab359287df30cb2559754a65dfa4"
        },
        "char/l.html": {
            "structure": "c99f3740be2d8da41cb4c88fea413f3ef89a0c36b9edc426f802be6d00bf0494",
            "text": "e98d4e71e99f552ebd82610fd737f25212aa7eb83cdef44b91e4a8c90feb027d"
        },
        "characters.html": {
            "structure": "88433ae48b0feccb56b71acbf7cd0d8deaf00740059e5dd651e7657d6a6f37f5",
            "text": "8824d3c7c60f3bd7184f969b95029de88a2f63d6b1648f5638d94097ce8796df"
        },
        "domain.html": {
            "structure": "767ba2f1f6b5f39d27f6ea342f46aac54f4e7c17b11e6176495196f1cceebe26",
            "text": "af355f510108ea9cf40ee49c39b7f29d2f7b42207dfa54e01ffd374806a95b54"
        },
        "home.html": {
            "structure": "4fb5136160315b6ba14435fbce257f25b8f7fe1d815c2c044d3c9b970d8c6e27",
            "text": "7c9cddda820bf89493d924eab5e75dadaf23105511ac6d768432d18996927538"
        },
        "index.html": {
            "content": "ef4f7d94851a72f3e8fe8e1efb953c1f2301b61a4954a58cd0ebcef5d463bfda",
            "structure": "b873050a5ef53b189e6068cd30639fcb6515d6bb0a3f65e2256956378c0a8abe",
            "text": "f3c89b1ff35fafb4223ebf5087b3d11cc7ae012a3d20fdfe523db99473df0a3b"
        },
        "start.html": {
            "structure": "4d6ba6e1247c4547958734c96816bf28ec46ac0235e81549c4264e18b952fdae",
            "text": "218dd32f9a4dbac264bf418112b233f53effd459e44478b97fdc7603dc008828"
        },
        "world.html": {
            "structure": "52d01706f0429bffc839dc89f9e909150402b56c8dc048d40d7da4457df2396f",
            "text": "1b4090b91d18f275411abf6ec0b515722d9874c27557c998144c6b36542e4fe9"
        }
    },
    "protected": {
        "PLAN.md": "bb48ebb1385031da1f4b8872616ab1fd6b45fc41914b864bcc3198464e36e398",
        "_build/data.py": "47d73ca1d9efef99f3430033c5d6c5ea28221b426a0e3a98c66c9c89b2c00057",
        "assets/css/style.css": "cf6e5ea029604783416eec6bd287b3c3ef76dead0f709b91ac276afcf8f57bb1"
    }
}


class BodySignature(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.svg_depth = 0
        self.script_depth = 0
        self.structure = []
        self.words = []
        self.elements = []

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
        if not self.in_body:
            return
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
        if self.in_body and not self.svg_depth and not self.script_depth:
            self.words.append(data)


def signatures(html):
    parser = BodySignature()
    parser.feed(html)
    structure = json.dumps(parser.structure, ensure_ascii=False, separators=(",", ":"))
    text = " ".join(" ".join(parser.words).split())
    return {
        "structure": sha256(structure.encode()).hexdigest(),
        "text": sha256(text.encode()).hexdigest(),
        "content": sha256(json.dumps(sorted(re.findall(r"\S+", text)), ensure_ascii=False).encode()).hexdigest(),
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
        actual = signatures(html)
        parts = ("content",) if name == "index.html" else ("structure", "text")
        for part in parts:
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
    print("PASS: entry preserves original copy and seal/name/home semantics while allowing its new envelope layout.")
    print("PASS: other 17 pages preserve original text, image locations, structure, and order.")
    print("PASS: original PLAN.md, _build/data.py, and assets/css/style.css are byte-for-byte unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Test suite for the Free AI Image Tools directory build.

Runs generate-html.py and validates the produced HTML:
  * parses cleanly (no unclosed tags)
  * contains required credit / copyright / print / A4 markers
  * features every promised tool and tutorial
  * contains no secrets, keys, emails, or phone numbers

Exit nonzero on any failure.
"""
import html.parser
import re
import subprocess
import sys


class TagChecker(html.parser.HTMLParser):
    """Flags unclosed / mismatched tags."""

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.void = {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        }

    def handle_starttag(self, tag, attrs):
        if tag not in self.void:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.void:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append("Unexpected close </%s> (stack tail: %s)" % (tag, self.stack[-5:]))


def main():
    html_path = "free-ai-image-tools.html"
    readme_path = "README.md"

    # 1. Build the HTML from README.
    result = subprocess.run(
        [sys.executable, "generate-html.py", readme_path, html_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("FAIL - generate-html.py exited %d" % result.returncode)
        print(result.stdout)
        print(result.stderr)
        return 1
    print("PASS - generate-html.py ran:", result.stdout.strip())

    with open(html_path, encoding="utf-8") as f:
        content = f.read()

    # 2. Parse HTML structure.
    checker = TagChecker()
    checker.feed(content)
    leftover = checker.stack + checker.errors
    if leftover:
        print("FAIL - HTML parse issues:", leftover)
        return 1
    print("PASS - HTML parses cleanly; no unclosed tags")

    # 3. Required content markers.
    checks = {
        "Exact LICENSE copyright line": "Copyright (c) 2026 Asdale Dynamics, LLC",
        "Asdale Dynamics credit": "Asdale Dynamics, LLC",
        "Author meta tag": '<meta name="author" content="Asdale Dynamics, LLC">',
        "Print styles": "@media print",
        "A4 page size": "size: A4",
        "Top-level heading": "<h1>",
        "Tables present": "<table>",
        "Ordered lists present": "<ol>",
        "Unordered lists present": "<ul>",
        "Code block present": "<pre>",
        "No-account promise": "no-account-required",
    }
    ok = True
    for name, needle in checks.items():
        found = needle in content
        ok &= found
        print(("PASS" if found else "FAIL"), "-", name)

    # Every featured tool / tutorial should appear.
    tools = [
        "Craiyon", "Pollinations", "Hugging Face Spaces",
        "Automatic1111", "ComfyUI", "Fooocus", "DiffusionBee", "InvokeAI",
        "Stable Diffusion 1.5", "Stable Diffusion XL", "Stable Diffusion 2.1",
        "Flux.1 [schnell]", "Flux.1 [dev]",
        "Tutorial 1", "Tutorial 2", "Tutorial 3",
    ]
    for tool in tools:
        found = tool in content
        ok &= found
        print(("PASS" if found else "FAIL"), "- features:", tool)

    # All featured tools must be no-account.
    for acct in ["Yes", "Required", "Account required? | Yes"]:
        if acct in content:
            print("FAIL - a featured tool may require an account:", acct)
            ok = False

    # 4. Secret / personal data scan (none allowed).
    patterns = {
        "API key / token": r"(?i)(api[-_]?key|sk[-_][A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})",
        "Email address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "Phone number": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "Password/secret assignment": r"(?i)(password|secret|token)[:=]\s*\S+",
    }
    for name, pat in patterns.items():
        matches = re.findall(pat, content)
        if matches:
            ok = False
            print("FAIL - possible secret/personal data (%s): %s" % (name, matches[:3]))
    print("PASS - secret/personal data scan clean" if ok else "")

    # 5. README also carries the exact copyright line and credit.
    with open(readme_path, encoding="utf-8") as f:
        readme = f.read()
    if "Copyright (c) 2026 Asdale Dynamics, LLC" not in readme:
        print("FAIL - README missing exact copyright line")
        ok = False
    else:
        print("PASS - README contains exact copyright line")
    if "Asdale Dynamics, LLC" not in readme:
        print("FAIL - README missing Asdale Dynamics credit")
        ok = False
    else:
        print("PASS - README contains Asdale Dynamics credit")

    print("ALL TESTS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

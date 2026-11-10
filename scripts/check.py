#!/usr/bin/env python3
"""Check registry entries and build index.json.

  check.py [--entries bricks/x.json ...]   validate entries (all, or the given ones)
  check.py --fetch bricks/x.json ...       also clone each repo and read its brick.json
  check.py --index                         write index.json and the README table from bricks/*.json

Entries are data from strangers: every field is checked for shape and length, and
the clone goes to a fresh directory that nothing is run from.
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS = ("github.com/", "gitlab.com/", "codeberg.org/", "bitbucket.org/")
RESERVED = {"stdlib", "web"}
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
TAG_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
REPO_RE = re.compile(r"^[a-z0-9.-]+(/[A-Za-z0-9._-]+)+$")
AUTHOR_FIELDS = {"name", "repo", "description", "tags", "license", "homepage"}
CI_FIELDS = {"native", "version"}


def fail(path, msg):
    print(f"{path}: {msg}")
    return False


def clean_text(s, limit):
    return isinstance(s, str) and 0 < len(s) <= limit and all(31 < ord(c) < 127 or ord(c) > 159 for c in s) and "\n" not in s


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def other_names(path):
    """the names of every other entry, for the look-alike check"""
    names = set()
    for fn in os.listdir(os.path.join(ROOT, "bricks")):
        if fn.endswith(".json") and os.path.abspath(os.path.join(ROOT, "bricks", fn)) != os.path.abspath(path):
            names.add(fn[:-5])
    return names


def check_entry(path):
    try:
        with open(path, encoding="utf-8") as f:
            e = json.load(f)
    except (OSError, ValueError) as ex:
        return fail(path, f"not valid JSON: {ex}")
    if not isinstance(e, dict):
        return fail(path, "must be a JSON object")
    ok = True
    for k in e:
        if k not in AUTHOR_FIELDS | CI_FIELDS:
            ok = fail(path, f"unknown field {k!r}")
    for k in ("name", "repo", "description", "license"):
        if k not in e:
            ok = fail(path, f"missing {k!r}")
    if not ok:
        return False
    name = e["name"]
    if not NAME_RE.match(name):
        ok = fail(path, "name: lower-case letters, digits and hyphens, starting with a letter")
    if os.path.basename(path) != f"{name}.json":
        ok = fail(path, f"file must be named {name}.json")
    if name in RESERVED and not e["repo"].startswith("github.com/mseminatore/clay-"):
        ok = fail(path, f"{name!r} is reserved")
    for other in sorted(other_names(path) | RESERVED):
        if other != name and (edit_distance(name, other) <= 1 or name.replace("-", "") == other.replace("-", "")):
            ok = fail(path, f"name looks like the listed brick {other!r}; pick a name that can't be mistaken for it")
    repo = e["repo"]
    if not (isinstance(repo, str) and REPO_RE.match(repo) and repo.startswith(HOSTS) and ".." not in repo):
        ok = fail(path, f"repo: a host/path on one of {', '.join(h.rstrip('/') for h in HOSTS)}, without a scheme")
    if not clean_text(e["description"], 200):
        ok = fail(path, "description: 1 to 200 characters, one line")
    if not clean_text(e["license"], 40):
        ok = fail(path, "license: an SPDX identifier such as MIT")
    tags = e.get("tags", [])
    if not (isinstance(tags, list) and len(tags) <= 8 and all(isinstance(t, str) and TAG_RE.match(t) for t in tags)):
        ok = fail(path, "tags: up to 8 lower-case words with hyphens")
    if "homepage" in e and not (isinstance(e["homepage"], str) and e["homepage"].startswith("https://") and clean_text(e["homepage"], 200)):
        ok = fail(path, "homepage: an https:// URL")
    return ok


def fetch(path):
    """Clone the entry's repo (shallow, into a throwaway directory) and record what its
    brick.json says: the name must match, and native/version come from there."""
    with open(path, encoding="utf-8") as f:
        e = json.load(f)
    with tempfile.TemporaryDirectory() as tmp:
        dest = os.path.join(tmp, "repo")
        r = subprocess.run(["git", "clone", "--depth", "1", "--quiet", "https://" + e["repo"], dest],
                           capture_output=True, text=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if r.returncode != 0:
            return fail(path, f"cannot clone https://{e['repo']}: {r.stderr.strip()[-200:]}")
        mpath = os.path.join(dest, "brick.json")
        try:
            with open(mpath, encoding="utf-8") as f:
                m = json.load(f)
        except (OSError, ValueError):
            return fail(path, "the repository has no valid brick.json at its root")
        if m.get("name") != e["name"]:
            return fail(path, f"brick.json names the brick {m.get('name')!r}, not {e['name']!r}")
        if not any(os.path.exists(os.path.join(dest, n)) for n in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")):
            return fail(path, "the repository has no LICENSE file")
        e["native"] = bool(m.get("native", {}).get("plugin")) if isinstance(m.get("native"), dict) else False
        if clean_text(m.get("version", ""), 32):
            e["version"] = m["version"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(e, f, indent=2)
        f.write("\n")
    print(f"{path}: ok ({'native' if e['native'] else 'pure Clay'})")
    return True


def build_index():
    entries = []
    for fn in sorted(os.listdir(os.path.join(ROOT, "bricks"))):
        if fn.endswith(".json"):
            with open(os.path.join(ROOT, "bricks", fn), encoding="utf-8") as f:
                entries.append(json.load(f))
    with open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"version": 1, "bricks": entries}, f, indent=2)
        f.write("\n")
    rows = "\n".join(f"| `{e['name']}` | {e['description']} | {'yes' if e.get('native') else ''} | https://{e['repo']} |" for e in entries)
    table = f"<!-- bricks:start -->\n| Brick | Description | Native | Repository |\n|-------|-------------|--------|------------|\n{rows}\n<!-- bricks:end -->"
    rp = os.path.join(ROOT, "README.md")
    with open(rp, encoding="utf-8") as f:
        readme = f.read()
    readme = re.sub(r"<!-- bricks:start -->.*<!-- bricks:end -->", lambda _: table, readme, flags=re.S)
    with open(rp, "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"index.json: {len(entries)} bricks")


def main(argv):
    if "--index" in argv:
        build_index()
        return 0
    do_fetch = "--fetch" in argv
    files = [a for a in argv if a.endswith(".json")]
    if not files:
        files = sorted(os.path.join(ROOT, "bricks", fn) for fn in os.listdir(os.path.join(ROOT, "bricks")) if fn.endswith(".json"))
    ok = True
    for p in files:
        if not check_entry(p):
            ok = False
        elif do_fetch and not fetch(p):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

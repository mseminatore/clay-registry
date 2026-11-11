# clay-registry

A list of [Clay](https://github.com/mseminatore/clay) bricks, for finding them. It is not where
bricks live: every brick stays in its own Git repository, and `clay bricks add <url>` installs
from there as it always has. This repository only holds links, one small JSON file per brick, so
that `clay bricks search` (and this README's table) can find them.

**Listing is not vetting.** Entries are checked by CI for being well formed and installable; nobody
reviews a brick's code. A brick runs code on your machine when you import it, and a native brick
compiles and runs C code. Read a brick before you depend on it, as you would any dependency, and
pin it (`clay bricks add <url>@<tag>`; `brick.lock` records the commit).

## Bricks

The list is [BRICKS.md on the `index` branch](https://github.com/mseminatore/clay-registry/blob/index/BRICKS.md),
rebuilt by CI from `bricks/*.json` whenever `main` changes and once a day, next to the `index.json`
that `clay bricks search` reads. Each rebuild reads every brick's own `brick.json`, so a new version
of a brick shows up within a day with no change here. (`main` only takes pull requests, so the generated files live on a
branch of their own.)

## Listing a brick

1. Make sure the repository has a `brick.json` (see the Clay guide,
   [Bricks](https://github.com/mseminatore/clay/blob/main/docs/bricks.md)), a license file, and
   that `clay bricks add <url>` followed by `import("<name>")` works from a clean project.
2. Add `bricks/<name>.json`, where `<name>` is the brick's name in its `brick.json`:

   ```json
   {
     "name": "ann",
     "repo": "github.com/mseminatore/clay-ann",
     "description": "Neural networks: a native brick over libann",
     "tags": ["machine-learning", "native"],
     "license": "MIT"
   }
   ```

   `name`, `repo`, `description` and `license` are required. `tags` (up to 8, lower-case words
   with hyphens) and `homepage` (a URL) are optional. Don't set `native` or `version`: CI reads them
   from the brick's own `brick.json`.
3. Open a pull request. CI checks the entry (`scripts/check.py`), then clones the repository,
   installs the brick with a fresh Clay build and imports it. If `tests/` holds `test_*.clay`
   files, it runs them too. A green check and one maintainer's approval merge the listing.

A monorepo lists once, under its top-level name (`stdlib`, with `import("stdlib/json")` and so on
described in its own README), not once per sub-brick.

Names are first come, first served, and must match the brick's `brick.json`. `stdlib` and `web`
are Clay's own and are reserved.

## Changing or removing a listing

Open a pull request against your entry. To report an entry that is malicious or that infringes
something, open an issue titled `takedown: <name>`; maintainers remove the entry first and ask
questions after. Removing an entry does not touch anyone's installed copy.

## How Clay uses this

`clay bricks search <words>` and `clay bricks info <name>` read `index.json` from this repository's `index` branch
(set `CLAY_REGISTRY` to use a mirror or your own list). They only print what they find: nothing is
downloaded, built or run until you `clay bricks add` the URL yourself. The index is treated as
untrusted data: only `https://` links on known hosts are shown, and text is clipped.

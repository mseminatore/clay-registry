# Reporting a malicious or infringing listing

Open an issue titled `takedown: <name>`, or, if you'd rather not report in public, email the
address on the maintainer's GitHub profile. Say which entry and what you found. The entry is
removed first and questions asked after; the author can ask for it back once the problem is gone.

Removing an entry only stops the brick being found through `clay bricks search` and this
repository's README. It does not change the brick's own repository, and does not touch copies
already installed: people who depend on it keep the commit their `brick.lock` records.

The registry is a list of links. It never hosts, builds or signs a brick's code, and a listing
does not mean the code was reviewed. For a vulnerability in Clay itself, see the
[Clay repository](https://github.com/mseminatore/clay).

# History purge plan

This plan removes uncleared image blobs from all git history. It is a procedure, not a rewrite that has been pushed. Do not run it against `origin` until the backup bundle verifies and every collaborator has agreed to re-clone. The dry run in the VM used a throwaway `git clone --mirror` and was not pushed.

Two sets of blobs have to disappear:

1. Every path listed in [`docs/WITHHELD_IMAGES.csv`](WITHHELD_IMAGES.csv) (the working-tree photos that are not on `site/PAGES_ALLOWLIST.txt`).
2. Every historical path for `ill2_037`, `ill2_066`, `ill2_312`, and `ill2_313`, including names that are not in the CSV. That covers images, thumbs, and blurred copies.

Text mentions of those four ids, and of their Wikimedia Commons file URLs, are removed with `--replace-text`. Manifests, metrics, and license records for every other image stay. Photographer names are not globally replaced: the same credit is not used as a search key, because a line delete already drops the credit on the row that names one of these four ids.

`ill2_017`, `ill2_018`, `ill2_019`, `ill2_317`, and `ill2_318` are an optional extension at the bottom. They are not in the default path globs or the default replace-text file. Their current-tree files are still removed, because those paths are in `WITHHELD_IMAGES.csv`.

## What this does to the tree you check out afterwards

`--invert-paths` deletes the files from every commit. `--replace-text` also rewrites any blob that contains the four ids or their Commons URLs, including `site/build_pages_artifact.py`, tests, this document, and one-line historical `data.json` objects. The rewritten history is not expected to build until a follow-up commit restores the hard-exclude list without restoring image bytes, credits, or Commons URLs. Binary files are left alone: `git filter-repo` skips a blob whose first 8 KiB contains a NUL byte.

## 1. Backup, before any rewrite

Work from a mirror, not from a checkout you still want to use. Keep the bundle off GitHub.

```bash
git clone --mirror git@github.com:jaideep-aher/stop.git /tmp/stop-backup.git
git -C /tmp/stop-backup.git bundle create /tmp/stop-backup.bundle --all
git -C /tmp/stop-backup.git bundle verify /tmp/stop-backup.bundle
```

Confirm `bundle verify` prints "is okay". Copy `/tmp/stop-backup.bundle` to a disk that is not this repository. Do not delete the mirror until the purge has been checked.

## 2. Path list and replace-text file

Clone a second mirror. The backup mirror stays untouched.

```bash
git clone --mirror git@github.com:jaideep-aher/stop.git /tmp/stop-purge.git
```

Build `/tmp/stop-purge-paths.txt` from the CSV plus the four filename globs. `git filter-repo --paths-from-file` treats a line as a literal path unless it starts with `glob:` or `regex:`. Lines starting with `#` are ignored.

```bash
python3 - << 'PY'
import csv
from pathlib import Path
rows = list(csv.DictReader(open("docs/WITHHELD_IMAGES.csv", newline="")))
lines = [row["path"] for row in rows]
lines.extend([
    "glob:*ill2_037*",
    "glob:*ill2_066*",
    "glob:*ill2_312*",
    "glob:*ill2_313*",
])
Path("/tmp/stop-purge-paths.txt").write_text("\n".join(lines) + "\n")
print(len(lines))
PY
```

Build `/tmp/stop-purge-replace.txt`. An empty replacement (`==>` with nothing after it) deletes the match. Without `==>`, `git filter-repo` substitutes `***REMOVED***`. Order matters: JSON objects first, then whole lines, then the Commons URLs and file titles, then any leftover id token.

The four Commons URLs, as stored in `pilot/pilot_v2/manifest.csv`, are:

- `ill2_037`: `https://commons.wikimedia.org/wiki/File:Young_Black_Lives_Matter_activists_are_holding_a_colorful_Stop_Racism_sign_(50115127871).jpg`
- `ill2_066`: `https://commons.wikimedia.org/wiki/File:Person_at_Pride_parade_holding_sign_with_text_%22Stop_biphobia%22_(51262325481).jpg`
- `ill2_312`: `https://commons.wikimedia.org/wiki/File:Stop_Adani%27s_coal_mine_-_-climatestrike_Melbourne_IMG_3471_(45203191905).jpg`
- `ill2_313`: `https://commons.wikimedia.org/wiki/File:Stop_Climate_Change_Now_-_-climatestrike_Melbourne_IMG_3491_(45390723384).jpg`

`site/build_pages_artifact.py` splits some of those URLs across string literals, so the file-title fragments and the numeric Commons ids are listed on their own.

```bash
cat > /tmp/stop-purge-replace.txt << 'EOF'
regex:\{"id":"ill2_037"[^}]*\},?==>
regex:\{"id":"ill2_066"[^}]*\},?==>
regex:\{"id":"ill2_312"[^}]*\},?==>
regex:\{"id":"ill2_313"[^}]*\},?==>
regex:(?m)^[^\n]*ill2_037[^\n]*\n==>
regex:(?m)^[^\n]*ill2_066[^\n]*\n==>
regex:(?m)^[^\n]*ill2_312[^\n]*\n==>
regex:(?m)^[^\n]*ill2_313[^\n]*\n==>
literal:https://commons.wikimedia.org/wiki/File:Young_Black_Lives_Matter_activists_are_holding_a_colorful_Stop_Racism_sign_(50115127871).jpg==>
literal:https://commons.wikimedia.org/wiki/File:Person_at_Pride_parade_holding_sign_with_text_%22Stop_biphobia%22_(51262325481).jpg==>
literal:https://commons.wikimedia.org/wiki/File:Stop_Adani%27s_coal_mine_-_-climatestrike_Melbourne_IMG_3471_(45203191905).jpg==>
literal:https://commons.wikimedia.org/wiki/File:Stop_Climate_Change_Now_-_-climatestrike_Melbourne_IMG_3491_(45390723384).jpg==>
literal:Young_Black_Lives_Matter_activists_are_holding_a_colorful_Stop_Racism_sign_==>
literal:Person_at_Pride_parade_holding_sign_with_text_%22Stop_biphobia%22_==>
literal:Stop_Adani%27s_coal_mine_-_-climatestrike_Melbourne_IMG_3471_==>
literal:Stop_Climate_Change_Now_-_-climatestrike_Melbourne_IMG_3491_==>
literal:50115127871==>
literal:51262325481==>
literal:45203191905==>
literal:45390723384==>
literal:ill2_037==>
literal:ill2_066==>
literal:ill2_312==>
literal:ill2_313==>
EOF
```

## 3. Rewrite the throwaway mirror

`git filter-repo` refuses to run on a repo that still has an `origin` remote unless `--force` is set. On a mirror that is the right flag. It also deletes the remote it just used, which is what you want on a throwaway.

```bash
git -C /tmp/stop-purge.git filter-repo --force \
  --invert-paths \
  --paths-from-file /tmp/stop-purge-paths.txt \
  --replace-text /tmp/stop-purge-replace.txt
```

Check that nothing matched is left:

```bash
git -C /tmp/stop-purge.git rev-list --all --objects \
  | grep -E 'ill2_037|ill2_066|ill2_312|ill2_313' || echo 'no ill2 paths'
# every CSV path should be absent
python3 - << 'PY'
import csv, subprocess
paths = {row["path"] for row in csv.DictReader(open("docs/WITHHELD_IMAGES.csv", newline=""))}
out = subprocess.check_output(["git", "-C", "/tmp/stop-purge.git", "rev-list", "--all", "--objects"], text=True)
left = [line for line in out.splitlines() if line.split(" ", 1)[-1] in paths]
print("withheld paths still present", len(left))
PY
```

Both checks must be empty before anyone talks about pushing.

## 4. Force-push, only after that check

This is the command that rewrites GitHub. It is not part of the dry run. It is a force-push, which this repository's normal work does not do.

```bash
git -C /tmp/stop-purge.git remote add origin git@github.com:jaideep-aher/stop.git
git -C /tmp/stop-purge.git push --force --all origin
git -C /tmp/stop-purge.git push --force --tags origin
```

`--force --all` rewrites every branch tip. It does not delete a remote branch that the mirror no longer has. If a stale branch must disappear, delete it by name (`git push origin --delete <branch>`). Do not use `git push --mirror` unless you intend to delete every GitHub ref that is absent from the mirror, including notes and PR bookkeeping you did not mean to drop.

## 5. Branches, pull requests, and GitHub's copy

Every commit SHA changes. Open pull requests still point at the old heads. GitHub keeps those commits on `refs/pull/<n>/head` and `refs/pull/<n>/merge`, and it keeps cached views of the diff, the files tab, and the patch, until GitHub Support purges them. Closing or retargeting a pull request does not delete the blobs. A garbage-collection request to GitHub Support, naming the repository, is what removes the cached objects. Forks are separate repositories and keep the blobs until those forks are deleted or purged the same way.

After the force-push, open a new commit that puts back the hard-exclude list and the tests, without the image files, the credits, or the Commons URLs. Reviewers should use that commit, not the raw rewritten history.

## 6. Collaborators

Anyone who cloned or fetched before the force-push has the old objects. A pull or rebase will merge the purged history back in. They should delete the local clone and clone again:

```bash
rm -rf stop
git clone git@github.com:jaideep-aher/stop.git
```

Do not run `git pull` on the old checkout.

## Optional extension

To drop `ill2_017`, `ill2_018`, `ill2_019`, `ill2_317`, and `ill2_318` the same way, add these lines to the path file:

```
glob:*ill2_017*
glob:*ill2_018*
glob:*ill2_019*
glob:*ill2_317*
glob:*ill2_318*
```

And add the same three replace-text stages (JSON object, whole line, literal id) plus these Commons URLs and titles:

- `ill2_017`: `https://commons.wikimedia.org/wiki/File:Person_holding_a_protest_sign_with_text_%22Stop_Putin%22_(51949180000).jpg`
- `ill2_018`: `https://commons.wikimedia.org/wiki/File:Person_protesting_vaccine_mandate_in_Austria_is_holding_a_%22Stop_Discrimination%22_sign_(51694528225).jpg`
- `ill2_019`: `https://commons.wikimedia.org/wiki/File:Protester_holding_a_sign_that_reads_%22Stop_CO2_Emission%22_at_a_Global_Climate_Strike_(51059102311).jpg`
- `ill2_317`: `https://commons.wikimedia.org/wiki/File:Stop_thinking_about_your_next_election,_start_thinking_about_OUR_future_-_-climatestrike_Melbourne_IMG_3477_(45203233755).jpg`
- `ill2_318`: `https://commons.wikimedia.org/wiki/File:Stop_thinking_about_your_next_election_-_-climatestrike_Melbourne_IMG_3519_(45390922084).jpg`

Numeric ids for the split string literals: `51949180000`, `51694528225`, `51059102311`, `45203233755`, `45390922084`.

Run the extension only as a separate rewrite after the four-id purge has been checked. Do not combine it into a push that has already been published without another backup bundle.

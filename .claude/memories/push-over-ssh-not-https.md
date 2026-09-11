---
name: push-over-ssh-not-https
description: the gh token here has no workflow scope, so an HTTPS push carrying a .github/workflows file is rejected; the org's remotes are SSH
metadata:
  type: project
---

# Push over SSH, not HTTPS

Push over SSH. `gh auth status` on this machine lists `admin:org`,
`admin:public_key`, `delete_repo`, `gist` and `repo` and no `workflow`, so
an HTTPS push that creates or changes anything under `.github/workflows/`
is refused with `refusing to allow an OAuth App to create or update
workflow ... without workflow scope`. Every 10U-Labs remote is already
`git@github.com:10U-Labs/...`; a repo created with `gh repo create` gets
an HTTPS remote, so set it to SSH before the first push.

**Why:** the rejection names the scope rather than the transport, which
reads like the token needs refreshing when the working fix is the remote
URL. `gh auth refresh -s workflow` would also work but needs the user at
a browser.

**How to apply:** after `gh repo create`, run `git remote set-url origin
git@github.com:<org>/<repo>.git`.

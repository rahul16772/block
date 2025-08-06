# Private

This directory is not to be mirrored to the public repo, and will contain scripts for managing
public<->private repo syncs as well as CI.

## Running CopyBara

[CopyBara](https://github.com/google/copybara) is a Starlark-based tool we use to manage syncing between our public and private repositories. I have set up the Bazel-based install
in this repository (which will also be excluded from the sync), but in order to use it, you will need to install java. On macOS the process I used is:

```bash
brew install openjdk

# I had to run this to get it to work but YMMV
sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
```

Then all you need to do to run CopyBara is, from the root of the repository

```bash
./bazelw build //private/tools:copybara
bazel-bin/private/tools/copybara migrate private/tools/copy.bara.sky WORKFLOW [ARGS...]
```

### push

---

```bash
bazel-bin/private/tools/copybara migrate --dry-run private/tools/copy.bara.sky push
bazel-bin/private/tools/copybara migrate private/tools/copy.bara.sky push
```

The "push" workflow is what we will run more often. It takes the current head of main on the private repo, excludes some files in the repo according to a pattern, and then pushes is out to the public repo, commit by commit. Each commit along the way, if it is labeled with a "ORIGINAL_AUTHOR" commit label, it will make sure to restore attribution to the original author, in case it was created by someone outside gensyn and pulled in. Use the `--dry-run` flag and the subsequently printed `GIT_DIR=... git log` command to view the public repo branch diff.

### pull

---

```bash
bazel-bin/private/tools/copybara migrate private/tools/copy.bara.sky pull <public-pr-number>
```

The "pull" workflow takes a PR number from the public repo, and opens a PR in the private repo, preserving the original author and pr number with a label. The description will point to the public repo, but it is intended to be modified/merged internally, and re-synced into the public repo when we run the next push workflow. NOTE: This PR has to be either squash and merged (which preserves the labels) or rebased and merged. We should not do a merge commit, as doing so will not preserve the author on push due to the default commit message

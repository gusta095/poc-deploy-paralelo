# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A proof of concept for a "wave" based dependency model for deploying Azure
resources in parallel: resources are grouped into numbered waves so that all
resources in a wave can be deployed concurrently, and wave N+1 only starts
after wave N has finished completely.

## Commands

```bash
python3 waves.py                  # reads ./interface.yaml, prints resources grouped by wave
python3 waves.py path/to/file.yaml  # reads a specific interface file
python3 waves.py --commit         # also prints an "alterado" section: resources changed between HEAD~1 and HEAD
python3 waves.py --merge          # also prints "alterado" for resources changed between the PR base branch and HEAD
```

`--commit` and `--merge` are mutually exclusive and additive: the full wave listing is always printed first, then an `alterado` section listing only the instance keys that were added, removed, or changed, grouped by wave (empty when there's no diff). `--commit` compares `HEAD~1` against `HEAD` and works both locally and in CI. `--merge` only works inside a GitHub Actions `pull_request` run — it reads the target branch from `GITHUB_BASE_REF` and compares it against `HEAD`; it has no local fallback and exits with an error if that env var isn't set, since there's no such thing as a local PR to diff against.

Requires PyYAML (`import yaml`).

## Architecture

There are three files, and they encode the same wave model in three
different forms that must be kept in sync manually:

- `ideia.md` — the canonical, human-readable definition of the model: which
  Azure resource types exist and which wave each belongs to.
- `interface.yaml` — a sample resource inventory. Top-level keys are Azure
  resource *types* in plural snake_case (e.g. `storage_accounts`,
  `resource_groups`); the keys nested under each type are individual
  resource instances (e.g. `sa-teste-001`), with no values.
- `waves.py` — `WAVE_BY_RESOURCE_TYPE` hardcodes the same resource
  type → wave mapping from `ideia.md`. `group_by_wave()` walks
  `interface.yaml`, looks up each resource type's wave, and collects the
  instance keys (not the type names) into per-wave lists. Unrecognized
  resource types are skipped with a warning to stderr rather than failing.

The core invariant of the model (documented previously in conversation, not
currently written in `ideia.md`): a resource may only depend on resources
from strictly earlier waves, never from its own wave, since resources
within a wave deploy in parallel with no ordering guarantee. If two
resources in the same wave turn out to depend on each other, the dependent
one must move to a later wave.

When adding a new Azure resource type to the model, update it in both
`ideia.md` and the `WAVE_BY_RESOURCE_TYPE` dict in `waves.py` (and add a
sample instance under a matching key in `interface.yaml` if relevant) —
there is no single source of truth the other two are generated from.

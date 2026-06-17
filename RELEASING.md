# Releasing the `agentberg` CLI to PyPI

The CLI is published to PyPI automatically by `.github/workflows/publish.yml` when a
version tag is pushed. Publishing uses **PyPI Trusted Publishing (OIDC)** — there is no
API token or secret to manage.

## One-time setup (PyPI side)

Do this once, before the first release:

1. Sign in at [pypi.org](https://pypi.org) → **Your projects** → **Publishing** →
   **Add a pending publisher**.
2. Fill in exactly:
   - **PyPI Project Name:** `agentberg`
   - **Owner:** `ganeshnallasivam-cell`
   - **Repository name:** `agentberg-starter`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
3. Save. (The project is created on first successful publish.)

That's it — no token is ever stored in GitHub.

## Cutting a release

The git tag must match the version in `pyproject.toml` (the workflow enforces this).

```bash
# 1. bump the version
#    edit pyproject.toml:  version = "1.4.0"
git commit -am "Release v1.4.0"

# 2. tag and push
git tag v1.4.0
git push origin main --tags
```

Pushing the tag triggers the workflow: it builds the sdist + wheel, checks the tag
matches `pyproject.toml`, smoke-tests `agentberg --help`, and publishes to PyPI.

Within a minute or two:

```bash
pipx install agentberg        # or: uv tool install agentberg
```

## Notes

- **Single source of truth.** The kit and the CLI live in this one repo; the package
  is *built from here*, so there is no separate copy to drift.
- **`kit_manifest.json` vs the package version** are independent: the manifest drives
  pull-to-review for the *kit files* an installed agent adopts; the PyPI version is the
  *CLI tool* itself. Bumping one doesn't require bumping the other.
- **CI** (`ci.yml`) builds and smoke-tests on every push/PR, so a broken build is
  caught before you tag.

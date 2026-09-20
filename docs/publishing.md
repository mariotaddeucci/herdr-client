# Publishing

## Package releases

Package releases are published to PyPI by `.github/workflows/publish.yml` when a
GitHub release is published. The package version is derived from the release tag by
`hatch-vcs`:

```bash
gh release create v0.1.0 --target main --generate-notes
```

The workflow checks that `v0.1.0` produces package version `0.1.0`, runs tests and
static checks, builds the wheel and source distribution, then publishes through PyPI
Trusted Publishing. It does not use a long-lived PyPI API token.

## Documentation releases

Documentation is deployed independently from package releases. Pushes to `main` build
the MkDocs site and deploy it to GitHub Pages.

The GitHub repository must have Pages configured with **GitHub Actions** as its source.
The workflow uses the standard Pages artifact and deployment actions:

- `actions/configure-pages`
- `actions/upload-pages-artifact`
- `actions/deploy-pages`

The public site is:

```text
https://mariotaddeucci.github.io/herdr-client/
```

## Local preview

```bash
uv run mkdocs serve
```

Open `http://127.0.0.1:8000` in a browser. Build the production site locally with:

```bash
uv run mkdocs build --strict
```

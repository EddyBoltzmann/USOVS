# Release & Docker Publishing

This project includes a GitHub Actions workflow (`.github/workflows/release.yml`) that builds a Docker image when a tag matching `v*.*.*` is pushed.

- By default images are pushed to GitHub Container Registry at `ghcr.io/<owner>/<repo>`.
- To also push to Docker Hub, set `DOCKER_USERNAME` and `DOCKER_PASSWORD` repository secrets.

Permissions & tokens
- GHCR push uses `GITHUB_TOKEN` (no extra secret required), but ensure `permissions.packages: write` is available in the workflow and repository settings.
- For Docker Hub, add `DOCKER_USERNAME` and `DOCKER_PASSWORD` as secrets.

Usage
- Create a release tag: `git tag v1.2.3 && git push origin v1.2.3`
- After the workflow completes, images will be available in GHCR and optionally Docker Hub.

Security
- Limit which users can create releases/tags if releases should be controlled.
- Prefer signed tags for important releases.

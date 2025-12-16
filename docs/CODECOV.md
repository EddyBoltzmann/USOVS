# Codecov Integration Guide

This document explains how to add Codecov to the project for private and public repositories.

Why use Codecov
- View coverage history and trends
- Get PR-level coverage comments and status checks
- Track coverage across test suites and matrices

Installation Options

1. Install the Codecov GitHub App (recommended)
   - Go to https://github.com/apps/codecov and install the Codecov app on your organization or repository.
   - Choose the repositories you want Codecov to monitor.
   - When installed, you do NOT need to set an upload token in CI. The Codecov GitHub App handles authentication.

2. Use a Codecov upload token (alternative)
   - Create a repository (or project) in Codecov and find the upload token in the project settings.
   - In GitHub, go to Settings → Secrets → Actions and add `CODECOV_TOKEN` with the token value.
   - In your workflow (`.github/workflows/coverage.yml`), the Codecov action will read `CODECOV_TOKEN` from `${{ secrets.CODECOV_TOKEN }}`.

Setting up the GitHub Action
- Example step (already present in this repo):
  - name: Upload coverage to Codecov
    uses: codecov/codecov-action@v4
    with:
      files: ./coverage.xml
    env:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

Secure Practices
- Prefer the GitHub App to avoid storing tokens.
- If using a token, store it as a GitHub Actions secret and restrict who can edit secrets.
- Rotate tokens periodically.

PR commentary and coverage checks
- Codecov can post PR comments and set a status check when configured.
- In Codecov, enable PR comments, and set a minimum coverage or enforce that new changes do not lower coverage.
Project policy (decisions)

- CI is the source of truth: the project uses the coverage check built into CI (`scripts/check_coverage.py` + `coverage.xml`) to enforce a minimum threshold and fail the workflow if the threshold is not met.
- Codecov is a visibility layer: Codecov is enabled to provide reports, history, and PR commentary, but it is not the authoritative enforcer of policy in this repository.
- Optional `.codecov.yml` snippet is included in the repo as a commented template; it may be used to add additional visibility or enforcement in Codecov's UI if desired.
Private repo notes
- The GitHub App works with private repos (install on the org and grant repo access).
- If network restrictions apply, consider self-hosted runners that can access your internal resources.

If you'd like, I can:
- Add a small GitHub Action that rejects PRs when Codecov reports a decreased coverage (requires Codecov token and webhook integration), or
- Add more detailed guidance for enterprise/organization installs.

Optional: Enforcing coverage thresholds in Codecov (quick guide)

- Overview: Codecov can enforce minimum coverage targets at both the project level and the patch (PR) level. You can configure these checks either via the Codecov web UI (Project Settings → Status) or by adding a `.codecov.yml` file in your repository root.

- Minimal `.codecov.yml` example (put at repo root):

  ```yaml
  coverage:
    status:
      project:
        default:
          # target is a percentage (no % sign required here in some versions); set to your minimum acceptable coverage
          target: 80
      patch:
        default:
          # ensure PRs do not decrease patch coverage below target
          target: 80
          # when true, the status will fail if the patch lowers coverage
          require_changes: true
  ```

  Note: Codecov's schema evolves; you can also configure these same settings in the Codecov UI under *Settings → Status* if you prefer a GUI.

- Protecting branches: In GitHub, add branch protection rules for `main` that *require* the Codecov status checks (commonly `codecov/patch` or `codecov/project`, depending on configuration) and require the `CI` check to pass. This ensures merges are blocked when coverage checks fail.

- PR UX: When the above is enabled, Codecov will set status checks and can post PR comments summarizing coverage changes. For private repos, prefer the Codecov GitHub App so you avoid storing an upload token in the repo.

- Security note: Enforcing coverage via Codecov does not require embedding tokens in the codebase; either install the GitHub App or store the token in GitHub Actions secrets securely.

If you'd like, I can add an example `.codecov.yml` tailored to your preferred policy (strict patch-only checks vs. global project minimums), or add a GitHub Action that gates merges by interpreting Codecov reports directly.

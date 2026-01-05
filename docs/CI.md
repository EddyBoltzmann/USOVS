# Continuous Integration (CI)

This project uses GitHub Actions to run automated checks on push and pull requests.

Workflow: `.github/workflows/ci.yml`
- Lints the codebase with `ruff`.
- Applies migrations using SQLite (for CI convenience).
- Runs Django tests with `manage.py test`.
- Uploads coverage to Codecov (when `CODECOV_TOKEN` secret is set) via `.github/workflows/coverage.yml`.
- Checks a minimum coverage threshold (default 80%) and fails the workflow if coverage is below threshold. The threshold can be configured by setting the `COVERAGE_THRESHOLD` repository secret (value is a number like `75`).
- Generates a minimal, non-sensitive coverage badge at `badges/coverage.svg` (shows percentage or FAIL) and commits it to the repository on push events. The badge intentionally does not include branch names or other repo-specific metadata.
- Provides a release workflow that builds and publishes Docker images on tags via `.github/workflows/release.yml`.

Using Codecov with private repositories (short note) 🔒

- Preferred approach: Install the Codecov GitHub App for your organization/repo. This avoids storing tokens in repo files and simplifies permissions management. See: https://docs.codecov.com/docs/github-app

- If you must use a token, create a Codecov upload token from your Codecov project settings and add it as a repository **secret** named `CODECOV_TOKEN` (or at the organization level). Never commit the token into the repository or include it in files.

- In CI, reference the token via `${{ secrets.CODECOV_TOKEN }}` when calling the Codecov action. For example, in `.github/workflows/coverage.yml` the step `Upload coverage to Codecov` reads the token from secrets.

- Security tips: restrict who can edit repository secrets, use organization secrets when possible, and rotate tokens periodically. Consider integrating with your cloud secret manager for extra control.

If you want a more detailed guide (org install steps, least-privilege settings, or self-hosted alternatives), I can add a full `docs/CODECOV.md` with step-by-step instructions. Let me know which you'd prefer.

Environment for CI
- `DJANGO_SECRET_KEY` is set to a test value in the workflow.
- `DJANGO_USE_SQLITE_FOR_TESTS=1` forces SQLite usage for migrations/tests so Postgres isn't required.

If you want code coverage, protected API checks, or additional Python versions added to the matrix, I'll add them next.

Postgres-backed CI job
- A second CI job `test-postgres` now runs the full test-suite against a real PostgreSQL service (useful for concurrency / transactional tests such as the OTP concurrency test). This job installs `requests` in CI so `LiveServerTestCase`-based concurrency tests can use `requests` to exercise the running test server.
- Note: Concurrency tests (e.g., `core.tests_concurrency.OTPConcurrencyTests`) are skipped when the test database is SQLite to avoid spurious failures. They will run in the `test-postgres` job which provides a Postgres service via Docker.

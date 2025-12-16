# CI Secrets & Protected Branch Rules

## Required Secrets

- `FIREBASE_CREDENTIALS_JSON` (recommended): Store the Firebase service account JSON as a **secret** (value is the JSON string). Avoid committing credentials to the repo. For extra security, use your cloud provider's secret manager and a GitHub Action that fetches secrets at runtime.

- `CODECOV_TOKEN` (optional): For Codecov uploads if you want Codecov to post PR comments and maintain coverage history. You can create an account at https://codecov.io and add the repo to get the token.

- `DOCKER_USERNAME` / `DOCKER_PASSWORD` (optional): Credentials for Docker Hub if you want CI to push Docker images there.

- `GITHUB_TOKEN`: Provided automatically by GitHub Actions; used for pushing images to GHCR and for workflow actions that require repo authentication.

## Best Practices

- Limit which users can update secrets in repository settings (use organization-level policies).
- Rotate service account keys regularly and audit usage.
- For Firebase credentials, prefer using short-lived tokens or cloud secret managers where possible.
- For production deploys, use separate service accounts/projects and limit permissions to the minimum necessary.

## Protected Branch Rules (Recommended)

Apply these rules to `main`/`master`:

- Require status checks to pass (enable the CI workflow(s) `CI` and `Coverage`).
- Require pull request reviews before merging (1 or 2 reviewers depending on your process).
- Require signed commits (optional).
- Include required reviewers for critical files (CODEOWNERS).
- Enforce linear history (require rebase/merge strategy).

These settings can be configured in GitHub under Settings → Branches → Branch protection rules.

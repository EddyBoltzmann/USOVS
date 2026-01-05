This PR adds a Postgres-backed CI job and a concurrency test to validate atomic OTP verification behavior.

**Changes included:**
- `core/tests_concurrency.py`: LiveServerTestCase concurrency test that asserts exactly one concurrent verification for the same token succeeds (others get 403 token_reuse).
- `requirements.txt`: added `requests` to support concurrency tests using the running test server.
- `docs/CI.md`: documents the new `test-postgres` CI job and explains that concurrency tests are skipped on SQLite.
- `.github/workflows/ci.yml`: CI workflow with `test-postgres` job that runs tests against a real PostgreSQL service.

**How it works:**
- The `test-and-lint` job runs on SQLite (fast, for quick feedback).
- The new `test-postgres` job spins up a Postgres 14 service and runs the full test suite, exercising transactional concurrency semantics.
- The concurrency test (`core.tests_concurrency.OTPConcurrencyTests.test_concurrent_verifications_only_one_succeeds`) fires 8 concurrent HTTP requests to `/auth/firebase/verify/` with the same token.
- The test expects exactly one success (200) and the rest to receive 403 (token_reuse), enforcing the atomicity of the check-and-mark operation in `firebase_verify`.

**Next steps:**
1. Review the PR and run CI via GitHub Actions.
2. If the `test-postgres` job passes, the concurrency test validates that token reuse is properly blocked under real transactional DB semantics.
3. If the test fails, I'll instrument the verification code, identify any race conditions, and apply targeted fixes until the test goes green.

CI: add Postgres job & concurrency test for OTP verification

This PR introduces a PostgreSQL-backed CI job that runs the full test suite against PostgreSQL (Postgres 14 service). It also adds a concurrency test that uses `LiveServerTestCase` and real HTTP requests to validate that only one concurrent verification of the same token succeeds (prevents double-claiming of one-time tokens).

Notes:
- The concurrency test is intentionally skipped on SQLite, and the CI job runs it on Postgres.
- The Postgres job uses a service container in GitHub Actions and runs migrations before tests.
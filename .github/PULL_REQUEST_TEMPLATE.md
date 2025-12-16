<!-- Please describe the change and motivation in a few sentences -->

## Summary

(What does this change do?)

## Checklist

- [ ] I have added/updated tests for my changes
- [ ] Linting passes (run `ruff check .`)
- [ ] CI (`CI` workflow) is passing on this PR
- [ ] Coverage is acceptable (see `coverage.yml`) or this PR has an explanation if coverage decreased and meets the configured threshold
- [ ] No secrets, credentials, or service account JSONs are included in this PR
- [ ] Relevant documentation updated (docs/, README.md)

## Reviewer notes

- How to test locally: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt -r dev-requirements.txt && python manage.py migrate && python manage.py test`
- Add any additional notes for reviewers here.

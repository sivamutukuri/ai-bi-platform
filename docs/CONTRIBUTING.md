# Contributing

Thanks for your interest in improving the AI BI Platform!

## Development setup

See the README for full local setup. In short:

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install ruff black

# Frontend
cd frontend && npm install
```

## Branching & commits

- Branch from `main` using `feat/...`, `fix/...`, `docs/...`, or `chore/...`.
- Follow [Conventional Commits](https://www.conventionalcommits.org/): `feat(scope): summary`.
- Keep commits focused and atomic.

## Code style

| Area | Tooling | Command |
| --- | --- | --- |
| Python lint | Ruff | `ruff check app` |
| Python format | Black | `black app` |
| TS/React lint | ESLint | `npm run lint` |
| TS/React format | Prettier | `npx prettier --write .` |

## Tests

All PRs must keep the test suites green:

```bash
cd backend && pytest
cd frontend && npm test
```

Add tests for any new service function, endpoint, or component.

## Pull requests

1. Ensure lint, type-check, and tests pass locally (CI enforces the same).
2. Update documentation (README / docs/API.md) when behaviour changes.
3. Describe the motivation and approach in the PR description.
4. Link any related issues.

## Reporting issues

Please include reproduction steps, expected vs actual behaviour, and environment
details (OS, Python/Node versions). For security issues, contact the maintainer
privately rather than opening a public issue.

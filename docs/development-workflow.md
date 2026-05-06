# Development Workflow

## Branches

- `dev`: shared development branch.
- Feature branches should be created from `dev` and merged back after review.

## Local Setup

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in local-only values.

## Collaboration

- Keep commits focused and descriptive.
- Run available checks before pushing.
- Do not commit local secrets or generated cache files.

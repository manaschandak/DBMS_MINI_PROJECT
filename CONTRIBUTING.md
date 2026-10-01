# Contributing: who owns what

Golden rule: if you don't own a file, don't edit it without coordinating with the owner.

| Area | Primary owner | Other person | Both edit? |
|---|---|---|---|
| frontend/ (incl. package.json) | Person 1 | Reads API contracts | No |
| backend/ | Person 2 | Consumes the API | No |
| database/ (schema, SQL) | Person 2 | Reads | No |
| ml/ | Person 1 | Uses it via the API | No |
| requirements.txt | Person 2 | - | No |
| README.md | Person 1 (initially) | Requests changes | Controlled |
| PROJECT_STATE.md, .gitignore, CONTRIBUTING.md | Coordinate first | Both | Controlled |
| .env | Each person locally | Never committed | No |
| .env.example | Person 2 | Reads | No |
|ml/requirements.txt | Person 1 | Person 2 reads | No

## Rules
1. Nobody works directly on `main`.
2. Person 1 works on `person1-frontend-ml`. Person 2 works on `person2-backend-database`.
3.. The boundaries are the API contract (frontend ↔ backend) and the ML prediction contract (backend ↔ ml). If you need a change in someone else's area or in either contract, ask the owner.
4. PRs that change the API or ML contract need approval from both people.
5. Never commit passwords, keys, or `.env`.
6. Editing a shared (Controlled) file: tell the other person, pull first, commit it separately, push, tell them.

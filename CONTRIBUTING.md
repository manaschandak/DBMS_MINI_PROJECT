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

## Rules
1. Nobody works directly on `main`.
2. Person 1 works on `person1-frontend`. Person 2 works on `person2-backend-ml`.
3. The API contract is the boundary. If you need a change in someone else's area, ask the owner.
4. Merging to `main` happens only through a Pull Request, merged by Person 2 (project lead).
   Person 2's own work also goes through a Pull Request, checked against the merge checklist
   before merging. Ask Person 1 to glance at it when practical.
5. Never commit passwords, keys, or `.env`.
6. Editing a shared (Controlled) file: tell the other person, pull first, commit it separately, push, tell them.

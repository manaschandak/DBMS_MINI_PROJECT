# PROJECT STATE

Project: AI-Enabled Battery Thermal Management & Multi-Chemistry Aging Database (KJS-CES-02)
Repo: github.com/mickey09-cyber/DBMS_MINI_PROJECT
Current phase: 2 - GitHub setup
Current step: Step 1 - push skeleton to main
Overall progress: 5%

## Completed
- Phase 1: requirements analysis, decisions confirmed
- GitHub repo created; collaborator invite sent to manaschandak (pending acceptance)

## In Progress
- Step 1: push project skeleton to main

## Not Started
- Phases 3-14

## Person 1 Branch (person1-frontend)
Not created yet

## Person 2 Branch (person2-backend-ml)
Not created yet

## Main Branch
Skeleton only

## Database Status
Not started (planned: 17 tables from the document + chemistry, aging_record, electrical_reading, alert, model_training, app_user)

## FastAPI Status
Not started

## Frontend Status
Not started

## ML Status
Not started (planned: risk classifier x2 [thermal, health], anomaly detector; synthetic data, labelled as synthetic)

## Important Decisions
- Roles: Person 2 = backend + database + ML, and project lead who does all merges. Person 1 = frontend.
- Work division: Option A (P1 frontend; P2 backend + DB + ML). Option B (P1 also takes ml/) still open.
- Synthetic data is the main dataset; live data is simulated (simulator script, CSV upload, manual entry)
- Two risk classifiers (thermal_risk, health_risk), 4 levels each
- Simple role-based login: Admin, BMS Engineer, Fleet Operator, Service Technician, Researcher
- CFD and digital twin are stored data only
- Poster is a secondary reference; the Word document wins on conflicts
- Repo is currently PUBLIC: never commit secrets

## Important Files
CONTRIBUTING.md (ownership), .env.example, PROJECT_STATE.md

## Known Issues
- DBMS IA rubric and deadline not yet provided
- Poster still has placeholder author and reference text

## Next Exact Action
Step 2: Person 2 creates branch person2-backend-ml; Person 1 clones the repo and creates person1-frontend

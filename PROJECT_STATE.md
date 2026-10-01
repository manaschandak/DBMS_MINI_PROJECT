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

## Database Status - LATEST (replaces the earlier "Database Status" section)
DONE: 23 tables, 6 views, 1 trigger, 54 indexes. Scripts are database/01 to database/16.
- Tables: all 23 created with constraints and sample rows (sample rows are marked SAMPLE)
- Views: v_live_accuracy, v_latest_risk, v_battery_overview, v_open_alerts, v_risk_distribution, v_chemistry_comparison
- Trigger: trg_alert_on_risk creates an OPEN alert when a risk assessment is HIGH or CRITICAL
- Indexes: 14 added in Step 20; Step 19 experiment (EXPLAIN ANALYZE) saved in database/index_experiment_output.txt
- Transactions: demo in database/16_transaction_demo.sql, output in database/transaction_demo_output.txt
- Schema reference: database/schema_snapshot.sql

DEFERRED (needed for the DBMS IA report, not yet done):
- ER diagram
- Normalization / BCNF document
- Optional: sample readings for PN-NCA-0001, GL-NMC-0001, FC-LFP-0001 (they have no temperature readings)
- Optional: concurrency demo, backup and restore demo

NOTE: Person 2 branch is named mahek_branch (the plan said person2-backend-ml).
NEXT: FastAPI backend and ML.

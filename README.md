# RubriMark AI - Component 2: Reliability-Aware Multi-Source Decision Framework (CARI)

Offline-runnable implementation. Components 1/3/4 are replaced by stand-ins behind a versioned data contract.

## Run
    pip install -r requirements.txt
    python -m pytest -q tests                 # 17 tests
    python scripts/run_experiment.py          # split-by-question experiment, writes results/ and models/engine.joblib
    python3 -m uvicorn cari.api.main:app --reload  # API (DATABASE_URL=postgresql+psycopg://... for PostgreSQL)
    psql -f db/schema.sql                     # research/service schema (parser-validated, not run on a live server)

For the Vite dashboard, install the frontend dependencies with `npm run frontend:install`
and run `npm run dev` from the project root; then open `http://127.0.0.1:5180/`. The API must also be running with
`python3 -m uvicorn cari.api.main:app --reload --port 8010` in a second terminal. Vite proxies dashboard
requests to the API. The dashboard shows
automatic releases, the validation queue, the configured CARI threshold note, and released
results. A lecturer can approve a queued answer to release the AI score or record an override
with a manually entered score and note. The dashboard uses `/dashboard`, `/queue`, and `/results`;
the JSON API remains available for integrations.

## Preparing a sample dataset from questionnaire responses

The OOP questionnaire can be converted into API-ready cases without copying student email
addresses:

    PYTHONPATH=. python scripts/prepare_oop_dataset.py "/path/to/Form Responses 1.csv"

This writes `data/oop_assessment_cases.jsonl` (one complete `AssessmentCase` per answer),
`data/oop_assessment_cases.csv` (a human-readable normalized version), and a summary file.
Rows that do not match all five OOP topics are excluded because the form includes responses
from a later, different question set. To submit the generated cases to the local API:

    PYTHONPATH=. python scripts/submit_dataset.py data/oop_assessment_cases.jsonl --api http://127.0.0.1:8010

After results are released, the dashboard supports editing an approved score, a separate
final-release view for each student, preparing a feedback email, and downloading
`student_marks.csv`. The CSV contains one row per student, one column for each of the five
question scores, and total/max-total columns. A student appears in the final CSV only after all
five question results are released (automatic or lecturer-reviewed); incomplete students remain
visible in the dashboard as waiting. The export also includes the Component 4 feedback column
and intentionally excludes email, status, and dashboard action fields.

Email delivery is sample-mode by default: it displays the complete total and Component 4
suggestions and stores the delivery record without contacting an external mail server. For a
real SMTP connector, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and
`SMTP_FROM` before starting the API. The final-release action then sends the email through SMTP.

For a visible end-to-end dashboard demo, seed five clearly labelled sample automatic-release
students (this changes only the local SQLite data):

    PYTHONPATH=. python scripts/seed_sample_releases.py --students 5

The seeded sample scores are not real model decisions and should not be used for evaluation.

## Build steps -> files
1. Contract            cari/contract.py, cari/labels.py (labels kept OUT of the contract: no leakage)
2. Indicators + gates  cari/indicators.py, cari/gates.py, cari/textutil.py
3. Aggregation (M0-M5), thresholds, metrics   cari/aggregation.py, cari/thresholds.py, cari/evaluation.py
4. Stand-ins + synthetic data   cari/adapters/standin.py, cari/synth/
5. Engine              cari/pipeline.py (fit on dev, assess one case)
6. Experiments         scripts/run_experiment.py (sign check, 6 methods x 2 levels x 2 threshold policies, ablation, sensitivity, fuzzy evidence)
7. API + DB            cari/api/main.py, cari/db.py, db/schema.sql

## Caveats
* Synthetic data validates the machinery, NOT the research claims. The C1 stand-in shares the generator's concept
  structure, so semantic indicators are near-oracle here. Re-run everything on real component outputs and real datasets.
* cari/adapters/hf_models.py (real NLI/embedding models) is written but was NOT run (no HuggingFace access when built).
* AHP priorities in cari/aggregation.py are placeholders; replace with expert pairwise elicitation.
* M5 (ELECTRE-style) and the rubric/semantic-grade agreement indicators are project-specific adaptations to justify in the thesis.

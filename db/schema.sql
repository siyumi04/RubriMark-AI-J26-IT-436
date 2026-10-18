-- PostgreSQL schema for Component 2 (research storage + service). Validated with pglast (PostgreSQL parser).
CREATE TABLE questions (
    question_id   TEXT PRIMARY KEY,
    text          TEXT NOT NULL,
    reference_answer TEXT NOT NULL,
    max_score     NUMERIC NOT NULL CHECK (max_score > 0)
);
CREATE TABLE rubrics (
    rubric_id TEXT NOT NULL, version INT NOT NULL, question_id TEXT NOT NULL REFERENCES questions,
    approved BOOLEAN NOT NULL DEFAULT FALSE, approved_by TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (rubric_id, version)
);
CREATE TABLE rubric_criteria (
    rubric_id TEXT NOT NULL, version INT NOT NULL, criterion_id TEXT NOT NULL, concept_id TEXT NOT NULL,
    description TEXT NOT NULL, weight NUMERIC NOT NULL CHECK (weight >= 0), max_points NUMERIC NOT NULL CHECK (max_points > 0),
    PRIMARY KEY (rubric_id, version, criterion_id),
    FOREIGN KEY (rubric_id, version) REFERENCES rubrics (rubric_id, version)
);
CREATE TABLE answers (
    assessment_id TEXT PRIMARY KEY, question_id TEXT NOT NULL REFERENCES questions,
    student_response TEXT NOT NULL, split TEXT CHECK (split IN ('dev', 'val', 'test')), dataset_version TEXT
);
CREATE TABLE grading_runs (
    assessment_id TEXT NOT NULL REFERENCES answers, run_no INT NOT NULL, total_score NUMERIC NOT NULL,
    model TEXT, temperature NUMERIC, PRIMARY KEY (assessment_id, run_no)
);
CREATE TABLE assessments (
    assessment_id TEXT PRIMARY KEY, question_id TEXT NOT NULL, payload JSONB NOT NULL, cari DOUBLE PRECISION,
    decision TEXT NOT NULL CHECK (decision IN ('AUTO_RELEASE', 'LECTURER_VALIDATION')),
    gates JSONB NOT NULL, indicators JSONB NOT NULL, reason TEXT NOT NULL, config_id TEXT NOT NULL, tau DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'released', 'reviewed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_assessments_decision ON assessments (decision, status);
CREATE TABLE lecturer_decisions (
    id BIGSERIAL PRIMARY KEY, assessment_id TEXT NOT NULL REFERENCES assessments, action TEXT NOT NULL CHECK (action IN ('approve', 'override')),
    final_score NUMERIC, comment TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE experiments (
    experiment_id BIGSERIAL PRIMARY KEY, config JSONB NOT NULL, seed INT, dataset_version TEXT, git_commit TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE cari_results (
    experiment_id BIGINT NOT NULL REFERENCES experiments, assessment_id TEXT NOT NULL, method TEXT NOT NULL,
    cari DOUBLE PRECISION, tau DOUBLE PRECISION, flagged BOOLEAN, gates JSONB, PRIMARY KEY (experiment_id, assessment_id, method)
);
-- Expert/lecturer routing labels: evaluation ONLY. Use a separate DB role that the decision service cannot read.
CREATE TABLE expert_labels (
    assessment_id TEXT NOT NULL, expert_id TEXT NOT NULL, needs_review BOOLEAN NOT NULL, score NUMERIC, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (assessment_id, expert_id)
);

import os, pathlib
import pglast
import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_postgres_schema_parses():
    stmts = pglast.parse_sql((ROOT / "db" / "schema.sql").read_text())
    kinds = [type(s.stmt).__name__ for s in stmts]
    assert kinds.count('CreateStmt') == 10 and kinds.count('IndexStmt') == 1


@pytest.fixture()
def client(tmp_path, monkeypatch):
    if not (ROOT / "models" / "engine.joblib").exists():
        pytest.skip("run scripts/run_experiment.py first")
    monkeypatch.setenv("CARI_ENGINE_PATH", str(ROOT / "models" / "engine.joblib"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    from cari.api import main
    main._state.clear()
    return TestClient(main.app)


def _cases(n=60):
    from cari.synth.generator import generate_dataset, SynthConfig
    ds = generate_dataset(SynthConfig(seed=11, n_per_question=8))
    return ds.cases[:n]


def test_assess_queue_and_lecturer_flow(client):
    results = [client.post("/assess", json=c.model_dump(mode="json")) for c in _cases()]
    assert all(r.status_code == 200 for r in results)
    decisions = {r.json()["decision"] for r in results}
    assert decisions <= {"AUTO_RELEASE", "LECTURER_VALIDATION"}
    q = client.get("/queue").json()
    assert q and all(x["assessment_id"] for x in q)
    cari_vals = [x["cari"] for x in q if x["cari"] is not None]
    assert cari_vals == sorted(cari_vals)                      # least reliable first
    aid = q[0]["assessment_id"]
    assert client.post("/lecturer-decision", json={"assessment_id": aid, "action": "override"}).status_code == 422
    ok = client.post("/lecturer-decision", json={"assessment_id": aid, "action": "override", "final_score": 3, "comment": "regraded"})
    assert ok.status_code == 200 and ok.json()["status"] == "reviewed"
    reviewed = client.get("/results?status=reviewed").json()
    result = next(x for x in reviewed if x["assessment_id"] == aid)
    assert result["final_score"] == 3
    assert result["review_action"] == "override"
    assert result["review_note"] == "regraded"
    edited = client.put(f"/results/{aid}/score", json={"final_score": 2, "comment": "second review"})
    assert edited.status_code == 200
    result = next(x for x in client.get("/results?status=reviewed").json() if x["assessment_id"] == aid)
    assert result["final_score"] == 2 and result["review_note"] == "second review"
    email = client.post(f"/results/{aid}/email")
    assert email.status_code == 200 and email.json()["status"] == "sample_sent"
    export = client.get("/results/export.csv")
    assert export.status_code == 200 and "total_score" in export.text
    assert aid not in [x["assessment_id"] for x in client.get("/queue").json()]
    assert client.post("/lecturer-decision", json={"assessment_id": "nope", "action": "approve"}).status_code == 404


def test_missing_component_is_routed_to_lecturer(client):
    c = _cases(1)[0].model_copy(deep=True); c.c4 = None
    r = client.post("/assess", json=c.model_dump(mode="json")).json()
    assert r["decision"] == "LECTURER_VALIDATION" and r["gates_fired"] == ["missing_component"]


def test_engine_never_imports_lecturer_decisions():
    src = (ROOT / "cari" / "pipeline.py").read_text() + (ROOT / "cari" / "indicators.py").read_text() + (ROOT / "cari" / "gates.py").read_text()
    assert "lecturer_decisions" not in src and "from .db" not in src and "expert_labels" not in src

import math
import numpy as np
import pytest
from cari.config import CariConfig
from cari.contract import AssessmentCase
from cari.gates import gates
from cari.indicators import consistency, mode_score, evidence_validity, explanation_support, rubric_agreement
from cari.aggregation import ahp_weights, ahp_from_priorities, wmean, Topsis, EqualWeight
from cari.thresholds import tau_f1, tau_recall, confusion
from cari.evaluation import auc, risk_coverage
from cari.labels import make_label, modal_set
from cari.textutil import span_grounded
from cari.synth.generator import generate_dataset, SynthConfig
from cari.adapters.standin import LexicalEntailment, make_known_syn


@pytest.fixture(scope="module")
def ds():
    return generate_dataset(SynthConfig(n_per_question=30, seed=3))


def test_consistency_matches_worked_example():
    assert consistency([4, 4, 3, 4, 4]) == pytest.approx(0.8)      # example from the proposal notes / SURE definition
    assert mode_score([4, 4, 3, 4, 4]) == 4


def test_label_uses_modal_human_score_with_ties():
    assert modal_set([3, 3, 4]) == {3}
    assert make_label(4, [3, 3, 4]) == 1
    assert make_label(4, [3, 4, 5]) == 0          # three-way tie: all valid


def test_span_grounding_exact_and_fuzzy():
    ans = "Plants absorb sunlight using chlorophyll."
    assert span_grounded("plants absorb sunlight", ans)
    assert not span_grounded("plants capture sunlight", ans)
    assert span_grounded("plants absorb sunlight using chlorophyll in leaves", ans, 0.7)


def test_ahp_consistent_matrix_gives_cr_zero_and_ratio_weights():
    w, cr = ahp_from_priorities(np.array([3, 1, 1, 1.0]))
    assert cr == pytest.approx(0, abs=1e-6) and w[0] == pytest.approx(0.5, abs=1e-6) and w.sum() == pytest.approx(1)
    w2, cr2 = ahp_weights(np.array([[1, 3, 5], [1/3, 1, 3], [1/5, 1/3, 1]]))
    assert 0 < cr2 < 0.1


def test_wmean_renormalises_over_missing():
    X = np.array([[1.0, np.nan], [0.5, 0.5]])
    assert wmean(X, np.array([1.0, 1.0])).tolist() == [1.0, 0.5]


def test_topsis_bounds():
    t = Topsis().fit(np.zeros((1, 3)), [0], ["c3_consistency", "c3_evidence_validity", "c1_no_contradiction"])
    s = t.score(np.array([[1, 1, 1], [0, 0, 0], [0.5, 0.5, 0.5]], float))
    assert s[0] == pytest.approx(1) and s[1] == pytest.approx(0) and s[2] == pytest.approx(0.5)


def test_thresholds_reach_recall_target():
    cari = np.array([.1, .2, .3, .6, .7, .8, .9, .95]); y = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    t = tau_recall(cari, y, 1.0)
    tp, fp, tn, fn = confusion(cari, y, t)
    assert fn == 0 and fp == 0
    assert tau_f1(cari, y) > .6


def test_auc_and_risk_coverage_direction():
    cari = np.array([.9, .8, .7, .2, .1]); y = np.array([0, 0, 0, 1, 1])
    assert auc(cari, y) == 1.0
    cov, risk = risk_coverage(cari, y)
    assert risk[2] == 0.0 and cov[-1] == 1.0


def test_no_label_fields_in_contract():
    fields = set(AssessmentCase.model_fields)
    assert not {"y", "label", "human_scores", "lecturer_decision", "expert_label"} & fields


def test_gates_fire_on_injected_faults(ds):
    cfg = CariConfig()
    base = next(c for c in ds.cases if c.c1 and c.c3 and c.c4 and not gates(c, cfg))
    assert gates(base, cfg) == []
    m = base.model_copy(deep=True); m.c3.ai_score += 1
    assert "total_mismatch" in gates(m, cfg)
    m = base.model_copy(deep=True); m.c3.rubric_approved = False
    assert "rubric_not_approved" in gates(m, cfg)
    m = base.model_copy(deep=True); m.c4 = None
    assert gates(m, cfg) == ["missing_component"]
    m = base.model_copy(deep=True); m.c1.nli.con = .9; m.c3.ai_score = m.c3.max_score
    for c in m.c3.criteria: c.points = c.max_points
    assert "contradiction_high_score" in gates(m, cfg)


def test_fabricated_evidence_lowers_evidence_validity(ds):
    cfg = CariConfig()
    c = next(c for c in ds.cases if c.c3 and sum(1 for k in c.c3.criteria if k.points > 0) >= 2
             and evidence_validity(c.c3, c.student_response, None) == 1.0)
    m = c.model_copy(deep=True)
    next(k for k in m.c3.criteria if k.points > 0).evidence_span = "something the student never wrote"
    assert evidence_validity(m.c3, m.student_response, None) < 1.0
    assert explanation_support(m.c3, m.c4, m.student_response, None) <= explanation_support(c.c3, c.c4, c.student_response, None) if m.c4 else True


def test_correct_low_grade_is_not_penalised_by_rubric_agreement(ds):
    """The flaw in the naive 'share of rubric satisfied' indicator: a correct zero must stay reliable."""
    ent = LexicalEntailment({})
    c = next(c for c in ds.cases if c.c3 and c.c3.ai_score == 0 and "not the case" not in c.student_response)
    assert rubric_agreement(c.c3, c.student_response, ent) > 0.7


def test_engine_is_deterministic_and_ignores_nothing_but_the_case(ds):
    from cari.pipeline import CariEngine
    from cari.aggregation import EqualWeight
    cfg = CariConfig()
    ent = LexicalEntailment(make_known_syn(np.random.default_rng(1), .6))
    eng = CariEngine(cfg, ent, EqualWeight()).fit(ds.cases, ds.labels, ds.meta["y"])
    a, b = eng.assess(ds.cases[5]), eng.assess(ds.cases[5])
    assert a.model_dump() == b.model_dump()

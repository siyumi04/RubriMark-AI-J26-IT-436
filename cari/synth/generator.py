"""Synthetic dataset generator: simulated answers + stand-in C1/C3/C4 outputs + simulated human labels.

IMPORTANT: results on this data validate the MACHINERY (indicators, gates, aggregation, evaluation),
not the research claims. Error patterns are simulated by design. Re-run on real component outputs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..contract import (AssessmentCase, C1Output, C3Output, C4Output, Claim, Criterion, NLIProbs, Provenance)
from ..labels import LabelRecord, make_label
from ..indicators import mode_score
from ..adapters.standin import SYN_PAIRS, LexicalMatcher, make_known_syn
from .bank import QUESTIONS

STATES = ["correct", "paraphrased", "missing", "vague", "negated"]
PROFILES = {  # per-concept state probabilities
    "strong": [.60, .30, .05, .03, .02], "medium": [.30, .25, .30, .10, .05],
    "weak": [.10, .10, .50, .20, .10], "tricky": [.10, .40, .10, .20, .20]}
PROFILE_P = {"strong": .30, "medium": .35, "weak": .20, "tricky": .15}
P_SYS = {"correct": .01, "paraphrased": .10, "missing": .01, "vague": .12, "negated": .15}    # persistent grader error
P_NOISE = {"correct": .02, "paraphrased": .20, "missing": .02, "vague": .15, "negated": .20}  # per-run flip
VAGUE = ["this is an important idea in the topic", "there are many factors involved here",
         "it depends on the situation and the context"]


@dataclass
class SynthConfig:
    seed: int = 7
    n_per_question: int = 150
    k_runs: int = 5
    p_total_fault: float = .02
    p_unapproved: float = .02
    p_missing_c4: float = .01
    p_missing_c1: float = .005


@dataclass
class Dataset:
    cases: list[AssessmentCase]
    labels: dict[str, LabelRecord]
    question_of: dict[str, str]
    meta: dict = field(default_factory=dict)   # simulation internals (never given to the engine)

    @property
    def y(self) -> np.ndarray:
        return np.array([self.meta["y"][c.assessment_id] for c in self.cases])


def paraphrase(sentence: str, rng) -> str:
    inv = {h: s for h, s in SYN_PAIRS.items()}
    out = [inv[t] if t in inv and rng.random() < .75 else t for t in sentence.split()]
    return " ".join(out)


def make_answer(q, profile, rng):
    probs = PROFILES[profile]
    states, sents = {}, {}
    for cid, text, _ in q["concepts"]:
        st = str(rng.choice(STATES, p=probs))
        states[cid] = st
        if st == "correct":
            sents[cid] = text
        elif st == "paraphrased":
            sents[cid] = paraphrase(text, rng)
            if sents[cid] == text:
                states[cid] = "correct"
        elif st == "negated":
            sents[cid] = f"it is not the case that {text}"
        elif st == "vague":
            first = [w for w in text.split() if len(w) > 4][0]
            sents[cid] = f"{rng.choice(VAGUE)} and relates to {first}"
    order = [c[0] for c in q["concepts"] if c[0] in sents]
    if rng.random() < .3:
        rng.shuffle(order)
    if not order:
        order_text = [str(rng.choice(VAGUE))]
    else:
        order_text = [sents[c] for c in order]
    return states, sents, order_text


def make_span(state, ref, own_sentence, others, rng):
    if state == "missing":
        return ref if (rng.random() < .6 or not others) else str(rng.choice(others))   # fabricated or irrelevant
    if state == "paraphrased" and rng.random() < .25:
        return ref   # model 'normalises' its quote to the reference wording -> not recoverable from answer
    return own_sentence


def generate_dataset(cfg: SynthConfig = SynthConfig()) -> Dataset:
    rng = np.random.default_rng(cfg.seed)
    known_c1 = make_known_syn(rng, .75)
    matcher = LexicalMatcher(known_c1)
    cases, labels, qof, ymap, truth = [], {}, {}, {}, {}
    names, p = list(PROFILE_P), list(PROFILE_P.values())

    for q in QUESTIONS:
        ref = ". ".join(c[1] for c in q["concepts"]) + "."
        raw = []
        for i in range(cfg.n_per_question):
            prof = str(rng.choice(names, p=p))
            states, sents, order_text = make_answer(q, prof, rng)
            raw.append((prof, states, sents, ". ".join(order_text) + "."))
        texts = [r[3] for r in raw]
        vec = TfidfVectorizer().fit([ref] + texts)
        M = vec.transform(texts)
        cos_ref = cosine_similarity(vec.transform([ref]), M)[0]
        S = cosine_similarity(M)
        np.fill_diagonal(S, -1)

        for i, (prof, states, sents, text) in enumerate(raw):
            aid = f"{q['id']}_{i:04d}"
            pts = {c[0]: c[2] for c in q["concepts"]}
            covered = {c: states[c] in ("correct", "paraphrased") for c in states}
            true_score = float(sum(pts[c] for c in covered if covered[c]))
            others_all = list(sents.values())

            # ---- C3 stand-in: persistent grader error + per-run noise, repeated k times
            base = {c: covered[c] ^ (rng.random() < P_SYS[states[c]]) for c in states}
            run_dec, run_tot = [], []
            for _ in range(cfg.k_runs):
                d = {c: base[c] ^ (rng.random() < P_NOISE[states[c]]) for c in states}
                run_dec.append(d)
                run_tot.append(float(sum(pts[c] for c in d if d[c])))
            final_total = mode_score(run_tot)
            final_dec = next(d for d, t in zip(run_dec, run_tot) if t == final_total)
            crits = []
            for cid, ctext, cp in q["concepts"]:
                awarded = final_dec[cid]
                span = None
                if awarded:
                    own = sents.get(cid)
                    others = [s for k, s in sents.items() if k != cid]
                    span = make_span(states[cid], ctext, own, others, rng)
                crits.append(Criterion(id=f"c_{cid}", concept_id=cid, description=ctext, weight=cp / 5.0,
                                       points=float(cp) if awarded else 0.0, max_points=float(cp), evidence_span=span))
            ai_score = final_total
            if rng.random() < cfg.p_total_fault:
                ai_score = ai_score + 1 if ai_score < 5 else ai_score - 1
            c3 = C3Output(rubric_id=f"r_{q['id']}", rubric_version=1, rubric_approved=bool(rng.random() >= cfg.p_unapproved),
                          max_score=5.0, runs=run_tot, ai_score=ai_score, criteria=crits)

            # ---- C4 stand-in
            claims = []
            for c in crits:
                if c.points > 0:
                    cid = c.concept_id
                    if rng.random() < .75:
                        span = c.evidence_span
                    else:
                        span = make_span(states[cid], c.description, sents.get(cid), [s for k, s in sents.items() if k != cid], rng)
                    claims.append(Claim(criterion_id=c.id, outcome="met", span=span))
                else:
                    claims.append(Claim(criterion_id=c.id, outcome="not_met"))
            for j, cl in enumerate(claims):
                if rng.random() < .04:
                    claims[j] = Claim(criterion_id=cl.criterion_id, outcome="not_met" if cl.outcome == "met" else "met", span=cl.span)
                elif rng.random() < .02:
                    claims[j] = Claim(criterion_id="c_x9", outcome=cl.outcome, span=cl.span)
            gaps = [c.concept_id for c in crits if c.points <= 0 and rng.random() > .12]
            gaps += [c.concept_id for c in crits if c.points > 0 and rng.random() < .08]
            stated = c3.ai_score if rng.random() < .98 else c3.ai_score + 1
            c4 = C4Output(claims=claims, direct_gaps=gaps, stated_score=stated) if rng.random() >= cfg.p_missing_c4 else None

            # ---- C1 stand-in (lexical proxies of bi-encoder, cross-encoder, NLI)
            ov = {c[0]: matcher.overlap(c[1], text) for c in q["concepts"]}
            neg = {c[0]: matcher.negated(c[1], text) for c in q["concepts"]}
            w = np.array([c[2] for c in q["concepts"]], float)
            cross = float(np.clip(sum(w[k] * (ov[c[0]] * (0.2 if neg[c[0]] else 1.0)) for k, c in enumerate(q["concepts"])) / w.sum(), 0, 1))
            ent_cov = float(sum(w[k] * (ov[c[0]] >= .5 and not neg[c[0]]) for k, c in enumerate(q["concepts"])) / w.sum())
            con = float(np.clip((.75 if any(neg.values()) else .05) + rng.normal(0, .05), 0, .99))
            ent = ent_cov * (1 - con)
            neu = max(0.0, 1 - ent - con)
            tot = ent + con + neu
            missing = [c[0] for c in q["concepts"] if ov[c[0]] < .5 or neg[c[0]]]
            knn = float(np.sort(S[i])[-5:].mean())
            c1 = C1Output(cos_bi=float(np.clip(cos_ref[i], 0, 1)), cross_enc=cross,
                          nli=NLIProbs(ent=ent / tot, con=con / tot, neu=neu / tot),
                          missing_concepts=missing, n_concepts=len(q["concepts"]),
                          knn_typicality=float(np.clip(knn, 0, 1))) if rng.random() >= cfg.p_missing_c1 else None

            case = AssessmentCase(assessment_id=aid, question_id=q["id"], student_response=text, reference_answer=ref,
                                  c1=c1, c3=c3, c4=c4, provenance=Provenance(model="standin", version="0", run_ids=[f"{aid}_r{k}" for k in range(cfg.k_runs)]))
            # ---- simulated human graders (3), mostly accurate
            hs = [float(np.clip(true_score + rng.choice([0, 1, -1], p=[.88, .06, .06]), 0, 5)) for _ in range(3)]
            labels[aid] = LabelRecord(human_scores=hs, max_score=5.0)
            ymap[aid] = make_label(c3.ai_score, hs)
            qof[aid] = q["id"]
            truth[aid] = {"profile": prof, "states": states, "true_score": true_score}
            cases.append(case)
    return Dataset(cases=cases, labels=labels, question_of=qof, meta={"y": ymap, "truth": truth})

"""End-to-end experiment: split BY QUESTION, fit on dev, select on val, report on test.
Usage: python scripts/run_experiment.py [--seed 7] [--n 150]"""
import argparse, copy, json, sys, pathlib
import numpy as np, pandas as pd, joblib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
from cari.config import CariConfig
from cari.synth.generator import generate_dataset, SynthConfig
from cari.synth.bank import QUESTIONS
from cari.adapters.standin import LexicalEntailment, make_known_syn
from cari.pipeline import build_table, fit_semantic_model, feature_cols, CariEngine
from cari.aggregation import make_aggregators, AHPWeighted, wmean, DEFAULT_PRIORITIES
from cari.thresholds import choose_tau
from cari.evaluation import evaluate, auc, pr_auc, aurc, risk_coverage

ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--n", type=int, default=150)
args = ap.parse_args()
OUT = pathlib.Path(__file__).resolve().parents[1] / "results"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(args.seed)

ds = generate_dataset(SynthConfig(seed=args.seed, n_per_question=args.n))
qs = [q["id"] for q in QUESTIONS]; rng.shuffle(qs)
split_q = {"dev": qs[:4], "val": qs[4:6], "test": qs[6:]}
part = {k: [c for c in ds.cases if c.question_id in v] for k, v in split_q.items()}
print("Question split:", split_q)
print({k: (len(v), round(float(np.mean([ds.meta['y'][c.assessment_id] for c in v])), 3)) for k, v in part.items()}, "(n, unreliable rate)")

entail = LexicalEntailment(make_known_syn(np.random.default_rng(args.seed + 1), .6))  # independent of C1's checker
cfg = CariConfig()
sem = fit_semantic_model(part["dev"], ds.labels)
T = {k: build_table(v, entail, sem, cfg, ds.meta["y"]) for k, v in part.items()}
y = {k: T[k]["y"].to_numpy() for k in T}

# ---- 1. sign check: univariate AUC of each indicator on dev (x low => unreliable; AUC < 0.5 => wrong sign)
rows = []
for col in feature_cols("indicator") + feature_cols("component"):
    x = np.nan_to_num(T["dev"][col].to_numpy(float), nan=0.0)
    rows.append({"feature": col, "dev_auc": roc_auc_score(y["dev"], -x), "test_auc": roc_auc_score(y["test"], -np.nan_to_num(T["test"][col].to_numpy(float), nan=0.0))})
sign = pd.DataFrame(rows).round(3); sign.to_csv(OUT / "indicator_sign_check.csv", index=False)
print("\n== Indicator sign check (AUC of 'low value => unreliable'; 0.5 = no signal) =="); print(sign.to_string(index=False))

# ---- 2. method comparison
def run(level, policy, tables=T, cfgx=cfg):
    cols = feature_cols(level); res = []
    for name, agg in make_aggregators(cols).items():
        agg.fit(tables["dev"][cols].to_numpy(float), y["dev"], cols)
        sc = {k: np.nan_to_num(agg.score(tables[k][cols].to_numpy(float)), nan=0.0) for k in tables}
        tau = choose_tau(sc["dev"], y["dev"], policy, recall_target=cfgx.recall_target)
        for split in ("val", "test"):
            m = evaluate(sc[split], tables[split]["gate"], y[split], tau)
            m.update(method=name, level=level, policy=policy, split=split, tau=tau, auc=auc(sc[split], y[split]),
                     pr_auc=pr_auc(sc[split], y[split]), aurc=aurc(sc[split], y[split]))
            res.append(m)
        res[-1]["scores"] = sc["test"]; res[-2]["scores"] = sc["val"]
    return res

allres = []
for level in ("indicator", "component"):
    for policy in ("recall", "f1"):
        allres += run(level, policy)
for split in ("val", "test"):
    for name, flag in (("B_always_auto", np.zeros(len(y[split]), bool)), ("B_always_human", np.ones(len(y[split]), bool)),
                       ("B_gates_only", T[split]["gate"].to_numpy())):
        tp, fp = int((flag & (y[split] == 1)).sum()), int((flag & (y[split] == 0)).sum())
        fn, tn = int((~flag & (y[split] == 1)).sum()), int((~flag & (y[split] == 0)).sum()); n = len(flag)
        pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
        allres.append({"method": name, "level": "-", "policy": "-", "split": split, "precision": pr, "recall": rc,
                       "f1": 2 * pr * rc / (pr + rc) if pr + rc else 0, "workload": (tp + fp) / n,
                       "released_error": fn / (tn + fn) if tn + fn else 0, "auc": np.nan, "aurc": np.nan, "pr_auc": np.nan, "tau": np.nan})
df = pd.DataFrame([{k: v for k, v in r.items() if k != "scores"} for r in allres])
df.round(4).to_csv(OUT / "method_comparison.csv", index=False)
show = ["method", "level", "auc", "aurc", "precision", "recall", "f1", "workload", "released_error"]
print("\n== TEST set, tau = smallest threshold giving >=95% recall on dev (gates ON) ==")
print(df[(df.split == "test") & (df.policy.isin(["recall", "-"]))][show].round(3).sort_values(["level", "auc"], ascending=[True, False]).to_string(index=False))
print("\n== TEST set, tau = argmax-F1 on dev (SURE-style) ==")
print(df[(df.split == "test") & (df.policy == "f1")][show].round(3).sort_values(["level", "f1"], ascending=[True, False]).to_string(index=False))

# ---- 3. pick best by VALIDATION AUC (indicator level), then ablation + sensitivity on it
cand = df[(df.split == "val") & (df.level == "indicator") & (df.policy == "recall") & (~df.method.str.startswith("M0"))]
best = cand.sort_values("auc", ascending=False).iloc[0]["method"]
print(f"\nBest indicator-level method by validation AUC: {best}")
cols = feature_cols("indicator"); abl = []
base_auc = None
for drop in [None] + cols:
    use = [c for c in cols if c != drop]
    agg = make_aggregators(use)[best].fit(T["dev"][use].to_numpy(float), y["dev"], use)
    a = auc(agg.score(T["test"][use].to_numpy(float)), y["test"]); base_auc = a if drop is None else base_auc
    abl.append({"dropped": drop or "(none)", "test_auc": a, "delta_auc": a - base_auc})
abl = pd.DataFrame(abl).round(4); abl.to_csv(OUT / "ablation.csv", index=False)
print("\n== Ablation (drop one indicator, refit) =="); print(abl.to_string(index=False))

sens = []
base_agg = AHPWeighted().fit(T["dev"][cols].to_numpy(float), y["dev"], cols)
base_sc = np.nan_to_num(base_agg.score(T["test"][cols].to_numpy(float)), nan=0.0)
base_flag = (base_sc < choose_tau(np.nan_to_num(base_agg.score(T["dev"][cols].to_numpy(float)), nan=0), y["dev"], "recall", recall_target=.95)) | T["test"]["gate"].to_numpy()
for d in range(60):
    g = np.random.default_rng(1000 + d)
    pr = {k: v * float(np.exp(g.normal(0, .35))) for k, v in DEFAULT_PRIORITIES.items()}   # independent factor per indicator
    ag = AHPWeighted(pr).fit(T["dev"][cols].to_numpy(float), y["dev"], cols)
    scd, sct = np.nan_to_num(ag.score(T["dev"][cols].to_numpy(float)), nan=0), np.nan_to_num(ag.score(T["test"][cols].to_numpy(float)), nan=0)
    tau = choose_tau(scd, y["dev"], "recall", recall_target=.95); m = evaluate(sct, T["test"]["gate"], y["test"], tau)
    sens.append({"draw": d, "f1": m["f1"], "recall": m["recall"], "workload": m["workload"], "decision_agreement": float(((sct < tau) | T["test"]["gate"].to_numpy() == base_flag).mean())})
sens = pd.DataFrame(sens); sens.to_csv(OUT / "sensitivity_ahp.csv", index=False)
print("\n== Sensitivity: 60 random perturbations of the AHP priorities (sd 0.35 in log space) ==")
print(sens[["f1", "recall", "workload", "decision_agreement"]].describe().loc[["mean", "min", "max"]].round(3).to_string())

# ---- 4. exact vs fuzzy evidence matching
cf = CariConfig(fuzzy_threshold=0.8)
Tf = build_table(part["test"], entail, sem, cf, ds.meta["y"])
print("\n== Evidence grounding variant (test AUC of the single indicator) ==")
for col in ("c3_evidence_validity", "c4_explanation_support"):
    print(f"{col}: exact={roc_auc_score(y['test'], -np.nan_to_num(T['test'][col], nan=0)):.3f}  fuzzy0.8={roc_auc_score(y['test'], -np.nan_to_num(Tf[col], nan=0)):.3f}")

# ---- 5. risk-coverage plot
fig, ax = plt.subplots(figsize=(6.2, 4))
for r in allres:
    if r.get("split") == "test" and r.get("policy") == "recall" and r.get("level") == "indicator" and r["method"] in ("M0_consistency_only", "M1_equal", best):
        cov, risk = risk_coverage(r["scores"], y["test"]); ax.plot(cov, risk, label=r["method"])
ax.axhline(y["test"].mean(), ls=":", c="grey", label="release everything"); ax.set_xlabel("coverage (share auto-released)"); ax.set_ylabel("error rate among released")
ax.set_title("Risk-coverage on test questions (synthetic data)"); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT / "risk_coverage.png", dpi=130)

# ---- 6. final engine for the API (best method, fitted on dev)
eng = CariEngine(CariConfig(), entail, make_aggregators(cols)[best]).fit(part["dev"], ds.labels, ds.meta["y"])
joblib.dump(eng, OUT.parent / "models" / "engine.joblib")
print(f"\nSaved models/engine.joblib  (method={best}, tau={eng.tau:.3f})")

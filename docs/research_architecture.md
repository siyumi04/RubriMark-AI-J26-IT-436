# Adaptive AI-Based Rubric Generation and Criterion-Based Scoring System for Subjective Assessments

**Research Component ID:** `IT23376472`  
**Group:** `RubriMark-AI-J26-IT-436`  
**Framework:** RubriMark AI - Trustworthy Explainable Short-Answer Evaluation  

---

## 1. Research Overview
This research component addresses the inconsistency, latency, and cognitive load associated with manual subjective grading in higher education. It delivers an AI framework capable of:
1. Deconstructing subjective questions using Bloom's Taxonomy.
2. Generating multi-tiered adaptive rubrics (Exemplary, Proficient, Developing, Unsatisfactory).
3. Normalizing and dynamically balancing criteria weights to ensure mathematical validity (100%).
4. Enforcing pedagogical validation rules.
5. Providing lecturers with editing, fine-tuning, and approval controls.
6. Performing criterion-by-criterion semantic evaluation with formative feedback.
7. Generating diagnostic assessment analytics for instructional intervention.

---

## 2. Architecture & File Structure

```
RubriMark-AI-J26-IT-436/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── assessments.py      # Feature 1: Assessment creation & management
│   │   │   ├── analysis.py         # Feature 2: AI Question analysis & Bloom's extraction
│   │   │   ├── rubrics.py          # Features 3, 4, 5, 6: Rubric generation, weights, validation, approval
│   │   │   ├── scoring.py          # Feature 7: Criterion-based student answer scoring
│   │   │   ├── results.py          # Feature 8: Assessment results & cohort analytics
│   │   │   └── __init__.py         # API v1 aggregator
│   │   ├── core/
│   │   │   ├── config.py           # Configuration & research component metadata
│   │   │   └── database.py         # SQLAlchemy engine, session generator, SQLite setup
│   │   ├── models/
│   │   │   ├── assessment.py       # Assessment ORM
│   │   │   ├── rubric.py           # Rubric & RubricCriterion ORMs
│   │   │   └── submission.py       # StudentSubmission & CriterionScore ORMs
│   │   ├── schemas/
│   │   │   ├── assessment.py       # Pydantic schemas for assessments
│   │   │   ├── rubric.py           # Pydantic schemas for rubrics & weights
│   │   │   └── submission.py       # Pydantic schemas for scoring & analytics
│   │   ├── services/
│   │   │   ├── ai_service.py       # Core AI rubric generation & scoring engine
│   │   │   └── weight_optimizer.py # Dynamic weight balancing & optimization algorithms
│   │   └── main.py                 # FastAPI application, CORS, database lifecycle
│   ├── requirements.txt            # Python dependencies
│   ├── run.py                      # Local backend launcher
│   └── .env                        # Local environment settings
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx         # Dark navy sidebar navigation
│   │   │   └── Header.jsx          # Academic header & researcher credentials
│   │   ├── services/
│   │   │   └── api.js              # REST client for FastAPI endpoints
│   │   ├── App.jsx                 # Interactive research dashboard with all 8 modules
│   │   ├── index.css               # Clean academic design system (Navy / White / Purple / Blue)
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
```

---

## 3. API Endpoints Summary

| Feature | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/api/v1/health` | Service health & research component status |
| **1. Assessments** | `POST` | `/api/v1/assessments/` | Create lecturer subjective assessment |
| | `GET` | `/api/v1/assessments/` | List all assessments |
| **2. Analysis** | `POST` | `/api/v1/analysis/question` | AI question Bloom's taxonomy & concepts analysis |
| **3. Rubrics** | `POST` | `/api/v1/rubrics/generate` | Adaptive multi-tier rubric generation |
| **4. Weights** | `POST` | `/api/v1/rubrics/{id}/optimize-weights` | Dynamic weight balancing (100% sum) |
| **5. Validation** | `POST` | `/api/v1/rubrics/{id}/validate` | Automated rubric quality & completeness check |
| **6. Approval** | `POST` | `/api/v1/rubrics/{id}/approve` | Lecturer official review and sign-off |
| **7. Scoring** | `POST` | `/api/v1/scoring/evaluate` | Criterion-based student evaluation & feedback |
| **8. Results** | `GET` | `/api/v1/results/assessment/{id}` | Cohort metrics & criterion performance heatmap |

"""
Dataset Integration & Research Evaluation API Router for RubriMark AI (IT23376472).
Provides endpoints for:
- Importing lecturer rubric CSVs (5 Java OOP questions)
- Importing student response questionnaires (62 students, handling missing emails/blank scores)
- Running batch evaluations (Semantic vs Keyword Baseline)
- Computing real research metrics (MAE, RMSE, Cohen's Kappa / agreement metrics)
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.rubric import Rubric
from app.models.submission import StudentSubmission
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/dataset", tags=["Dataset Integration & Research Evaluation"])

# Local data file paths
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"
DEFAULT_RUBRIC_CSV = DATA_DIR / "IT23376472_Complete_Lecturer_Rubric_Template (1).csv"
DEFAULT_STUDENT_CSV = DATA_DIR / "student_responses.csv"


class BatchEvaluationRequest(BaseModel):
    assessment_id: Optional[int] = None
    scoring_method: Optional[str] = "semantic"  # "semantic" or "keyword_baseline"


@router.get("/status")
def get_dataset_status(
    scope: str = Query("benchmark", description="Scope of dataset statistics: 'benchmark' or 'full'/'all'"),
    db: Session = Depends(get_db)
):
    """
    Returns current dataset integration status:
    - scope='benchmark': Filtered to 5 verified Java OOP benchmark questions (IT4360)
    - scope='full' or 'all': Whole database status across all assessments
    """
    return DatasetService.compute_dataset_status(db=db, scope=scope)



@router.post("/import-lecturer-rubric")
async def import_lecturer_rubric(
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Imports the lecturer rubric CSV template.
    If no file uploaded, loads the project's actual IT23376472_Complete_Lecturer_Rubric_Template CSV.
    Creates 5 Java OOP assessments and approved rubrics.
    """
    if file:
        content_bytes = await file.read()
        csv_text = content_bytes.decode("utf-8", errors="replace")
    else:
        # Load default file from disk
        candidate_paths = [
            DEFAULT_RUBRIC_CSV,
            DATA_DIR / "lecturer_rubric.csv"
        ]
        target_path = None
        for p in candidate_paths:
            if p.exists():
                target_path = p
                break

        if not target_path:
            raise HTTPException(status_code=404, detail="Default lecturer rubric CSV not found in data directory.")

        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            csv_text = f.read()

    result = DatasetService.import_lecturer_rubric_csv(csv_text, db)
    return result


@router.post("/import-student-responses")
async def import_student_responses(
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Imports the student responses questionnaire (62 students x 5 questions).
    Handles missing emails, blank scores, and prevents duplicate records.
    """
    if file:
        content_bytes = await file.read()
        csv_text = content_bytes.decode("utf-8", errors="replace")
    else:
        target_path = DEFAULT_STUDENT_CSV
        if not target_path.exists():
            # Check candidate filenames
            candidates = list(DATA_DIR.glob("*Responses*.csv"))
            if candidates:
                target_path = candidates[0]
            else:
                raise HTTPException(status_code=404, detail="Default student responses CSV not found in data directory.")

        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            csv_text = f.read()

    result = DatasetService.import_student_responses_csv(csv_text, db)
    return result


@router.post("/batch-evaluate")
def batch_evaluate_submissions(
    request: BatchEvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Runs batch scoring on imported student responses using either 'semantic' (default)
    or 'keyword_baseline'.
    """
    result = DatasetService.run_batch_evaluation(
        db=db,
        assessment_id=request.assessment_id,
        scoring_method=request.scoring_method or "semantic"
    )
    return result


@router.get("/research-metrics")
def get_research_evaluation_metrics(
    scope: str = Query("benchmark", description="Scope: 'benchmark' or 'full'/'all'"),
    db: Session = Depends(get_db)
):
    """
    Returns authentic research metrics evaluating Semantic AI vs Keyword Baseline.
    - scope='benchmark': 5 Java OOP benchmark questions (IDs 47–51, 310 submissions)
    - scope='full' or 'all': Full database submissions
    """
    return DatasetService.compute_research_evaluation_metrics(db=db, scope=scope)


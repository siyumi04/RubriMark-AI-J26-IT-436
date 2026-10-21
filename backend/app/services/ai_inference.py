import os
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("rubrimark.ai")


class AIInferenceService:
    def __init__(self, model_path: Optional[str] = None):
        default_model = os.getenv("ML_MODEL_PATH", "./ml_models/rubrimark_oop_model.joblib")
        self.model_path = model_path or default_model
        self.model = None
        self.classifiers: List[Any] = []
        self.label_classes: List[str] = []
        self.embedding_model_name: Optional[str] = None
        self.sentence_transformer = None
        self.threshold: float = 0.5
        self.label_status: str = "Uninitialized"
        self.vectorizer = None
        self.model_type: str = "generic"
        self.is_loaded = False
        self.status_message = "Model not initialized"
        self.model_metadata: Dict[str, Any] = {}

    def _find_model_file(self) -> Optional[str]:
        """Resolves the best available path for the trained model artifact."""
        here = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(here))
        
        candidates = [
            self.model_path,
            os.path.join(backend_dir, "ml_models", "rubrimark_oop_model.joblib"),
            os.path.join(backend_dir, "ml_models", "feedback_model.joblib"),
            "./ml_models/rubrimark_oop_model.joblib",
            "./ml_models/feedback_model.joblib",
            "backend/ml_models/rubrimark_oop_model.joblib",
            "backend/ml_models/feedback_model.joblib",
        ]
        for path in candidates:
            if path and os.path.exists(path) and os.path.isfile(path):
                return os.path.abspath(path)
        return None

    def load_model(self) -> Tuple[bool, str]:
        """
        Safely attempts to load the trained Joblib model during backend startup.
        Never retrains the model. If the file is not found or corrupted, reports
        unavailability transparently without fabricating predictions.
        """
        resolved_path = self._find_model_file()
        if not resolved_path:
            self.is_loaded = False
            self.status_message = (
                f"AI model file not found at '{self.model_path}'. "
                "AI inference is unavailable. Please place 'rubrimark_oop_model.joblib' in backend/ml_models/."
            )
            logger.warning(self.status_message)
            return False, self.status_message

        self.model_path = resolved_path

        try:
            import joblib
            logger.info(f"Loading AI model from {self.model_path}...")
            loaded_artifact = joblib.load(self.model_path)

            if isinstance(loaded_artifact, dict) and "classifiers" in loaded_artifact and "embedding_model" in loaded_artifact:
                # Custom MultiOutput SentenceTransformer + Classifier Ensemble
                self.model_type = "sentence_transformer_ensemble"
                self.classifiers = loaded_artifact["classifiers"]
                self.label_classes = loaded_artifact.get("label_classes", [])
                self.embedding_model_name = loaded_artifact.get("embedding_model", "all-MiniLM-L6-v2")
                self.threshold = float(loaded_artifact.get("threshold", 0.5))
                self.label_status = loaded_artifact.get("label_status", "Provisional labels")

                # Load sentence transformer
                logger.info(f"Initializing SentenceTransformer: {self.embedding_model_name}...")
                from sentence_transformers import SentenceTransformer
                self.sentence_transformer = SentenceTransformer(self.embedding_model_name)

                self.model_metadata = {
                    "model_class": "SentenceTransformerEnsemble",
                    "embedding_model": self.embedding_model_name,
                    "num_classifiers": len(self.classifiers),
                    "num_classes": len(self.label_classes),
                    "label_classes": self.label_classes,
                    "threshold": self.threshold,
                    "label_status": self.label_status,
                    "has_predict": True,
                    "has_predict_proba": True,
                }
                self.is_loaded = True
                self.status_message = (
                    f"RubriMark OOP Model loaded successfully ({len(self.classifiers)} binary classifiers, "
                    f"embedding: {self.embedding_model_name}, threshold: {self.threshold})"
                )
                logger.info(self.status_message)
                return True, self.status_message

            elif isinstance(loaded_artifact, dict):
                # Wrapped generic dict
                self.model = loaded_artifact.get("model", loaded_artifact)
                self.vectorizer = loaded_artifact.get("vectorizer") or loaded_artifact.get("tfidf")
                self.label_classes = loaded_artifact.get("concept_mapping") or loaded_artifact.get("classes", [])
                self.model_type = "sklearn_generic"
            else:
                self.model = loaded_artifact
                self.model_type = "sklearn_generic"

            model_type_name = type(self.model).__name__
            self.model_metadata["model_class"] = model_type_name
            self.model_metadata["has_predict"] = hasattr(self.model, "predict")
            self.model_metadata["has_predict_proba"] = hasattr(self.model, "predict_proba")

            # Check if companion vectorizer exists separately
            model_dir = os.path.dirname(self.model_path)
            for vec_name in ["vectorizer.joblib", "tfidf.joblib", "tokenizer.joblib"]:
                vec_path = os.path.join(model_dir, vec_name)
                if os.path.exists(vec_path) and self.vectorizer is None:
                    try:
                        self.vectorizer = joblib.load(vec_path)
                        logger.info(f"Loaded companion vectorizer from {vec_path}")
                        self.model_metadata["companion_vectorizer"] = vec_path
                    except Exception as e:
                        logger.warning(f"Failed to load companion vectorizer: {e}")

            self.is_loaded = True
            self.status_message = f"Model loaded successfully ({model_type_name})"
            logger.info(self.status_message)
            return True, self.status_message

        except Exception as e:
            self.is_loaded = False
            self.status_message = f"Error loading AI model: {str(e)}"
            logger.error(self.status_message)
            return False, self.status_message

    def predict_detailed(
        self,
        student_answer: str,
        question_text: Optional[str] = None,
        question_id: Optional[str] = None,
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs detailed model inference returning question-specific concept predictions,
        distinguishing detected concepts, expected-but-undetected concepts, model uncertainty,
        and safely isolating out-of-domain cross-question anomalies.
        """
        # Question-specific expected concepts mapping (curriculum Q1-Q5)
        CURRICULUM_EXPECTED_CONCEPTS: Dict[str, List[str]] = {
            "Q1": [
                "Class as blueprint/template",
                "Object as class instance",
                "Concrete class-object example"
            ],
            "Q2": [
                "Inheritance of accessible fields",
                "Inheritance of accessible methods"
            ],
            "Q3": [
                "Child provides overriding implementation",
                "Child implementation executes on child object"
            ],
            "Q4": [
                "Static belongs to class",
                "instance variable belongs to object",
                "No direct instance-variable access from static method",
                "Instance reference required for access"
            ],
            "Q5": [
                "Handles runtime exceptions/errors",
                "Prevents abrupt termination or supports graceful recovery"
            ]
        }

        # Resolve question ID
        qid = None
        if question_id and question_id.upper() in CURRICULUM_EXPECTED_CONCEPTS:
            qid = question_id.upper()
        elif question_text:
            q_clean = question_text.lower()
            if "01." in q_clean or "difference between a class and an object" in q_clean or "blueprint" in q_clean:
                qid = "Q1"
            elif "02." in q_clean or "car class extends a vehicle" in q_clean or "car class get from the vehicle" in q_clean:
                qid = "Q2"
            elif "03." in q_clean or "overrides a method" in q_clean or "child class overrides" in q_clean:
                qid = "Q3"
            elif "04." in q_clean or "static method directly access" in q_clean or "non-static variable" in q_clean:
                qid = "Q4"
            elif "05." in q_clean or "exception handling" in q_clean:
                qid = "Q5"

        expected_for_q = CURRICULUM_EXPECTED_CONCEPTS.get(qid, []) if qid else []

        if not self.is_loaded:
            return {
                "success": False,
                "student_id": student_id,
                "question_id": qid,
                "expected_concepts": expected_for_q,
                "detected_concepts": [],
                "question_relevant_concepts": [],
                "substantive_missing_concepts": [],
                "expected_undetected_concepts": expected_for_q,
                "unrelated_cross_question_concepts": [],
                "cross_question_anomalies_filtered": [],
                "concept_probabilities": {},
                "requires_human_review": False,
                "none_identified": False,
                "is_uncertain": False,
                "uncertainty_info": "Model not loaded.",
                "message": "AI inference is unavailable: No trained model loaded in the backend."
            }

        try:
            input_text = student_answer.strip()
            detected_concepts = []
            concept_probabilities = {}

            if self.model_type == "sentence_transformer_ensemble":
                if not self.sentence_transformer:
                    from sentence_transformers import SentenceTransformer
                    self.sentence_transformer = SentenceTransformer(self.embedding_model_name)

                embedding = self.sentence_transformer.encode([input_text])

                for c_name, clf in zip(self.label_classes, self.classifiers):
                    if hasattr(clf, "predict_proba"):
                        prob = float(clf.predict_proba(embedding)[0][1])
                    else:
                        prob = float(clf.predict(embedding)[0])
                    concept_probabilities[c_name] = round(prob, 4)
                    if prob >= self.threshold:
                        detected_concepts.append(c_name)

            elif hasattr(self.model, "predict"):
                if self.vectorizer is not None:
                    features = self.vectorizer.transform([input_text])
                    raw = self.model.predict(features)
                else:
                    raw = self.model.predict([input_text])

                if hasattr(raw, "tolist"):
                    raw = raw.tolist()

                if isinstance(raw, list) and len(raw) > 0:
                    pred_item = raw[0]
                    if isinstance(pred_item, (list, set, tuple)):
                        detected_concepts = [str(x).strip() for x in pred_item if str(x).strip()]
                    elif isinstance(pred_item, str):
                        detected_concepts = [c.strip() for c in pred_item.replace(";", ",").split(",") if c.strip()]
                    else:
                        detected_concepts = [str(pred_item)]

            # 1. Meta-labels filtering (Requirement 4)
            # These are diagnostic flags and MUST NEVER be counted as OOP concepts or knowledge gaps
            requires_human_review = "requires human review" in detected_concepts
            none_identified = "None clearly identified" in detected_concepts

            # Substantive concepts (pure OOP concepts)
            substantive_raw = [
                c for c in detected_concepts
                if c not in ["requires human review", "None clearly identified"]
            ]

            # 2. Compare model predictions with expected concepts for that specific question (Requirement 3 & 7)
            question_relevant_concepts = []
            unrelated_cross_question_concepts = []
            cross_question_anomalies_filtered = []

            if expected_for_q:
                for c in substantive_raw:
                    if c in expected_for_q:
                        question_relevant_concepts.append(c)
                    else:
                        unrelated_cross_question_concepts.append(c)
                        cross_question_anomalies_filtered.append(
                            f"Unrelated concept '{c}' flagged under question {qid} - filtered as cross-question anomaly"
                        )
            else:
                question_relevant_concepts = substantive_raw

            # 3. Model Uncertainty Determination (Requirement 5 & 6)
            # Check borderline probabilities (0.45 <= prob <= 0.55) or meta flags
            borderline_concepts = [
                c for c, p in concept_probabilities.items()
                if 0.45 <= p <= 0.55 and c not in ["requires human review", "None clearly identified"]
            ]

            is_uncertain = requires_human_review or none_identified or len(unrelated_cross_question_concepts) > 0 or len(borderline_concepts) > 0
            uncertainty_reasons = []
            if requires_human_review:
                uncertainty_reasons.append("Model activated 'requires human review' flag")
            if none_identified:
                uncertainty_reasons.append("Model activated 'None clearly identified' flag")
            if unrelated_cross_question_concepts:
                uncertainty_reasons.append(f"Cross-question concept anomaly detected ({', '.join(unrelated_cross_question_concepts)})")
            if borderline_concepts:
                uncertainty_reasons.append(f"Borderline classification confidence for: {', '.join(borderline_concepts[:2])}")

            uncertainty_info = "; ".join(uncertainty_reasons) if uncertainty_reasons else "Prediction confidence is within normal operational bounds."

            # 4. Question-Specific Substantive Gaps
            # Substantive gaps strictly exclude metadata labels AND unrelated cross-question concepts
            substantive_missing_concepts = question_relevant_concepts

            # 5. Expected concepts not detected
            expected_undetected_concepts = [c for c in expected_for_q if c not in substantive_missing_concepts]

            return {
                "success": True,
                "student_id": student_id,
                "question_id": qid,
                "expected_concepts": expected_for_q,
                "detected_concepts": detected_concepts,
                "question_relevant_concepts": question_relevant_concepts,
                "substantive_missing_concepts": substantive_missing_concepts,
                "expected_undetected_concepts": expected_undetected_concepts,
                "unrelated_cross_question_concepts": unrelated_cross_question_concepts,
                "cross_question_anomalies_filtered": cross_question_anomalies_filtered,
                "concept_probabilities": concept_probabilities,
                "requires_human_review": requires_human_review or is_uncertain,
                "none_identified": none_identified,
                "is_uncertain": is_uncertain,
                "uncertainty_info": uncertainty_info,
                "message": "AI inference completed successfully."
            }

        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {
                "success": False,
                "student_id": student_id,
                "question_id": qid,
                "expected_concepts": expected_for_q,
                "detected_concepts": [],
                "question_relevant_concepts": [],
                "substantive_missing_concepts": [],
                "expected_undetected_concepts": expected_for_q,
                "unrelated_cross_question_concepts": [],
                "cross_question_anomalies_filtered": [],
                "concept_probabilities": {},
                "requires_human_review": False,
                "none_identified": False,
                "is_uncertain": False,
                "uncertainty_info": f"Inference failure: {str(e)}",
                "message": f"AI inference error: {str(e)}"
            }

    def predict_missing_concepts(
        self,
        student_answer: str,
        question_text: Optional[str] = None,
        question_id: Optional[str] = None,
        student_id: Optional[str] = None
    ) -> Tuple[bool, List[str], str]:
        """
        Runs model inference to identify missing concepts for a specific question.
        Returns (success, substantive_missing_concepts, status_message)
        """
        details = self.predict_detailed(
            student_answer=student_answer,
            question_text=question_text,
            question_id=question_id,
            student_id=student_id
        )
        if not details["success"]:
            return False, [], details["message"]
        
        return True, details["substantive_missing_concepts"], details["message"]


# Singleton instance for application lifecycle
ai_service = AIInferenceService()

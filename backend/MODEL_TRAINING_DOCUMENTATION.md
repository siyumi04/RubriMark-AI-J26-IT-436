# RubriMark AI – Model Training & Architecture Documentation

## 1. Overview & Artifact Information
* **Artifact File**: `backend/ml_models/rubrimark_oop_model.joblib`
* **File Size**: ~29,315 bytes
* **Container Type**: Python dictionary serialized with `joblib`
* **Artifact Keys**: `['classifiers', 'label_classes', 'embedding_model', 'threshold', 'label_status']`
* **Component Role**: Evaluates student short answers across 5 core Java Object-Oriented Programming (OOP) questions, extracting present and missing concept components to power Knowledge Gap Detection and personalized learning recommendations.

---

## 2. Model Architecture & Embedding Model
* **Pipeline Type**: Multi-label semantic sentence classification ensemble (Binary Relevance strategy).
* **Dense Text Representation**:
  * **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
  * **Embedding Dimension**: 384 dimensions
  * **Pooling**: Mean pooling over transformer token representations
  * **Normalization**: L2 normalized embeddings
* **Inference Strategy**:
  1. Raw student response text is mapped to a 384-dimensional dense vector using `all-MiniLM-L6-v2`.
  2. The dense vector is independently evaluated by 15 separate binary classifiers.
  3. Classifiers output class probability $P(\text{concept} = 1 \mid \vec{x})$.

---

## 3. Classification Algorithm & 13 Educational Labels
* **Base Estimator**: `sklearn.linear_model.LogisticRegression`
  * **Solver**: `lbfgs`
  * **Class Weight**: `balanced` (adjusts weights inversely proportional to class frequencies)
  * **Regularization**: $C = 1.0$ ($L_2$ penalty)
  * **Tolerance**: $1\text{e-}4$
  * **Max Iterations**: 1000
  * **Random State**: 42
* **Total Classifier Heads**: 15 binary classifiers

### Exact Educational Concept Labels (13 Total)
Excluding the 2 system/metadata triage labels (`"None clearly identified"`, `"requires human review"`), the 13 educational concept labels aligned with the curriculum DAG are:

| # | Question | Concept Label | Concept Role / Focus |
|---|---|---|---|
| 1 | Q1 | `Class as blueprint/template` | Class definition as template/specification |
| 2 | Q1 | `Object as class instance` | Object as heap-allocated class instance |
| 3 | Q1 | `Concrete class-object example` | Practical example differentiating class vs object |
| 4 | Q2 | `Inheritance of accessible fields` | Subclass acquisition of parent attributes |
| 5 | Q2 | `Inheritance of accessible methods` | Subclass acquisition of parent methods/behaviors |
| 6 | Q3 | `Child provides overriding implementation` | Subclass method redefinition with matching signature |
| 7 | Q3 | `Child implementation executes on child object` | Dynamic method dispatch at runtime |
| 8 | Q4 | `Static belongs to class` | Class-level scoping for static members |
| 9 | Q4 | `instance variable belongs to object` | Object-level scoping for non-static members |
| 10 | Q4 | `No direct instance-variable access from static method` | Static constraint (lack of implicit `this`) |
| 11 | Q4 | `Instance reference required for access` | Need for explicit object reference in static context |
| 12 | Q5 | `Handles runtime exceptions/errors` | Intercepting exceptional runtime events |
| 13 | Q5 | `Prevents abrupt termination or supports graceful recovery` | System resilience and crash prevention |

*System Triage Labels (Excluded from educational missing concepts)*:
* `None clearly identified`
* `requires human review`

---

## 4. Prediction Threshold
* **Decision Threshold**: `0.5`
* **Decision Rule**: Concept $k$ is marked active/present if $P_k \ge 0.5$.
* In missing concept derivation:
  $$\text{Missing Concepts} = \text{Target Question Concepts} \setminus \text{Predicted Active Concepts}$$

---

## 5. Available Dataset Information
The repository contains the following dataset files under `datasets/`:

1. **`oop_student_questionnaire_responses.csv`**:
   * **Rows**: 62 student responses (Students S001–S062).
   * **Columns**: `Timestamp`, `Email Address`, `Score`, and verbatim answers for Q1, Q2, Q3, Q4, and Q5.
   * **Nature**: Source academic survey collection.
2. **`oop_model_experimental_results.csv`**:
   * **Rows**: 50 student answer instances (across 10 students: S001, S004, S010, S014, S026, S035, S049, S055, S057, S058).
   * **Columns**: `student_id`, `question_id`, `student_answer`, `predicted_missing_concepts`, `provisional_reference_labels`.
   * **Overlap**: 100% of the answers in this file are identical subsets of `oop_student_questionnaire_responses.csv`.
3. **`sample_student_answers.csv`**:
   * **Rows**: 3 sample demonstration records.
4. **`independent_eval_template.csv` & `independent_oop_test_template.csv`**:
   * Blank templates prepared for independent data collection and human review.

---

## 6. Known Training Details
* **Annotation Mode**: The model dictionary explicitly declares `"label_status": "AI-generated provisional labels"`.
* **Seed Dataset**: Model training utilized survey responses drawn from `oop_student_questionnaire_responses.csv`.
* **Preprocessing**: Text inputs were lowercased and fed directly to `all-MiniLM-L6-v2` transformer embeddings prior to Logistic Regression fitting.
* **Optimization Convergence**: Number of solver iterations observed across estimators ranges from 8 to 11 iterations, confirming fast L-BFGS convergence on balanced linear embeddings.

---

## 7. Missing Training Information & Research Limitations
1. **Missing Standalone Training Script**:
   * The original training script (e.g., Jupyter notebook or `.py` file used to fit the model) is not present in the repository.
2. **Absence of Separate Held-Out Test Split**:
   * The experimental evaluation records (`oop_model_experimental_results.csv`) are an exact subset of the training survey questionnaire; an isolated hold-out test set was not partitioned at train time.
3. **Provisional Reference Labels**:
   * Ground truth annotations used during model fitting were AI-generated provisional labels rather than dual-blind human expert annotations. 28 of 50 evaluated answers in the experimental set contain only generic triage labels (`"None clearly identified; requires human review"`).
4. **Extreme Class Imbalance**:
   * Fine-grained concepts (such as `Child provides overriding implementation` with only 1 positive support in the experimental subset, and `Class as blueprint/template` with 2 supports) suffer from low positive sample counts, impacting macro-averaged generalization metrics.

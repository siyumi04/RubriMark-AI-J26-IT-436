# RubriMark AI Model Artifacts

This directory stores the trained Machine Learning / NLP model artifacts for:
**AI-Powered Personalized Feedback, Knowledge Gap Detection, and Learning Recommendations.**

## Required Model Files:
1. **Primary Model**: `feedback_model.joblib`
   - Trained Google Colab model for missing concepts / rubric feature extraction.
2. **Vectorizer / Preprocessor (Optional / If Separate)**: `vectorizer.joblib` or `tfidf.joblib`
   - Fitted TF-IDF or tokenizer vectorizer used during model training.

## Loading Policy:
- The backend loads the model once during FastAPI startup (`lifespan` event).
- If the model file is not yet present, the system transparently reports `AI inference is unavailable` without fabricating predictions.
- The model is **never retrained** inside this web application.
- All inference outputs adhere strictly to explainable and verifiable academic assessment standards.

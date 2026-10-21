import os
import joblib
from sentence_transformers import SentenceTransformer

model_path = "backend/ml_models/rubrimark_oop_model.joblib"
m = joblib.load(model_path)
print("Keys in model:", m.keys())
print("Label classes:", m.get("label_classes"))
print("Threshold:", m.get("threshold"))

st = SentenceTransformer(m["embedding_model"])

samples = [
    ("S001_Q1", "Class: A blueprint; Object: An instance of a class. Example: Car is a class, myCar is an object."),
    ("S010_Q1", "object is an instance of a class"),
    ("S010_Q4", "i cant remember"),
    ("S004_Q2", "The Car class inherits the variables and methods of the Vehicle class. It can also add its own features.")
]

for label, text in samples:
    emb = st.encode([text])
    print(f"\n--- {label}: '{text}' ---")
    active_predictions = []
    for c_name, clf in zip(m["label_classes"], m["classifiers"]):
        prob = float(clf.predict_proba(emb)[0][1])
        if prob >= m.get("threshold", 0.5):
            active_predictions.append((c_name, round(prob, 4)))
    print("Classes >= 0.5:", active_predictions)

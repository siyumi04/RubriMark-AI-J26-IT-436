# RubriMark AI – Independent Test Dataset Reference Guide

This document defines the exact question mapping and 13 educational concept labels used by the RubriMark AI model for populating [`datasets/independent_oop_test_template.csv`](file:///c:/Users/ASUS/RubriMark-AI-J26-IT-436/datasets/independent_oop_test_template.csv).

---

## 1. Questions & Aligned Educational Concepts (13 Total)

### **Q1: Difference between a class and an object in Java**
* **Prompt**: *"01. What is the difference between a class and an object in Java? Give a simple example."*
* **Target Educational Concepts**:
  1. `Class as blueprint/template`
  2. `Object as class instance`
  3. `Concrete class-object example`

---

### **Q2: Inheritance in Java (Car extends Vehicle)**
* **Prompt**: *"02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?"*
* **Target Educational Concepts**:
  4. `Inheritance of accessible fields`
  5. `Inheritance of accessible methods`

---

### **Q3: Method Overriding in Java**
* **Prompt**: *"03. What happens when a child class overrides a method inherited from its parent class?"*
* **Target Educational Concepts**:
  6. `Child provides overriding implementation`
  7. `Child implementation executes on child object`

---

### **Q4: Static Method & Instance Variable Access**
* **Prompt**: *"04. Can a static method directly access a non-static variable? Why or why not?"*
* **Target Educational Concepts**:
  8. `Static belongs to class`
  9. `instance variable belongs to object`
  10. `No direct instance-variable access from static method`
  11. `Instance reference required for access`

---

### **Q5: Exception Handling in Java**
* **Prompt**: *"05. Why is exception handling important in Java?"*
* **Target Educational Concepts**:
  12. `Handles runtime exceptions/errors`
  13. `Prevents abrupt termination or supports graceful recovery`

---

## 2. Review & Annotation Instructions

* **`test_id`**: Unique identifier for each independent test sample (e.g., `TEST-001`, `TEST-002`).
* **`question_id`**: Must be one of `Q1`, `Q2`, `Q3`, `Q4`, or `Q5`.
* **`student_answer`**: Exact verbatim student answer collected independently (not copied from questionnaire).
* **`human_verified_concepts`**: Semicolon-separated (` ; `) list of exact concept names from the 13 concepts above identified by the human reviewer. If no target concept is present, write `None`.
* **`reviewer`**: Name or ID of the human expert reviewer.
* **`review_status`**: Review workflow state (e.g., `Verified`, `Pending Review`, `Dual Reviewed`).

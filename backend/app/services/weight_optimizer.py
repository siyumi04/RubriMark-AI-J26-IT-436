from typing import List, Dict, Any, Tuple


class DynamicWeightOptimizer:
    """
    Rule-Based Dynamic Weight Optimization Engine (Research Component IT23376472)
    Developed and benchmarked on Java OOP subjective questions.
    
    Responsibilities:
    - Checks duplicate criteria.
    - Dynamically adjusts criterion weights based on Bloom's taxonomy & question/lecturer requirements.
    - Mathematically normalizes weights to exactly 100.0%.
    - Allocates marks according to the question's maximum marks without rounding divergence.
    - Validates weight and mark consistency.
    """

    COGNITIVE_PRIORITIES = {
        "Remember": {"Conceptual": 1.4, "Theory": 1.3, "Implementation": 0.8, "Analytical": 0.7},
        "Understand": {"Conceptual": 1.3, "Theory": 1.3, "Implementation": 0.9, "Analytical": 0.8},
        "Apply": {"Implementation": 1.4, "Syntax": 1.3, "Applied": 1.3, "Conceptual": 0.85, "Analytical": 0.85},
        "Analyze": {"Analytical": 1.4, "Comparative": 1.4, "Conceptual": 0.9, "Implementation": 0.9},
        "Evaluate": {"Analytical": 1.4, "Comparative": 1.3, "Conceptual": 0.9, "Applied": 0.85},
        "Create": {"Implementation": 1.4, "Applied": 1.3, "Conceptual": 0.85, "Analytical": 0.85},
    }

    @classmethod
    def check_and_deduplicate_criteria(cls, criteria: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Checks for duplicate criteria by normalized name.
        Deduplicates if found and returns warnings.
        """
        seen_names = set()
        unique_criteria = []
        warnings = []

        for crit in criteria:
            norm_name = crit.get("criterion_name", "").strip().lower()
            if not norm_name:
                continue
            if norm_name in seen_names:
                warnings.append(f"Duplicate criterion detected and merged: '{crit.get('criterion_name')}'.")
            else:
                seen_names.add(norm_name)
                unique_criteria.append(dict(crit))

        return unique_criteria, warnings

    @classmethod
    def calculate_criterion_multiplier(
        cls,
        criterion: Dict[str, Any],
        target_blooms_level: str = "Analyze",
        combined_context: str = ""
    ) -> float:
        """
        Calculates the combined cognitive + contextual multiplier for a criterion.
        """
        multipliers = cls.COGNITIVE_PRIORITIES.get(target_blooms_level, cls.COGNITIVE_PRIORITIES["Analyze"])
        dim = criterion.get("blooms_dimension", "Analytical")
        mult = multipliers.get(dim, 1.0)

        name_lower = (criterion.get("criterion_name") or "").lower()
        context_lower = combined_context.lower()

        # Factor 2: Question/guideline requirement emphasis
        if any(term in context_lower for term in ["code", "syntax", "implementation", "program", "class"]):
            if any(k in name_lower for k in ["syntax", "code", "implementation", "example", "structure"]):
                mult *= 1.25

        if any(term in context_lower for term in ["compare", "contrast", "difference", "versus", "vs", "trade-off"]):
            if any(k in name_lower for k in ["comparative", "contrast", "distinction", "trade-off"]):
                mult *= 1.30

        if any(term in context_lower for term in ["exception", "try-catch", "finally", "throw", "error"]):
            if any(k in name_lower for k in ["exception", "error", "defensive", "robustness"]):
                mult *= 1.25

        if any(term in context_lower for term in ["encapsulation", "data hiding", "getter", "setter", "access modifier", "private"]):
            if any(k in name_lower for k in ["encapsulation", "data hiding", "access control", "getter"]):
                mult *= 1.25

        return mult

    @classmethod
    def adjust_weights_dynamically(
        cls,
        criteria: List[Dict[str, Any]],
        target_blooms_level: str = "Analyze",
        question_text: str = "",
        learning_outcome: str = "",
        lecturer_guidelines: str = "",
        is_already_optimized: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Dynamically adjusts criterion weights based on:
        1. Cognitive demands of Bloom's Taxonomy tier.
        2. Explicit requirements in question text, learning outcome, and lecturer guidelines.

        Stable Base-Weight Strategy:
        - If 'base_weight' is present on criterion, uses it directly.
        - If 'proposed_marks' is present, uses it as the proportional base weight.
        - If criterion is marked 'is_optimized' or is_already_optimized is True, un-scales by current multiplier to recover stable base weight.
        - Otherwise, preserves meaningful lecturer priorities from 'weight_percentage' as initial base weight.
        - Ensures repeated optimization is strictly idempotent and does not compound multipliers.
        """
        if not criteria:
            return []

        adjusted_criteria = [dict(c) for c in criteria]
        combined_context = f"{question_text} {learning_outcome} {lecturer_guidelines}".lower()

        for crit in adjusted_criteria:
            mult = cls.calculate_criterion_multiplier(crit, target_blooms_level, combined_context)

            # Determine stable base weight
            if "base_weight" in crit and crit["base_weight"] is not None and float(crit["base_weight"]) > 0:
                base_w = float(crit["base_weight"])
                target_w = base_w * mult
            elif "proposed_marks" in crit and crit["proposed_marks"] is not None and float(crit["proposed_marks"]) > 0:
                base_w = float(crit["proposed_marks"])
                target_w = base_w * mult
            elif is_already_optimized or crit.get("is_optimized"):
                current_w = float(crit.get("weight_percentage", 25.0))
                base_w = current_w / max(mult, 0.001)
                target_w = current_w
            else:
                base_w = float(crit.get("weight_percentage", 25.0))
                target_w = base_w * mult

            crit["base_weight"] = round(base_w, 4)
            crit["weight_percentage"] = target_w
            crit["is_optimized"] = True
            crit["applied_multiplier"] = round(mult, 3)

        return adjusted_criteria

    @classmethod
    def normalize_weights(cls, criteria: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mathematically normalizes criteria weights to sum to exactly 100.00%.
        Reconciles rounding discrepancies on the highest-weighted criterion.
        """
        if not criteria:
            return []

        current_sum = sum(float(c.get("weight_percentage", 0.0)) for c in criteria)
        if current_sum <= 0:
            # Fallback to equal distribution
            share = round(100.0 / len(criteria), 2)
            normalized = []
            for idx, c in enumerate(criteria):
                c_copy = dict(c)
                c_copy["weight_percentage"] = share
                normalized.append(c_copy)
        else:
            normalized = []
            for c in criteria:
                c_copy = dict(c)
                raw_w = float(c_copy.get("weight_percentage", 0.0))
                norm_w = round((raw_w / current_sum) * 100.0, 2)
                c_copy["weight_percentage"] = norm_w
                normalized.append(c_copy)

        # Fix floating point precision so sum is strictly 100.00
        total_norm = round(sum(c["weight_percentage"] for c in normalized), 2)
        diff = round(100.0 - total_norm, 2)
        if diff != 0 and normalized:
            # Add difference to the criterion with highest weight
            highest_idx = max(range(len(normalized)), key=lambda i: normalized[i]["weight_percentage"])
            normalized[highest_idx]["weight_percentage"] = round(normalized[highest_idx]["weight_percentage"] + diff, 2)

        return normalized

    @classmethod
    def allocate_marks(cls, criteria: List[Dict[str, Any]], max_marks: float) -> List[Dict[str, Any]]:
        """
        Allocates marks according to the question's maximum marks.
        Ensures sum(criterion_marks) == max_marks exactly.
        """
        if not criteria or max_marks <= 0:
            return criteria

        allocated = []
        for c in criteria:
            c_copy = dict(c)
            w = float(c_copy.get("weight_percentage", 0.0))
            marks = round((w / 100.0) * max_marks, 2)
            c_copy["max_marks"] = marks
            allocated.append(c_copy)

        # Check total marks allocated and reconcile any cent/penny rounding difference
        total_allocated = round(sum(c["max_marks"] for c in allocated), 2)
        marks_diff = round(max_marks - total_allocated, 2)
        if marks_diff != 0 and allocated:
            highest_idx = max(range(len(allocated)), key=lambda i: allocated[i]["max_marks"])
            allocated[highest_idx]["max_marks"] = round(allocated[highest_idx]["max_marks"] + marks_diff, 2)

        return allocated

    @classmethod
    def optimize_and_allocate(
        cls,
        criteria: List[Dict[str, Any]],
        max_marks: float = 100.0,
        target_blooms_level: str = "Analyze",
        question_text: str = "",
        learning_outcome: str = "",
        lecturer_guidelines: str = "",
        is_already_optimized: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the full dynamic optimization, normalization, and mark allocation pipeline.
        """
        # Step 1: Check and deduplicate criteria
        unique_criteria, dup_warnings = cls.check_and_deduplicate_criteria(criteria)

        # Step 2: Dynamic weight adjustment based on cognitive tier and question demands
        adjusted = cls.adjust_weights_dynamically(
            criteria=unique_criteria,
            target_blooms_level=target_blooms_level,
            question_text=question_text,
            learning_outcome=learning_outcome,
            lecturer_guidelines=lecturer_guidelines,
            is_already_optimized=is_already_optimized
        )

        # Step 3: Normalize weights to exactly 100.0%
        normalized = cls.normalize_weights(adjusted)

        # Step 4: Allocate marks according to max_marks
        final_criteria = cls.allocate_marks(normalized, max_marks=max_marks)

        # Validation checks
        val_summary = cls.validate_weight_and_marks(final_criteria, max_marks)

        return {
            "criteria": final_criteria,
            "total_weight": 100.0,
            "total_marks": max_marks,
            "validation": val_summary,
            "duplicate_warnings": dup_warnings,
            "rationale": (
                f"Weights dynamically optimized for Bloom's '{target_blooms_level}' "
                f"and normalized to 100.0%. Marks allocated to total {max_marks} marks."
            ),
            "status": "optimized"
        }

    @classmethod
    def validate_weight_and_marks(cls, criteria: List[Dict[str, Any]], max_marks: float) -> Dict[str, Any]:
        """
        Validates weights, criteria uniqueness, and total marks.
        """
        errors = []
        if not criteria:
            errors.append("Criteria list is empty.")
            return {"is_valid": False, "errors": errors}

        total_weight = round(sum(float(c.get("weight_percentage", 0.0)) for c in criteria), 2)
        total_marks = round(sum(float(c.get("max_marks", 0.0)) for c in criteria), 2)

        weight_valid = abs(total_weight - 100.0) < 0.001
        marks_valid = abs(total_marks - max_marks) < 0.001

        if not weight_valid:
            errors.append(f"Total weight is {total_weight}%, expected 100.0%.")
        if not marks_valid:
            errors.append(f"Allocated marks sum to {total_marks}, expected {max_marks}.")

        names = [c.get("criterion_name", "").strip().lower() for c in criteria]
        if len(names) != len(set(names)):
            errors.append("Duplicate criteria names detected.")

        for c in criteria:
            if float(c.get("weight_percentage", 0.0)) <= 0:
                errors.append(f"Criterion '{c.get('criterion_name')}' has non-positive weight.")

        return {
            "is_valid": len(errors) == 0,
            "total_weight": total_weight,
            "total_marks": total_marks,
            "max_marks": max_marks,
            "errors": errors,
            "criterion_count": len(criteria)
        }

    # Backward compatibility wrapper for existing callers
    @classmethod
    def optimize_weights(
        cls,
        criteria: List[Dict[str, Any]],
        target_blooms_level: str = "Analyze"
    ) -> Dict[str, Any]:
        result = cls.optimize_and_allocate(
            criteria=criteria,
            max_marks=100.0,
            target_blooms_level=target_blooms_level
        )
        return {
            "criteria": result["criteria"],
            "total_weight": result["total_weight"],
            "rationale": result["rationale"],
            "status": result["status"]
        }

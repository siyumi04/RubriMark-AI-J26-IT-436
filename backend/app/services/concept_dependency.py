"""
IT23436244 Research Component:
Concept Dependency Analysis & Knowledge Gap Remediation Framework
Part of RubriMark AI: A Trustworthy Explainable AI Framework for Automated Short-Answer Assessment.
"""

from typing import List, Dict, Any, Set, Optional


# Directed Acyclic Graph (DAG) of OOP Concepts and Prerequisite Relationships
OOP_CONCEPT_DAG: Dict[str, Dict[str, Any]] = {
    "Class as blueprint/template": {
        "id": "class_blueprint",
        "module": "Foundational OOP",
        "question_id": "Q1",
        "prerequisites": [],
        "description": "Defines a class as an abstract blueprint, specification, or type definition that models attributes and behaviors without runtime memory allocation.",
        "difficulty": "Foundational"
    },
    "Object as class instance": {
        "id": "object_instance",
        "module": "Foundational OOP",
        "question_id": "Q1",
        "prerequisites": ["Class as blueprint/template"],
        "description": "Recognizes an object as a concrete entity instantiated from a class definition, possessing its own unique state in heap memory.",
        "difficulty": "Foundational"
    },
    "Concrete class-object example": {
        "id": "concrete_example",
        "module": "Foundational OOP",
        "question_id": "Q1",
        "prerequisites": ["Class as blueprint/template", "Object as class instance"],
        "description": "Demonstrates the class-object dichotomy via a concrete technical code example or domain analog (e.g., Car class vs. myCar object).",
        "difficulty": "Foundational"
    },
    "Inheritance of accessible fields": {
        "id": "inheritance_fields",
        "module": "Inheritance",
        "question_id": "Q2",
        "prerequisites": ["Class as blueprint/template", "Object as class instance"],
        "description": "Understands that a subclass acquires non-private fields (attributes) from its parent superclass according to access specifiers.",
        "difficulty": "Core"
    },
    "Inheritance of accessible methods": {
        "id": "inheritance_methods",
        "module": "Inheritance",
        "question_id": "Q2",
        "prerequisites": ["Class as blueprint/template", "Object as class instance"],
        "description": "Understands that a subclass inherits accessible behaviors/methods from its superclass, fostering code reuse and modularity.",
        "difficulty": "Core"
    },
    "Child provides overriding implementation": {
        "id": "method_overriding",
        "module": "Polymorphism",
        "question_id": "Q3",
        "prerequisites": ["Inheritance of accessible methods"],
        "description": "Defines method overriding where a subclass provides its own specific implementation matching the inherited superclass method signature.",
        "difficulty": "Core"
    },
    "Child implementation executes on child object": {
        "id": "dynamic_dispatch",
        "module": "Polymorphism",
        "question_id": "Q3",
        "prerequisites": ["Child provides overriding implementation"],
        "description": "Explains dynamic method dispatch: runtime invocation selects the overriding subclass implementation when triggered on a child object.",
        "difficulty": "Advanced"
    },
    "Static belongs to class": {
        "id": "static_class_scope",
        "module": "Memory & Scope",
        "question_id": "Q4",
        "prerequisites": ["Class as blueprint/template"],
        "description": "Understands that static members belong to the class level and exist loaded in class memory independently of object instantiations.",
        "difficulty": "Core"
    },
    "instance variable belongs to object": {
        "id": "instance_variable_scope",
        "module": "Memory & Scope",
        "question_id": "Q4",
        "prerequisites": ["Object as class instance"],
        "description": "Understands that non-static instance variables belong to specific object instances and maintain distinct state per object.",
        "difficulty": "Core"
    },
    "No direct instance-variable access from static method": {
        "id": "static_access_constraint",
        "module": "Memory & Scope",
        "question_id": "Q4",
        "prerequisites": ["Static belongs to class", "instance variable belongs to object"],
        "description": "Articulates why static methods lack an implicit 'this' reference and cannot directly read or write instance variables.",
        "difficulty": "Advanced"
    },
    "Instance reference required for access": {
        "id": "instance_reference_requirement",
        "module": "Memory & Scope",
        "question_id": "Q4",
        "prerequisites": ["No direct instance-variable access from static method"],
        "description": "Specifies that accessing instance members from a static context requires creating or receiving an explicit object reference.",
        "difficulty": "Advanced"
    },
    "Handles runtime exceptions/errors": {
        "id": "exception_handling",
        "module": "Exception Handling",
        "question_id": "Q5",
        "prerequisites": [],
        "description": "Defines exception handling mechanisms (try, catch, throw, finally) to intercept and process exceptional runtime events.",
        "difficulty": "Foundational"
    },
    "Prevents abrupt termination or supports graceful recovery": {
        "id": "graceful_recovery",
        "module": "Exception Handling",
        "question_id": "Q5",
        "prerequisites": ["Handles runtime exceptions/errors"],
        "description": "Recognizes the critical architectural role of exception handling in preventing sudden application crashes and maintaining normal flow.",
        "difficulty": "Core"
    }
}


class ConceptDependencyService:
    """
    IT23436244 Component:
    Executes Concept Dependency Analysis across detected knowledge gaps to isolate
    root causes, identify downstream learning risks, and build topologically
    ordered remediation paths.
    """

    def __init__(self):
        self.dag = OOP_CONCEPT_DAG
        self.component_name = "Concept Dependency Analysis & Knowledge Gap Remediation"

    def analyze_student_profile(
        self,
        missing_concepts: List[str],
        assessed_answers: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Performs in-depth dependency analysis on a student's detected missing concepts.
        """
        # Normalize and filter out meta-labels
        substantive_gaps: Set[str] = {
            c.strip() for c in missing_concepts
            if c.strip() in self.dag
        }

        all_concepts = list(self.dag.keys())
        total_concepts = len(all_concepts)
        mastered_concepts = [c for c in all_concepts if c not in substantive_gaps]
        mastery_rate = round((len(mastered_concepts) / total_concepts) * 100, 1)

        # 1. Identify Root Cause Knowledge Gaps
        # A gap is a root cause if:
        # (a) It has NO prerequisites among other gaps, BUT is a prerequisite to another gap the student has, OR
        # (b) Its prerequisites are mastered, meaning this gap is where the breakdown started.
        root_causes = []
        isolated_gaps = []

        for gap in substantive_gaps:
            prereqs = self.dag[gap]["prerequisites"]
            unmastered_prereqs = [p for p in prereqs if p in substantive_gaps]

            # Check if this gap is a prerequisite to other gaps
            dependents_with_gaps = [
                other for other in substantive_gaps
                if gap in self.dag[other]["prerequisites"]
            ]

            if unmastered_prereqs:
                # Student missed the prerequisite first! So this gap is a downstream symptom.
                pass
            elif dependents_with_gaps:
                # No unmastered prerequisites, but downstream concepts failed -> Primary Root Cause!
                root_causes.append({
                    "concept": gap,
                    "module": self.dag[gap]["module"],
                    "difficulty": self.dag[gap]["difficulty"],
                    "caused_downstream_gaps": dependents_with_gaps,
                    "description": self.dag[gap]["description"]
                })
            else:
                # An isolated concept gap
                isolated_gaps.append({
                    "concept": gap,
                    "module": self.dag[gap]["module"],
                    "difficulty": self.dag[gap]["difficulty"],
                    "description": self.dag[gap]["description"]
                })

        # 2. Downstream Risk Analysis
        # Concepts NOT YET FLAGGED as gaps, but whose prerequisites are unmastered
        at_risk_concepts = []
        for concept, meta in self.dag.items():
            if concept not in substantive_gaps:
                missing_prereqs = [p for p in meta["prerequisites"] if p in substantive_gaps]
                if missing_prereqs:
                    at_risk_concepts.append({
                        "concept": concept,
                        "module": meta["module"],
                        "blocked_by": missing_prereqs,
                        "difficulty": meta["difficulty"]
                    })

        # 3. Topologically Sorted Remediation Path
        # Order the substantive gaps so prerequisites are learned before dependents
        remediation_path = self._topological_sort_gaps(substantive_gaps)

        # 4. Generate Graph Visualization Data (Nodes & Edges)
        graph_nodes = []
        graph_edges = []

        for concept, meta in self.dag.items():
            is_gap = concept in substantive_gaps
            is_root = any(r["concept"] == concept for r in root_causes)
            is_at_risk = any(ar["concept"] == concept for ar in at_risk_concepts)

            status = "mastered"
            if is_root:
                status = "root_cause"
            elif is_gap:
                status = "missing"
            elif is_at_risk:
                status = "at_risk"

            graph_nodes.append({
                "id": meta["id"],
                "label": concept,
                "module": meta["module"],
                "question_id": meta["question_id"],
                "difficulty": meta["difficulty"],
                "status": status,
                "description": meta["description"]
            })

            for prereq in meta["prerequisites"]:
                if prereq in self.dag:
                    graph_edges.append({
                        "from": self.dag[prereq]["id"],
                        "to": meta["id"],
                        "prereq_name": prereq,
                        "target_name": concept
                    })

        # 5. Formulate Academic Summary
        if not substantive_gaps:
            summary = (
                "Comprehensive Concept Dependency Analysis confirms zero active foundational bottlenecks. "
                "The student displays robust conceptual alignment across all core OOP curriculum dimensions."
            )
        elif root_causes:
            root_names = ", ".join([f"'{r['concept']}'" for r in root_causes])
            summary = (
                f"Concept Dependency Analysis identified {len(root_causes)} primary root-cause bottleneck(s): {root_names}. "
                "Downstream misconceptions stem directly from incomplete grounding in these core prerequisites. "
                "Remediation must prioritize resolving these foundational gaps prior to tackling advanced topics."
            )
        else:
            summary = (
                f"Identified {len(substantive_gaps)} conceptual gap(s) without upstream prerequisite failures. "
                "These represent localized, isolated deficiencies that can be remediated directly."
            )

        return {
            "research_component": {
                "name": self.component_name,
                "scope": "Automated Concept Dependency & Prerequisite DAG Analysis"
            },
            "mastery_rate": mastery_rate,
            "total_curriculum_concepts": total_concepts,
            "mastered_concepts_count": len(mastered_concepts),
            "missing_concepts_count": len(substantive_gaps),
            "root_causes": root_causes,
            "isolated_gaps": isolated_gaps,
            "at_risk_concepts": at_risk_concepts,
            "remediation_learning_path": remediation_path,
            "academic_summary": summary,
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges
        }

    def _topological_sort_gaps(self, gaps: Set[str]) -> List[Dict[str, Any]]:
        """Sorts missing concepts so prerequisites appear first in the learning sequence."""
        ordered = []
        visited = set()

        def visit(concept: str):
            if concept in visited:
                return
            visited.add(concept)
            # Visit prerequisites first (guarantees topological prerequisite-first ordering)
            for p in self.dag.get(concept, {}).get("prerequisites", []):
                if p in gaps:
                    visit(p)
            ordered.append({
                "step": len(ordered) + 1,
                "concept": concept,
                "module": self.dag[concept]["module"],
                "difficulty": self.dag[concept]["difficulty"],
                "description": self.dag[concept]["description"]
            })

        for g in sorted(gaps):
            visit(g)

        return ordered


concept_dependency_service = ConceptDependencyService()

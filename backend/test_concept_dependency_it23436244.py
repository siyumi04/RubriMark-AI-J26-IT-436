"""
Test Suite for IT23436244 Research Component:
Concept Dependency Analysis & Root Knowledge Gap Detection.

Evaluates:
1. DAG Structure and Acyclicity (13 OOP educational concepts).
2. Prerequisite relationship integrity.
3. Root cause vs. downstream symptom identification.
4. Isolated gap handling.
5. Downstream risk assessment for unflagged concepts.
6. Topological ordering of the remediation learning pathway.
7. Handling of edge cases (0 gaps, all 13 gaps, non-DAG metadata filtering).
"""

import sys
from app.services.concept_dependency import concept_dependency_service, OOP_CONCEPT_DAG

def run_tests():
    print("=" * 75)
    print("IT23436244 COMPONENT EVALUATION: CONCEPT DEPENDENCY & ROOT GAP DETECTION")
    print("=" * 75)

    passed_tests = 0
    failed_tests = 0

    def record(name: str, passed: bool, details: str = ""):
        nonlocal passed_tests, failed_tests
        status = "[PASS]" if passed else "[FAIL]"
        if passed:
            passed_tests += 1
        else:
            failed_tests += 1
        print(f"{status} - {name}")
        if details:
            print(f"       Details: {details}")

    # TEST 1: Exact 13 concepts in DAG
    dag_concepts = set(OOP_CONCEPT_DAG.keys())
    t1_pass = len(dag_concepts) == 13
    record(
        "TEST 1: Exact 13 educational concept nodes present in DAG",
        t1_pass,
        f"Found {len(dag_concepts)} concepts in OOP_CONCEPT_DAG"
    )

    # TEST 2: Acyclicity Check (Cycle Detection via DFS)
    def has_cycle():
        visited = set()
        rec_stack = set()
        for node in OOP_CONCEPT_DAG:
            if node not in visited:
                if _cycle_util(node, visited, rec_stack):
                    return True
        return False

    def _cycle_util(curr, visited, rec_stack):
        visited.add(curr)
        rec_stack.add(curr)
        for prereq in OOP_CONCEPT_DAG[curr]["prerequisites"]:
            if prereq not in visited:
                if _cycle_util(prereq, visited, rec_stack):
                    return True
            elif prereq in rec_stack:
                return True
        rec_stack.remove(curr)
        return False

    is_dag = not has_cycle()
    record("TEST 2: Directed Acyclic Graph (DAG) is strictly acyclic (no circular dependencies)", is_dag)

    # TEST 3: Root Cause vs. Downstream Symptom (Single Chain)
    # Chain: Class as blueprint/template -> Object as class instance -> Concrete class-object example
    gaps_chain = ["Class as blueprint/template", "Object as class instance", "Concrete class-object example"]
    res_chain = concept_dependency_service.analyze_student_profile(gaps_chain)
    root_names = [r["concept"] for r in res_chain["root_causes"]]
    t3_pass = (root_names == ["Class as blueprint/template"])
    record(
        "TEST 3: Root Cause Isolation on Linear Prerequisite Chain",
        t3_pass,
        f"Expected root: ['Class as blueprint/template']. Got: {root_names}"
    )

    # TEST 4: Isolated Knowledge Gap
    # Exception handling Q5 has no prerequisites and is not prereq to Q1-Q4
    gaps_iso = ["Handles runtime exceptions/errors"]
    res_iso = concept_dependency_service.analyze_student_profile(gaps_iso)
    iso_names = [r["concept"] for r in res_iso["isolated_gaps"]]
    t4_pass = (len(res_iso["root_causes"]) == 0 and iso_names == ["Handles runtime exceptions/errors"])
    record(
        "TEST 4: Isolated Knowledge Gap Identification (No downstream failure)",
        t4_pass,
        f"Root causes: {len(res_iso['root_causes'])}, Isolated gaps: {iso_names}"
    )

    # TEST 5: Downstream Learning Risk Detection
    # If student misses 'Inheritance of accessible methods', then 'Child provides overriding implementation' is at risk
    gaps_risk = ["Inheritance of accessible methods"]
    res_risk = concept_dependency_service.analyze_student_profile(gaps_risk)
    at_risk_names = [ar["concept"] for ar in res_risk["at_risk_concepts"]]
    t5_pass = ("Child provides overriding implementation" in at_risk_names)
    record(
        "TEST 5: Downstream Risk Detection for Unflagged Dependent Concepts",
        t5_pass,
        f"Concepts flagged at risk: {at_risk_names}"
    )

    # TEST 6: Multi-Prerequisite Convergence & Topological Remediation Path
    # 'No direct instance-variable access from static method' requires:
    # 1. 'Static belongs to class'
    # 2. 'instance variable belongs to object'
    # Plus its downstream 'Instance reference required for access'
    gaps_static = [
        "Instance reference required for access",
        "No direct instance-variable access from static method",
        "Static belongs to class",
        "instance variable belongs to object"
    ]
    res_static = concept_dependency_service.analyze_student_profile(gaps_static)
    path_order = [p["concept"] for p in res_static["remediation_learning_path"]]
    
    # Topological validation: every concept must appear AFTER its prerequisites
    topo_valid = True
    seen_in_path = set()
    for concept in path_order:
        prereqs_in_gaps = [p for p in OOP_CONCEPT_DAG[concept]["prerequisites"] if p in gaps_static]
        for p in prereqs_in_gaps:
            if p not in seen_in_path:
                topo_valid = False
                break
        seen_in_path.add(concept)

    record(
        "TEST 6: Topological Sorting of Remediation Learning Pathway (Multi-Prerequisite)",
        topo_valid and len(path_order) == 4,
        f"Remediation pathway: {path_order}"
    )

    # TEST 7: Metadata Filtering
    # System meta-labels ('None clearly identified', 'requires human review') must be filtered
    gaps_meta = [
        "None clearly identified",
        "requires human review",
        "Class as blueprint/template"
    ]
    res_meta = concept_dependency_service.analyze_student_profile(gaps_meta)
    t7_pass = (res_meta["missing_concepts_count"] == 1 and res_meta["mastery_rate"] == 92.3)
    record(
        "TEST 7: Triage Metadata & Non-DAG Concept Filtering",
        t7_pass,
        f"Missing count: {res_meta['missing_concepts_count']}, Mastery: {res_meta['mastery_rate']}%"
    )

    # TEST 8: Full Curriculum Mastery (0 Gaps)
    res_zero = concept_dependency_service.analyze_student_profile([])
    t8_pass = (
        res_zero["mastery_rate"] == 100.0 and
        len(res_zero["root_causes"]) == 0 and
        len(res_zero["remediation_learning_path"]) == 0 and
        res_zero["mastered_concepts_count"] == 13
    )
    record(
        "TEST 8: Edge Case - 100% Concept Mastery (0 Gaps)",
        t8_pass,
        f"Mastery rate: {res_zero['mastery_rate']}%, Root causes: {len(res_zero['root_causes'])}"
    )

    # TEST 9: Comprehensive Failure (All 13 Gaps)
    all_13 = list(OOP_CONCEPT_DAG.keys())
    res_all = concept_dependency_service.analyze_student_profile(all_13)
    path_all = [p["concept"] for p in res_all["remediation_learning_path"]]
    
    topo_all_valid = True
    seen_all = set()
    for concept in path_all:
        for p in OOP_CONCEPT_DAG[concept]["prerequisites"]:
            if p not in seen_all:
                topo_all_valid = False
                break
        seen_all.add(concept)

    t9_pass = (
        res_all["mastery_rate"] == 0.0 and
        topo_all_valid and
        len(path_all) == 13
    )
    record(
        "TEST 9: Edge Case - All 13 Concepts Missing (Complete DAG Traversal)",
        t9_pass,
        f"Mastery: {res_all['mastery_rate']}%, All 13 topologically ordered: {topo_all_valid}"
    )

    # TEST 10: Transitive Prerequisite Chains with Mastered Intermediate Nodes
    # Chain A: 'Class as blueprint/template' -> 'Inheritance of accessible methods' -> 'Child provides overriding implementation' -> 'Child implementation executes on child object'
    # Student misses step 1 and step 4, but mastered steps 2 and 3.
    transitive_gaps = {
        "Child implementation executes on child object",
        "Class as blueprint/template"
    }
    res_trans = concept_dependency_service.analyze_student_profile(list(transitive_gaps))
    path_trans = [p["concept"] for p in res_trans["remediation_learning_path"]]
    t10_pass = (
        len(path_trans) == 2 and
        path_trans[0] == "Class as blueprint/template" and
        path_trans[1] == "Child implementation executes on child object"
    )
    record(
        "TEST 10: Regression - Transitive Prerequisite Chain with Mastered Intermediates",
        t10_pass,
        f"Remediation order: {path_trans}"
    )

    print("\n" + "=" * 75)
    print(f"SUMMARY: {passed_tests} PASSED, {failed_tests} FAILED out of {passed_tests + failed_tests} tests.")
    print("=" * 75)
    return failed_tests == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

import json
import logging
import os
import re
from typing import List, Dict, Any, Optional
import httpx

from app.services.weight_optimizer import DynamicWeightOptimizer

try:
    from app.core.config import settings
except ImportError:
    settings = None

logger = logging.getLogger(__name__)


class AIService:
    """
    Research Component Engine for IT23376472:
    Adaptive AI-Based Rubric Generation and Criterion-Based Scoring System for Subjective Assessments.

    NOTE: This is currently a rule-based baseline prototype (developed and tested in Google Colab
    using Java OOP subjective assessment questions), NOT a trained deep learning / LLM model.
    It systematically selects question-specific marking criteria, assigns initial weights,
    dynamically adjusts weights based on question demands and lecturer guidelines, normalizes
    weights to 100.0%, allocates marks according to max_marks, and performs automated validation.
    """

    BLOOM_KEYWORDS = {
        "Remember": ["define", "list", "recall", "name", "state", "identify"],
        "Understand": ["explain", "describe", "summarize", "interpret", "clarify", "discuss"],
        "Apply": ["apply", "demonstrate", "calculate", "implement", "solve", "execute", "use", "write", "provide code"],
        "Analyze": ["analyze", "compare", "contrast", "differentiate", "distinguish", "trade-off", "deconstruct"],
        "Evaluate": ["evaluate", "critique", "justify", "defend", "assess", "rate", "validate"],
        "Create": ["design", "develop", "construct", "formulate", "synthesize", "architect", "propose"],
    }

    # ----------------------------------------------------------------------------------
    # Rule-Based Java OOP Domain Knowledge Bases (Colab Prototype Baseline)
    # ----------------------------------------------------------------------------------
    OOP_CRITERIA_CATALOG = {
        "encapsulation": [
            {
                "criterion_name": "Encapsulation Concepts & Data Hiding",
                "description": "Understanding of data protection, access modifier scopes (private vs public), and rationale for getter/setter methods.",
                "weight_percentage": 25.0,
                "blooms_dimension": "Conceptual",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Accurately defines encapsulation, data hiding, and explain why private attributes with public accessors preserve object state integrity."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Good explanation of encapsulation with minor omissions regarding access modifier implications."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Basic definition provided but confuses data hiding with general abstraction."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Vague or incorrect understanding of encapsulation principles."}
                ]
            },
            {
                "criterion_name": "Class Implementation & Access Modifiers",
                "description": "Declaration of private instance variables and appropriate public getter and setter methods.",
                "weight_percentage": 35.0,
                "blooms_dimension": "Implementation",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Correctly declares private variables with properly formatted public accessor and mutator methods following Java bean conventions."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Working Java class with private variables and getters/setters, minor syntactic imperfection."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Variables declared public or mutators missing proper parameter assignments."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Code syntax invalid or access modifiers entirely missing."}
                ]
            },
            {
                "criterion_name": "Mutator Validation & Defensive Logic",
                "description": "Implementation of validation checks inside setter methods to prevent invalid state.",
                "weight_percentage": 25.0,
                "blooms_dimension": "Applied",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Includes meaningful validation constraints (e.g. range/null checks) within setter methods."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Basic validation present in at least one setter method."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Validation mentioned theoretically but omitted from the code implementation."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "No validation logic present; values assigned unconditionally without checks."}
                ]
            },
            {
                "criterion_name": "Code Syntax & Java Conventions",
                "description": "Syntactic correctness, naming conventions, and proper encapsulation structuring.",
                "weight_percentage": 15.0,
                "blooms_dimension": "Syntax",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Flawless Java syntax, camelCase naming, comments, and standard class design."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Clean code with minor naming or indentation inconsistencies."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Syntactic issues or unidiomatic Java conventions."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Severely malformed code that does not follow Java language rules."}
                ]
            }
        ],
        "inheritance": [
            {
                "criterion_name": "Inheritance Principles & Hierarchy Design",
                "description": "Comprehension of 'is-a' relationships, code reusability, and superclass/subclass extension via the 'extends' keyword.",
                "weight_percentage": 25.0,
                "blooms_dimension": "Conceptual",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Comprehensive explanation of inheritance hierarchy, state sharing, and reusability benefits."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Solid understanding of superclass-subclass relationship with minor gaps in generalization/specialization."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Basic definition but confuses inheritance with composition ('has-a')."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Inaccurate or missing explanation of inheritance."}
                ]
            },
            {
                "criterion_name": "Constructor Chaining & Super Keyword Usage",
                "description": "Correct utilization of super() for invoking superclass constructors and super.method() for accessing overridden members.",
                "weight_percentage": 30.0,
                "blooms_dimension": "Implementation",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Explicit demonstration of super() as first statement in subclass constructor and correct member resolution."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "super keyword used correctly in constructor with minor formatting slip."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "super keyword mentioned but misapplied or placed incorrectly in constructor."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "super keyword omitted or misunderstood."}
                ]
            },
            {
                "criterion_name": "Method Overriding & Polymorphic Behavior",
                "description": "Proper implementation of method overriding with matching signatures and @Override annotation.",
                "weight_percentage": 30.0,
                "blooms_dimension": "Analytical",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Flawless method overriding in subclass with identical signature, @Override annotation, and distinct behavior."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Method overridden correctly; missing @Override annotation or minor return type nuance."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Confuses method overriding with method overloading (changes parameter list)."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "No overriding demonstrated or illegal signature changes."}
                ]
            },
            {
                "criterion_name": "Code Structure & Syntactic Correctness",
                "description": "Proper class hierarchy definition, compilation viability, and naming conventions.",
                "weight_percentage": 15.0,
                "blooms_dimension": "Syntax",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Compilable, elegant Java code demonstrating clear superclass and subclass structure."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Well-structured code with minor syntax blemishes."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Syntactic errors that hinder direct compilation."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Incomplete or incoherent code blocks."}
                ]
            }
        ],
        "polymorphism": [
            {
                "criterion_name": "Polymorphism Taxonomy & Concepts",
                "description": "Clear conceptual distinction between compile-time (static/overloading) and runtime (dynamic/overriding) polymorphism.",
                "weight_percentage": 25.0,
                "blooms_dimension": "Conceptual",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Thoroughly articulates static vs dynamic binding, method signatures, and dispatch timing."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Clear differentiation with minor omissions regarding compiler binding mechanics."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Mentions both forms but exhibits confusion on when binding occurs."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Unable to distinguish overloading from overriding."}
                ]
            },
            {
                "criterion_name": "Dynamic Method Dispatch Mechanics",
                "description": "Explanation and demonstration of upcasting and runtime method resolution via superclass references.",
                "weight_percentage": 35.0,
                "blooms_dimension": "Analytical",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Clearly explains how JVM resolves method calls at runtime based on the actual object instance rather than reference type."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Demonstrates upcasting (Parent p = new Child()) with sound explanation of dynamic dispatch."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Shows upcasting code snippet but fails to explain the underlying dispatch mechanism."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Fails to explain dynamic method dispatch."}
                ]
            },
            {
                "criterion_name": "Comparative Demonstration & Code Examples",
                "description": "Concrete Java code illustrating both method overloading and method overriding in action.",
                "weight_percentage": 25.0,
                "blooms_dimension": "Implementation",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Includes fully functional code examples demonstrating both overloading and overriding with test invocation."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Code examples for both types present with minor execution or syntax minor issue."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Demonstrates only one type of polymorphism in code."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "No code examples or completely broken snippets."}
                ]
            },
            {
                "criterion_name": "Technical Precision & Terminology",
                "description": "Accurate technical vocabulary including early binding, late binding, vtable, and signature rules.",
                "weight_percentage": 15.0,
                "blooms_dimension": "Syntax",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Flawless technical vocabulary, concise explanations, and structured comparative table/points."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Accurate vocabulary with minor informal phrasing."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Imprecise terminology used interchangeably."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Incorrect terminology throughout the response."}
                ]
            }
        ],
        "abstraction": [
            {
                "criterion_name": "Abstraction Principles & Design Contracts",
                "description": "Understanding of abstract specifications, hiding implementation details, and defining contracts for subclasses/implementers.",
                "weight_percentage": 25.0,
                "blooms_dimension": "Conceptual",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Articulates abstraction depth, partial vs complete contracts, and interface design principles."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Solid understanding of abstraction with minor gaps in contract enforcement."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Superficial understanding; confuses abstraction with simple method hiding."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Fails to define abstraction accurately."}
                ]
            },
            {
                "criterion_name": "Comparative Analysis: Abstract Classes vs Interfaces",
                "description": "Rigorous comparison covering multiple inheritance, state (instance variables vs constants), constructors, and Java 8+ default methods.",
                "weight_percentage": 35.0,
                "blooms_dimension": "Comparative",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Exhaustive side-by-side contrast covering state, constructors, multiple inheritance, and modern default/static methods."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Strong comparison covering at least 3 major differences with valid reasoning."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Lists 1 or 2 basic differences without deeper technical context."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Inaccurate or one-sided comparison."}
                ]
            },
            {
                "criterion_name": "Design Decision & Scenario Selection",
                "description": "Clear rationale on when to select an abstract class versus an interface based on architectural requirements.",
                "weight_percentage": 25.0,
                "blooms_dimension": "Analytical",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Provides realistic design scenarios clearly justifying when to use interfaces (unrelated classes, multiple contracts) vs abstract classes (code sharing, non-static state)."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Presents valid use cases for both constructs with sound justification."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Vague scenario description without architectural rationale."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "No scenarios provided or incorrect guidance."}
                ]
            },
            {
                "criterion_name": "Syntactic Correctness & Implementation",
                "description": "Correct usage of abstract, interface, implements, and extends keywords in Java snippets.",
                "weight_percentage": 15.0,
                "blooms_dimension": "Syntax",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Flawless code snippets exhibiting correct keywords, method declarations, and implementation classes."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Working code with minor syntax deviations."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Attempted code with syntax errors in implements/extends or abstract method headers."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Broken or non-compilable code representation."}
                ]
            }
        ],
        "exception_handling": [
            {
                "criterion_name": "Exception Hierarchy & Categorization",
                "description": "Understanding of the Throwable hierarchy, differentiating Checked exceptions (compile-time) and Unchecked exceptions (runtime).",
                "weight_percentage": 25.0,
                "blooms_dimension": "Conceptual",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Thoroughly diagrams Throwable -> Exception/Error and contrasts Checked vs RuntimeException handling requirements."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Accurately distinguishes checked vs unchecked exceptions with representative examples."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Mentions checked and unchecked exceptions but mixes up compiler enforcement rules."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Inaccurate or missing hierarchy explanation."}
                ]
            },
            {
                "criterion_name": "Robust Handling with try-catch-finally",
                "description": "Correct implementation of try-catch-finally blocks, throw vs throws, and deterministic resource release.",
                "weight_percentage": 30.0,
                "blooms_dimension": "Implementation",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Demonstrates robust try-catch-finally logic, explaining that finally always executes for cleanup, and distinguishes throw from throws."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Correct try-catch block with finally cleanup; minor terminology omission."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Basic try-catch shown but finally omitted or throw/throws confused."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Malformed error handling structure."}
                ]
            },
            {
                "criterion_name": "Custom Exception Design & Defensive Programming",
                "description": "Declaration of domain-specific custom exception classes extending Exception or RuntimeException, with constructor chaining.",
                "weight_percentage": 30.0,
                "blooms_dimension": "Applied",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Defines custom exception class with super(message) constructor chaining and demonstrates throwing and catching it."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Custom exception defined and used correctly with minor constructor limitation."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Custom exception class declared but not thrown or constructor chained."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Custom exception omitted or severely incorrect."}
                ]
            },
            {
                "criterion_name": "Code Robustness & Best Practices",
                "description": "Avoiding empty catch blocks, providing informative diagnostic error messages, and adhering to Java conventions.",
                "weight_percentage": 15.0,
                "blooms_dimension": "Syntax",
                "performance_levels": [
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Exemplary defensive coding practices, informative messages, no swallowed exceptions."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Good coding practices with minor informative message improvements possible."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Catch block empty or generic without helpful diagnostic trace."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Poor practices that suppress errors without handling."}
                ]
            }
        ]
    }

    @classmethod
    def detect_question_domain(cls, text: str) -> str:
        """
        Rule-based classifier to identify the core Java OOP topic of the assessment.
        Scores matching keyword occurrences across domain dictionaries to select the dominant topic.
        """
        lower = text.lower()
        domain_keywords = {
            "encapsulation": ["encapsulat", "data hiding", "getter", "setter", "private variable", "private field", "access modifier", "mutator", "accessor"],
            "inheritance": ["inheritance", "subclass", "superclass", "reusability", "extends", "super keyword", "constructor chaining", "super("],
            "polymorphism": ["polymorph", "overload", "dynamic method dispatch", "dynamic dispatch", "late binding", "static binding", "runtime polymorphism", "compile-time polymorphism"],
            "abstraction": ["abstract class", "interface", "pure abstraction", "contract", "default method", "abstract method"],
            "exception_handling": ["exception", "try-catch", "throw", "throws", "checked exception", "unchecked exception", "finally block", "custom exception"]
        }

        domain_scores = {}
        for domain, kws in domain_keywords.items():
            score = sum(1 for kw in kws if kw in lower)
            domain_scores[domain] = score

        best_domain = max(domain_scores, key=domain_scores.get)
        if domain_scores[best_domain] > 0:
            return best_domain
        return "general"

    @classmethod
    def analyze_question(
        cls,
        question_text: str,
        reference_answer: str = None,
        learning_outcome: str = None,
        lecturer_guidelines: str = None
    ) -> Dict[str, Any]:
        """
        Feature 2: AI Question Analysis (Rule-Based Baseline).
        Analyzes cognitive depth, Bloom's level, key concepts, and structure of a question.
        """
        text_lower = f"{question_text} {learning_outcome or ''} {lecturer_guidelines or ''}".lower()
        detected_level = "Analyze"
        highest_hits = 0

        for level, keywords in cls.BLOOM_KEYWORDS.items():
            hits = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
            if hits > highest_hits:
                highest_hits = hits
                detected_level = level

        # Determine cognitive complexity
        word_count = len(question_text.split())
        if word_count > 35 or detected_level in ["Evaluate", "Create"]:
            complexity = "High"
        elif word_count > 15 or detected_level in ["Apply", "Analyze"]:
            complexity = "Medium"
        else:
            complexity = "Low"

        # Topic detection
        domain = cls.detect_question_domain(text_lower)

        # Concept extraction heuristics
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b|\b[a-zA-Z]{5,}\b', question_text)
        stopwords = {"explain", "between", "versus", "terms", "question", "assessment", "student", "should", "provide", "discuss"}
        concepts = list(dict.fromkeys([w.title() for w in words if w.lower() not in stopwords]))[:6]

        return {
            "blooms_level": detected_level,
            "cognitive_complexity": complexity,
            "detected_domain": domain,
            "extracted_concepts": concepts if concepts else ["Core Principles", "Implementation"],
            "rationale": f"Rule-based detection identified cognitive tier '{detected_level}' ({complexity} complexity) within the '{domain}' domain.",
            "recommended_criteria": [
                {"name": "Domain Concepts & Theory", "weight": 25.0},
                {"name": "Technical Implementation & Syntax", "weight": 35.0},
                {"name": "Analytical Depth & Trade-offs", "weight": 25.0},
                {"name": "Code Structure & Clarity", "weight": 15.0},
            ]
        }

    @staticmethod
    def _synthesize_performance_levels(criterion_name: str, description: str) -> List[Dict[str, Any]]:
        """
        Synthesizes 4-tier graduated performance descriptors (Exemplary, Proficient, Developing, Unsatisfactory)
        for an AI-generated criterion to satisfy academic rubric validation requirements.
        """
        c_name = criterion_name.strip()
        c_desc = description.strip()
        return [
            {
                "level": "Exemplary",
                "score_percentage": 100.0,
                "description": f"Exemplary demonstration of {c_name}: fully and accurately satisfies all aspects. {c_desc}"
            },
            {
                "level": "Proficient",
                "score_percentage": 80.0,
                "description": f"Proficient understanding of {c_name}: addresses the core requirement with minor omissions or slight lack of precision."
            },
            {
                "level": "Developing",
                "score_percentage": 50.0,
                "description": f"Developing grasp of {c_name}: partially addresses the criterion with noticeable gaps or conceptual ambiguities."
            },
            {
                "level": "Unsatisfactory",
                "score_percentage": 20.0,
                "description": f"Unsatisfactory: incorrect, incomplete, or fails to address {c_name}."
            }
        ]

    @classmethod
    def generate_rule_based_rubric(
        cls,
        question_text: str,
        blooms_level: str = "Analyze",
        reference_answer: Optional[str] = None,
        learning_outcome: Optional[str] = None,
        lecturer_guidelines: Optional[str] = None,
        max_marks: float = 100.0,
        generation_mode: str = "rule_based",
        fallback_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Baseline Rule-Based Rubric Generator.
        Used as deterministic baseline and as a resilient fallback when Ollama is offline or times out.
        """
        combined = f"{question_text} {learning_outcome or ''} {lecturer_guidelines or ''}"
        domain = cls.detect_question_domain(combined)

        if domain in cls.OOP_CRITERIA_CATALOG:
            raw_criteria = [dict(c) for c in cls.OOP_CRITERIA_CATALOG[domain]]
        else:
            # Fallback for general software architecture / engineering questions
            raw_criteria = [
                {
                    "criterion_name": "Domain Knowledge & Theoretical Rigor",
                    "description": "Comprehensiveness and fidelity of theoretical concepts relevant to the assessment task.",
                    "weight_percentage": 25.0,
                    "blooms_dimension": "Conceptual",
                    "performance_levels": [
                        {"level": "Exemplary", "score_percentage": 100.0, "description": "Demonstrates thorough, flawless grasp of core principles with exhaustive context."},
                        {"level": "Proficient", "score_percentage": 80.0, "description": "Solid understanding with minor omissions in non-critical nuances."},
                        {"level": "Developing", "score_percentage": 50.0, "description": "Partial grasp with noticeable conceptual ambiguities or inaccuracies."},
                        {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Significant gaps, misconceptions, or failure to address fundamental theory."}
                    ]
                },
                {
                    "criterion_name": "Comparative Analysis & Trade-off Evaluation",
                    "description": f"Depth of multi-dimensional evaluation, examining benefits, pitfalls, and constraints at the {blooms_level} tier.",
                    "weight_percentage": 35.0,
                    "blooms_dimension": "Analytical",
                    "performance_levels": [
                        {"level": "Exemplary", "score_percentage": 100.0, "description": "In-depth, balanced evaluation of all major trade-offs with sophisticated synthesis."},
                        {"level": "Proficient", "score_percentage": 80.0, "description": "Competent comparison covering main trade-offs with logical arguments."},
                        {"level": "Developing", "score_percentage": 50.0, "description": "Superficial comparison; lists items without substantive trade-off reasoning."},
                        {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Lacks comparative evaluation or demonstrates one-sided bias."}
                    ]
                },
                {
                    "criterion_name": "Practical Application & Evidence",
                    "description": "Use of realistic scenarios, concrete examples, or technical metrics to validate claims.",
                    "weight_percentage": 25.0,
                    "blooms_dimension": "Applied",
                    "performance_levels": [
                        {"level": "Exemplary", "score_percentage": 100.0, "description": "Provides highly relevant, technically precise real-world examples and metrics."},
                        {"level": "Proficient", "score_percentage": 80.0, "description": "Includes suitable examples that substantiate primary assertions."},
                        {"level": "Developing", "score_percentage": 50.0, "description": "Examples are abstract, generic, or weakly connected to claims."},
                        {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "No tangible examples or evidence provided."}
                    ]
                },
                {
                    "criterion_name": "Academic Coherence & Clarity",
                    "description": "Logical flow, terminology precision, structured presentation, and academic tone.",
                    "weight_percentage": 15.0,
                    "blooms_dimension": "Syntax",
                    "performance_levels": [
                        {"level": "Exemplary", "score_percentage": 100.0, "description": "Exceptionally clear, cohesive structure with precise technical terminology."},
                        {"level": "Proficient", "score_percentage": 80.0, "description": "Well-structured response with clear progression and proper terminology."},
                        {"level": "Developing", "score_percentage": 50.0, "description": "Disorganized structure requiring reader interpretation; informal tone."},
                        {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Incoherent presentation, high grammatical friction, and incorrect terminology."}
                    ]
                }
            ]

        # Apply Dynamic Weight Optimization & Mark Allocation
        optimization_result = DynamicWeightOptimizer.optimize_and_allocate(
            criteria=raw_criteria,
            max_marks=max_marks,
            target_blooms_level=blooms_level,
            question_text=question_text,
            learning_outcome=learning_outcome or "",
            lecturer_guidelines=lecturer_guidelines or ""
        )

        final_criteria = optimization_result["criteria"]
        validation = cls.validate_rubric(final_criteria, max_marks=max_marks)

        rationale = f"Rule-based baseline rubric generated for domain '{domain}' with Bloom's tier '{blooms_level}'."
        if fallback_reason:
            rationale += f" (Engaged as fallback: {fallback_reason})"

        return {
            "criteria": final_criteria,
            "generation_mode": generation_mode,
            "rag_context_used": None,
            "rag_sources": [],
            "generation_rationale": rationale,
            "validation": validation,
        }

    @classmethod
    def generate_rubric_with_rag(
        cls,
        question_text: str,
        blooms_level: str = "Analyze",
        reference_answer: Optional[str] = None,
        learning_outcome: Optional[str] = None,
        lecturer_guidelines: Optional[str] = None,
        max_marks: float = 100.0,
        use_rag: bool = True,
        force_fallback: bool = False,
    ) -> Dict[str, Any]:
        """
        Phase 2: Ollama + RAG-Based Adaptive Rubric Generation.

        Workflow:
        1. Retrieves relevant lecturer rubric examples from RAG knowledge base.
           Clearly marks all Pending rubrics as [UNVERIFIED DRAFT REFERENCE].
        2. Constructs prompt injecting question, model answer, Bloom's level,
           learning outcome, requested total marks, and RAG context.
        3. Calls local Ollama llama3.2:1b model with JSON schema enforcement.
        4. Validates parsed JSON; rejects invalid or off-topic criteria.
        5. Reconciles marks and applies Dynamic Weight Optimization so criteria
           weights sum to 100.0% and allocated marks equal max_marks exactly.
        6. Runs automated rubric validation.
        7. If Ollama fails, times out, or returns invalid output, falls back
           gracefully to the rule-based generator, recording 'rule_based_fallback'.
        """
        # Step 0: Check force fallback
        enabled = True
        if settings is not None and hasattr(settings, "ENABLE_RAG_RUBRIC_GENERATION"):
            enabled = bool(settings.ENABLE_RAG_RUBRIC_GENERATION)

        if force_fallback or not enabled:
            logger.info("RAG/Ollama generation bypassed (force_fallback=%s, enabled=%s). Using rule-based generator.", force_fallback, enabled)
            return cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                generation_mode="rule_based" if not force_fallback else "rule_based_fallback",
                fallback_reason="Explicit fallback requested" if force_fallback else "RAG generation disabled",
            )

        # Step 1: Retrieve RAG Knowledge Context
        rag_context_text = ""
        rag_sources = []
        rag_context_summary = None

        if use_rag:
            try:
                from app.services.rag_retrieval_service import get_rag_service
                rag_service = get_rag_service(auto_init=True)
                rag_res = rag_service.retrieve(query=question_text, top_k=2)

                results = rag_res.get("results", [])
                for r in results:
                    qid = r.get("question_id", r.get("doc_id", "Q?"))
                    topic = r.get("rag_topic", "")
                    approval = r.get("lecturer_approval", "Pending")
                    trust = r.get("rag_trust_level", "DRAFT_REFERENCE_ONLY")
                    rag_sources.append(f"{qid} ({topic}) - Approval: {approval} [{trust}]")

                if results:
                    rag_context_summary = f"Retrieved {len(results)} references: " + "; ".join(rag_sources)
                    # Benchmark-optimized: Condense RAG context to style/format examples to prevent context bloat and off-topic copying
                    sample_crit = []
                    for r in results:
                        r_topic = r.get("rag_topic", "General")
                        r_cr = r.get("criteria", [])
                        cr_names = [c.get("criterion") or c.get("criterion_name") for c in r_cr[:3] if isinstance(c, dict)]
                        clean_cr_names = [n for n in cr_names if n]
                        if clean_cr_names:
                            sample_crit.append(f"- Reference Style ({r_topic}): {', '.join(clean_cr_names)}")
                    if sample_crit:
                        rag_context_text = (
                            "STYLE & STRUCTURAL REFERENCE ONLY (from Knowledge Base - DO NOT copy unrelated topics):\n"
                            + "\n".join(sample_crit)
                        )
            except Exception as e:
                logger.warning("RAG retrieval failed during rubric generation: %s", e)

        # Step 2: Extract Target Concepts & Formulate Concise Ollama Prompt
        concepts = []
        try:
            analysis = cls.analyze_question(
                question_text=question_text,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
            )
            concepts = analysis.get("extracted_concepts", [])
        except Exception as e:
            logger.debug("Concept pre-extraction notice: %s", e)

        concepts_str = f"Target Question Concepts: {', '.join(concepts[:6])}\n" if concepts else ""

        prompt = (
            "You are an academic assessment rubric generator.\n"
            "Generate a question-specific marking rubric specifically tailored to this assessment question.\n\n"
            f"Assessment Question: {question_text}\n"
            f"Model Answer: {reference_answer or 'N/A'}\n"
            f"Bloom's Taxonomy Level: {blooms_level}\n"
            f"Total Marks: {max_marks}\n"
        )
        if learning_outcome:
            prompt += f"Learning Outcome: {learning_outcome}\n"
        if lecturer_guidelines:
            prompt += f"Lecturer Guidelines: {lecturer_guidelines}\n"
        if concepts_str:
            prompt += concepts_str
        if rag_context_text:
            prompt += f"\n{rag_context_text}\n"

        prompt += (
            "\nCRITICAL INSTRUCTIONS:\n"
            "1. Generate exactly 3 or 4 criteria that are STRICTLY relevant to this specific assessment question and model answer.\n"
            "2. DO NOT copy criterion names or topics from the style reference if they are from a different subject.\n"
            "3. Output ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "generation_rationale": "Brief 10-word summary",\n'
            '  "criteria": [\n'
            '    {"criterion_name": "...", "description": "...", "proposed_marks": float, "blooms_dimension": "Analytical"}\n'
            "  ]\n"
            "}\n"
            f"4. The proposed_marks sum should equal {max_marks}.\n"
            "5. Keep descriptions concise (under 20 words)."
        )

        # Step 3: Query Ollama llama3.2:1b (Benchmark-optimized options)
        base_url = "http://localhost:11434"
        gen_model = "llama3.2:1b"
        gen_timeout = 180.0

        if settings is not None:
            base_url = getattr(settings, "OLLAMA_BASE_URL", base_url)
            gen_model = getattr(settings, "OLLAMA_GEN_MODEL", gen_model)
            gen_timeout = float(getattr(settings, "OLLAMA_GEN_TIMEOUT_SECONDS", gen_timeout))

        base_url = os.environ.get("OLLAMA_BASE_URL", base_url).rstrip("/")
        gen_model = os.environ.get("OLLAMA_GEN_MODEL", gen_model)
        gen_timeout = float(os.environ.get("OLLAMA_GEN_TIMEOUT_SECONDS", str(gen_timeout)))

        raw_response_text = ""
        try:
            logger.info("Requesting rubric from Ollama model '%s' at %s...", gen_model, base_url)
            with httpx.Client(timeout=gen_timeout) as client:
                r = client.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": gen_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 380,
                            "num_ctx": 2048,
                            "num_thread": 6,
                        },
                    },
                )
                if r.status_code == 200:
                    raw_response_text = r.json().get("response", "").strip()
                else:
                    logger.warning("Ollama generation returned HTTP %d: %s", r.status_code, r.text[:200])
                    return cls.generate_rule_based_rubric(
                        question_text=question_text,
                        blooms_level=blooms_level,
                        reference_answer=reference_answer,
                        learning_outcome=learning_outcome,
                        lecturer_guidelines=lecturer_guidelines,
                        max_marks=max_marks,
                        generation_mode="rule_based_fallback",
                        fallback_reason=f"Ollama returned HTTP {r.status_code}",
                    )
        except httpx.TimeoutException:
            logger.warning("Ollama rubric generation timed out after %.0fs. Falling back to rule-based generator.", gen_timeout)
            return cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                generation_mode="rule_based_fallback",
                fallback_reason=f"Ollama generation timed out after {gen_timeout}s",
            )
        except (httpx.ConnectError, OSError) as e:
            logger.warning("Ollama connection error: %s. Falling back to rule-based generator.", e)
            return cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                generation_mode="rule_based_fallback",
                fallback_reason=f"Ollama connection error: {e}",
            )
        except Exception as e:
            logger.warning("Unexpected error during Ollama generation: %s", e)
            return cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                generation_mode="rule_based_fallback",
                fallback_reason=f"Ollama error: {e}",
            )

        # Step 4: Parse & Validate JSON
        clean_text = raw_response_text.strip()
        if "```" in clean_text:
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE).strip()
        if "{" in clean_text:
            clean_text = clean_text[clean_text.find("{"):]

        parsed_data = None
        try:
            parsed_data = json.loads(clean_text)
        except json.JSONDecodeError:
            # Resilient JSON repair: try finding the last completed object brace '}' and closing brackets
            last_brace = clean_text.rfind("}")
            if last_brace != -1:
                candidate = clean_text[:last_brace + 1].strip()
                for suffix in ["]}", "}]}", "}"]:
                    try:
                        parsed_data = json.loads(candidate + suffix)
                        logger.info("Successfully repaired truncated Ollama JSON.")
                        break
                    except Exception:
                        pass

        if parsed_data is None:
            logger.warning("Failed to decode Ollama JSON response. Raw: %s", raw_response_text[:200])
            return cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                generation_mode="rule_based_fallback",
                fallback_reason="Ollama output was not valid JSON",
            )

        # Extract criteria list (support both {"criteria": [...]} and root list [...])
        if isinstance(parsed_data, list):
            criteria_raw = parsed_data
            rationale_text = "Generated from list output"
        elif isinstance(parsed_data, dict):
            criteria_raw = parsed_data.get("criteria", [])
            rationale_text = parsed_data.get("generation_rationale", "")
        else:
            criteria_raw = []
            rationale_text = ""

        if not isinstance(criteria_raw, list) or len(criteria_raw) < 2:
            logger.warning("Ollama generated insufficient criteria (%d). Falling back to rule-based generator.", len(criteria_raw) if isinstance(criteria_raw, list) else 0)
            return cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                generation_mode="rule_based_fallback",
                fallback_reason="Ollama produced fewer than 2 valid criteria",
            )

        # Step 5: Validate each criterion and synthesize performance descriptors
        valid_criteria = []
        for item in criteria_raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("criterion_name") or item.get("name") or "").strip()
            desc = str(item.get("description") or "").strip()
            raw_dim = str(item.get("blooms_dimension") or "Analytical").strip()

            # Map numeric Bloom's levels (1..6) to dimension labels
            dim_mapping = {
                "1": "Remember", "2": "Understand", "3": "Apply",
                "4": "Analyze", "5": "Evaluate", "6": "Create"
            }
            dim = dim_mapping.get(raw_dim, raw_dim) if raw_dim in dim_mapping else raw_dim
            if not dim or dim.isdigit():
                dim = "Analytical"

            try:
                p_marks = float(item.get("proposed_marks") or item.get("marks") or item.get("max_marks") or 1.0)
            except (ValueError, TypeError):
                p_marks = 1.0

            # Reject invalid criteria
            if len(name) < 3 or len(desc) < 5 or p_marks <= 0:
                continue

            # Topic relevance safeguard: Filter criteria leaked from unrelated RAG references
            name_l = name.lower()
            desc_l = desc.lower()
            q_combined = f"{question_text} {reference_answer or ''}".lower()
            if any(term in name_l or term in desc_l for term in ["try/catch", "try-catch", "runtime exception"]):
                if not any(term in q_combined for term in ["exception", "try", "catch"]):
                    logger.warning("Filtering out off-topic criterion '%s' leaked from unrelated reference.", name)
                    continue

            # Populate performance levels if not provided
            perf_levels = item.get("performance_levels")
            if not perf_levels or not isinstance(perf_levels, list) or len(perf_levels) < 3:
                perf_levels = cls._synthesize_performance_levels(name, desc)

            valid_criteria.append({
                "criterion_name": name,
                "description": desc,
                "proposed_marks": p_marks,
                "weight_percentage": 25.0,  # will be computed dynamically
                "blooms_dimension": dim,
                "performance_levels": perf_levels,
            })

        if len(valid_criteria) < 2:
            logger.warning("Fewer than 2 criteria survived validation. Falling back to rule-based.")
            return cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                generation_mode="rule_based_fallback",
                fallback_reason="Validation rejected all or most criteria",
            )

        # Step 6: Mark Reconciliation & Dynamic Weight Optimization
        total_proposed = sum(c["proposed_marks"] for c in valid_criteria)
        if total_proposed > 0:
            for c in valid_criteria:
                c["weight_percentage"] = (c["proposed_marks"] / total_proposed) * 100.0

        # Apply Dynamic Weight Optimization & exact mark allocation
        optimization_result = DynamicWeightOptimizer.optimize_and_allocate(
            criteria=valid_criteria,
            max_marks=max_marks,
            target_blooms_level=blooms_level,
            question_text=question_text,
            learning_outcome=learning_outcome or "",
            lecturer_guidelines=lecturer_guidelines or "",
        )

        final_criteria = optimization_result["criteria"]

        # Step 7: Automated Rubric Validation
        validation = cls.validate_rubric(final_criteria, max_marks=max_marks)

        actual_mode = "ollama_rag" if rag_context_summary else "ollama"
        method_desc = f"via Ollama ({gen_model}) with RAG retrieval" if rag_context_summary else f"via Ollama ({gen_model})"
        full_rationale = (
            f"Generated {method_desc}. "
            f"Criteria weights dynamically optimized for Bloom's tier '{blooms_level}' "
            f"and normalized to 100.0%. Marks allocated to exactly {max_marks} marks."
        )
        if rationale_text:
            full_rationale += f" Model rationale: {rationale_text}"

        return {
            "criteria": final_criteria,
            "generation_mode": actual_mode,
            "rag_context_used": rag_context_summary,
            "rag_sources": rag_sources,
            "generation_rationale": full_rationale,
            "validation": validation,
        }

    @classmethod
    def regenerate_rule_based_rubric_with_feedback(
        cls,
        question_text: str,
        blooms_level: str = "Analyze",
        reference_answer: Optional[str] = None,
        learning_outcome: Optional[str] = None,
        lecturer_guidelines: Optional[str] = None,
        max_marks: float = 100.0,
        previous_criteria: Optional[List[Dict[str, Any]]] = None,
        rejection_reasons: Optional[List[str]] = None,
        rejection_feedback: Optional[str] = None,
        generation_mode: str = "rule_based_fallback",
        fallback_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Feedback-Driven Rule-Based Rubric Regeneration (Baseline & Resilient Fallback).
        Analyzes lecturer rejection reasons and written feedback to dynamically adjust
        rubric criteria, descriptions, Bloom's cognitive depth, and weight distribution.
        """
        import copy
        reasons = [r.strip() for r in (rejection_reasons or []) if r.strip()]
        feedback = (rejection_feedback or "").strip()

        # Step 1: Base criteria from previous rubric or rule-based generator
        raw_criteria: List[Dict[str, Any]] = []
        if previous_criteria and len(previous_criteria) >= 2:
            raw_criteria = copy.deepcopy(previous_criteria)
        else:
            base_gen = cls.generate_rule_based_rubric(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
            )
            raw_criteria = base_gen["criteria"]

        # Step 2: Handle "Missing criteria"
        has_missing_reason = any("missing" in r.lower() for r in reasons) or "missing" in feedback.lower() or "add" in feedback.lower()
        if has_missing_reason and len(raw_criteria) < 5:
            existing_names_lower = " ".join(c.get("criterion_name", "").lower() for c in raw_criteria)
            combined_context = f"{question_text} {reference_answer or ''} {learning_outcome or ''}".lower()

            if "code" not in existing_names_lower and ("code" in combined_context or "example" in combined_context or "syntax" in feedback.lower()):
                raw_criteria.append({
                    "criterion_name": "Code Implementation & Practical Syntax",
                    "description": "Syntactically correct, executable code demonstrating accurate implementation of required concepts.",
                    "weight_percentage": 20.0,
                    "proposed_marks": max(1.0, max_marks * 0.2),
                    "blooms_dimension": "Applied",
                })
            elif "exception" not in existing_names_lower and ("error" in combined_context or "exception" in combined_context):
                raw_criteria.append({
                    "criterion_name": "Exception Handling & Robustness",
                    "description": "Graceful handling of edge cases, invalid inputs, and runtime exceptions.",
                    "weight_percentage": 20.0,
                    "proposed_marks": max(1.0, max_marks * 0.2),
                    "blooms_dimension": "Analytical",
                })
            elif "trade-off" not in existing_names_lower and ("difference" in combined_context or "compare" in combined_context or "trade" in combined_context):
                raw_criteria.append({
                    "criterion_name": "Comparative Synthesis & Practical Trade-offs",
                    "description": "Critical evaluation of trade-offs, operational implications, and design rationale.",
                    "weight_percentage": 20.0,
                    "proposed_marks": max(1.0, max_marks * 0.2),
                    "blooms_dimension": "Analytical",
                })
            else:
                raw_criteria.append({
                    "criterion_name": "Pedagogical Clarity & Technical Rigor",
                    "description": "Precision in technical terminology, structured explanations, and comprehensive coverage.",
                    "weight_percentage": 15.0,
                    "proposed_marks": max(1.0, max_marks * 0.15),
                    "blooms_dimension": "Communicative",
                })

        # Step 3: Handle "Bloom's taxonomy mismatch"
        has_blooms_mismatch = any("bloom" in r.lower() for r in reasons) or "bloom" in feedback.lower()
        if has_blooms_mismatch or blooms_level:
            for c in raw_criteria:
                c["blooms_dimension"] = blooms_level
                desc = c.get("description", "")
                if blooms_level.lower() in ["analyze", "analytical"]:
                    if not any(v in desc.lower() for v in ["analyze", "distinguish", "contrast", "differentiate"]):
                        c["description"] = f"Analyze, contrast, and critically evaluate {desc.lower()}"
                elif blooms_level.lower() in ["evaluate", "create"]:
                    if not any(v in desc.lower() for v in ["justify", "synthesize", "design", "critique"]):
                        c["description"] = f"Critically justify, synthesize, and assess {desc.lower()}"
                elif blooms_level.lower() in ["understand", "conceptual"]:
                    if not any(v in desc.lower() for v in ["explain", "describe", "comprehend"]):
                        c["description"] = f"Clearly explain and illustrate core concepts of {desc.lower()}"

        # Step 4: Handle "Unclear criterion descriptions"
        has_unclear_desc = any("unclear" in r.lower() for r in reasons) or "vague" in feedback.lower() or "clarity" in feedback.lower()
        if has_unclear_desc:
            for c in raw_criteria:
                name = c.get("criterion_name", "")
                desc = c.get("description", "")
                if len(desc) < 65:
                    c["description"] = f"{desc} Requires concrete evidence, accurate terminology, and explicit justification relevant to {name}."

        # Step 5: Handle "Incorrect or irrelevant criteria"
        has_irrelevant_reason = any("irrelevant" in r.lower() or "incorrect" in r.lower() for r in reasons)
        if has_irrelevant_reason and len(raw_criteria) > 3:
            q_keywords = [w.lower() for w in question_text.split() if len(w) > 3]
            scored_c = []
            for c in raw_criteria:
                c_text = f"{c.get('criterion_name', '')} {c.get('description', '')}".lower()
                relevance = sum(1 for kw in q_keywords if kw in c_text)
                scored_c.append((relevance, c))
            scored_c.sort(key=lambda x: x[0], reverse=True)
            raw_criteria = [item[1] for item in scored_c[:4]]

        # Step 6: Incorporate lecturer written feedback directly
        if feedback:
            for idx, c in enumerate(raw_criteria):
                if idx == 0:
                    c["description"] = f"{c.get('description', '')} [Lecturer Note: {feedback}]".strip()

        # Step 7: Synthesize graduated performance descriptors
        for c in raw_criteria:
            c["performance_levels"] = cls._synthesize_performance_levels(
                c.get("criterion_name", "Criterion"),
                c.get("description", "")
            )

        # Step 8: Apply Dynamic Weight Optimization & exact mark allocation
        optimization_result = DynamicWeightOptimizer.optimize_and_allocate(
            criteria=raw_criteria,
            max_marks=max_marks,
            target_blooms_level=blooms_level,
            question_text=question_text,
            learning_outcome=learning_outcome or "",
            lecturer_guidelines=lecturer_guidelines or "",
        )
        final_criteria = optimization_result["criteria"]

        # Step 9: Automated validation
        validation = cls.validate_rubric(final_criteria, max_marks=max_marks)

        reasons_summary = ", ".join(reasons) if reasons else "Feedback-driven adjustments"
        rationale = f"Regenerated rubric incorporating lecturer review ({reasons_summary})."
        if feedback:
            rationale += f" Lecturer feedback addressed: '{feedback}'."
        if fallback_reason:
            rationale += f" (Engaged as fallback: {fallback_reason})"

        return {
            "criteria": final_criteria,
            "generation_mode": generation_mode,
            "rag_context_used": None,
            "rag_sources": [],
            "generation_rationale": rationale,
            "validation": validation,
            "fallback_reason": fallback_reason,
        }

    @classmethod
    def regenerate_rubric_with_feedback(
        cls,
        question_text: str,
        blooms_level: str = "Analyze",
        reference_answer: Optional[str] = None,
        learning_outcome: Optional[str] = None,
        lecturer_guidelines: Optional[str] = None,
        max_marks: float = 100.0,
        previous_criteria: Optional[List[Dict[str, Any]]] = None,
        rejection_reasons: Optional[List[str]] = None,
        rejection_feedback: Optional[str] = None,
        previous_version: int = 1,
        use_rag: bool = True,
        force_fallback: bool = False,
    ) -> Dict[str, Any]:
        """
        Phase 3: Feedback-Driven Rubric Regeneration via Ollama llama3.2:1b + RAG.
        Incorporates original inputs, previous criteria, lecturer rejection reasons,
        and written feedback to synthesize a corrected rubric version.
        Guarantees unlabelled fallbacks are NEVER silently deployed.
        """
        enabled = True
        if settings is not None and hasattr(settings, "ENABLE_RAG_RUBRIC_GENERATION"):
            enabled = bool(settings.ENABLE_RAG_RUBRIC_GENERATION)

        if force_fallback or not enabled:
            logger.info("Feedback regeneration fallback engaged (force_fallback=%s, enabled=%s).", force_fallback, enabled)
            return cls.regenerate_rule_based_rubric_with_feedback(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                previous_criteria=previous_criteria,
                rejection_reasons=rejection_reasons,
                rejection_feedback=rejection_feedback,
                generation_mode="rule_based_fallback",
                fallback_reason="Explicit fallback requested" if force_fallback else "RAG generation disabled",
            )

        # Step 1: Retrieve RAG Knowledge Context
        rag_context_text = ""
        rag_sources = []
        rag_context_summary = None

        if use_rag:
            try:
                from app.services.rag_retrieval_service import get_rag_service
                rag_service = get_rag_service(auto_init=True)
                rag_res = rag_service.retrieve(query=question_text, top_k=2)
                results = rag_res.get("results", [])
                for r in results:
                    qid = r.get("question_id", r.get("doc_id", "Q?"))
                    topic = r.get("rag_topic", "")
                    approval = r.get("lecturer_approval", "Pending")
                    trust = r.get("rag_trust_level", "DRAFT_REFERENCE_ONLY")
                    rag_sources.append(f"{qid} ({topic}) - Approval: {approval} [{trust}]")

                if results:
                    rag_context_text = (
                        "Reference Lecturer Rubrics from Knowledge Base:\n"
                        + rag_res.get("retrieved_context", "")
                    )
                    rag_context_summary = f"Retrieved {len(results)} references: " + "; ".join(rag_sources)
            except Exception as e:
                logger.warning("RAG retrieval failed during rubric regeneration: %s", e)

        # Step 2: Formulate Optimized Ollama Prompt
        # Benchmark-verified: condensed prompt (~500 tokens) with num_ctx=2048, num_thread=6
        # yields ~62s generation vs 120s+ timeout with the verbose prompt.
        reasons_list = rejection_reasons or ["General Revision Required"]
        reasons_bullets = "\n".join(f"- {r}" for r in reasons_list)
        feedback_text = (rejection_feedback or "Address selected rejection reasons thoroughly.").strip()

        prev_criteria_summary = []
        for idx, c in enumerate(previous_criteria or [], 1):
            c_name = c.get("criterion_name", f"Criterion {idx}")
            c_weight = c.get("weight_percentage", 0)
            c_marks = c.get("max_marks", 0)
            prev_criteria_summary.append(
                f"{idx}. {c_name} ({c_weight}%, {c_marks}m)"
            )
        prev_criteria_str = "\n".join(prev_criteria_summary) if prev_criteria_summary else "None"

        # Truncate RAG context to limit prompt tokens (benchmark-verified: <=400 chars)
        rag_context_condensed = rag_context_text[:400].strip() if rag_context_text else ""

        prompt = (
            f"You are an academic rubric regeneration engine. A previously generated rubric was REJECTED by the lecturer.\n"
            f"Output an improved JSON rubric with 3 or 4 criteria totaling {max_marks} marks that incorporates the lecturer's feedback.\n\n"
            f"Assessment Question: {question_text}\n"
            f"Bloom's Level: {blooms_level} | Total Marks: {max_marks}\n"
        )
        if learning_outcome:
            prompt += f"Learning Outcome: {learning_outcome}\n"
        if lecturer_guidelines:
            prompt += f"Lecturer Guidelines: {lecturer_guidelines}\n"

        prompt += (
            f"\nPREVIOUS REJECTED RUBRIC:\n"
            f"{prev_criteria_str}\n\n"
            f"LECTURER FEEDBACK:\n"
            f"{reasons_bullets}\n"
            f"Feedback: {feedback_text}\n\n"
        )
        if rag_context_condensed:
            prompt += f"{rag_context_condensed}\n\n"

        prompt += (
            "INSTRUCTIONS:\n"
            f"1. Address every rejection reason and incorporate lecturer feedback.\n"
            f"2. Output exactly 3 or 4 criteria summing to {max_marks} marks.\n"
            "3. Keep descriptions concise (under 20 words).\n"
            "4. Output valid JSON in this exact structure:\n"
            "{\n"
            '  "generation_rationale": "Brief 10-word summary",\n'
            '  "criteria": [\n'
            '    {"criterion_name": "...", "description": "...", "proposed_marks": float, "blooms_dimension": "..."}\n'
            "  ]\n"
            "}"
        )

        # Step 3: Query Ollama llama3.2:1b (Benchmark-optimized options)
        base_url = "http://localhost:11434"
        gen_model = "llama3.2:1b"
        gen_timeout = 180.0

        if settings is not None:
            base_url = getattr(settings, "OLLAMA_BASE_URL", base_url)
            gen_model = getattr(settings, "OLLAMA_GEN_MODEL", gen_model)
            gen_timeout = float(getattr(settings, "OLLAMA_GEN_TIMEOUT_SECONDS", gen_timeout))

        base_url = os.environ.get("OLLAMA_BASE_URL", base_url).rstrip("/")
        gen_model = os.environ.get("OLLAMA_GEN_MODEL", gen_model)
        gen_timeout = float(os.environ.get("OLLAMA_GEN_TIMEOUT_SECONDS", str(gen_timeout)))

        raw_response_text = ""
        try:
            logger.info(
                "Requesting rubric feedback regeneration from Ollama model '%s' at %s (optimized prompt: %d chars)...",
                gen_model, base_url, len(prompt),
            )
            with httpx.Client(timeout=gen_timeout) as client:
                r = client.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": gen_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 280,
                            "num_ctx": 2048,
                            "num_thread": 6,
                        },
                    },
                )
                if r.status_code == 200:
                    raw_response_text = r.json().get("response", "").strip()
                else:
                    logger.warning("Ollama regeneration returned HTTP %d: %s", r.status_code, r.text[:200])
                    return cls.regenerate_rule_based_rubric_with_feedback(
                        question_text=question_text,
                        blooms_level=blooms_level,
                        reference_answer=reference_answer,
                        learning_outcome=learning_outcome,
                        lecturer_guidelines=lecturer_guidelines,
                        max_marks=max_marks,
                        previous_criteria=previous_criteria,
                        rejection_reasons=rejection_reasons,
                        rejection_feedback=rejection_feedback,
                        generation_mode="rule_based_fallback",
                        fallback_reason=f"Ollama returned HTTP {r.status_code}",
                    )
        except httpx.TimeoutException:
            logger.warning("Ollama rubric feedback regeneration timed out after %.0fs.", gen_timeout)
            return cls.regenerate_rule_based_rubric_with_feedback(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                previous_criteria=previous_criteria,
                rejection_reasons=rejection_reasons,
                rejection_feedback=rejection_feedback,
                generation_mode="rule_based_fallback",
                fallback_reason=f"Ollama generation timed out after {gen_timeout}s",
            )
        except (httpx.ConnectError, OSError) as e:
            logger.warning("Ollama connection error during regeneration: %s.", e)
            return cls.regenerate_rule_based_rubric_with_feedback(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                previous_criteria=previous_criteria,
                rejection_reasons=rejection_reasons,
                rejection_feedback=rejection_feedback,
                generation_mode="rule_based_fallback",
                fallback_reason=f"Ollama connection error: {e}",
            )
        except Exception as e:
            logger.warning("Unexpected error during Ollama regeneration: %s", e)
            return cls.regenerate_rule_based_rubric_with_feedback(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                previous_criteria=previous_criteria,
                rejection_reasons=rejection_reasons,
                rejection_feedback=rejection_feedback,
                generation_mode="rule_based_fallback",
                fallback_reason=f"Ollama error: {e}",
            )

        # Step 4: Parse & Validate JSON
        clean_text = raw_response_text.strip()
        if "```" in clean_text:
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE).strip()
        if "{" in clean_text:
            clean_text = clean_text[clean_text.find("{"):]

        parsed_data = None
        try:
            parsed_data = json.loads(clean_text)
        except json.JSONDecodeError:
            last_brace = clean_text.rfind("}")
            if last_brace != -1:
                candidate = clean_text[:last_brace + 1].strip()
                for suffix in ["]}", "}]}", "}"]:
                    try:
                        parsed_data = json.loads(candidate + suffix)
                        logger.info("Successfully repaired truncated Ollama regeneration JSON.")
                        break
                    except Exception:
                        pass

        if parsed_data is None:
            logger.warning("Failed to decode Ollama regeneration JSON response. Raw: %s", raw_response_text[:200])
            return cls.regenerate_rule_based_rubric_with_feedback(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                previous_criteria=previous_criteria,
                rejection_reasons=rejection_reasons,
                rejection_feedback=rejection_feedback,
                generation_mode="rule_based_fallback",
                fallback_reason="Ollama output was not valid JSON",
            )

        if isinstance(parsed_data, list):
            criteria_raw = parsed_data
            rationale_text = "Regenerated from list output"
        elif isinstance(parsed_data, dict):
            criteria_raw = parsed_data.get("criteria", [])
            rationale_text = parsed_data.get("generation_rationale", "")
        else:
            criteria_raw = []
            rationale_text = ""

        if not isinstance(criteria_raw, list) or len(criteria_raw) < 2:
            logger.warning("Ollama generated insufficient criteria during regeneration (%d).", len(criteria_raw) if isinstance(criteria_raw, list) else 0)
            return cls.regenerate_rule_based_rubric_with_feedback(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                previous_criteria=previous_criteria,
                rejection_reasons=rejection_reasons,
                rejection_feedback=rejection_feedback,
                generation_mode="rule_based_fallback",
                fallback_reason="Ollama produced fewer than 2 valid criteria",
            )

        # Step 5: Validate each criterion and synthesize performance descriptors
        valid_criteria = []
        for item in criteria_raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("criterion_name") or item.get("name") or "").strip()
            desc = str(item.get("description") or "").strip()
            dim = str(item.get("blooms_dimension") or "Analytical").strip()

            try:
                p_marks = float(item.get("proposed_marks") or item.get("marks") or item.get("max_marks") or 1.0)
            except (ValueError, TypeError):
                p_marks = 1.0

            if len(name) < 3 or len(desc) < 5 or p_marks <= 0:
                continue

            perf_levels = item.get("performance_levels")
            if not perf_levels or not isinstance(perf_levels, list) or len(perf_levels) < 3:
                perf_levels = cls._synthesize_performance_levels(name, desc)

            valid_criteria.append({
                "criterion_name": name,
                "description": desc,
                "proposed_marks": p_marks,
                "weight_percentage": 25.0,
                "blooms_dimension": dim,
                "performance_levels": perf_levels,
            })

        if len(valid_criteria) < 2:
            logger.warning("Fewer than 2 criteria survived validation in regeneration. Falling back.")
            return cls.regenerate_rule_based_rubric_with_feedback(
                question_text=question_text,
                blooms_level=blooms_level,
                reference_answer=reference_answer,
                learning_outcome=learning_outcome,
                lecturer_guidelines=lecturer_guidelines,
                max_marks=max_marks,
                previous_criteria=previous_criteria,
                rejection_reasons=rejection_reasons,
                rejection_feedback=rejection_feedback,
                generation_mode="rule_based_fallback",
                fallback_reason="Validation rejected all or most criteria",
            )

        # Step 6: Mark Reconciliation & Dynamic Weight Optimization
        total_proposed = sum(c["proposed_marks"] for c in valid_criteria)
        if total_proposed > 0:
            for c in valid_criteria:
                c["weight_percentage"] = (c["proposed_marks"] / total_proposed) * 100.0

        optimization_result = DynamicWeightOptimizer.optimize_and_allocate(
            criteria=valid_criteria,
            max_marks=max_marks,
            target_blooms_level=blooms_level,
            question_text=question_text,
            learning_outcome=learning_outcome or "",
            lecturer_guidelines=lecturer_guidelines or "",
        )
        final_criteria = optimization_result["criteria"]

        # Step 7: Automated Rubric Validation
        validation = cls.validate_rubric(final_criteria, max_marks=max_marks)

        actual_regen_mode = "ollama_feedback_regenerated"
        regen_method_desc = f"via Ollama ({gen_model}) with RAG retrieval" if rag_context_summary else f"via Ollama ({gen_model})"
        reasons_summary = ", ".join(reasons_list)
        full_rationale = (
            f"Feedback-driven regeneration {regen_method_desc}. "
            f"Addressed lecturer rejection reasons: [{reasons_summary}]. "
            f"Criteria weights dynamically optimized for Bloom's tier '{blooms_level}' "
            f"and reconciled to {max_marks} marks."
        )
        if rationale_text:
            full_rationale += f" Model rationale: {rationale_text}"

        return {
            "criteria": final_criteria,
            "generation_mode": actual_regen_mode,
            "rag_context_used": rag_context_summary,
            "rag_sources": rag_sources,
            "generation_rationale": full_rationale,
            "validation": validation,
        }

    @classmethod
    def generate_adaptive_rubric(
        cls,
        question_text: str,
        blooms_level: str = "Analyze",
        reference_answer: str = None,
        learning_outcome: str = None,
        lecturer_guidelines: str = None,
        max_marks: float = 100.0,
        use_rag: bool = True,
        force_fallback: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for adaptive rubric generation (Backward Compatible).
        Returns the optimized list of criteria.
        """
        result = cls.generate_rubric_with_rag(
            question_text=question_text,
            blooms_level=blooms_level,
            reference_answer=reference_answer,
            learning_outcome=learning_outcome,
            lecturer_guidelines=lecturer_guidelines,
            max_marks=max_marks,
            use_rag=use_rag,
            force_fallback=force_fallback,
        )
        return result["criteria"]

    @classmethod
    def validate_rubric(cls, criteria: List[Dict[str, Any]], max_marks: float = 100.0) -> Dict[str, Any]:
        """
        Feature 5: Rubric Validation.
        Automated verification of duplicate criteria, 100% weight sum, total mark consistency,
        and graduated performance descriptors.
        """
        checks = []
        messages = []
        recommendations = []

        # Check 1: Criteria count & presence
        count = len(criteria)
        if count >= 3:
            checks.append({"name": "Criterion Coverage", "passed": True, "detail": f"{count} criteria defined (Recommended: 3 to 6)."})
        else:
            checks.append({"name": "Criterion Coverage", "passed": False, "detail": f"Only {count} criteria defined. At least 3 are required."})
            messages.append("Insufficient criteria count.")
            recommendations.append("Define at least 3 distinct criteria covering concepts, implementation, and analysis.")

        # Check 2: Duplicate criteria check
        names = [c.get("criterion_name", "").strip().lower() for c in criteria if c.get("criterion_name")]
        has_duplicates = len(names) != len(set(names))
        checks.append({
            "name": "Duplicate Criteria Check",
            "passed": not has_duplicates,
            "detail": "No duplicate criteria detected." if not has_duplicates else "Duplicate criteria names identified."
        })
        if has_duplicates:
            messages.append("Duplicate criteria names detected.")
            recommendations.append("Remove or merge duplicate criteria.")

        # Check 3: Weight total (strictly 100.0%)
        total_weight = round(sum(float(c.get("weight_percentage", 0.0)) for c in criteria), 2)
        weight_ok = abs(total_weight - 100.0) < 0.01
        checks.append({
            "name": "Weight Sum Verification",
            "passed": weight_ok,
            "detail": f"Total weight is {total_weight:.2f}% (Required: exactly 100.00%)."
        })
        if not weight_ok:
            messages.append(f"Weights sum to {total_weight:.2f}%, which diverges from 100.00%.")
            recommendations.append("Normalize criteria weights to 100.0%.")

        # Check 4: Total marks check
        total_marks = round(sum(float(c.get("max_marks", 0.0)) for c in criteria), 2)
        marks_ok = abs(total_marks - max_marks) < 0.05
        checks.append({
            "name": "Allocated Marks Verification",
            "passed": marks_ok,
            "detail": f"Total allocated marks: {total_marks:.2f} / {max_marks:.2f}."
        })
        if not marks_ok:
            messages.append(f"Allocated marks sum to {total_marks:.2f}, diverging from total assessment marks {max_marks:.2f}.")
            recommendations.append("Reallocate criterion marks to match question maximum marks.")

        # Check 5: Performance level completeness
        levels_ok = all(len(c.get("performance_levels", [])) >= 3 for c in criteria)
        checks.append({
            "name": "Performance Granularity",
            "passed": levels_ok,
            "detail": "All criteria feature graduated performance descriptors." if levels_ok else "One or more criteria lack sufficient performance tiers."
        })
        if not levels_ok:
            messages.append("Missing performance level descriptors in some criteria.")
            recommendations.append("Ensure each criterion specifies Exemplary, Proficient, Developing, and Unsatisfactory descriptors.")

        # Check 6: Non-zero positive weights
        non_zero_ok = all(float(c.get("weight_percentage", 0.0)) > 0 for c in criteria)
        checks.append({
            "name": "Non-Zero Allocation",
            "passed": non_zero_ok,
            "detail": "All criteria have active positive weight." if non_zero_ok else "One or more criteria have zero or negative weight."
        })

        is_valid = all(c["passed"] for c in checks)
        score = sum(1.0 for c in checks if c["passed"]) / len(checks)

        return {
            "is_valid": is_valid,
            "validation_score": round(score, 2),
            "status": "valid" if is_valid else ("warning" if score >= 0.6 else "invalid"),
            "checks": checks,
            "messages": messages,
            "recommendations": recommendations,
        }

    @classmethod
    def _extract_scoring_keywords(cls, text: str) -> List[str]:
        """
        Extracts meaningful technical keywords from criterion descriptions and reference answers.
        Filters out common stopwords and short words.
        """
        stopwords = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her",
            "was", "one", "our", "out", "has", "its", "with", "from", "this", "that",
            "which", "their", "will", "each", "make", "like", "into", "them", "then",
            "than", "been", "have", "many", "some", "what", "when", "where", "why",
            "how", "should", "must", "also", "using", "used", "use", "provide",
            "explain", "describe", "discuss", "understanding", "assessment", "student",
            "answer", "response", "question", "based", "demonstrate", "including",
            "correctly", "properly", "appropriate", "accurate", "correct", "clear",
            "proper", "relevant", "important", "various", "different", "specific",
            "examples", "example", "concepts", "concept", "approach", "method",
        }
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in stopwords]

    @classmethod
    def _compute_keyword_coverage(cls, answer_text: str, keywords: List[str]) -> float:
        """
        Computes how many of the target keywords appear in the student answer.
        Returns a ratio between 0.0 and 1.0.
        """
        if not keywords:
            return 0.5  # neutral when no keywords to match
        answer_lower = answer_text.lower()
        hits = sum(1 for kw in keywords if kw in answer_lower)
        return min(hits / len(keywords), 1.0)

    @classmethod
    def score_student_answer(
        cls,
        answer_text: str,
        criteria: List[Dict[str, Any]],
        reference_answer: str = None
    ) -> Dict[str, Any]:
        """
        Feature 7: Criterion-based scoring of subjective student answers.

        Multi-signal scoring algorithm:
        1. Per-criterion keyword coverage — extracts domain keywords from criterion name,
           description, and reference answer, then measures how many appear in the student response.
        2. Answer depth signal — longer, more detailed answers receive a depth bonus.
        3. Reference answer alignment — if provided, checks overlap of technical terms.
        4. Combines signals to determine performance level and marks awarded.
        """
        answer_lower = answer_text.lower()
        answer_words = answer_text.split()
        answer_len = len(answer_words)

        # Global depth signal (0.0 to 1.0)
        if answer_len > 120:
            depth_signal = 1.0
        elif answer_len > 70:
            depth_signal = 0.85
        elif answer_len > 35:
            depth_signal = 0.65
        elif answer_len > 15:
            depth_signal = 0.40
        else:
            depth_signal = 0.15

        # Reference answer keyword extraction (global)
        ref_keywords = []
        if reference_answer:
            ref_keywords = cls._extract_scoring_keywords(reference_answer)

        criterion_scores = []
        weighted_total = 0.0
        max_possible = sum(float(c.get("max_marks", 25.0)) for c in criteria)
        if max_possible <= 0:
            max_possible = 100.0

        for crit in criteria:
            name = crit.get("criterion_name", "Criterion")
            description = crit.get("description", "")
            weight = float(crit.get("weight_percentage", 25.0))
            max_c_marks = float(crit.get("max_marks", (weight / 100.0) * max_possible))

            # Signal 1: Criterion-specific keyword coverage
            crit_keywords = cls._extract_scoring_keywords(f"{name} {description}")
            crit_coverage = cls._compute_keyword_coverage(answer_text, crit_keywords)

            # Signal 2: Reference answer keyword overlap for this criterion
            ref_coverage = cls._compute_keyword_coverage(answer_text, ref_keywords) if ref_keywords else 0.5

            # Signal 3: Check if the criterion's core domain terms appear in the answer
            # Extract 2-3 most specific terms from criterion name
            core_terms = [w.lower() for w in name.split() if len(w) > 4][:3]
            core_hit = sum(1 for t in core_terms if t in answer_lower) / max(len(core_terms), 1)

            # Composite score: weighted combination of all signals
            composite = (
                crit_coverage * 0.35 +      # criterion keyword matching
                ref_coverage * 0.25 +        # reference answer alignment
                depth_signal * 0.20 +        # answer depth/length
                core_hit * 0.20              # core criterion term presence
            )

            # Map composite score to performance level
            if composite >= 0.75:
                level = "Exemplary"
                ratio = min(0.88 + (composite - 0.75) * 0.48, 0.98)  # 0.88 to 0.98
                feedback = f"Demonstrates thorough, insightful exploration of {name.lower()} with strong technical depth and relevant supporting detail."
                confidence = round(min(0.88 + composite * 0.08, 0.96), 2)
            elif composite >= 0.55:
                level = "Proficient"
                ratio = 0.72 + (composite - 0.55) * 0.80  # 0.72 to 0.88
                feedback = f"Competently addresses {name.lower()} with clear articulation, though minor gaps in specificity or depth."
                confidence = round(0.82 + composite * 0.06, 2)
            elif composite >= 0.30:
                level = "Developing"
                ratio = 0.40 + (composite - 0.30) * 1.28  # 0.40 to 0.72
                feedback = f"Identifies foundational aspects of {name.lower()} but lacks sufficient depth, precision, or supporting rationale."
                confidence = round(0.72 + composite * 0.05, 2)
            else:
                level = "Unsatisfactory"
                ratio = max(0.10 + composite * 1.0, 0.10)  # 0.10 to 0.40
                feedback = f"Minimal or vague treatment of {name.lower()}. Key concepts missing or inaccurately stated."
                confidence = round(0.60 + composite * 0.08, 2)

            awarded = round(max_c_marks * ratio, 2)
            weighted_total += awarded

            criterion_scores.append({
                "criterion_id": crit.get("id", 0),
                "criterion_name": name,
                "score_awarded": awarded,
                "max_score": round(max_c_marks, 2),
                "weight_percentage": weight,
                "performance_level": level,
                "feedback": feedback,
                "confidence_score": confidence,
            })

        total_score = round(weighted_total, 2)
        percentage = round((total_score / max_possible) * 100.0, 1)

        # Generate holistic feedback
        if percentage >= 85:
            overall = f"Excellent performance ({percentage}% mastery). The response demonstrates comprehensive understanding across all evaluated criteria with strong analytical depth."
        elif percentage >= 70:
            overall = f"Good performance ({percentage}% mastery). Solid grasp of core concepts with room for deeper technical elaboration in selected dimensions."
        elif percentage >= 50:
            overall = f"Developing performance ({percentage}% mastery). Foundational understanding present but significant gaps in depth, precision, or applied reasoning."
        else:
            overall = f"Below expectations ({percentage}% mastery). Major conceptual gaps across multiple criteria. Substantial revision and deeper study recommended."

        return {
            "total_score": total_score,
            "max_marks": max_possible,
            "percentage": percentage,
            "overall_feedback": overall,
            "criterion_scores": criterion_scores,
        }

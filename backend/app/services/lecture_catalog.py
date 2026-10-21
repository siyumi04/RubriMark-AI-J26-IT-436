"""
SLIIT IT2030 Object Oriented Programming Lecture Repository Catalog.
Fully verified from the 10 original IT2030 Lecture PDFs in backend/lecture_materials.
Provides verified page numbers, titles, concept linkages, pedagogical rationale,
and practice activities for explainable student remediation.
"""

from typing import Dict, Any, List, Optional


IT2030_LECTURE_FILES: Dict[str, Dict[str, Any]] = {
    "Lecture 01": {
        "filename": "Lecture-01-Introduction.pdf",
        "title": "Introduction to Java and Object Oriented Concepts",
        "total_pages": 50
    },
    "Lecture 02": {
        "filename": "Lecture 02 - Classes and Objects.pdf",
        "title": "Java Classes and Objects",
        "total_pages": 58
    },
    "Lecture 03": {
        "filename": "Lecture-03-OOP recap.pdf",
        "title": "A Few Things in Java (Static Members & Method Overriding)",
        "total_pages": 29
    },
    "Lecture 04": {
        "filename": "Lecture 04 - Abstract Classes and Interfaces.pdf",
        "title": "Abstract Classes and Interfaces",
        "total_pages": 32
    },
    "Lecture 05": {
        "filename": "Lecture-05-Errors and Exception.pdf",
        "title": "Errors and Exception Handling",
        "total_pages": 41
    },
    "Lecture 06": {
        "filename": "Lecture 06 - Strings.pdf",
        "title": "Strings in Java (String Pool, Immutability & Manipulation)",
        "total_pages": 21
    },
    "Lecture 07": {
        "filename": "Lecture-07-Collections Framwork.pdf",
        "title": "Java Collections Framework",
        "total_pages": 39
    },
    "Lecture 08": {
        "filename": "Lecture 08 - Generics.pdf",
        "title": "Generics in Java (Type Parameters & Bounded Types)",
        "total_pages": 32
    },
    "Lecture 09": {
        "filename": "Lecture 09 -Threads.pdf",
        "title": "Threads & Concurrency in Java",
        "total_pages": 42
    },
    "Lecture 10": {
        "filename": "Lecture-10-Design Patterns.pdf",
        "title": "Design Patterns in Object Oriented Design",
        "total_pages": 63
    }
}


# Exact Verified Slide Mapping for all OOP Concepts
VERIFIED_CONCEPT_LECTURE_MAP: Dict[str, Dict[str, Any]] = {
    "Class as blueprint/template": {
        "lecture_number": "Lecture 02",
        "lecture_title": "Java Classes and Objects",
        "pdf_filename": "Lecture 02 - Classes and Objects.pdf",
        "verified_page": 9,
        "concept_name": "Class as blueprint/template",
        "reason": "Slide 9 defines a Class as an abstract blueprint/template using the architectural House vs Blueprint analogy, contrasting specifications against instances.",
        "learning_priority": "High",
        "practice_activity": "Lecture 02 Exercise 1 (Slide 12): Identify classes and attributes for a Hospital Management System and write the class specification.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Object as class instance": {
        "lecture_number": "Lecture 02",
        "lecture_title": "Java Classes and Objects",
        "pdf_filename": "Lecture 02 - Classes and Objects.pdf",
        "verified_page": 10,
        "concept_name": "Object as class instance",
        "reason": "Slide 10 details how objects are concrete instances instantiated in memory to store distinct data, supported by instantiation syntax on Slide 17 ('new Student()').",
        "learning_priority": "High",
        "practice_activity": "Lecture 02 Exercise 6 (Slide 33): Implement class MyMain with a main method and instantiate multiple objects to demonstrate state manipulation.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Concrete class-object example": {
        "lecture_number": "Lecture 02",
        "lecture_title": "Java Classes and Objects",
        "pdf_filename": "Lecture 02 - Classes and Objects.pdf",
        "verified_page": 8,
        "concept_name": "Concrete class-object example",
        "reason": "Slide 8 provides concrete domain examples (Car class with attributes 'fuel', 'maxspeed' and methods 'refuel', 'drive') to ground theoretical definitions.",
        "learning_priority": "Medium",
        "practice_activity": "Lecture 02 Exercise 7 (Slide 37): Take a domain class and implement default and parameterized constructors to initialize attributes.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Inheritance of accessible fields": {
        "lecture_number": "Lecture 02",
        "lecture_title": "Java Classes and Objects",
        "pdf_filename": "Lecture 02 - Classes and Objects.pdf",
        "verified_page": 42,
        "concept_name": "Inheritance of accessible fields",
        "reason": "Slide 42 and Slide 49 (Shape_example.java) illustrate how child classes inherit accessible protected/public attributes from the superclass.",
        "learning_priority": "High",
        "practice_activity": "Lecture 02 Exercise 10 (Slide 50): Write Java code to implement inheritance from base Shape to child Rectangle/Circle classes.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Inheritance of accessible methods": {
        "lecture_number": "Lecture 02",
        "lecture_title": "Java Classes and Objects",
        "pdf_filename": "Lecture 02 - Classes and Objects.pdf",
        "verified_page": 44,
        "concept_name": "Inheritance of accessible methods",
        "reason": "Slide 43 and 44 explain method inheritance using 'extends' and calling base class implementations via the 'super' keyword in Java.",
        "learning_priority": "High",
        "practice_activity": "Lecture 02 Exercise 12 (Slide 56-57): Implement Employee and Manager classes, inheriting attributes and reusing Read() and Print() methods.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Child provides overriding implementation": {
        "lecture_number": "Lecture 03",
        "lecture_title": "A Few Things in Java (Static & Overriding)",
        "pdf_filename": "Lecture-03-OOP recap.pdf",
        "verified_page": 27,
        "concept_name": "Child provides overriding implementation",
        "reason": "Slide 27 defines method overriding: a descendant class replaces an inherited superclass method with identical signature to provide specialized behavior.",
        "learning_priority": "High",
        "practice_activity": "Lecture 03 Slide 28 (Override.java demo): Implement class B extending A, overriding show() to display child-specific values.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Child implementation executes on child object": {
        "lecture_number": "Lecture 02",
        "lecture_title": "Java Classes and Objects",
        "pdf_filename": "Lecture 02 - Classes and Objects.pdf",
        "verified_page": 45,
        "concept_name": "Child implementation executes on child object",
        "reason": "Slide 45 and Slide 54 explain dynamic method dispatch: all Java methods are virtual by default, resolving to the runtime child object implementation.",
        "learning_priority": "High",
        "practice_activity": "Lecture 02 Exercise 11 (Slide 55): Implement polymorphic array of Animal references (Cat, Dog, Cow) and call overridden song() at runtime.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Static belongs to class": {
        "lecture_number": "Lecture 03",
        "lecture_title": "A Few Things in Java (Static & Overriding)",
        "pdf_filename": "Lecture-03-OOP recap.pdf",
        "verified_page": 12,
        "concept_name": "Static belongs to class",
        "reason": "Slide 12 explains that static members belong to the whole class rather than any individual object, loaded once in class memory.",
        "learning_priority": "High",
        "practice_activity": "Lecture 03 Slide 13 (StaticDemo.java): Define static variable batchId and invoke static method setBatchId2() directly using ClassName.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "instance variable belongs to object": {
        "lecture_number": "Lecture 03",
        "lecture_title": "A Few Things in Java (Static & Overriding)",
        "pdf_filename": "Lecture-03-OOP recap.pdf",
        "verified_page": 15,
        "concept_name": "instance variable belongs to object",
        "reason": "Slide 15 illustrates the memory model: distinct heap storage for non-static instance variables per object instance (s1 vs s2) vs shared static variables.",
        "learning_priority": "High",
        "practice_activity": "Lecture 03 Slide 15: Trace stack and heap memory diagrams showing how modifying an instance variable affects only that specific object instance.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "No direct instance-variable access from static method": {
        "lecture_number": "Lecture 03",
        "lecture_title": "A Few Things in Java (Static & Overriding)",
        "pdf_filename": "Lecture-03-OOP recap.pdf",
        "verified_page": 16,
        "concept_name": "No direct instance-variable access from static method",
        "reason": "Slide 16 details static method constraints: a static method does not operate on an object, has no implicit 'this' reference, and cannot directly access instance members.",
        "learning_priority": "High",
        "practice_activity": "Lecture 03 Slide 16-17: Explain why referencing 'name' directly inside 'public static void main' results in a Java compilation error.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Instance reference required for access": {
        "lecture_number": "Lecture 03",
        "lecture_title": "A Few Things in Java (Static & Overriding)",
        "pdf_filename": "Lecture-03-OOP recap.pdf",
        "verified_page": 16,
        "concept_name": "Instance reference required for access",
        "reason": "Slide 16 and Slide 17 specify that to access an instance member from a static context, an explicit object instance must be instantiated or passed as a reference.",
        "learning_priority": "High",
        "practice_activity": "Lecture 02 Slide 17 & Lecture 03 Slide 16: Refactor static code to instantiate 'Student s = new Student();' and access instance members via 's.variable'.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Handles runtime exceptions/errors": {
        "lecture_number": "Lecture 05",
        "lecture_title": "Errors and Exception Handling",
        "pdf_filename": "Lecture-05-Errors and Exception.pdf",
        "verified_page": 17,
        "concept_name": "Handles runtime exceptions/errors",
        "reason": "Slide 17 and Slide 18 explain structured exception handling using try and catch blocks to monitor code, intercept runtime errors, and avoid termination.",
        "learning_priority": "High",
        "practice_activity": "Lecture 05 Slide 22 Coding Exercise: Wrap Integer.parseInt(s) inside a try-catch block to catch NumberFormatException and print an informative error.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    },
    "Prevents abrupt termination or supports graceful recovery": {
        "lecture_number": "Lecture 05",
        "lecture_title": "Errors and Exception Handling",
        "pdf_filename": "Lecture-05-Errors and Exception.pdf",
        "verified_page": 21,
        "concept_name": "Prevents abrupt termination or supports graceful recovery",
        "reason": "Slide 9 and Slide 21 contrast unhandled crashes (abrupt execution stop) with graceful recovery where catch blocks allow remaining statements to continue.",
        "learning_priority": "High",
        "practice_activity": "Lecture 05 Slide 20 (Exc2.java): Run division-by-zero with and without try-catch, verifying that handled code resumes execution cleanly.",
        "resource_type": "SLIIT IT2030 Lecture PDF"
    }
}


def get_recommendation_for_concept(concept_name: str, base_api_url: str = "") -> Optional[Dict[str, Any]]:
    """Returns the verified IT2030 lecture recommendation for a specific missing concept."""
    clean_name = concept_name.strip()
    if clean_name in VERIFIED_CONCEPT_LECTURE_MAP:
        info = dict(VERIFIED_CONCEPT_LECTURE_MAP[clean_name])
        filename = info["pdf_filename"]
        page = info["verified_page"]
        
        # Build working URLs
        info["resource_url"] = f"/api/lectures/{filename}#page={page}"
        info["download_url"] = f"/api/lectures/{filename}?download=true"
        info["frontend_view_url"] = f"/lectures/{filename}#page={page}"
        info["resource_title"] = f"{info['lecture_number']}: {info['lecture_title']} (Slide {page})"
        return info
    return None

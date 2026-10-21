import os
import pypdf

materials_dir = os.path.join(os.path.dirname(__file__), "lecture_materials")
files = sorted([f for f in os.listdir(materials_dir) if f.endswith(".pdf")])

print(f"Total PDFs found: {len(files)}")

keywords = [
    "blueprint", "instance of", "class and object",
    "inheritance", "extends", "subclass",
    "override", "overriding", "polymorphism",
    "static", "non-static", "instance variable",
    "exception", "try", "catch", "runtime error"
]

results = {}

for f in files:
    path = os.path.join(materials_dir, f)
    reader = pypdf.PdfReader(path)
    total_pages = len(reader.pages)
    
    # Get title from first page
    first_page_text = reader.pages[0].extract_text()
    first_line = first_page_text.split("\n")[0] if first_page_text else f
    
    print(f"\n=======================================================")
    print(f"FILE: {f} ({total_pages} pages)")
    print(f"First page snippet: {first_page_text[:120].strip()}")
    
    matches = {}
    for page_idx, page in enumerate(reader.pages, start=1):
        txt = (page.extract_text() or "").lower()
        for kw in keywords:
            if kw in txt:
                matches.setdefault(kw, []).append(page_idx)
    
    for kw, p_list in matches.items():
        print(f"  Keyword '{kw}': pages {p_list[:8]}")

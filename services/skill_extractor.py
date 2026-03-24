import re
from difflib import SequenceMatcher

# ------------------ COMMON SKILLS ------------------
COMMON_SKILLS = [
    "Python","Java","C++","JavaScript","HTML","CSS","React","Angular","Vue",
    "Node.js","Express","Django","Flask","SQL","MongoDB","Git","Docker",
    "Kubernetes","AWS","Azure","GCP","REST API","GraphQL","Microservices",
    "Agile","Scrum","Figma","Machine Learning","Deep Learning",
    "Artificial Intelligence","NLP","Computer Vision","Generative AI",
    "TypeScript","React Native","Next.js","Expo","MySQL","PostgreSQL",
    "SQLite","Firebase","Supabase","Prisma","NestJS"
]

# ------------------ STEP 1: SKILL SECTION ------------------
def extract_skills_section(text: str):
    text = text.replace("\n", " ")

    patterns = [
        r"(technical skills.*?)(projects|education|experience|$)",
        r"(skills.*?)(projects|education|experience|$)",
        r"(professional skills.*?)(projects|education|experience|$)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower(), re.IGNORECASE)
        if match:
            return match.group(1)

    return ""

# ------------------ STEP 2: SECTION PARSING ------------------
def extract_section_skills(text: str):
    skills = set()
    section = extract_skills_section(text)

    if not section:
        return []

    pattern = r"([A-Za-z &]+)\s*:\s*(.+)"
    matches = re.findall(pattern, section)

    for _, skill_line in matches:
        parts = re.split(r",|\|", skill_line)

        for p in parts:
            skill = p.strip()
            if 2 < len(skill) < 30:
                skills.add(skill)

    return list(skills)

# ------------------ STEP 3: DYNAMIC EXTRACTION ------------------
def extract_dynamic_skills(text: str):
    patterns = [
        r"stack\s*:\s*(.*)",
        r"technologies\s*:\s*(.*)",
        r"tools\s*:\s*(.*)"
    ]

    found = []

    for pattern in patterns:
        matches = re.findall(pattern, text.lower())

        for match in matches:
            parts = re.split(r",|\|", match)
            for p in parts:
                skill = p.strip()
                if len(skill) > 2:
                    found.append(skill)

    return found

# ------------------ STEP 4: FILTER ------------------
def is_valid_skill(skill: str):
    skill = skill.strip()

    if len(skill) > 30:
        return False

    if re.search(r"\d{4}", skill):
        return False

    if len(skill.split()) > 3:
        return False

    if "http" in skill:
        return False

    junk = ["duration", "role", "features", "project", "recommendations"]
    if any(j in skill.lower() for j in junk):
        return False

    return True

# ------------------ STEP 5: NORMALIZE ------------------
def normalize_skill(skill: str):
    skill = skill.strip().lower()

    mapping = {
        "react.js": "React",
        "reactjs": "React",
        "node": "Node.js",
        "node.js": "Node.js",
        "express.js": "Express",
        "nestjs": "NestJS",
        "nest.js": "NestJS",
        "mongo": "MongoDB",
        "mongodb": "MongoDB",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "sqlite": "SQLite",
        "webrtc": "WebRTC"
    }

    return mapping.get(skill, skill.title())

# ------------------ STEP 6: BASIC NORMALIZATION ------------------
def basic_normalize(skill: str):
    skill = skill.lower().strip()
    skill = skill.replace(".js", "")
    skill = skill.replace("-", " ")
    return skill

# ------------------ STEP 7: SIMILARITY ------------------
def is_similar(a, b, threshold=0.8):
    return SequenceMatcher(None, a, b).ratio() > threshold

# ------------------ STEP 8: DEDUPLICATION ------------------
def deduplicate_skills(skills):
    clusters = []

    for skill in skills:
        norm = basic_normalize(skill)
        found = False

        for cluster in clusters:
            if is_similar(norm, cluster["key"]):
                cluster["items"].append(skill)
                found = True
                break

        if not found:
            clusters.append({"key": norm, "items": [skill]})

    final = []

    for cluster in clusters:
        items = cluster["items"]
        best = max(set(items), key=lambda x: (items.count(x), len(x)))
        final.append(best)

    return final

# ------------------ FINAL FUNCTION ------------------
def extract_skills(text: str):
    text_lower = text.lower()
    skills = []

    # 1. dictionary
    for skill in COMMON_SKILLS:
        if skill.lower() in text_lower:
            skills.append(skill)

    # 2. section + dynamic
    skills += extract_section_skills(text)
    skills += extract_dynamic_skills(text)

    # 3. filter + normalize
    cleaned = []
    for skill in skills:
        if is_valid_skill(skill):
            cleaned.append(normalize_skill(skill))

    # 4. deduplicate (🔥 IMPORTANT)
    final = deduplicate_skills(cleaned)

    return sorted(set(final))
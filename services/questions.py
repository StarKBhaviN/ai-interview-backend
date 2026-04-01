import random

class QuestionBank:
    def __init__(self):
        self.categories = {
            "Behavioral": [
                {"text": "Tell me about yourself and your background.", "difficulty": "Easy", "tags": ["intro"]},
                {"text": "Why are you interested in this position?", "difficulty": "Easy", "tags": ["interest"]},
                {"text": "Describe a major challenge you faced at work and how you handled it.", "difficulty": "Medium", "tags": ["problem-solving"]},
                {"text": "Where do you see yourself in five years?", "difficulty": "Easy", "tags": ["goals"]},
                {"text": "Tell me about a time you worked in a team to achieve a goal.", "difficulty": "Medium", "tags": ["teamwork"]}
            ],
            "Situational": [
                {"text": "How would you handle a conflict with a close colleague?", "difficulty": "Medium", "tags": ["conflict"]},
                {"text": "If you were assigned a task with an impossible deadline, what would you do?", "difficulty": "Hard", "tags": ["pressure"]},
                {"text": "Describe a situation where you had to explain a complex topic to a non-technical person.", "difficulty": "Medium", "tags": ["communication"]}
            ],
            "Technical": {
                "react": [
                    {"text": "What are React Hooks and how do they change how we write components?", "difficulty": "Medium", "tags": ["react", "hooks"]},
                    {"text": "Explain the Virtual DOM and its benefits.", "difficulty": "Medium", "tags": ["react", "performance"]},
                    {"text": "How do you manage global state in a large React application?", "difficulty": "Hard", "tags": ["react", "state"]}
                ],
                "python": [
                    {"text": "What is the difference between a list and a tuple in Python?", "difficulty": "Easy", "tags": ["python", "basics"]},
                    {"text": "Explain decorators in Python and provide a use case.", "difficulty": "Medium", "tags": ["python", "advanced"]},
                    {"text": "How does memory management work in Python?", "difficulty": "Hard", "tags": ["python", "internals"]}
                ],
                "javascript": [
                    {"text": "Explain closures in JavaScript.", "difficulty": "Medium", "tags": ["javascript", "scope"]},
                    {"text": "What is the difference between '==' and '==='?", "difficulty": "Easy", "tags": ["javascript", "basics"]},
                    {"text": "How does the event loop work in Node.js/JavaScript?", "difficulty": "Hard", "tags": ["javascript", "async"]}
                ],
                "database": [
                    {"text": "Explain the difference between SQL and NoSQL databases.", "difficulty": "Medium", "tags": ["db", "theory"]},
                    {"text": "What is normalization and why is it important?", "difficulty": "Medium", "tags": ["db", "design"]},
                    {"text": "How do indexes improve query performance?", "difficulty": "Hard", "tags": ["db", "performance"]}
                ],
                "general": [
                    {"text": "What is a REST API and what are its key constraints?", "difficulty": "Medium", "tags": ["api", "web"]},
                    {"text": "Explain the concept of Git version control.", "difficulty": "Easy", "tags": ["git", "tools"]},
                    {"text": "What are the SOLID principles in object-oriented design?", "difficulty": "Hard", "tags": ["design", "patterns"]}
                ]
            }
        }

    def generate_session(self, skills: list, position: str):
        session_questions = []
        
        # 1. Start with an Intro (Behavioral)
        intro = random.choice(self.categories["Behavioral"][:2])
        session_questions.append(self._format(intro, "1"))

        # 2. Add 3 Technical Questions based on skills
        tech_pool = []
        lower_skills = [s.lower() for s in skills]
        
        for skill, qs in self.categories["Technical"].items():
            if skill in lower_skills or any(skill in s for s in lower_skills):
                tech_pool.extend(qs)
        
        # Fallback to general tech if no matches
        if len(tech_pool) < 3:
            tech_pool.extend(self.categories["Technical"]["general"])
            
        selected_tech = random.sample(tech_pool, min(3, len(tech_pool)))
        for i, q in enumerate(selected_tech):
            session_questions.append(self._format(q, str(i + 2)))

        # 3. Add 1 Situational Question
        situational = random.choice(self.categories["Situational"])
        session_questions.append(self._format(situational, str(len(session_questions) + 1)))

        # 4. Add a Closing Question
        session_questions.append({
            "id": str(len(session_questions) + 1),
            "text": f"That concludes our technical questions for the {position} role. Do you have any questions for us or anything else you'd like to highlight?",
            "category": "Closing",
            "difficulty": "Easy",
            "tags": ["closing"],
            "keywords": ["questions", "closing"]
        })

        return session_questions

    def _format(self, q, q_id):
        return {
            "id": q_id,
            "text": q["text"],
            "category": next((cat for cat, content in self.categories.items() if (isinstance(content, list) and q in content) or (isinstance(content, dict) and any(q in sublist for sublist in content.values()))), "General"),
            "difficulty": q["difficulty"],
            "tags": q["tags"],
            "keywords": q["tags"] # Using tags as keywords for relevance
        }

question_bank = QuestionBank()

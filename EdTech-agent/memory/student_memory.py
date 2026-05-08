import json
import os
from config import DATA_FILE


class StudentMemory:
    """
    Handles persistent student profiles stored in a JSON file.
    Tracks name, grade, weak topics, and completed lessons.
    """

    def __init__(self):
        self._ensure_data_file()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)

    def _load(self) -> dict:
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_student(self, student_id: str) -> dict | None:
        """Retrieve a student profile by ID."""
        return self._load().get(student_id)

    def create_student(self, student_id: str, name: str, grade: int) -> dict:
        """Create a new student profile."""
        data = self._load()
        if student_id in data:
            return data[student_id]
        profile = {
            "name": name,
            "grade": grade,
            "weak_topics": [],
            "completed_lessons": [],
            "study_plans": [],
            "gamification": {
                "points": 0,
                "badges": [],
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity": None
            },
            "analytics": {
                "quizzes_taken": 0,
                "average_score": 0,
                "total_questions": 0,
                "correct_answers": 0,
                "time_spent_minutes": 0,
                "subjects_practiced": []
            }
        }
        data[student_id] = profile
        self._save(data)
        return profile

    def add_weak_topic(self, student_id: str, topic: str):
        """Add a topic to the student's weak areas (avoids duplicates)."""
        data = self._load()
        if student_id not in data:
            return
        topic = topic.lower().strip()
        if topic not in data[student_id]["weak_topics"]:
            data[student_id]["weak_topics"].append(topic)
            self._save(data)

    def mark_lesson_complete(self, student_id: str, lesson: str):
        """Mark a lesson as completed for the student."""
        data = self._load()
        if student_id not in data:
            return
        if lesson not in data[student_id]["completed_lessons"]:
            data[student_id]["completed_lessons"].append(lesson)
            self._save(data)

    def remove_weak_topic(self, student_id: str, topic: str):
        """Remove a topic from weak areas once mastered."""
        data = self._load()
        if student_id not in data:
            return
        data[student_id]["weak_topics"] = [
            t for t in data[student_id]["weak_topics"] if t != topic.lower().strip()
        ]
        self._save(data)

    def get_all_students(self) -> dict:
        """Return all student profiles."""
        return self._load()

    def add_study_plan(self, student_id: str, plan: dict):
        """Add a study plan for the student."""
        data = self._load()
        if student_id not in data:
            return
        data[student_id]["study_plans"].append(plan)
        self._save(data)

    def get_study_plans(self, student_id: str) -> list:
        """Get all study plans for a student."""
        profile = self.get_student(student_id)
        return profile.get("study_plans", []) if profile else []

    def update_gamification(self, student_id: str, points_earned: int = 0, badge: str = None, activity: bool = True):
        """Update gamification data for a student."""
        data = self._load()
        if student_id not in data:
            return
        gf = data[student_id]["gamification"]

        # Add points
        gf["points"] += points_earned

        # Add badge if provided
        if badge and badge not in gf["badges"]:
            gf["badges"].append(badge)

        # Update streak
        import datetime
        now = datetime.datetime.now().isoformat()
        if activity:
            gf["last_activity"] = now
            gf["current_streak"] += 1
            if gf["current_streak"] > gf["longest_streak"]:
                gf["longest_streak"] = gf["current_streak"]
        else:
            # Reset streak if no activity for a day
            gf["current_streak"] = 0

        self._save(data)

    def update_analytics(self, student_id: str, quiz_score: float = None, questions_count: int = 0, correct_count: int = 0, time_spent: int = 0, subject: str = None):
        """Update analytics data for a student."""
        data = self._load()
        if student_id not in data:
            return
        an = data[student_id]["analytics"]

        if quiz_score is not None:
            an["quizzes_taken"] += 1
            # Recalculate average score
            total_score = an["average_score"] * (an["quizzes_taken"] - 1) + quiz_score
            an["average_score"] = total_score / an["quizzes_taken"]

        an["total_questions"] += questions_count
        an["correct_answers"] += correct_count
        an["time_spent_minutes"] += time_spent

        if subject and subject not in an["subjects_practiced"]:
            an["subjects_practiced"].append(subject)

        self._save(data)

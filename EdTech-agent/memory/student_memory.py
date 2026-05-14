import hashlib
import json
import os
import secrets
from config import DATA_FILE


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 with a random salt."""
    salt = secrets.token_bytes(16)
    iters = 200_000
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iters)
    return f"pbkdf2_sha256${iters}${salt.hex()}${dk.hex()}"


def verify_password(stored: str, password: str) -> bool:
    """Constant-time verify a password against a stored hash."""
    if not stored or not password:
        return False
    try:
        algo, iters_s, salt_hex, hash_hex = stored.split('$')
        if algo != 'pbkdf2_sha256':
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(iters_s))
        return secrets.compare_digest(expected, actual)
    except Exception:
        return False


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

    def set_email(self, student_id: str, email: str):
        """Attach / update the email on a student profile."""
        data = self._load()
        if student_id not in data:
            return
        data[student_id]["email"] = email
        self._save(data)

    def set_password(self, student_id: str, password: str):
        """Hash and store a password for a student."""
        data = self._load()
        if student_id not in data:
            return
        data[student_id]["password_hash"] = hash_password(password)
        self._save(data)

    def verify_credentials(self, student_id: str, password: str) -> bool:
        """Return True if the given password matches the stored hash."""
        profile = self.get_student(student_id)
        if not profile:
            return False
        return verify_password(profile.get("password_hash", ""), password)

    def find_id_by_email(self, email: str) -> str | None:
        """Look up a student id by email (case-insensitive)."""
        if not email:
            return None
        e = email.strip().lower()
        for sid, p in self._load().items():
            if sid.lower() == e:
                return sid
            if (p.get("email") or "").lower() == e:
                return sid
        return None

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

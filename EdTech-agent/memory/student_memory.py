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
            "completed_lessons": []
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

"""
Postgres-backed student memory.

Public API matches the previous JSON-backed implementation so the rest of the
app does not need to change.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import secrets
from typing import Any

from db import execute, fetch, fetchrow


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iters = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
    return f"pbkdf2_sha256${iters}${salt.hex()}${dk.hex()}"


def verify_password(stored: str, password: str) -> bool:
    if not stored or not password:
        return False
    try:
        algo, iters_s, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iters_s))
        return secrets.compare_digest(expected, actual)
    except Exception:
        return False


# ── Row → dict helpers ─────────────────────────────────────────────────────────

def _row_to_profile(row: dict | None) -> dict | None:
    if not row:
        return None
    p = dict(row)
    p["weak_topics"] = p.get("weak_topics") or []
    p["completed_lessons"] = p.get("completed_lessons") or []
    p["gamification"] = p.get("gamification") or {}
    p["analytics"] = p.get("analytics") or {}
    p["study_plans"] = []
    p.pop("created_at", None)
    return p


# ── Public API ─────────────────────────────────────────────────────────────────

class StudentMemory:
    """Postgres-backed implementation of the student profile store."""

    # ------- read -------

    def get_student(self, student_id: str) -> dict | None:
        row = fetchrow(
            "select id, email, name, grade, password_hash, weak_topics, "
            "completed_lessons, gamification, analytics from students where id = %s",
            (student_id,),
        )
        return _row_to_profile(row)

    def get_all_students(self) -> dict:
        rows = fetch(
            "select id, email, name, grade, password_hash, weak_topics, "
            "completed_lessons, gamification, analytics from students order by created_at"
        )
        return {r["id"]: _row_to_profile(r) for r in rows}

    def find_id_by_email(self, email: str) -> str | None:
        if not email:
            return None
        row = fetchrow(
            "select id from students where lower(email) = lower(%s) or lower(id) = lower(%s) limit 1",
            (email, email),
        )
        return row["id"] if row else None

    # ------- create / update -------

    def create_student(self, student_id: str, name: str, grade: int) -> dict:
        existing = self.get_student(student_id)
        if existing:
            return existing
        execute(
            "insert into students (id, name, grade) values (%s, %s, %s)",
            (student_id, name, grade),
        )
        return self.get_student(student_id) or {}

    def set_email(self, student_id: str, email: str) -> None:
        execute("update students set email = %s where id = %s", (email, student_id))

    def set_password(self, student_id: str, password: str) -> None:
        execute(
            "update students set password_hash = %s where id = %s",
            (hash_password(password), student_id),
        )

    def verify_credentials(self, student_id: str, password: str) -> bool:
        row = fetchrow(
            "select password_hash from students where id = %s",
            (student_id,),
        )
        return bool(row) and verify_password(row.get("password_hash") or "", password)

    # ------- weak topics / lessons -------

    def add_weak_topic(self, student_id: str, topic: str) -> None:
        topic = (topic or "").lower().strip()
        if not topic:
            return
        execute(
            """
            update students
               set weak_topics = (
                   select coalesce(array_agg(distinct t), '{}')
                   from unnest(weak_topics || array[%s]) as t
               )
             where id = %s
            """,
            (topic, student_id),
        )

    def remove_weak_topic(self, student_id: str, topic: str) -> None:
        topic = (topic or "").lower().strip()
        execute(
            "update students set weak_topics = array_remove(weak_topics, %s) where id = %s",
            (topic, student_id),
        )

    def mark_lesson_complete(self, student_id: str, lesson: str) -> None:
        if not lesson:
            return
        execute(
            """
            update students
               set completed_lessons = (
                   select coalesce(array_agg(distinct t), '{}')
                   from unnest(completed_lessons || array[%s]) as t
               )
             where id = %s
            """,
            (lesson, student_id),
        )

    # ------- gamification -------

    def update_gamification(
        self,
        student_id: str,
        points_earned: int = 0,
        badge: str | None = None,
        activity: bool = True,
    ) -> None:
        profile = self.get_student(student_id)
        if not profile:
            return
        gf = dict(profile.get("gamification") or {})
        gf["points"] = int(gf.get("points") or 0) + int(points_earned)
        if badge:
            badges = list(gf.get("badges") or [])
            if badge not in badges:
                badges.append(badge)
            gf["badges"] = badges
        if activity:
            gf["last_activity"] = datetime.datetime.utcnow().isoformat()
            gf["current_streak"] = int(gf.get("current_streak") or 0) + 1
            if gf["current_streak"] > int(gf.get("longest_streak") or 0):
                gf["longest_streak"] = gf["current_streak"]
        else:
            gf["current_streak"] = 0
        execute(
            "update students set gamification = %s::jsonb where id = %s",
            (json.dumps(gf), student_id),
        )

    # ------- analytics -------

    def update_analytics(
        self,
        student_id: str,
        quiz_score: float | None = None,
        questions_count: int = 0,
        correct_count: int = 0,
        time_spent: int = 0,
        subject: str | None = None,
    ) -> None:
        profile = self.get_student(student_id)
        if not profile:
            return
        an = dict(profile.get("analytics") or {})
        if quiz_score is not None:
            taken = int(an.get("quizzes_taken") or 0)
            avg = float(an.get("average_score") or 0)
            new_taken = taken + 1
            an["quizzes_taken"] = new_taken
            an["average_score"] = (avg * taken + float(quiz_score)) / new_taken
        an["total_questions"] = int(an.get("total_questions") or 0) + int(questions_count)
        an["correct_answers"] = int(an.get("correct_answers") or 0) + int(correct_count)
        an["time_spent_minutes"] = int(an.get("time_spent_minutes") or 0) + int(time_spent)
        if subject:
            subs = list(an.get("subjects_practiced") or [])
            if subject not in subs:
                subs.append(subject)
            an["subjects_practiced"] = subs
        execute(
            "update students set analytics = %s::jsonb where id = %s",
            (json.dumps(an), student_id),
        )

    # ------- study plans -------

    def add_study_plan(self, student_id: str, plan: dict) -> None:
        execute(
            "insert into study_plans (student_id, plan) values (%s, %s::jsonb)",
            (student_id, json.dumps(plan)),
        )

    def get_study_plans(self, student_id: str) -> list[dict]:
        rows = fetch(
            "select plan, created_at from study_plans where student_id = %s order by created_at desc",
            (student_id,),
        )
        return [{"plan": r["plan"], "created_at": r["created_at"].isoformat()} for r in rows]

    # ------- chat history -------

    def add_chat_message(self, student_id: str, role: str, content: str) -> None:
        execute(
            "insert into chat_messages (student_id, role, content) values (%s, %s, %s)",
            (student_id, role, content),
        )

    def get_chat_history(self, student_id: str, limit: int = 50) -> list[dict]:
        rows = fetch(
            "select role, content, created_at from chat_messages "
            "where student_id = %s order by created_at desc limit %s",
            (student_id, limit),
        )
        return [
            {"role": r["role"], "content": r["content"], "created_at": r["created_at"].isoformat()}
            for r in reversed(rows)
        ]

    def clear_chat_history(self, student_id: str) -> None:
        execute("delete from chat_messages where student_id = %s", (student_id,))

    # ------- quiz results -------

    def add_quiz_result(self, student_id: str, **kwargs: Any) -> None:
        execute(
            """
            insert into quiz_results
                (student_id, topic, score_percentage, questions_count, correct_count, time_spent_minutes)
            values (%s, %s, %s, %s, %s, %s)
            """,
            (
                student_id,
                kwargs.get("topic"),
                kwargs.get("score_percentage"),
                kwargs.get("questions_count"),
                kwargs.get("correct_count"),
                kwargs.get("time_spent_minutes"),
            ),
        )

    def get_quiz_results(self, student_id: str, limit: int = 50) -> list[dict]:
        rows = fetch(
            "select topic, score_percentage, questions_count, correct_count, "
            "time_spent_minutes, created_at from quiz_results "
            "where student_id = %s order by created_at desc limit %s",
            (student_id, limit),
        )
        return [
            {
                "topic": r["topic"],
                "score_percentage": r["score_percentage"],
                "questions_count": r["questions_count"],
                "correct_count": r["correct_count"],
                "time_spent_minutes": r["time_spent_minutes"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]

import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "gym_data.json")

class Database:
    def __init__(self):
        if not os.path.exists(DATA_FILE):
            self._save({"students": [], "payments": [], "next_id": 1})
        self.data = self._load()

    def _load(self):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data=None):
        if data is None:
            data = self.data
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_students(self):
        self.data = self._load()
        return self.data.get("students", [])

    def add_student(self, student_data):
        self.data = self._load()
        sid = self.data.get("next_id", 1)
        student_data["id"] = sid
        self.data["students"].append(student_data)
        self.data["next_id"] = sid + 1
        self._save()
        return sid

    def update_student(self, student_id, updated_data):
        self.data = self._load()
        for i, s in enumerate(self.data["students"]):
            if s["id"] == student_id:
                updated_data["id"] = student_id
                self.data["students"][i] = updated_data
                self._save()
                return True
        return False

    def update_schedule(self, student_id, schedule):
        self.data = self._load()
        for s in self.data["students"]:
            if s["id"] == student_id:
                s["schedule"] = schedule
                self._save()
                return True
        return False

    def delete_student(self, student_id):
        self.data = self._load()
        self.data["students"] = [s for s in self.data["students"] if s["id"] != student_id]
        self._save()

    def get_payments(self):
        self.data = self._load()
        return self.data.get("payments", [])

    def add_payment(self, payment_data):
        self.data = self._load()
        if "payments" not in self.data:
            self.data["payments"] = []
        self.data["payments"].append(payment_data)
        self._save()

    def delete_payment(self, index):
        self.data = self._load()
        if 0 <= index < len(self.data.get("payments", [])):
            self.data["payments"].pop(index)
            self._save()

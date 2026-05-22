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

    def get_transactions(self):
        self.data = self._load()
        return self.data.get("transactions", [])

    def add_transaction(self, tx_data):
        self.data = self._load()
        if "transactions" not in self.data:
            self.data["transactions"] = []
        self.data["transactions"].append(tx_data)
        self._save()

    def delete_transaction(self, index):
        self.data = self._load()
        txs = self.data.get("transactions", [])
        if 0 <= index < len(txs):
            txs.pop(index)
            self.data["transactions"] = txs
            self._save()

    def delete_payment(self, index):
        self.data = self._load()
        if 0 <= index < len(self.data.get("payments", [])):
            self.data["payments"].pop(index)
            self._save()

    # ---------- Packages ----------
    def get_packages(self):
        self.data = self._load()
        return self.data.get("packages", [])

    def add_package(self, pkg):
        self.data = self._load()
        if "packages" not in self.data:
            self.data["packages"] = []
        self.data["packages"].append(pkg)
        self._save()

    def update_package(self, index, pkg):
        self.data = self._load()
        if 0 <= index < len(self.data.get("packages",[])):
            self.data["packages"][index] = pkg
            self._save()

    def delete_package(self, index):
        self.data = self._load()
        pkgs = self.data.get("packages",[])
        if 0 <= index < len(pkgs):
            pkgs.pop(index)
            self.data["packages"] = pkgs
            self._save()

    # ---------- Attendance ----------
    def get_attendance(self, student_id):
        self.data = self._load()
        return [a for a in self.data.get("attendance",[])
                if a["student_id"] == student_id]

    def add_attendance(self, student_id, record):
        self.data = self._load()
        if "attendance" not in self.data:
            self.data["attendance"] = []
        self.data["attendance"] = [
            a for a in self.data["attendance"]
            if not (a["student_id"]==student_id and a["date"]==record["date"])
        ]
        self.data["attendance"].append({**record, "student_id": student_id})
        self._save()

    # ---------- Notes ----------
    def get_notes(self, student_id):
        self.data = self._load()
        return [n for n in self.data.get("notes",[])
                if n["student_id"] == student_id]

    def add_note(self, student_id, note):
        self.data = self._load()
        if "notes" not in self.data:
            self.data["notes"] = []
        self.data["notes"].append({**note, "student_id": student_id})
        self._save()


from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import Database
from datetime import date, datetime

app = Flask(__name__)
db = Database()

# ─── STUDENTS ────────────────────────────────────────────
@app.route("/")
def index():
    students = db.get_students()
    payments  = db.get_payments()
    today     = date.today()
    current_month = today.strftime("%Y-%m")

    active  = sum(1 for s in students if s["status"] == "Aktif")
    income  = sum(p["amount"] for p in payments if p.get("month","") == current_month)
    paid_ids = {p["student_id"] for p in payments if p.get("month","") == current_month}
    expiring = sum(1 for s in students if 0 <= _days_left(s.get("end_date","")) <= 30)

    return render_template("index.html",
        students=students, active=active, income=income,
        expiring=expiring, total=len(students),
        days_left=_days_left, paid_ids=paid_ids,
        current_month=current_month)

@app.route("/student/add", methods=["GET","POST"])
def add_student():
    if request.method == "POST":
        db.add_student(_form_to_student(request.form))
        return redirect(url_for("index"))
    return render_template("student_form.html", student=None, title="Yeni Öğrenci")

@app.route("/student/edit/<int:sid>", methods=["GET","POST"])
def edit_student(sid):
    students = db.get_students()
    s = next((x for x in students if x["id"] == sid), None)
    if not s:
        return redirect(url_for("index"))
    if request.method == "POST":
        db.update_student(sid, _form_to_student(request.form))
        return redirect(url_for("index"))
    return render_template("student_form.html", student=s, title="Öğrenciyi Düzenle")

@app.route("/student/delete/<int:sid>", methods=["POST"])
def delete_student(sid):
    db.delete_student(sid)
    return redirect(url_for("index"))

@app.route("/student/schedule/<int:sid>", methods=["GET","POST"])
def edit_schedule(sid):
    students = db.get_students()
    s = next((x for x in students if x["id"] == sid), None)
    if not s:
        return redirect(url_for("index"))
    if request.method == "POST":
        days  = request.form.getlist("days")
        hour  = request.form.get("hour","09:00")
        schedule = "/".join(days) + " " + hour if days else ""
        db.update_schedule(sid, schedule)
        return redirect(url_for("index"))
    return render_template("schedule_form.html", student=s)

# ─── PAYMENTS ─────────────────────────────────────────────
@app.route("/payments")
def payments():
    students = db.get_students()
    pays     = db.get_payments()
    current_month = date.today().strftime("%Y-%m")
    paid_ids = {p["student_id"] for p in pays if p.get("month","") == current_month}

    income  = sum(p["amount"] for p in pays if p.get("month","") == current_month)
    pending = sum(s["monthly_fee"] for s in students
                  if s["status"]=="Aktif" and s["id"] not in paid_ids)

    # enrich payments with student name
    enriched = []
    for i, p in enumerate(pays):
        sname = next((st["name"] for st in students if st["id"]==p["student_id"]), "?")
        enriched.append({**p, "student_name": sname, "idx": i})
    enriched.sort(key=lambda x: x.get("date",""), reverse=True)

    pending_students = [s for s in students
                        if s["status"]=="Aktif" and s["id"] not in paid_ids]

    return render_template("payments.html",
        payments=enriched, income=income, pending=pending,
        pending_students=pending_students,
        total_students=len(students),
        current_month=current_month)

@app.route("/payment/add", methods=["GET","POST"])
def add_payment():
    students = db.get_students()
    if request.method == "POST":
        sid = int(request.form.get("student_id"))
        try:
            amount = float(request.form.get("amount","0"))
        except:
            amount = 0
        db.add_payment({
            "student_id": sid,
            "amount": amount,
            "date": date.today().strftime("%Y-%m-%d"),
            "month": request.form.get("month", date.today().strftime("%Y-%m")),
            "note": request.form.get("note","")
        })
        return redirect(url_for("payments"))
    return render_template("payment_form.html", students=students,
                           current_month=date.today().strftime("%Y-%m"))

@app.route("/payment/quick/<int:sid>", methods=["POST"])
def quick_payment(sid):
    students = db.get_students()
    s = next((x for x in students if x["id"]==sid), None)
    if s:
        db.add_payment({
            "student_id": sid,
            "amount": s["monthly_fee"],
            "date": date.today().strftime("%Y-%m-%d"),
            "month": date.today().strftime("%Y-%m"),
            "note": "Hızlı ödeme"
        })
    return redirect(url_for("payments"))

@app.route("/payment/delete/<int:idx>", methods=["POST"])
def delete_payment(idx):
    db.delete_payment(idx)
    return redirect(url_for("payments"))

# ─── REPORTS ──────────────────────────────────────────────
@app.route("/reports")
def reports():
    students = db.get_students()
    pays     = db.get_payments()

    months_income = {}
    for p in pays:
        m = p.get("month","")
        if m:
            months_income[m] = months_income.get(m,0) + p["amount"]
    months_sorted = sorted(months_income.items())[-6:]
    max_income = max((v for _,v in months_sorted), default=1)

    status_count = {}
    for s in students:
        st = s["status"]
        status_count[st] = status_count.get(st,0)+1

    expiring = sorted(
        [(s, _days_left(s.get("end_date",""))) for s in students
         if 0 <= _days_left(s.get("end_date","")) <= 30],
        key=lambda x: x[1])

    return render_template("reports.html",
        months=months_sorted, max_income=max_income,
        status_count=status_count, expiring=expiring,
        total=len(students))

# ─── HELPERS ──────────────────────────────────────────────
def _days_left(end_date_str):
    if not end_date_str:
        return 999
    try:
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        return (end - date.today()).days
    except:
        return 999

def _form_to_student(form):
    try:
        fee = float(form.get("monthly_fee","0"))
    except:
        fee = 0
    return {
        "name":        form.get("name","").strip(),
        "phone":       form.get("phone","").strip(),
        "email":       form.get("email","").strip(),
        "birth_date":  form.get("birth_date","").strip(),
        "start_date":  form.get("start_date","").strip(),
        "end_date":    form.get("end_date","").strip(),
        "monthly_fee": fee,
        "schedule":    form.get("schedule","").strip(),
        "notes":       form.get("notes","").strip(),
        "status":      form.get("status","Aktif"),
    }

if __name__ == "__main__":
    app.run(debug=True)

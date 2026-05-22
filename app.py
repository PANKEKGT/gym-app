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

@app.route("/student/<int:sid>")
def student_detail(sid):
    students = db.get_students()
    s = next((x for x in students if x["id"] == sid), None)
    if not s:
        return redirect(url_for("index"))

    payments  = [p for p in db.get_payments() if p["student_id"] == sid]
    total_paid = sum(p["amount"] for p in payments)
    current_month = date.today().strftime("%Y-%m")
    paid_this_month = any(p.get("month","") == current_month for p in payments)

    attendance = db.get_attendance(sid)
    total_att  = len(attendance)
    came       = sum(1 for a in attendance if a["status"] == "geldi")
    rate       = int((came / total_att * 100) if total_att > 0 else 0)

    notes      = db.get_notes(sid)
    days_left  = _days_left(s.get("end_date",""))

    return render_template("student_detail.html",
        student=s, payments=payments, total_paid=total_paid,
        paid_this_month=paid_this_month, attendance=attendance,
        attendance_rate=rate, notes=notes, days_left=days_left,
        today=date.today().strftime("%Y-%m-%d"))

@app.route("/student/note/<int:sid>", methods=["GET","POST"])
def add_note(sid):
    students = db.get_students()
    s = next((x for x in students if x["id"] == sid), None)
    if not s:
        return redirect(url_for("index"))
    if request.method == "POST":
        db.add_note(sid, {
            "date": date.today().strftime("%Y-%m-%d"),
            "text": request.form.get("text","").strip()
        })
        return redirect(url_for("student_detail", sid=sid))
    return render_template("note_form.html", student=s)

@app.route("/student/<int:sid>/attendance", methods=["POST"])
def mark_attendance(sid):
    att_date   = request.form.get("date", date.today().strftime("%Y-%m-%d"))
    att_action = request.form.get("action","geldi")
    db.add_attendance(sid, {"date": att_date, "status": att_action})
    return redirect(url_for("student_detail", sid=sid))

@app.route("/receipt/<int:sid>")
def receipt(sid):
    students = db.get_students()
    s = next((x for x in students if x["id"] == sid), None)
    if not s:
        return redirect(url_for("index"))
    payments = sorted(
        [p for p in db.get_payments() if p["student_id"] == sid],
        key=lambda x: x.get("date",""), reverse=True)
    last = payments[:3]
    total = sum(p["amount"] for p in last)
    receipt_no = f"{sid:04d}{date.today().strftime('%Y%m')}"
    return render_template("receipt.html",
        student=s, last_payments=last, total=total,
        receipt_no=receipt_no, today=date.today().strftime("%Y-%m-%d"))

# ─── PACKAGES ─────────────────────────────────────────────
@app.route("/packages")
def packages():
    pkgs     = db.get_packages()
    students = db.get_students()
    for pkg in pkgs:
        pkg["member_count"] = sum(1 for s in students if s.get("package") == pkg["name"])
    return render_template("packages.html", packages=pkgs, students=students)

@app.route("/packages/add", methods=["GET","POST"])
def add_package():
    if request.method == "POST":
        try: price = float(request.form.get("price","0"))
        except: price = 0
        try: days = int(request.form.get("duration_days","30"))
        except: days = 30
        db.add_package({
            "name":         request.form.get("name","").strip(),
            "price":        price,
            "duration_days":days,
            "color":        request.form.get("color","#2563eb"),
            "description":  request.form.get("description","").strip(),
        })
        return redirect(url_for("packages"))
    return render_template("package_form.html", pkg=None, title="Yeni Paket")

@app.route("/packages/edit/<int:idx>", methods=["GET","POST"])
def edit_package(idx):
    pkgs = db.get_packages()
    if idx >= len(pkgs):
        return redirect(url_for("packages"))
    pkg = pkgs[idx]
    if request.method == "POST":
        try: price = float(request.form.get("price","0"))
        except: price = 0
        try: days = int(request.form.get("duration_days","30"))
        except: days = 30
        db.update_package(idx, {
            "name":         request.form.get("name","").strip(),
            "price":        price,
            "duration_days":days,
            "color":        request.form.get("color","#2563eb"),
            "description":  request.form.get("description","").strip(),
        })
        return redirect(url_for("packages"))
    return render_template("package_form.html", pkg=pkg, title="Paketi Düzenle")

@app.route("/packages/delete/<int:idx>", methods=["POST"])
def delete_package(idx):
    db.delete_package(idx)
    return redirect(url_for("packages"))

@app.route("/packages/assign/<int:sid>", methods=["POST"])
def assign_package(sid):
    pkg_name = request.form.get("package","")
    students = db.get_students()
    s = next((x for x in students if x["id"] == sid), None)
    if s:
        s["package"] = pkg_name
        db.update_student(sid, s)
    return redirect(url_for("packages"))


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

# ─── FINANCE ──────────────────────────────────────────────
@app.route("/finance")
def finance():
    year = int(request.args.get("year", date.today().year))
    transactions = db.get_transactions()
    current_month = date.today().strftime("%Y-%m")

    month_names = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
                   "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]

    # Filter by year, add idx
    year_txs = []
    for i, tx in enumerate(transactions):
        if tx.get("date","").startswith(str(year)):
            year_txs.append({**tx, "idx": i})

    # Monthly summary
    monthly_summary = []
    for m in range(1, 13):
        month_str = f"{year}-{m:02d}"
        inc = sum(t["amount"] for t in year_txs
                  if t.get("date","").startswith(month_str) and t["type"]=="gelir")
        exp = sum(t["amount"] for t in year_txs
                  if t.get("date","").startswith(month_str) and t["type"]=="gider")
        monthly_summary.append({
            "month": month_str,
            "month_name": month_names[m-1],
            "income": inc, "expense": exp, "profit": inc - exp
        })

    yearly_income  = sum(r["income"]  for r in monthly_summary)
    yearly_expense = sum(r["expense"] for r in monthly_summary)
    yearly_profit  = yearly_income - yearly_expense

    cm_data = next((r for r in monthly_summary if r["month"]==current_month), {})
    this_month_income  = cm_data.get("income",0)
    this_month_expense = cm_data.get("expense",0)
    this_month_profit  = this_month_income - this_month_expense

    categories = sorted({tx["category"] for tx in year_txs if tx.get("category")})
    txs_sorted = sorted(year_txs, key=lambda x: x.get("date",""), reverse=True)

    # Also include member payments as income transactions
    payments = db.get_payments()
    students = db.get_students()
    pay_txs = []
    for i, p in enumerate(payments):
        if p.get("date","").startswith(str(year)):
            sname = next((s["name"] for s in students if s["id"]==p["student_id"]), "?")
            pay_txs.append({
                "idx": f"pay_{i}", "date": p.get("date",""),
                "type": "gelir", "category": "Üyelik Geliri",
                "description": f"{sname} — {p.get('month','')} {p.get('note','')}",
                "amount": p["amount"]
            })

    all_txs = sorted(txs_sorted + pay_txs, key=lambda x: x.get("date",""), reverse=True)
    all_cats = sorted({tx["category"] for tx in all_txs if tx.get("category")})

    # Recalculate yearly with payments
    pay_income = sum(p["amount"] for p in payments if p.get("date","").startswith(str(year)))
    yearly_income_total  = yearly_income + pay_income
    yearly_profit_total  = yearly_income_total - yearly_expense

    pay_this_month = sum(p["amount"] for p in payments if p.get("date","").startswith(current_month))
    this_month_income_total = this_month_income + pay_this_month
    this_month_profit_total = this_month_income_total - this_month_expense

    # Update monthly summary with payment income
    for row in monthly_summary:
        m_pay = sum(p["amount"] for p in payments if p.get("date","").startswith(row["month"]))
        row["income"]  += m_pay
        row["profit"]   = row["income"] - row["expense"]

    return render_template("finance.html",
        year=year, monthly_summary=monthly_summary,
        yearly_income=sum(r["income"] for r in monthly_summary),
        yearly_expense=yearly_expense,
        yearly_profit=sum(r["income"] for r in monthly_summary) - yearly_expense,
        this_month_income=this_month_income_total,
        this_month_expense=this_month_expense,
        this_month_profit=this_month_profit_total,
        transactions=all_txs, categories=all_cats)

@app.route("/finance/add", methods=["GET","POST"])
def add_transaction():
    year = int(request.args.get("year", date.today().year))
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount","0"))
        except:
            amount = 0
        db.add_transaction({
            "date":        request.form.get("date", date.today().strftime("%Y-%m-%d")),
            "type":        request.form.get("type","gelir"),
            "category":    request.form.get("category",""),
            "description": request.form.get("description",""),
            "amount":      amount,
        })
        return redirect(url_for("finance", year=request.form.get("year", year)))
    return render_template("finance_form.html",
        year=year, today=date.today().strftime("%Y-%m-%d"))

@app.route("/finance/delete/<path:idx>", methods=["POST"])
def delete_transaction(idx):
    year = request.args.get("year", date.today().year)
    if not str(idx).startswith("pay_"):
        db.delete_transaction(int(idx))
    return redirect(url_for("finance", year=year))

# ─── SCHEDULE ─────────────────────────────────────────────
@app.route("/schedule")
def schedule():
    students = db.get_students()
    days     = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]
    abbr_map = {"pzt":"Pazartesi","sal":"Salı","çar":"Çarşamba",
                "per":"Perşembe","cum":"Cuma","cmt":"Cumartesi","paz":"Pazar"}
    hours    = [f"{h:02d}:00" for h in range(6, 23)]

    grid = {d: {h: [] for h in hours} for d in days}

    for s in students:
        sch = s.get("schedule","") or ""
        parts = sch.replace(","," ").split()
        found_days, found_time = [], None
        for p in parts:
            for sub in p.split("/"):
                sl = sub.lower()
                if sl in abbr_map:
                    found_days.append(abbr_map[sl])
            if ":" in p and p in hours:
                found_time = p
        if found_time:
            first = s["name"].split()[0]
            for d in found_days:
                if d in grid and found_time in grid[d]:
                    grid[d][found_time].append(first)

    return render_template("schedule.html",
        students=students, days=days, hours=hours, schedule_grid=grid)

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
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

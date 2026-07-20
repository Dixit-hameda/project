import os
import sqlite3
from datetime import datetime
from io import BytesIO

import qrcode
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["DATABASE"] = os.path.join(app.instance_path, "safety.db")
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")


def get_db():
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                badge_id TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                zone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_name TEXT NOT NULL,
                zone TEXT NOT NULL,
                ppe_checked INTEGER NOT NULL,
                tools_inspected INTEGER NOT NULL,
                lockout_verified INTEGER NOT NULL,
                panels_secured INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hazards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter TEXT NOT NULL,
                zone TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                image TEXT,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL
            );
            """
        )

        if db.execute("SELECT COUNT(*) FROM workers").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO workers (name, badge_id, role, zone) VALUES (?, ?, ?, ?)",
                [
                    ("Aarav Mehta", "ES-1042", "Electrician", "Panel Room A"),
                    ("Priya Nair", "ES-2210", "Safety Officer", "Substation Bay"),
                    ("Kabir Singh", "ES-3308", "Maintenance Lead", "Generator Yard"),
                ],
            )


@app.before_request
def prepare_database():
    init_db()


def dashboard_stats():
    with get_db() as db:
        checklist_count = db.execute("SELECT COUNT(*) FROM checklists").fetchone()[0]
        hazard_count = db.execute("SELECT COUNT(*) FROM hazards").fetchone()[0]
        open_hazards = db.execute("SELECT COUNT(*) FROM hazards WHERE status='Open'").fetchone()[0]
        workers = db.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
    compliance = 100 if checklist_count else 0
    return {
        "checklists": checklist_count,
        "hazards": hazard_count,
        "open_hazards": open_hazards,
        "workers": workers,
        "compliance": compliance,
    }


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/worker-login", methods=["GET", "POST"])
def worker_login():
    if request.method == "POST":
        badge_id = request.form["badge_id"].strip()
        with get_db() as db:
            worker = db.execute("SELECT * FROM workers WHERE badge_id = ?", (badge_id,)).fetchone()
        if worker:
            flash(f"Welcome, {worker['name']}. Complete today's safety check.", "success")
            return redirect(url_for("checklist", worker=worker["name"], zone=worker["zone"]))
        flash("Badge not recognised. Try ES-1042 for the demo.", "danger")
    return render_template("worker_login.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            flash("Admin access granted.", "success")
            return redirect(url_for("dashboard"))
        flash("Use admin / admin123 for this prototype.", "danger")
    return render_template("admin_login.html")


@app.route("/checklist", methods=["GET", "POST"])
def checklist():
    if request.method == "POST":
        fields = request.form
        with get_db() as db:
            db.execute(
                """
                INSERT INTO checklists
                (worker_name, zone, ppe_checked, tools_inspected, lockout_verified, panels_secured, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fields["worker_name"],
                    fields["zone"],
                    int("ppe_checked" in fields),
                    int("tools_inspected" in fields),
                    int("lockout_verified" in fields),
                    int("panels_secured" in fields),
                    fields.get("notes", ""),
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
        flash("Daily safety checklist submitted.", "success")
        return redirect(url_for("dashboard"))
    return render_template("checklist.html", worker=request.args.get("worker", ""), zone=request.args.get("zone", ""))


@app.route("/hazard-report", methods=["GET", "POST"])
def hazard_report():
    if request.method == "POST":
        image_name = None
        image = request.files.get("image")
        if image and image.filename:
            image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(image.filename)}"
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        with get_db() as db:
            db.execute(
                """
                INSERT INTO hazards (reporter, zone, severity, description, image, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    request.form["reporter"],
                    request.form["zone"],
                    request.form["severity"],
                    request.form["description"],
                    image_name,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
        flash("Hazard report recorded.", "success")
        return redirect(url_for("dashboard"))
    return render_template("hazard_report.html")


@app.route("/dashboard")
def dashboard():
    with get_db() as db:
        hazards = db.execute("SELECT * FROM hazards ORDER BY id DESC LIMIT 6").fetchall()
        checklists = db.execute("SELECT * FROM checklists ORDER BY id DESC LIMIT 6").fetchall()
    return render_template("dashboard.html", stats=dashboard_stats(), hazards=hazards, checklists=checklists)


@app.route("/analytics")
def analytics():
    with get_db() as db:
        severities = db.execute("SELECT severity, COUNT(*) total FROM hazards GROUP BY severity").fetchall()
        zones = db.execute("SELECT zone, COUNT(*) total FROM checklists GROUP BY zone").fetchall()
    return render_template("analytics.html", stats=dashboard_stats(), severities=severities, zones=zones)


@app.route("/qr-generate")
def qr_generate():
    badge = request.args.get("badge", "ES-1042")
    scan_url = url_for("qr_scan", badge=badge, _external=True)
    image = qrcode.make(scan_url)
    buffer = BytesIO()
    image.save(buffer, "PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png", download_name="worker-qr.png")


@app.route("/qr")
def qr_page():
    return render_template("qr.html", badge=request.args.get("badge", "ES-1042"))


@app.route("/scan")
def qr_scan():
    badge = request.args.get("badge", "")
    return render_template("scan.html", badge=badge)


@app.route("/report.pdf")
def report_pdf():
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Electrical Safety Compliance Report", styles["Title"]), Spacer(1, 16)]

    stats = dashboard_stats()
    rows = [["Metric", "Value"], ["Workers", stats["workers"]], ["Checklists", stats["checklists"]], ["Hazards", stats["hazards"]], ["Open Hazards", stats["open_hazards"]]]
    table = Table(rows, hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f5132")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("PADDING", (0, 0), (-1, -1), 8)]))
    story.append(table)
    story.append(Spacer(1, 16))

    with get_db() as db:
        hazards = db.execute("SELECT zone, severity, status, created_at FROM hazards ORDER BY id DESC LIMIT 10").fetchall()
    hazard_rows = [["Zone", "Severity", "Status", "Created"]] + [list(row) for row in hazards]
    story.append(Paragraph("Recent Hazards", styles["Heading2"]))
    story.append(Table(hazard_rows, hAlign="LEFT"))

    document.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name="electrical-safety-report.pdf")


if __name__ == "__main__":
    app.run(debug=True)

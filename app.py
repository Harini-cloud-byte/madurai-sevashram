from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "sevashram_secret"

UPLOAD = "static/uploads"

# ---------------- DB CONNECTION ----------------
def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- USER PAGES ----------------
@app.route("/")
def home():
    d = db()

    hero_images = d.execute("SELECT image FROM gallery ORDER BY id DESC").fetchall()

    home_data = d.execute("SELECT * FROM home_settings WHERE id=1").fetchone()

    if not home_data:
        home_data = {
            "title": "Madurai Sevashram",
            "description": "Serving Humanity",
            "bgcolor": "#eef5ff",
            "textcolor": "#1e293b"
        }

    d.close()

    return render_template("user/index.html", hero_images=hero_images, home=home_data)


@app.route("/events")
def events():
    d = db()
    data = d.execute("SELECT * FROM events").fetchall()
    d.close()
    return render_template("user/events.html", events=data)


@app.route("/reports")
def reports():
    d = db()
    data = d.execute("SELECT * FROM reports").fetchall()
    d.close()
    return render_template("user/reports.html", reports=data)


@app.route("/gallery")
def gallery():
    d = db()
    data = d.execute("SELECT * FROM gallery").fetchall()
    d.close()
    return render_template("user/gallery.html", images=data)


# ✅ UPDATED CONTACT (PHONE + ADDRESS)
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        d = db()
        d.execute(
            "INSERT INTO feedback (name,email,phone,message) VALUES (?,?,?,?)",
            (
                request.form["name"],
                request.form["email"],
                request.form["phone"],
                request.form["message"]
            )
        )
        d.commit()
        d.close()
        flash("Message Sent Successfully")

    return render_template("user/contact.html")


@app.route("/about")
def about():
    return render_template("user/about.html")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def login():
    TRUST_USERNAME = "maduraisevashram"
    TRUST_PASSWORD_HASH = generate_password_hash("malathy")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == TRUST_USERNAME and check_password_hash(TRUST_PASSWORD_HASH, password):
            session["admin"] = TRUST_USERNAME
            return redirect("/admin/dashboard")

        flash("Invalid Login")

    return render_template("admin/login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- DASHBOARD ----------------
@app.route("/admin/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    d = db()

    event_count = d.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    report_count = d.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    gallery_count = d.execute("SELECT COUNT(*) FROM gallery").fetchone()[0]
    feedback_count = d.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]

    yearly = d.execute("""
        SELECT substr(datetime,1,4) AS year, COUNT(*) as total
        FROM events
        GROUP BY year
        ORDER BY year
    """).fetchall()

    years = [row["year"] for row in yearly]
    yearly_event_counts = [row["total"] for row in yearly]

    # ✅ FIX: home data
    home_data = d.execute("SELECT * FROM home_settings WHERE id=1").fetchone()

    if not home_data:
        home_data = {
            "title": "Madurai Sevashram",
            "description": "Serving Humanity",
            "bgcolor": "#eef5ff",
            "textcolor": "#1e293b"
        }

    d.close()

    return render_template(
        "admin/dashboard.html",
        event_count=event_count,
        report_count=report_count,
        gallery_count=gallery_count,
        feedback_count=feedback_count,
        years=years,
        yearly_event_counts=yearly_event_counts,
        home=home_data
    )


# ---------------- UPDATE HOME ----------------
@app.route("/admin/update-home", methods=["POST"])
def update_home():
    if "admin" not in session:
        return redirect("/admin")

    d = db()

    d.execute("""
        UPDATE home_settings
        SET title=?, description=?, bgcolor=?, textcolor=?
        WHERE id=1
    """, (
        request.form["title"],
        request.form["description"],
        request.form["bgcolor"],
        request.form["textcolor"]
    ))

    d.commit()
    d.close()

    flash("Home Page Updated Successfully ✅")
    return redirect("/admin/dashboard")


# ---------------- EVENTS CRUD (UPDATED STRUCTURE) ----------------
@app.route("/admin/events")
def manage_events():
    d = db()
    e = d.execute("SELECT * FROM events").fetchall()
    d.close()
    return render_template("admin/manage_events.html", events=e)


@app.route("/admin/add-event", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":
        files = request.files.getlist("images")
        filenames = []

        for f in files:
            if f.filename:
                name = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD, "events", name))
                filenames.append(name)

        images = ",".join(filenames)

        d = db()
        d.execute(
            "INSERT INTO events VALUES(NULL,?,?,?,?,?)",
            (
                request.form["name"],
                request.form["datetime"],
                request.form["location"],
                request.form["description"],
                images
            )
        )
        d.commit()
        d.close()
        return redirect("/admin/events")

    return render_template("admin/add_event.html")


@app.route("/admin/edit-event/<int:id>", methods=["GET", "POST"])
def edit_event(id):
    d = db()
    e = d.execute("SELECT * FROM events WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        files = request.files.getlist("images")
        filenames = []

        for f in files:
            if f.filename:
                name = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD, "events", name))
                filenames.append(name)

        if filenames:
            images = ",".join(filenames)
            d.execute(
                "UPDATE events SET name=?,datetime=?,location=?,description=?,image=? WHERE id=?",
                (
                    request.form["name"],
                    request.form["datetime"],
                    request.form["location"],
                    request.form["description"],
                    images,
                    id
                )
            )
        else:
            d.execute(
                "UPDATE events SET name=?,datetime=?,location=?,description=? WHERE id=?",
                (
                    request.form["name"],
                    request.form["datetime"],
                    request.form["location"],
                    request.form["description"],
                    id
                )
            )

        d.commit()
        return redirect("/admin/events")

    return render_template("admin/edit_event.html", e=e)


@app.route("/admin/delete-event/<int:id>")
def delete_event(id):
    d = db()
    e = d.execute("SELECT * FROM events WHERE id=?", (id,)).fetchone()

    if e and e["image"]:
        for img in e["image"].split(","):
            path = os.path.join(UPLOAD, "events", img)
            if os.path.exists(path):
                os.remove(path)

    d.execute("DELETE FROM events WHERE id=?", (id,))
    d.commit()
    return redirect("/admin/events")


# ---------------- REPORTS CRUD ----------------
@app.route("/admin/reports")
def manage_reports():
    d = db()
    r = d.execute("SELECT * FROM reports").fetchall()
    d.close()
    return render_template("admin/manage_reports.html", reports=r)


@app.route("/admin/add-report", methods=["GET", "POST"])
def add_report():
    if request.method == "POST":
        files = request.files.getlist("files")
        filenames = []

        for f in files:
            if f.filename:
                name = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD, "reports", name))
                filenames.append(name)

        filedata = ",".join(filenames)

        d = db()
        d.execute(
            "INSERT INTO reports VALUES(NULL,?,?)",
            (request.form["year"], filedata)
        )
        d.commit()
        d.close()
        return redirect("/admin/reports")

    return render_template("admin/add_report.html")


@app.route("/admin/edit-report/<int:id>", methods=["GET", "POST"])
def edit_report(id):
    d = db()
    r = d.execute("SELECT * FROM reports WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        files = request.files.getlist("files")
        filenames = []

        for f in files:
            if f.filename:
                name = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD, "reports", name))
                filenames.append(name)

        if filenames:
            filedata = ",".join(filenames)
            d.execute(
                "UPDATE reports SET year=?,file=? WHERE id=?",
                (request.form["year"], filedata, id)
            )
        else:
            d.execute(
                "UPDATE reports SET year=? WHERE id=?",
                (request.form["year"], id)
            )

        d.commit()
        return redirect("/admin/reports")

    return render_template("admin/edit_report.html", r=r)


@app.route("/admin/delete-report/<int:id>")
def delete_report(id):
    d = db()
    r = d.execute("SELECT * FROM reports WHERE id=?", (id,)).fetchone()

    if r and r["file"]:
        for f in r["file"].split(","):
            path = os.path.join(UPLOAD, "reports", f)
            if os.path.exists(path):
                os.remove(path)

    d.execute("DELETE FROM reports WHERE id=?", (id,))
    d.commit()
    return redirect("/admin/reports")


# ---------------- GALLERY CRUD ----------------
@app.route("/admin/gallery")
def manage_gallery():
    d = db()
    g = d.execute("SELECT * FROM gallery").fetchall()
    d.close()
    return render_template("admin/manage_gallery.html", images=g)


@app.route("/admin/add-gallery", methods=["GET", "POST"])
def add_gallery():
    if request.method == "POST":
        files = request.files.getlist("images")
        filenames = []

        for f in files:
            if f.filename:
                name = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD, "gallery", name))
                filenames.append(name)

        if filenames:
            images = ",".join(filenames)
            d = db()
            d.execute(
                "INSERT INTO gallery VALUES(NULL,?,?)",
                (images, request.form["category"])
            )
            d.commit()
            d.close()
            flash("Gallery Images Added Successfully")
            return redirect("/admin/gallery")

        flash("No files selected")
        return redirect("/admin/add-gallery")

    return render_template("admin/add_gallery.html")


@app.route("/admin/edit-gallery/<int:id>", methods=["GET", "POST"])
def edit_gallery(id):
    d = db()
    g = d.execute("SELECT * FROM gallery WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        files = request.files.getlist("images")
        filenames = []

        for f in files:
            if f.filename:
                name = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD, "gallery", name))
                filenames.append(name)

        if filenames:
            images = ",".join(filenames)
            d.execute(
                "UPDATE gallery SET category=?,image=? WHERE id=?",
                (request.form["category"], images, id)
            )
        else:
            d.execute(
                "UPDATE gallery SET category=? WHERE id=?",
                (request.form["category"], id)
            )

        d.commit()
        flash("Gallery Updated Successfully")
        return redirect("/admin/gallery")

    return render_template("admin/edit_gallery.html", g=g)


@app.route("/admin/delete-gallery/<int:id>")
def delete_gallery(id):
    d = db()
    g = d.execute("SELECT * FROM gallery WHERE id=?", (id,)).fetchone()

    if g and g["image"]:
        for img in g["image"].split(","):
            path = os.path.join(UPLOAD, "gallery", img)
            if os.path.exists(path):
                os.remove(path)

    d.execute("DELETE FROM gallery WHERE id=?", (id,))
    d.commit()
    flash("Gallery Deleted Successfully")
    return redirect("/admin/gallery")


# ---------------- FEEDBACK ----------------
@app.route("/admin/feedback")
def feedback():
    d = db()
    f = d.execute("SELECT * FROM feedback").fetchall()
    d.close()
    return render_template("admin/feedback.html", messages=f)


# ✅ DELETE FEEDBACK
@app.route("/admin/delete-feedback/<int:id>", methods=["POST"])
def delete_feedback(id):
    d = db()
    d.execute("DELETE FROM feedback WHERE id=?", (id,))
    d.commit()
    d.close()
    flash("Feedback deleted successfully")
    return redirect("/admin/feedback")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template_string, request, redirect, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secreto"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- BASE DE DATOS ----------------

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            archivo TEXT,
            fecha TEXT,
            estado TEXT,
            usuario TEXT
        )
    ''')

    # Usuario inicial
    user = conn.execute("SELECT * FROM users WHERE username='admin'").fetchone()
    if not user:
        conn.execute("INSERT INTO users (username, password, role) VALUES ('admin','1234','admin')")
        conn.execute("INSERT INTO users (username, password, role) VALUES ('impresor','1234','impresor')")
    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        u = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (user, password)).fetchone()
        conn.close()

        if u:
            session["user"] = user
            session["role"] = u["role"]
            return redirect("/dashboard")

    return '''
    <h2>Login</h2>
    <form method="post">
        Usuario: <input name="username"><br>
        Clave: <input name="password" type="password"><br>
        <button>Entrar</button>
    </form>
    '''

# ---------------- DASHBOARD ----------------

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = get_db()

    if request.method == "POST":
        file = request.files["archivo"]
        filename = file.filename
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        conn.execute(
            "INSERT INTO documentos (nombre, archivo, fecha, estado, usuario) VALUES (?, ?, ?, ?, ?)",
            (filename, path, datetime.now().strftime("%Y-%m-%d %H:%M"), "pendiente", session["user"])
        )
        conn.commit()

    docs = conn.execute("SELECT * FROM documentos ORDER BY id DESC").fetchall()
    conn.close()

    html = "<h2>Bienvenido " + session["user"] + "</h2>"

    # Subir archivo (solo profesores/admin)
    if session["role"] != "impresor":
        html += '''
        <h3>Subir documento</h3>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="archivo">
            <button>Subir</button>
        </form>
        '''

    html += "<h3>Documentos</h3>"

    for d in docs:
        html += f"<p>{d['nombre']} | {d['estado']} | {d['usuario']} "

        # Botón imprimir solo impresor
        if session["role"] == "impresor" and d["estado"] == "pendiente":
            html += f"<a href='/imprimir/{d['id']}'>[Marcar como impreso]</a>"

        html += "</p>"

    html += "<br><a href='/logout'>Cerrar sesión</a>"

    return html

# ---------------- IMPRIMIR ----------------

@app.route("/imprimir/<int:id>")
def imprimir(id):
    conn = get_db()
    conn.execute("UPDATE documentos SET estado='impreso' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


from flask import Flask, request, redirect, render_template_string, session
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Carpeta para archivos
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Usuarios
users = {
    "admin": "1234",
    "profesor": "1234"
}

# Lista de trabajos
print_jobs = []

# HTML LOGIN
LOGIN_HTML = """
<h2>Login</h2>
<form method='post'>
<input name='user' placeholder='Usuario'><br>
<input name='pass' type='password' placeholder='Clave'><br>
<button>Ingresar</button>
</form>
"""

# HTML PRINCIPAL
HTML = """
<h2>🖨️ Sistema de Impresiones</h2>
<p>Usuario: {{session['user']}}</p>
<a href='/logout'>Cerrar sesión</a>

<h3>Agregar documento</h3>
<form method='post' action='/add' enctype='multipart/form-data'>
<input name='name' placeholder='Nombre documento'><br>
<input name='course' placeholder='Curso'><br>
<input type='date' name='date'><br>
<input type='time' name='time'><br>

<input type='file' name='file'><br>

<select name='priority'>
<option value='1'>Alta</option>
<option value='2'>Media</option>
<option value='3'>Baja</option>
</select><br>

<button>Agregar</button>
</form>

<h3>Cola de impresión</h3>
{% for job in jobs %}
<div style="border:1px solid black; margin:10px; padding:10px;">
<b>{{job['name']}}</b><br>
Curso: {{job['course']}}<br>
Fecha: {{job['date']}} {{job['time']}}<br>
Prioridad: {{job['priority']}}<br>
Estado: {{job['status']}}<br>
Archivo: {{job['file']}}<br>

{% if job['status']=='pendiente' %}
<a href='/print/{{loop.index0}}'>
<button>Marcar como impreso</button>
</a>
{% else %}
<p>✅ Impreso</p>
{% endif %}
</div>
{% endfor %}
"""

# Ordenar trabajos
def sort_jobs():
    return sorted(print_jobs, key=lambda x: (x['date'], x['time'], x['priority']))

# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        pw = request.form['pass']
        if user in users and users[user] == pw:
            session['user'] = user
            return redirect('/home')
        else:
            return "Login incorrecto"
    return render_template_string(LOGIN_HTML)

# HOME
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')
    return render_template_string(HTML, jobs=sort_jobs(), session=session)

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# AGREGAR TRABAJO + ARCHIVO
@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/')

    file = request.files['file']
    filename = ""

    if file and file.filename != "":
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    job = {
        'name': request.form['name'],
        'course': request.form['course'],
        'date': request.form['date'],
        'time': request.form['time'],
        'priority': int(request.form['priority']),
        'status': 'pendiente',
        'file': filename
    }

    print_jobs.append(job)
    return redirect('/home')

# MARCAR COMO IMPRESO
@app.route('/print/<int:id>')
def print_job(id):
    if 'user' not in session:
        return redirect('/')
    print_jobs[id]['status'] = 'impreso'
    print(f"IMPRESO: {print_jobs[id]['name']}")
    return redirect('/home')

# INICIAR APP
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
from flask import Flask, render_template, request, redirect, session, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from uuid import uuid4

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "minha_chave_segura")

# --- Configuração Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client = gspread.authorize(creds)

planilha_id = os.getenv("PLANILHA_ID")
sheet = client.open_by_key(planilha_id).sheet1  # primeira aba

# --- Funções auxiliares ---
def get_tasks(usuario):
    registros = sheet.get_all_records()
    return [t for t in registros if t["usuario"] == usuario]

def save_task(usuario, atividade, status):
    sheet.append_row([usuario, atividade, status, str(uuid4())])

def update_task(task_id, status):
    registros = sheet.get_all_records()
    for idx, row in enumerate(registros, start=2):  # linha 2 em diante
        if str(row["id"]) == str(task_id):
            sheet.update_cell(idx, 3, status)  # coluna 3 = status
            break

def delete_task(task_id):
    registros = sheet.get_all_records()
    for idx, row in enumerate(registros, start=2):
        if str(row["id"]) == str(task_id):
            sheet.delete_rows(idx)
            break

# --- Rotas ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        session["usuario"] = usuario
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/tarefas")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]
    tarefas = get_tasks(usuario)

    pendentes = [t for t in tarefas if t["status"] == "Pendente"]
    iniciadas = [t for t in tarefas if t["status"] == "Iniciado"]
    completas = [t for t in tarefas if t["status"] == "Completo"]

    return render_template("index.html",
                           usuario_nome=usuario,
                           pendentes=pendentes,
                           iniciadas=iniciadas,
                           completas=completas)

@app.route("/add", methods=["POST"])
def add():
    if "usuario" not in session:
        return redirect(url_for("login"))

    atividade = request.form.get("atividade")
    status = request.form.get("status")
    save_task(session["usuario"], atividade, status)
    return redirect(url_for("index"))

@app.route("/update/<task_id>", methods=["POST"])
def update(task_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    status = request.form.get("status")
    update_task(task_id, status)
    return redirect(url_for("index"))

@app.route("/delete/<task_id>")
def delete(task_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    delete_task(task_id)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- Rodar local ---
if __name__ == "__main__":
    app.run(debug=True)

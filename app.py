from flask import Flask, render_template, request, redirect, session, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import uuid

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # Troque por algo seguro

# ====== Conexão com Google Sheets ======
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client = gspread.authorize(creds)

# Planilhas
usuarios_sheet = client.open("GerenciadorTarefas").worksheet("usuarios")
tarefas_sheet = client.open("GerenciadorTarefas").worksheet("tarefas")


# ====== Funções auxiliares ======
def get_user(username, password):
    users = usuarios_sheet.get_all_records()
    for u in users:
        if u["usuario"] == username and u["senha"] == password:
            return u
    return None


def get_tasks(user):
    registros = tarefas_sheet.get_all_records()
    return [r for r in registros if r["usuario"] == user]


def add_task(usuario, atividade, status):
    tarefas_sheet.append_row([usuario, atividade, status, str(uuid.uuid4())])


def update_task(task_id, status):
    registros = tarefas_sheet.get_all_records()
    for idx, row in enumerate(registros, start=2):  # começa na linha 2
        if str(row["id"]) == str(task_id):
            tarefas_sheet.update_cell(idx, 3, status)  # coluna 3 = status
            break


def delete_task(task_id):
    registros = tarefas_sheet.get_all_records()
    for idx, row in enumerate(registros, start=2):
        if str(row["id"]) == str(task_id):
            tarefas_sheet.delete_rows(idx)
            break


# ====== Rotas ======
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        user = get_user(usuario, senha)
        if user:
            session["usuario"] = usuario
            return redirect(url_for("index"))
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/tarefas")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]
    todas = get_tasks(usuario)
    pendentes = [t for t in todas if t["status"] == "Pendente"]
    iniciadas = [t for t in todas if t["status"] == "Iniciado"]
    completas = [t for t in todas if t["status"] == "Completo"]

    return render_template("index.html", usuario_nome=usuario,
                           pendentes=pendentes, iniciadas=iniciadas, completas=completas)


@app.route("/add", methods=["POST"])
def add():
    if "usuario" not in session:
        return redirect(url_for("login"))

    atividade = request.form["atividade"]
    status = request.form["status"]
    add_task(session["usuario"], atividade, status)
    return redirect(url_for("index"))


@app.route("/update/<task_id>", methods=["POST"])
def update(task_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    novo_status = request.form["status"]
    update_task(task_id, novo_status)
    return redirect(url_for("index"))


@app.route("/delete/<task_id>")
def delete(task_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    delete_task(task_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)


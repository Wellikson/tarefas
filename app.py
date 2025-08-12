from flask import Flask, render_template, request, redirect, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = "chave_secreta"

# Configuração do Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Gerenciador de Tarefas").sheet1

@app.route("/")
def index():
    if "usuario" not in session:
        return redirect("/login")

    tarefas = sheet.get_all_records()
    tarefas_usuario = [t for t in tarefas if t["usuario"] == session["usuario"]]

    pendentes = [t for t in tarefas_usuario if t["status"] == "Pendente"]
    iniciadas = [t for t in tarefas_usuario if t["status"] == "Iniciado"]
    completas = [t for t in tarefas_usuario if t["status"] == "Completo"]

    return render_template(
        "index.html",
        usuario_nome=session["usuario"],
        pendentes=pendentes,
        iniciadas=iniciadas,
        completas=completas
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["usuario"] = request.form["usuario"]
        return redirect("/")
    return render_template("login.html")

@app.route("/add", methods=["POST"])
def add():
    if "usuario" in session:
        atividade = request.form["atividade"]
        status = request.form.get("status", "Pendente")
        sheet.append_row([session["usuario"], atividade, status])
    return redirect("/")

@app.route("/update/<int:linha>", methods=["POST"])
def update(linha):
    novo_status = request.form["status"]
    sheet.update_cell(linha + 2, 3, novo_status)
    return redirect("/")

@app.route("/delete/<int:linha>")
def delete(linha):
    sheet.delete_rows(linha + 2)
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)

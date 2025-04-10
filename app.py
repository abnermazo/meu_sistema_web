from flask import Flask, render_template, request, redirect, url_for, session
from flask import jsonify
import json
import os

app = Flask(__name__)
app.secret_key = "chave_secreta_segura"  # Chave para gerenciar sessões

FILE_NAME = "alunos.json"
USERS_FILE = "usuarios.json"

def carregar_usuarios():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4)

#Rota para login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        senha = request.form["senha"]

        usuarios = carregar_usuarios()
        if username in usuarios and usuarios[username]["senha"] == senha:
            session["usuario"] = username
            session["permissao"] = usuarios[username]["permissao"]
            return redirect(url_for("home"))  # Redireciona para a página inicial
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos!", title="Login")

    return render_template("login.html", title="Login")

#Rota para logout
@app.route("/logout")
def logout():
    session.clear()  # Limpa a sessão
    return redirect(url_for("login"))

# Rota para cadastro de usuários (admin)
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro_usuario():
    if "usuario" not in session or session["permissao"] != "admin":
        return redirect(url_for("login"))  # Redireciona para o login se não for admin

    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        matricula = request.form["matricula"]
        status = request.form["status"]

        alunos = carregar_dados()
        alunos[cpf] = {"nome": nome, "matricula": matricula, "status": status}
        salvar_dados(alunos)
        return render_template("cadastro.html", mensagem="Aluno cadastrado com sucesso!", title="Cadastro de Aluno")

    return render_template("cadastro.html", title="Cadastro de Aluno")

# Rota para usuarios visualizar os alunos cadastrados (admin)
@app.route("/relatorios")
def relatorios_usuario():
    if "usuario" not in session:
        return redirect(url_for("login"))  # Redireciona para o login

    alunos = carregar_dados()
    ativos = {cpf: aluno for cpf, aluno in alunos.items() if aluno["status"] == "Ativo"}
    inativos = {cpf: aluno for cpf, aluno in alunos.items() if aluno["status"] == "Inativo"}
    return render_template("relatorios.html", ativos=ativos, inativos=inativos, title="Relatórios")

def carregar_dados():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_dados(dados):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

@app.route("/")
def home():
    return render_template("base.html", title="Sistema de Alunos")

# Rota para editar alunos (admin)
@app.route("/editar", methods=["GET", "POST"])
def editar_aluno():
    # Verificar se o usuário está logado
    if "usuario" not in session:
        return redirect(url_for("login"))  # Redireciona para o login

    # Verificar se o usuário tem permissão de administrador
    if session.get("permissao") != "admin":
        return render_template("erro.html", mensagem="Acesso negado! Apenas administradores podem editar alunos.", title="Erro de Permissão")

    if request.method == "POST":
        cpf = request.form["cpf"]
        novo_nome = request.form.get("nome")
        nova_matricula = request.form.get("matricula")
        novo_status = request.form.get("status")

        alunos = carregar_dados()
        if cpf in alunos:
            if novo_nome:
                alunos[cpf]["nome"] = novo_nome
            if nova_matricula:
                alunos[cpf]["matricula"] = nova_matricula
            if novo_status:
                alunos[cpf]["status"] = novo_status
            salvar_dados(alunos)
            return render_template("editar.html", mensagem="Aluno atualizado com sucesso!", title="Editar Aluno")
        else:
            return render_template("editar.html", erro="Aluno não encontrado!", title="Editar Aluno")

    return render_template("editar.html", title="Editar Aluno")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        matricula = request.form["matricula"]
        status = request.form["status"]

        # Valida o CPF antes de cadastrar
        if not validar_cpf(cpf):
            return render_template("cadastro.html", erro="CPF inválido!", title="Cadastro de Aluno")

        alunos = carregar_dados()
        if cpf in alunos:
            return render_template("cadastro.html", erro="CPF já cadastrado!", title="Cadastro de Aluno")

        alunos[cpf] = {"nome": nome, "matricula": matricula, "status": status}
        salvar_dados(alunos)
        return render_template("cadastro.html", mensagem="Aluno cadastrado com sucesso!", title="Cadastro de Aluno")

    return render_template("cadastro.html", title="Cadastro de Aluno")

@app.route("/pesquisar", methods=["GET", "POST"])
def pesquisar():
    if request.method == "POST":
        cpf = request.form["cpf"]
        alunos = carregar_dados()
        aluno = alunos.get(cpf)
        if aluno:
            return render_template("pesquisar.html", aluno=aluno, cpf=cpf, title="Pesquisar Aluno")
        else:
            return render_template("pesquisar.html", erro="Aluno não encontrado!", title="Pesquisar Aluno")
    return render_template("pesquisar.html", title="Pesquisar Aluno")

@app.route("/relatorios")
def relatorios():
    alunos = carregar_dados()
    ativos = {cpf: aluno for cpf, aluno in alunos.items() if aluno["status"] == "Ativo"}
    inativos = {cpf: aluno for cpf, aluno in alunos.items() if aluno["status"] == "Inativo"}
    return render_template("relatorios.html", title="Relatórios", ativos=ativos, inativos=inativos)

@app.route("/editar", methods=["GET", "POST"])
def editar():
    if request.method == "POST":
        cpf = request.form["cpf"]
        novo_nome = request.form.get("nome")
        nova_matricula = request.form.get("matricula")
        novo_status = request.form.get("status")

        alunos = carregar_dados()
        if cpf in alunos:
            if novo_nome:
                alunos[cpf]["nome"] = novo_nome
            if nova_matricula:
                alunos[cpf]["matricula"] = nova_matricula
            if novo_status:
                alunos[cpf]["status"] = novo_status
            salvar_dados(alunos)
            return render_template("editar.html", mensagem="Aluno atualizado com sucesso!", title="Editar Aluno")
        else:
            return render_template("editar.html", erro="Aluno não encontrado!", title="Editar Aluno")

    return render_template("editar.html", title="Editar Aluno")

@app.route("/alunos")
def alunos():
    alunos = carregar_dados()
    return render_template("alunos.html", alunos=alunos, title="Alunos Cadastrados")

def validar_cpf(cpf):
    cpf = cpf.replace(".", "").replace("-", "")  # Remove pontos e traços
    if len(cpf) != 11 or not cpf.isdigit():
        return False

    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * len(cpf):
        return False

    # Calcula o primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    primeiro_dv = (soma * 10 % 11) % 10

    # Calcula o segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    segundo_dv = (soma * 10 % 11) % 10

    # Verifica os dígitos verificadores
    return primeiro_dv == int(cpf[9]) and segundo_dv == int(cpf[10])

# Rota para apagar alunos (admin)
@app.route("/apagar", methods=["POST"])
def apagar():
    if "usuario" not in session or session.get("permissao") != "admin":
        return render_template("erro.html", mensagem="Acesso negado! Apenas administradores podem apagar alunos.", title="Erro de Permissão")

    cpf = request.form["cpf"]
    alunos = carregar_dados()
    if cpf in alunos:
        del alunos[cpf]  # Remove o aluno pelo CPF
        salvar_dados(alunos)
        return redirect(url_for("alunos"))  # Redireciona para a página de alunos
    else:
        return render_template("erro.html", mensagem="Aluno não encontrado!", title="Erro de Permissão")
    

if __name__ == "__main__":
    app.run(debug=True)
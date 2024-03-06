import random
import string
import sqlite3
import base64
from flask import Flask, render_template, request, session, redirect, url_for
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('app_secret_key')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gerar-senha')
def gerar_senha():
    return render_template('gerar-senha.html', tamanho_range=10)

@app.route('/generate-password', methods=['POST'])
def generate_password():
    maius_checked = None
    minus_checked = None
    especial_checked = None
    numeros_checked = None
    

    tamanho = request.form.get('tamanho')
    if tamanho is not None:
        tamanho = int(tamanho)
    else:
        tamanho = 10
    # tamanho_range = tamanho
    
    use_uppercase = request.form.get('maius') == 'on'
    use_lowercase = request.form.get('minus') == 'on'
    use_special_chars = request.form.get('especial') == 'on'
    use_numbers = request.form.get('numeros') == 'on'

    characters = ''

    if use_uppercase:
        characters += string.ascii_uppercase
        maius_checked = 'checked'
    if use_lowercase:
        characters += string.ascii_lowercase
        minus_checked = 'checked'
    if use_special_chars:
        characters += string.punctuation + string.punctuation
        especial_checked = 'checked'
    if use_numbers:
        characters += string.digits + string.digits + string.digits + string.digits + string.digits
        numeros_checked = 'checked'
    if not characters:
        characters = string.ascii_lowercase
    
    senha_nome = request.form.get('senha_nome')
    senha_gerada = request.form.get('senha_gerada')
    acao = request.form['action']
    if acao == 'salvar-senha':
        if senha_gerada != '':
            password = senha_gerada
        else:
            password = ''.join(random.choice(characters) for _ in range(tamanho))
        if senha_nome != '':
            #senha_gerada = request.form.get('senha_gerada')
            print(senha_nome, password)
            session['apenas_criar_conta'] = False
            session['password'] = password
            session['senha_nome'] = senha_nome
            return redirect(url_for('registrar'))
            #cadastrar_senha_e_chave_do_usuario(password, senha_nome, id_usuario=session['id_usuario'])
    else:
        password = ''.join(random.choice(characters) for _ in range(tamanho))

    return render_template('gerar-senha.html', senha_nome=senha_nome, password=password, tamanho_range=tamanho, maius_checked=maius_checked, minus_checked=minus_checked, especial_checked=especial_checked, numeros_checked=numeros_checked)

@app.route('/register', methods=['GET','POST'])
def registrar():
    if request.method == 'POST':
        try:
            apenas_criar_conta = session['apenas_criar_conta']
        except:
            apenas_criar_conta = True
        
        nome_usuario = request.form.get('nome_usuario')
        email = request.form.get('email')
        senha = request.form.get('senha')
        try:
            print('apenas criar conta: ', apenas_criar_conta)
            if apenas_criar_conta == True:
                cadastrar_novo_usuario(nome_usuario, email, senha)
            else:
                senha_nome = session['senha_nome']
                password = session['password']
                id_usuario = cadastrar_novo_usuario(nome_usuario, email, senha)
                cadastrar_senha_e_chave_do_usuario(password, senha_nome, id_usuario)
                session.pop('apenas_criar_conta', None)
                session.pop('senha_nome', None)
                session.pop('id_usuario', None)
            return redirect(url_for('logar'))
        except AttributeError as e:
            if 'NoneType' in str(e):
                # Ignorar completamente o erro
                pass
            else:
                # Lidar com outros erros AttributeError
                print(f"Erro: {e}")
        except Exception as e:
            # Lidar com outros tipos de exceções, se necessário
            print(f"Erro: {e}")
        
    
    elif request.method == 'GET':
        return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def logar():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        print(email, senha)
        consulta = busca_senha_e_chave_base64(email)
        senha_base64 = consulta[0][0]
        chave_base64 = consulta[0][1]

        banco_senha_bytes = base64.b64decode(senha_base64).decode('utf-8')
        banco_chave_bytes = base64.b64decode(chave_base64).decode('utf-8')

        fernet = Fernet(banco_chave_bytes)
        senha_informada = str(senha)
        senha_banco = descriptografar(banco_senha_bytes, fernet)
        print(senha_informada, senha_banco)
        if senha_informada == senha_banco:
            print('login')
            consulta = buscar_usuario(email)
            id_usuario = consulta[0][0]
            nome_usuario = consulta[0][1]
            # Armazenar na sessão
            session['nome_usuario'] = nome_usuario
            session['id_usuario'] = id_usuario
            print(id_usuario, nome_usuario)
            return redirect(url_for('painel_minhas_senhas', id_usuario=id_usuario, nome_usuario=nome_usuario))
        else:
            return render_template('login.html')
    elif request.method == 'GET':
        print('metodo get')
        return render_template('login.html')

@app.route('/painel-gerar-senhas')
def painel_gerar_senhas():
    return render_template('painel-gerar-senhas.html', tamanho_range=10, nome_usuario=session['nome_usuario'])

@app.route('/painel-generate-password', methods=['POST'])
def painel_generate_password():
    maius_checked = None
    minus_checked = None
    especial_checked = None
    numeros_checked = None
    senha_nome = request.form.get('senha_nome')

    tamanho = request.form.get('tamanho')
    if tamanho is not None:
        tamanho = int(tamanho)
    else:
        tamanho = 10

    use_uppercase = request.form.get('maius') == 'on'
    use_lowercase = request.form.get('minus') == 'on'
    use_special_chars = request.form.get('especial') == 'on'
    use_numbers = request.form.get('numeros') == 'on'

    characters = ''

    if use_uppercase:
        characters += string.ascii_uppercase
        maius_checked = 'checked'
    if use_lowercase:
        characters += string.ascii_lowercase
        minus_checked = 'checked'
    if use_special_chars:
        characters += string.punctuation + string.punctuation
        especial_checked = 'checked'
    if use_numbers:
        characters += string.digits + string.digits + string.digits + string.digits + string.digits
        numeros_checked = 'checked'
    if not characters:
        characters = string.ascii_lowercase
    
    acao = request.form['action']
    if acao == 'salvar-senha':
        senha_gerada = request.form.get('senha_gerada')
        if senha_gerada != '':
            password = senha_gerada
        else:
            password = ''.join(random.choice(characters) for _ in range(tamanho))
        
        if senha_nome != '':
            senha_gerada = request.form.get('senha_gerada')
            print(senha_nome, password)
            cadastrar_senha_e_chave_do_usuario(password, senha_nome, id_usuario=session['id_usuario'])
    else:
        password = ''.join(random.choice(characters) for _ in range(tamanho))
    
    return render_template('painel-gerar-senhas.html', id_usuario=session['id_usuario'], nome_usuario=session['nome_usuario'] , senha_nome=senha_nome, password=password, tamanho_range=tamanho, maius_checked=maius_checked, minus_checked=minus_checked, especial_checked=especial_checked, numeros_checked=numeros_checked)

@app.route('/painel-minhas-senhas', methods=['GET', 'POST'])
def painel_minhas_senhas():
    # Obter parâmetros de consulta da URL
    id_usuario = session['id_usuario']
    nome_usuario = session['nome_usuario']
    if nome_usuario is None:
        nome_usuario = 'Usuário'

    if request.method == 'POST':
        nome_senha_selecionado = request.form.get('nome_senha_selecionado')
        acao = request.form['action']
        if acao == 'salvar':
            editar_senha(nome_senha_selecionado, id_usuario)
        elif acao == 'apagar':
            apagar_senha(nome_senha_selecionado)

            
    #SELECIONANDO TODAS AS SENHAS E CHAVES DO USUARIO
    consulta = selecionar_todas_as_senhas_e_chaves(id_usuario)

    #CONVERTENDO E DESCRIPTOGRAFANDO AS SENHAS
    dict_senhas = converter_e_descriptografar_senhas(consulta)

    return render_template('painel-minhas-senhas.html', dict_senhas=dict_senhas, nome_usuario=nome_usuario)

@app.route('/editar-senha/<nome_senha>')
def editar_senha(nome_senha, id_usuario):
    nova_senha = request.form.get('password')
    print(f"Nova senha para {nome_senha}: {nova_senha}")
    if nova_senha is not None:
        chave_bytes = busca_chave_bytes(nome_senha, id_usuario)
        fernet = Fernet(chave_bytes)
        nova_senha_bytes = criptografar(nova_senha,fernet)
        # Converta a senha de bytes para uma representação de texto (base64)
        nova_senha_base64 = base64.b64encode(nova_senha_bytes).decode('utf-8')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(f'''
                    UPDATE senha
                        SET senha = '{nova_senha_base64}'
                        WHERE senha_nome = '{nome_senha}'
                        AND id_usuario = {id_usuario};
        ''')
        conn.commit()
        conn.close()
    return redirect(url_for('painel_minhas_senhas'))

@app.route('/apagar-senha/<nome_senha>')
def apagar_senha(nome_senha):
    nova_senha = request.form.get('password')
    print(f"Nova senha para APAGAR {nome_senha}: {nova_senha}")
    if nome_senha is not None:
        print('comando de banco de dados para APAGAR')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(f'''
                    DELETE FROM chave
                       WHERE id_senha IN (SELECT id_senha FROM senha WHERE senha_nome = '{nome_senha}');
        ''')
        conn.commit()
        cursor.execute(f'''
                    DELETE FROM senha
                       WHERE senha_nome = '{nome_senha}';
        ''')
        conn.commit()
        conn.close()

@app.route('/delete_account')
def delete_account():
    id_usuario = session['id_usuario']
    with sqlite3.connect('database.db', timeout=5) as conn:
        cursor = conn.cursor()
        # Desvincule e exclua as chaves relacionadas
        cursor.execute('''
                       DELETE FROM CHAVE
                        WHERE id_senha IN (SELECT id_senha FROM SENHA WHERE id_usuario = ?);
        ''', (id_usuario,))
    
        #Exclua as senhas relacionadas
        cursor.execute('''
                       DELETE FROM SENHA WHERE id_usuario = ?;
        ''', (id_usuario,))

        # Exclua o usuário
        cursor.execute('''
                       DELETE FROM USUARIO WHERE id_usuario = ?;
        ''', (id_usuario,))
        
    # Limpar as variáveis de sessão
    session.pop('nome_usuario', None)
    session.pop('id_usuario', None)

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # Limpar as variáveis de sessão
    session.pop('nome_usuario', None)
    session.pop('id_usuario', None)

    return redirect(url_for('index'))

#########    Funções auxiliares    #########

def criptografar(senha, fernet):
    return fernet.encrypt(senha.encode())

def descriptografar(senha_criptografada, fernet):
        if type(senha_criptografada) == bytes:
            return fernet.decrypt(senha_criptografada).decode()
        else:
            return fernet.decrypt(senha_criptografada.encode()).decode()   

def cadastrar_novo_usuario(nome_usuario, email, senha):
    #INSERINDO NOVO USUARIO E SENHA E CHAVE
    # Conecte-se ao banco de dados
    with sqlite3.connect('database.db', timeout=5) as conn:
        cursor = conn.cursor()
        chave_bytes = Fernet.generate_key()
        fernet = Fernet(chave_bytes)
        senha_bytes = criptografar(senha, fernet)

        # Converta a senha de bytes para uma representação de texto (base64)
        senha_base64 = base64.b64encode(senha_bytes).decode('utf-8')
        chave_base64 = base64.b64encode(chave_bytes).decode('utf-8')

        # Insira o usuario no banco de dados
        cursor.execute("INSERT INTO usuario (nome_usuario, email) VALUES (?, ?)", (nome_usuario, email))
        id_usuario = cursor.lastrowid

        # Insira a senha no banco de dados
        cursor.execute("INSERT INTO senha (id_usuario, senha_nome, senha) VALUES (?, ?, ?)", (id_usuario, 'senha_conta', senha_base64))
        id_senha = cursor.lastrowid

        # Insira a chave no banco de dados
        cursor.execute("INSERT INTO chave (id_senha, chave) VALUES (?, ?)", (id_senha, chave_base64))

        # Commit para salvar as alterações no banco de dados
        conn.commit()

        return id_usuario

def buscar_usuario(email):
    # Conecte-se ao banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Execute uma consulta para recuperar a chave atraves do nome da senha e do id_usuario
    cursor.execute(f'''
                SELECT usuario.id_usuario, usuario.nome_usuario
                    FROM usuario
                    WHERE usuario.email = ?;
    ''', (email,))
    resultado = cursor.fetchall()
    # Feche a conexão com o banco de dados
    conn.close()
    return resultado

def busca_senha_e_chave_base64(email):
    # Conecte-se ao banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Execute uma consulta para recuperar a chave atraves do nome da senha e do id_usuario
    cursor.execute(f'''
                SELECT senha.senha, chave.chave
                    FROM usuario
                    JOIN senha ON usuario.id_usuario = senha.id_usuario
                    JOIN chave ON senha.id_senha = chave.id_senha
                    WHERE senha.senha_nome = 'senha_conta'
                    AND usuario.email = ?;
    ''', (email,))
    resultado = cursor.fetchall()
    # Feche a conexão com o banco de dados
    conn.close()
    return resultado

def cadastrar_senha_e_chave_do_usuario(password, senha_nome, id_usuario):
    chave_bytes = Fernet.generate_key()
    fernet = Fernet(chave_bytes)
    print(type(password), password)
    senha_bytes = criptografar(password, fernet)
    
    # Conecte-se ao banco de dados
    with sqlite3.connect('database.db', timeout=5) as conn:
        cursor = conn.cursor()
        # Converta a senha de bytes para uma representação de texto (base64)
        senha_base64 = base64.b64encode(senha_bytes).decode('utf-8')
        chave_base64 = base64.b64encode(chave_bytes).decode('utf-8')

        # Insira a senha no banco de dados
        cursor.execute("INSERT INTO senha (id_usuario, senha_nome, senha) VALUES (?, ?, ?)", (id_usuario, senha_nome, senha_base64))
        id_senha = cursor.lastrowid

        # Insira a chave no banco de dados
        # id_senha = 1
        cursor.execute("INSERT INTO chave (id_senha, chave) VALUES (?, ?)", (id_senha, chave_base64))

        # Commit para salvar as alterações no banco de dados
        conn.commit()

def busca_chave_bytes(senha_nome, id_usuario):
    # Conecte-se ao banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Execute uma consulta para recuperar a chave atraves do nome da senha e do id_usuario
    cursor.execute(f'''
                SELECT chave.chave
                    FROM usuario
                    JOIN senha ON usuario.id_usuario = senha.id_usuario
                    JOIN chave ON senha.id_senha = chave.id_senha
                    WHERE senha.senha_nome = ?
                    AND usuario.id_usuario = ?;
    ''', (senha_nome, id_usuario))
    chave_base64 = cursor.fetchone()[0]

    # Feche a conexão com o banco de dados
    conn.close()
    chave_bytes = base64.b64decode(chave_base64)
    return chave_bytes

def busca_senha_bytes_pelo_nome(senha_nome, id_usuario):
    # Conecte-se ao banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Execute uma consulta para recuperar a senha e a chave
    cursor.execute(f'''
                SELECT senha.senha
                    FROM usuario
                    JOIN senha ON usuario.id_usuario = senha.id_usuario
                    JOIN chave ON senha.id_senha = chave.id_senha
                    WHERE senha.senha_nome = '{senha_nome}'
                    AND usuario.id_usuario = {id_usuario};
    ''')
    senha_base64 = cursor.fetchall()[0][0]

    # Feche a conexão com o banco de dados
    conn.close()
    senha_bytes = base64.b64decode(senha_base64)
    return senha_bytes

def converter_e_descriptografar_senhas(consulta):
    dict_senhas = {}
    for i in consulta:
        senha_nome = i[0]
        senha_base64 = i[1]
        chave_base64 = i[2]
        #print(f'senha_base64: {senha_base64}\nchave_base64: {chave_base64}')
        senha_bytes = base64.b64decode(senha_base64).decode()
        chave_bytes = base64.b64decode(chave_base64).decode()
        #print(f'senha_bytes: {senha_bytes}\nchave_bytes: {chave_bytes}')
        fernet = Fernet(chave_bytes)
        senha_descriptografada = descriptografar(senha_bytes, fernet)
        #print(f'senha descriptografada: {senha_descriptografada}')
        #print('--------------')
        dict_senhas.update({senha_nome: senha_descriptografada})
    return dict_senhas

def selecionar_todas_as_senhas_e_chaves(id_usuario):
    # Conecte-se ao banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Execute uma consulta para recuperar a senha e a chave
    cursor.execute(f'''
                SELECT senha.senha_nome, senha.senha, chave.chave
                    FROM usuario
                    JOIN senha ON usuario.id_usuario = senha.id_usuario
                    JOIN chave ON senha.id_senha = chave.id_senha
                    WHERE usuario.id_usuario = {id_usuario};
    ''')
    resultado = cursor.fetchall()

    # Feche a conexão com o banco de dados
    conn.close()
    return resultado


# @app.route('/painel-minhas-senhas-editar')


if __name__ == '__main__':
    app.run(debug=True)

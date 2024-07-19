from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo
import MySQLdb
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['UPLOAD_FOLDER'] = 'archivos'

# Configuración de la base de datos
db = MySQLdb.connect(user='root', passwd='', host='localhost', db='digitalizacion_archivos')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, nombre, numero_empleado, rol, password):
        self.id = id
        self.nombre = nombre
        self.numero_empleado = numero_empleado
        self.rol = rol
        self.password = password


def registrar_historial(documento_id, accion, detalles=""):
    cursor = db.cursor()
    sql = """INSERT INTO historial_versiones (documento_id, accion, usuario_id, detalles) 
             VALUES (%s, %s, %s, %s)"""
    cursor.execute(sql, (documento_id, accion, current_user.id, detalles))
    db.commit()


@login_manager.user_loader
def load_user(user_id):
    cursor = db.cursor()
    cursor.execute('SELECT id, nombre, numero_empleado, rol, password FROM usuarios WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        return User(*user)
    return None


# Formularios
class LoginForm(FlaskForm):
    numero_empleado = IntegerField('Número de Empleado', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')


class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    numero_empleado = IntegerField('Número de Empleado', validators=[DataRequired()])
    rol = StringField('Rol', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')


# Rutas
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        numero_empleado = form.numero_empleado.data
        rol = form.rol.data
        password = generate_password_hash(form.password.data)

        cursor = db.cursor()
        cursor.execute('INSERT INTO usuarios (nombre, numero_empleado, rol, password) VALUES (%s, %s, %s, %s)',
                       (nombre, numero_empleado, rol, password))
        db.commit()
        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/contacto', methods=['GET'])
def contacto():
    if request.method ==  "GET":
        return render_template("contacto.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        numero_empleado = form.numero_empleado.data
        password = form.password.data

        cursor = db.cursor()
        cursor.execute('SELECT id, nombre, numero_empleado, rol, password FROM usuarios WHERE numero_empleado = %s',
                       (numero_empleado,))
        user = cursor.fetchone()
        if user and check_password_hash(user[4], password):
            user_obj = User(*user)
            login_user(user_obj)
            return redirect(url_for('index'))
        flash('Número de empleado o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    cursor = db.cursor()
    cursor.execute("SELECT id, nombre FROM categorias")
    cat = cursor.fetchall()
    print(cat)

    cursor.execute("SELECT id, nombre FROM subcategorias")
    subcat = cursor.fetchall()
    print(subcat)

    if request.method == 'POST':
        # Obtener los datos del formulario
        asunto = request.form['asunto']
        numero_oficio = request.form['numero_oficio']
        fecha_creacion = request.form['fecha_creacion']
        unidad_administrativa = request.form['unidad_administrativa']
        folio_inicial = request.form['folio_inicial']
        folio_final = request.form['folio_final']
        emisor = request.form['emisor']
        remitente = request.form['remitente']
        resumen = request.form['resumen']
        categoria_id = request.form['categoria']
        subcategoria_id = request.form['subcategoria']
        archivo = request.files['archivo']

        # Guardar el archivo en la carpeta correspondiente
        fecha_subida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """INSERT INTO archivos (asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor, remitente, resumen, categoria_id, subcategoria_id) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (
        asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor,
        remitente, resumen, categoria_id, subcategoria_id))
        documento_id = cursor.lastrowid
        db.commit()

        # archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], str(documento_id)))

        # Registrar la acción en el historial
        archivo_id = cursor.lastrowid

        if archivo:
            filename = secure_filename(archivo.filename)
            archivo_path = os.path.join(app.config['UPLOAD_FOLDER'], str(archivo_id))
            if not os.path.exists(archivo_path):
                os.makedirs(archivo_path)
            archivo.save(os.path.join(archivo_path, filename))

            flash('Archivo subido y datos guardados correctamente', 'success')
            registrar_historial(documento_id, "subido", f"Archivo subido: {archivo.filename}")
            return redirect(url_for('index'))

    return render_template('index.html', categorias=cat, subcategorias=subcat)

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    search_query = request.args.get('search')
    cursor = db.cursor()

    if search_query:
        sql = """SELECT archivos.id, asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor, remitente, resumen, categorias.nombre, subcategorias.nombre
                 FROM archivos 
                 INNER JOIN categorias on archivos.categoria_id = categorias.id
                 INNER JOIN subcategorias on archivos.subcategoria_id = subcategorias.id
                 WHERE asunto LIKE %s OR numero_oficio LIKE %s OR emisor LIKE %s OR remitente LIKE %s
                 """

        cursor.execute(sql, (
        '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    else:
        sql = """SELECT archivos.id, asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor, remitente, resumen, categorias.nombre, subcategorias.nombre 
                 FROM archivos 
                 INNER JOIN categorias on archivos.categoria_id = categorias.id
                 INNER JOIN subcategorias on archivos.subcategoria_id = subcategorias.id
                 """
        cursor.execute(sql)

    archivos = cursor.fetchall()
    return render_template('dashboard.html', archivos=archivos)


@app.route('/archivo/<int:archivo_id>')
@login_required
def ver_archivo(archivo_id):
    archivo_path = os.path.join(app.config['UPLOAD_FOLDER'], str(archivo_id))
    if os.path.exists(archivo_path):
        archivos = os.listdir(archivo_path)
        if archivos:
            registrar_historial(archivo_id, "visitado", f"Archivo visitado por usuario ID {current_user.id}")
            return send_from_directory(archivo_path, archivos[0])
    flash('Archivo no encontrado', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/archivo/<int:archivo_id>/eliminar', methods=['POST'])
@login_required
def eliminar_archivo(archivo_id):
    cursor = db.cursor()
    sql = "DELETE FROM archivos WHERE id = %s"
    cursor.execute(sql, (archivo_id,))
    db.commit()

    registrar_historial(archivo_id, "eliminado", f"Archivo eliminado por usuario ID {current_user.id}")

    flash('Archivo eliminado exitosamente')
    return redirect(url_for('dashboard'))

@app.route('/historial/<int:archivo_id>', methods=['GET'])
@login_required
def historial(archivo_id):
    cursor = db.cursor()
    sql = """SELECT accion, fecha, usuarios.nombre, detalles FROM historial_versiones
         inner join usuarios on usuarios.id = historial_versiones.usuario_id
         WHERE documento_id = %s"""
    cursor.execute(sql, (archivo_id,))
    versiones = cursor.fetchall()
    return render_template('historial.html', versiones=versiones)




@app.route('/dashboard_user', methods=['GET'])
@login_required
def dashboard_reducido():
    search_query = request.args.get('search')
    cursor = db.cursor()

    if search_query:
        sql = """SELECT archivos.id, asunto, numero_oficio, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor
                 FROM archivos 
                 WHERE asunto LIKE %s OR numero_oficio LIKE %s OR emisor LIKE %s
                 """
        cursor.execute(sql, (
        '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    else:
        sql = """SELECT archivos.id, asunto, numero_oficio, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor 
                 FROM archivos 
                 """
        cursor.execute(sql)

    archivos = cursor.fetchall()
    return render_template('repo_user.html', archivos=archivos)

#inicio
@app.route('/inicio')
def inicio():
    return render_template('inicio.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

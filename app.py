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
from functools import wraps
from flask import abort

from flask import Flask, jsonify, request
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, HiddenField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo



app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['UPLOAD_FOLDER'] = 'archivos'

# Configuración de la base de datos
db = MySQLdb.connect(user='root', passwd='', host='localhost', db='digitalizacion_archivos')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Manejo de los usuarios
class User(UserMixin):
    def __init__(self, id, nombre, numero_empleado, rol, password, nivel):
        self.id = id
        self.nombre = nombre
        self.numero_empleado = numero_empleado
        self.rol = rol
        self.password = password
        self.nivel = nivel


    def is_admin(self):
        return self.nivel == 'admin'

#Funcion para el historial de movimientos
def registrar_historial(documento_id, accion, detalles=""):
    cursor = db.cursor()
    sql = """INSERT INTO historial_versiones (documento_id, accion, usuario_id, detalles) 
             VALUES (%s, %s, %s, %s)"""
    cursor.execute(sql, (documento_id, accion, current_user.id, detalles))
    db.commit()

#Funcion para solicitar acceso solo a admins
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.nivel != 'admin':
            abort(403)  # Forbidden access
        return f(*args, **kwargs)
    return decorated_function

#Funcion del conteo actual de administradores
def count_admins():
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM usuarios WHERE nivel = %s', ('admin',))
    count = cursor.fetchone()[0]
    return count

#Funcion para cargar usuario
@login_manager.user_loader
def load_user(user_id):
    cursor = db.cursor()
    cursor.execute('SELECT id, nombre, numero_empleado, rol, password, nivel FROM usuarios WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        return User(*user)
    return None



# Formularios

#Funciones para formulario login
class LoginForm(FlaskForm):
    numero_empleado = IntegerField('Número de Empleado', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')

#Funciones para formulario de registro
class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    numero_empleado = IntegerField('Número de Empleado', validators=[DataRequired()])
    rol = StringField('Rol', validators=[DataRequired(), Length(max=50)])
    nivel = HiddenField(default='usuario')  # Campo invisible con valor predeterminado
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')


# Rutas

#Ruta para registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        numero_empleado = form.numero_empleado.data
        rol = form.rol.data
        nivel = form.nivel.data
        password = generate_password_hash(form.password.data)

        cursor = db.cursor()
        # Verifica si el número de empleado ya existe
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE numero_empleado = %s', (numero_empleado,))
        if cursor.fetchone()[0] > 0:
            flash('Número de empleado ya registrado. Por favor, ingrese otro.', 'danger')
            return render_template('register.html', form=form)

        # Inserta el nuevo usuario
        cursor.execute('INSERT INTO usuarios (nombre, numero_empleado, rol, password, nivel) VALUES (%s, %s, %s, %s, %s)',
                       (nombre, numero_empleado, rol, password, nivel))
        db.commit()
        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# funcion para no autorizar acceso a nivel usuario
@login_manager.unauthorized_handler
def unauthorized():
    flash('Por favor, inicie sesión para acceder a esta página.', 'warning')
    return redirect(url_for('login'))


#Funciones login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        numero_empleado = form.numero_empleado.data
        password = form.password.data

        cursor = db.cursor()
        cursor.execute('SELECT id, nombre, numero_empleado, rol, password, nivel FROM usuarios WHERE numero_empleado = %s',
                       (numero_empleado,))
        user = cursor.fetchone()
        if user and check_password_hash(user[4], password):
            user_obj = User(*user)
            login_user(user_obj)
            return redirect(url_for('inicio'))
        flash('Número de empleado o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

#cerrar seccion
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



#
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Obtener las unidades categorias
    cursor = db.cursor()
    cursor.execute("SELECT id, nombre FROM categorias")
    cat = cursor.fetchall()
    print(cat)
    # Obtener las unidades subcategorias
    cursor.execute("SELECT id, nombre FROM subcategorias")
    subcat = cursor.fetchall()
    print(subcat)

    # Obtener las unidades administrativas
    cursor.execute("SELECT nombre FROM unidades_administrativas")
    unidaadmin = cursor.fetchall()
    print(unidaadmin)

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

    return render_template('index.html', categorias=cat, subcategorias=subcat, unidades_administrativas=unidaadmin)

#Fucniones dashboard (Pagina para consultar archivos admin )
@app.route('/dashboard', methods=['GET'])
@login_required

#restringe el acceso al nivel usuario
def dashboard():
    if current_user.nivel != 'admin':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('inicio'))

    search_asunto = request.args.get('search_asunto')
    search_num_oficio = request.args.get("search_num_oficio")
    search_fecha_creacion = request.args.get("search_fecha_creacion")
    search_fecha_subida = request.args.get("search_fecha_subida")
    search_unidad_administrativa = request.args.get("search_unidad_administrativa")
    search_emisor = request.args.get("search_emisor")
    search_remitente = request.args.get("search_remitente")
    search_categoria = request.args.get("search_categoria")
    search_subcategoria = request.args.get("search_subcategoria")
    search_resumen = request.args.get("search_resumen")
    search_folio_inicial = request.args.get("search_folio_inicial")
    search_folio_final = request.args.get("search_folio_final")

    cursor = db.cursor()
    sql = """
        SELECT archivos.id, asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor, remitente, resumen, categorias.nombre, subcategorias.nombre 
        FROM archivos 
        INNER JOIN categorias ON archivos.categoria_id = categorias.id
        INNER JOIN subcategorias ON archivos.subcategoria_id = subcategorias.id
        WHERE 1=1
    """
    params = []

    if search_asunto:
        sql += " AND asunto LIKE %s"
        params.append(f"%{search_asunto}%")
    if search_num_oficio:
        sql += " AND numero_oficio LIKE %s"
        params.append(f"%{search_num_oficio}%")
    if search_fecha_creacion:
        sql += " AND fecha_creacion LIKE %s"
        params.append(f"%{search_fecha_creacion}%")
    if search_fecha_subida:
        sql += " AND fecha_subida LIKE %s"
        params.append(f"%{search_fecha_subida}%")
    if search_unidad_administrativa:
        sql += " AND unidad_administrativa LIKE %s"
        params.append(f"%{search_unidad_administrativa}%")
    if search_emisor:
        sql += " AND emisor LIKE %s"
        params.append(f"%{search_emisor}%")
    if search_folio_inicial:
        sql += " AND folio_inicial LIKE %s"
        params.append(f"%{search_folio_inicial}%")
    if search_folio_final:
        sql += " AND folio_final LIKE %s"
        params.append(f"%{search_folio_final}%")
    if search_remitente:
        sql += " AND remitente LIKE %s"
        params.append(f"%{search_remitente}%")
    if search_categoria:
        sql += " AND categorias.nombre LIKE %s"
        params.append(f"%{search_categoria}%")
    if search_subcategoria:
        sql += " AND subcategorias.nombre LIKE %s"
        params.append(f"%{search_subcategoria}%")
    if search_resumen:
        sql += " AND resumen LIKE %s"
        params.append(f"%{search_resumen}%")

    cursor.execute(sql, params)
    archivos = cursor.fetchall()

    return render_template('dashboard.html', archivos=archivos)


#Historial de versiones
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

#eliminar archivos
@app.route('/archivo/<int:archivo_id>/eliminar', methods=['POST'])
@login_required
def eliminar_archivo(archivo_id):
    cursor = db.cursor()
    try:
        # Llama al procedimiento almacenado
        cursor.callproc('eliminar_archivo', (archivo_id, current_user.id))

        db.commit()

        flash('Archivo eliminado exitosamente', 'success')
    except MySQLdb.IntegrityError as e:
        db.rollback()  # Rollback en caso de error
        flash(f'Error al eliminar el archivo: {e}', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'Error inesperado: {e}', 'danger')
    finally:
        return redirect(url_for('dashboard'))




#historial de movimientos
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



#funciones pagina consultar archivos
@app.route('/dashboard_user', methods=['GET'])
@login_required
def dashboard_reducido():
    search_asunto = request.args.get('search_asunto')
    search_num_oficio = request.args.get("search_num_oficio")
    search_fecha_subida = request.args.get("search_fecha_subida")
    search_unidad_administrativa = request.args.get("search_unidad_administrativa")
    search_folio_inicial = request.args.get("search_folio_inicial")
    search_folio_final = request.args.get("search_folio_final")
    search_emisor = request.args.get("search_emisor")
    search_remitente = request.args.get("search_remitente")
    search_categoria = request.args.get("search_categoria")
    search_subcategoria = request.args.get("search_subcategoria")
    search_resumen = request.args.get("search_resumen")

    cursor = db.cursor()
    sql = """
            SELECT archivos.id, asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor, remitente, resumen, categorias.nombre, subcategorias.nombre 
            FROM archivos 
            INNER JOIN categorias ON archivos.categoria_id = categorias.id
            INNER JOIN subcategorias ON archivos.subcategoria_id = subcategorias.id
            WHERE 1=1
        """
    params = []

    if search_asunto:
        sql += " AND asunto LIKE %s"
        params.append(f"%{search_asunto}%")
    if search_num_oficio:
        sql += " AND numero_oficio LIKE %s"
        params.append(f"%{search_num_oficio}%")
    if search_fecha_subida:
        sql += " AND fecha_subida LIKE %s"
        params.append(f"%{search_fecha_subida}%")
    if search_unidad_administrativa:
        sql += " AND unidad_administrativa LIKE %s"
        params.append(f"%{search_unidad_administrativa}%")
    if search_emisor:
        sql += " AND emisor LIKE %s"
        params.append(f"%{search_emisor}%")
    if search_folio_inicial:
        sql += " AND folio_inicial LIKE %s"
        params.append(f"%{search_folio_inicial}%")
    if search_folio_final:
        sql += " AND folio_final LIKE %s"
        params.append(f"%{search_folio_final}%")
    if search_remitente:
        sql += " AND remitente LIKE %s"
        params.append(f"%{search_remitente}%")
    if search_categoria:
        sql += " AND categorias.nombre LIKE %s"
        params.append(f"%{search_categoria}%")
    if search_subcategoria:
        sql += " AND subcategorias.nombre LIKE %s"
        params.append(f"%{search_subcategoria}%")
    if search_resumen:
        sql += " AND resumen LIKE %s"
        params.append(f"%{search_resumen}%")

    cursor.execute(sql, params)
    archivos = cursor.fetchall()

    return render_template('repo_user.html', archivos=archivos)

#seleccion de categorias y subcategorias
@app.route('/get_subcategorias/<int:categoria_id>')
def get_subcategorias(categoria_id):
    cursor = db.cursor()
    cursor.execute('SELECT id, nombre FROM subcategorias WHERE categoria_id = %s', (categoria_id,))
    subcategorias = cursor.fetchall()
    cursor.close()
    return jsonify({'subcategorias': [{'id': subcat[0], 'nombre': subcat[1]} for subcat in subcategorias]})

#funciones de la pagina de administracion de usuarios
@app.route('/admin/usuarios', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.nivel != 'admin':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('inicio'))

    # Obtener parámetros de búsqueda
    search_name = request.args.get('search_name')
    search_number = request.args.get('search_number')

    cursor = db.cursor()
    sql = "SELECT id, nombre, numero_empleado, rol, password, nivel FROM usuarios WHERE 1=1"
    params = []

    if search_name:
        sql += " AND nombre LIKE %s"
        params.append(f"%{search_name}%")
    if search_number:
        sql += " AND numero_empleado LIKE %s"
        params.append(f"%{search_number}%")

    cursor.execute(sql, params)
    users = cursor.fetchall()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')

        if action == 'delete':
            # Verifica el número de administradores antes de eliminar
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE nivel = %s', ('admin',))
            admin_count = cursor.fetchone()[0]

            # Asegúrate de que no sea el último admin
            cursor.execute('SELECT nivel FROM usuarios WHERE id = %s', (user_id,))
            user_nivel = cursor.fetchone()[0]

            if admin_count <= 1 and user_nivel == 'admin':
                flash('No se puede eliminar al último administrador.', 'danger')
                return redirect(url_for('manage_users'))

            try:
                # Elimina los registros dependientes primero
                cursor.execute('DELETE FROM historial_versiones WHERE usuario_id = %s', (user_id,))
                cursor.execute('DELETE FROM usuarios WHERE id = %s', (user_id,))
                db.commit()
                flash('Usuario eliminado correctamente.', 'success')
            except Exception as e:
                db.rollback()
                flash('Error al eliminar el usuario: ' + str(e), 'danger')

        elif action == 'make_admin':
            cursor.execute('UPDATE usuarios SET nivel = %s WHERE id = %s', ('admin', user_id))
            db.commit()
            flash('Usuario ahora es admin.', 'success')

        elif action == 'make_user':
            # Verifica el número de administradores antes de cambiar el rol
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE nivel = %s', ('admin',))
            admin_count = cursor.fetchone()[0]

            # Asegúrate de que no se convierte en el último admin
            if admin_count <= 1:
                cursor.execute('SELECT nivel FROM usuarios WHERE id = %s', (user_id,))
                user_nivel = cursor.fetchone()[0]

                if user_nivel == 'admin':
                    flash('No se puede cambiar el rol del último administrador.', 'danger')
                    return redirect(url_for('manage_users'))

            cursor.execute('UPDATE usuarios SET nivel = %s WHERE id = %s', ('usuario', user_id))
            db.commit()
            flash('Usuario ahora es usuario.', 'success')

        return redirect(url_for('manage_users'))

    return render_template('admin_users.html', users=users)



#funciones de la pagina de administracion de usuarios
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Verificar cuántos administradores hay en total
    if count_admins() <= 1:
        flash('No se puede eliminar al único administrador.', 'danger')
        return redirect(url_for('dashboard'))

    cursor = db.cursor()
    cursor.execute('SELECT nivel FROM usuarios WHERE id = %s', (user_id,))
    user = cursor.fetchone()

    if user and user[0] == 'admin':
        flash('No puedes eliminar a un administrador.', 'danger')
        return redirect(url_for('dashboard'))

    cursor.execute('DELETE FROM usuarios WHERE id = %s', (user_id,))
    db.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('dashboard'))


#pagina inicio
@app.route('/inicio')
@login_required
def inicio():
    usuario = current_user.nombre
    return render_template('inicio.html', usuario=usuario)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


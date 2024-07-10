from flask import Flask, request, render_template, redirect, url_for, flash
import MySQLdb
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['UPLOAD_FOLDER'] = 'archivos'

# Configuración de la base de datos
db = MySQLdb.connect(user='bernal', passwd='bernal9913', host='localhost', db='digitalizacion_archivos')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        asunto = request.form['asunto']
        numero_oficio = request.form['numero_oficio']
        fecha_creacion = request.form['fecha_creacion']
        unidad_administrativa = request.form['unidad_administrativa']
        folio_inicial = request.form['folio_inicial']
        folio_final = request.form['folio_final']
        emisor = request.form['emisor']
        remitente = request.form['remitente']
        resumen = request.form['resumen']
        archivo = request.files['archivo']

        cursor = db.cursor()
        sql = """INSERT INTO archivos (asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor, remitente, resumen)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        fecha_subida = datetime.now()
        cursor.execute(sql, (asunto, numero_oficio, fecha_creacion, fecha_subida, unidad_administrativa, folio_inicial, folio_final, emisor, remitente, resumen))
        db.commit()
        archivo_id = cursor.lastrowid

        if archivo:
            filename = secure_filename(archivo.filename)
            archivo_path = os.path.join(app.config['UPLOAD_FOLDER'], str(archivo_id))
            if not os.path.exists(archivo_path):
                os.makedirs(archivo_path)
            archivo.save(os.path.join(archivo_path, filename))

            flash('Archivo subido y datos guardados correctamente', 'success')
            return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    # git: JuanCarlosBL
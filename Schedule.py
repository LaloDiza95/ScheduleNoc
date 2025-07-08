from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta'

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

INGENIEROS_FILE = "ingenieros.csv"

def obtener_nombre_archivo(mes):
    return f"Horarios de NOC_{mes}.csv"

def cargar_ingenieros():
    if not os.path.exists(INGENIEROS_FILE):
        return []
    with open(INGENIEROS_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def guardar_ingenieros(lista):
    with open(INGENIEROS_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["id", "nombre"])
        writer.writeheader()
        writer.writerows(lista)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        if usuario == ADMIN_USER and contrasena == ADMIN_PASS:
            session['usuario'] = usuario
            return redirect(url_for('programar'))
        else:
            flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Has cerrado sesión')
    return redirect(url_for('login'))

@app.route('/programar')
def programar():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    mes_actual = datetime.now().strftime('%B')
    nombre_archivo = obtener_nombre_archivo(mes_actual)
    horarios_guardados = []
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, mode='r') as file:
            reader = csv.DictReader(file)
            horarios_guardados = list(reader)
    ingenieros = cargar_ingenieros()
    mes_actual_completo = datetime.now().strftime('%B %Y')
    return render_template('programar.html', ingenieros=ingenieros, horarios_guardados=horarios_guardados, mes_actual=mes_actual_completo)

@app.route('/cargar_horarios', methods=['POST'])
def cargar_horarios():
    mes = request.json['mes']
    nombre_archivo = obtener_nombre_archivo(mes)
    horarios = []
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, mode='r') as file:
            reader = csv.DictReader(file)
            horarios = list(reader)
    return jsonify(horarios)

@app.route('/programar', methods=['POST'])
def guardar_programacion():
    data = request.json['horarios']
    mes = request.json['mes']
    nombre_archivo = obtener_nombre_archivo(mes)
    if data:
        with open(nombre_archivo, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return jsonify({'message': 'Horarios guardados exitosamente'})
    return jsonify({'message': 'No hay datos para guardar'})

@app.route('/agregar_ingeniero', methods=['POST'])
def agregar_ingeniero():
    if 'usuario' not in session:
        return jsonify({"status": "error", "mensaje": "No autenticado"}), 401

    datos = request.get_json()
    nombre = datos.get("nombre", "").strip()
    id_empleado = datos.get("id_empleado", "").strip()

    if not nombre or not id_empleado:
        return jsonify({"status": "error", "mensaje": "Faltan datos"}), 400

    ingenieros = cargar_ingenieros()

    for ing in ingenieros:
        if ing["id"] == id_empleado:
            return jsonify({"status": "error", "mensaje": "ID duplicado"}), 400

    ingenieros.append({"id": id_empleado, "nombre": nombre})
    guardar_ingenieros(ingenieros)

    return jsonify({"status": "ok", "mensaje": "Ingeniero agregado"})

@app.route('/eliminar_ingeniero', methods=['POST'])
def eliminar_ingeniero():
    id_eliminar = request.json['id']
    ingenieros = cargar_ingenieros()
    ingenieros = [i for i in ingenieros if i["id"] != id_eliminar]
    guardar_ingenieros(ingenieros)

    # Eliminar del sistema (todos los archivos de horarios)
    for archivo in os.listdir():
        if archivo.startswith("horarios_") and archivo.endswith(".csv"):
            with open(archivo, mode='r') as file:
                reader = csv.DictReader(file)
                filas = [row for row in reader if row["id"] != id_eliminar]
                campos = reader.fieldnames

            with open(archivo, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=campos)
                writer.writeheader()
                writer.writerows(filas)

    return jsonify({"message": "Ingeniero eliminado exitosamente"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:kpi2030@10.1.46.182/disponibilidadlic'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Docente(db.Model):
    __tablename__ = 'dim_docentes'
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    correo_electronico = db.Column(db.String(100), nullable=False)

class Asignatura(db.Model):
    __tablename__ = 'dim_asignaturas'
    id = db.Column(db.Integer, primary_key=True)
    clave_asignatura = db.Column(db.String(20), unique=True, nullable=False)
    nombre_asignatura = db.Column(db.String(100), nullable=False)
    bimestre = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)

class Imparticion(db.Model):
    __tablename__ = 'fact_imparticiones'
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('dim_docentes.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('dim_asignaturas.id'), nullable=False)
    numero_veces = db.Column(db.Integer, default=0)

class PerfilAsignatura(db.Model):
    __tablename__ = 'fact_perfil'
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('dim_docentes.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('dim_asignaturas.id'), nullable=False)

class Seleccion(db.Model):
    __tablename__ = 'seleccion_asignaturas'
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('dim_docentes.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('dim_asignaturas.id'), nullable=False)
    telefono_celular = db.Column(db.String(20), nullable=False)

def convert_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        matricula = request.form['matricula']
        correo = request.form['correo']
        respuesta = request.form['respuesta']

        if respuesta == 'no':
            return render_template('index.html', agradecimiento=True, nombre=matricula)

        docente = Docente.query.filter_by(matricula=matricula, correo_electronico=correo).first()
        if docente:
            # Verificar si el docente ya ha registrado su disponibilidad
            seleccion = Seleccion.query.filter_by(docente_id=docente.id).first()
            if seleccion:
                return render_template('ya_registrado.html', docente=docente)
            
            imparticiones = db.session.query(Imparticion, Asignatura).join(Asignatura, Imparticion.asignatura_id == Asignatura.id).filter(Imparticion.docente_id == docente.id).all()
            perfiles = db.session.query(PerfilAsignatura, Asignatura).join(Asignatura, PerfilAsignatura.asignatura_id == Asignatura.id).filter(PerfilAsignatura.docente_id == docente.id).all()
            image_base64 = convert_image_to_base64('D:/Users/jvelazhe/Desktop/Development/flask_project/static/asignaturas.png')
            return render_template('seleccion.html', docente=docente, imparticiones=imparticiones, perfiles=perfiles, image_base64=image_base64)
        else:
            return "Docente no encontrado"
    return render_template('index.html', agradecimiento=False)

@app.route('/seleccionar', methods=['POST'])
def seleccionar():
    asignaturas_seleccionadas = request.form.getlist('asignaturas')
    docente_id = request.form['docente_id']
    telefono_celular = request.form['telefono_celular']
    if len(asignaturas_seleccionadas) > 3:
        return "No puedes seleccionar más de 3 asignaturas"
    for asignatura_id in asignaturas_seleccionadas:
        seleccion = Seleccion(docente_id=docente_id, asignatura_id=asignatura_id, telefono_celular=telefono_celular)
        db.session.add(seleccion)
    db.session.commit()
    docente = Docente.query.get(docente_id)
    return render_template('finalizacion.html', docente_nombre=docente.nombre, correo_electronico=docente.correo_electronico)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')

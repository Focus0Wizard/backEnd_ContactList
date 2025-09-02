from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from io import StringIO, BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://agenda_user:agenda_pass@localhost/agenda_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Tabla Usuario
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)        
    last_name = db.Column(db.String(100), nullable=False)   
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    contactos = db.relationship('Contacto', backref='usuario', lazy=True)

# Tabla Categoría
class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    

# Tabla Contacto
class Contacto(db.Model):
    __tablename__ = 'contactos'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

# -------------------
# Crear un usuario
# -------------------
@app.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'last_name', 'email', 'password')):
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    
    nuevo_usuario = Usuario(
        name=data['name'],
        last_name=data['last_name'],
        email=data['email'],
        password=hashed_pw
    )
    db.session.add(nuevo_usuario)
    db.session.commit()
    return jsonify({'mensaje': 'Usuario creado', 'id': nuevo_usuario.id}), 201

# -------------------
# Obtener todos los usuarios
# -------------------
@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    resultado = []
    for u in usuarios:
        resultado.append({
            'id': u.id,
            'name': u.name,
            'last_name': u.last_name,
            'email': u.email,
            'creado_en': u.creado_en
        })
    return jsonify(resultado), 200

# -------------------
# Obtener un usuario por id
# -------------------
@app.route('/usuarios/<int:id>', methods=['GET'])
def obtener_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    return jsonify({
        'id': usuario.id,
        'name': usuario.name,
        'last_name': usuario.last_name,
        'email': usuario.email,
        'creado_en': usuario.creado_en
    }), 200

# -------------------
# Actualizar usuario
# -------------------
@app.route('/usuarios/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        usuario.name = data['name']
    if 'last_name' in data:
        usuario.last_name = data['last_name']
    if 'email' in data:
        usuario.email = data['email']
    if 'password' in data:
        usuario.password = generate_password_hash(data['password'], method='sha256')
    
    db.session.commit()
    return jsonify({'mensaje': 'Usuario actualizado'}), 200

# -------------------
# Eliminar usuario
# -------------------
@app.route('/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({'mensaje': 'Usuario eliminado'}), 200


# Crear categoria
# -------------------
@app.route('/categorias', methods=['POST'])
def crear_categoria():
    data = request.get_json()
    if not data or not all(k in data for k in ('nombre', 'descripcion')):
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    
    nueva_categoria = Categoria(
        nombre=data['nombre'],
        descripcion=data['descripcion'],
    )
    db.session.add(nueva_categoria)
    db.session.commit()
    return jsonify({'mensaje': 'Categoria creada', 'id': nueva_categoria.id}), 201

# -------------------
# Obtener todas las categorias
# -------------------
@app.route('/categorias', methods=['GET'])
def listar_categorias():
    categorias = Categoria.query.all()
    resultado = []
    for c in categorias:
        resultado.append({
            'id': c.id,
            'nombre': c.nombre,
            'descripcion': c.descripcion
})
    return jsonify(resultado), 200

# -------------------
# Obtener una categoria por id
# -------------------
@app.route('/categorias/<int:id>', methods=['GET'])
def obtener_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    return jsonify({
        'id': categoria.id,
        'nombre': categoria.nombre,
        'descripcion': categoria.descripcion
    }), 200

# -------------------
# Eliminar categoria
# -------------------
@app.route('/categorias/<int:id>', methods=['DELETE'])
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    return jsonify({'mensaje': 'Categoria eliminada'}), 200



# Endpoint de login
def get_user_by_email(correo):
    return Usuario.query.filter_by(email=correo).first()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    correo = data.get("email")
    password = data.get("password")

    if not correo or not password:
        return jsonify({"error": "Correo y contraseña son obligatorios"}), 400

    user = get_user_by_email(correo)

    if user and check_password_hash(user.password, password):
        return jsonify({
            "id": user.id,
            "mensaje": "Login exitoso"
        }), 200
    else:
        return jsonify({"error": "Credenciales incorrectas"}), 401
    


# Crear contacto
@app.route("/usuarios/<int:usuario_id>/contactos", methods=["POST"])
def agregar_contacto(usuario_id):
    data = request.get_json()

    # Verificar que exista el usuario
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404


    # Crear contacto
    nuevo_contacto = Contacto(
        name=data.get("name"),
        last_name=data.get("last_name"),
        telefono=data.get("telefono"),
        email=data.get("email"),
        usuario_id=usuario_id
    )

    db.session.add(nuevo_contacto)
    db.session.commit()

    return jsonify({
        "mensaje": "Contacto agregado exitosamente",
        "contacto": {
            "id": nuevo_contacto.id,
            "nombre": nuevo_contacto.name,
            "apellido": nuevo_contacto.last_name,
            "telefono": nuevo_contacto.telefono,
            "email": nuevo_contacto.email,
            "usuario_id": nuevo_contacto.usuario_id
        }
    }), 201


# EDITAR CONTACTO
@app.route("/contactos/<int:contacto_id>", methods=["PATCH"])
def editar_contacto(contacto_id):
    data = request.get_json()

    # VERIFICAR QUE EXISTA EL CONTACTO
    contacto = Contacto.query.get(contacto_id)
    if not contacto:
        return jsonify({"error": "Contacto no encontrado"}), 404

    # ACTUALIZA SOLO LOS CAMPOS PROPORCIONADOS
    contacto.name = data.get("name", contacto.name)
    contacto.last_name = data.get("last_name", contacto.last_name)
    contacto.telefono = data.get("telefono", contacto.telefono)
    contacto.email = data.get("email", contacto.email)
    

    db.session.commit()

    return jsonify({
        "mensaje": "Contacto actualizado exitosamente",
        "contacto": {
            "id": contacto.id,
            "nombre": contacto.name,
            "apellido": contacto.last_name,
            "telefono": contacto.telefono,
            "email": contacto.email,
            "usuario_id": contacto.usuario_id
        }
    }), 200

#  VER CONTACTOS DE UN USUARIO
@app.route("/usuarios/<int:usuario_id>/contactos", methods=["GET"])
def ver_contactos(usuario_id):
    # VERIFICAR QUE EXISTA EL USUARIO
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    contactos = Contacto.query.filter_by(usuario_id=usuario_id).all()
    resultado = []
    for c in contactos:
        resultado.append({
            "id": c.id,
            "nombre": c.name,
            "apellido": c.last_name,
            "telefono": c.telefono,
            "email": c.email
        })

    return jsonify(resultado), 200

# -------------------
# Eliminar contacto
# -------------------
@app.route('/contactos/<int:id>', methods=['DELETE'])
def eliminar_contacto(id):
    data = request.get_json() 
    
    if not data or 'confirmar' not in data or not data['confirmar']:
        return jsonify({'error': 'Se requiere confirmación para eliminar el contacto'}), 400
    
    contacto = Contacto.query.get_or_404(id)
    db.session.delete(contacto)
    db.session.commit()
    
    return jsonify({'mensaje': 'Contacto eliminado correctamente'}), 200



# -------------------
# Buscar contacto por nombre
# -------------------
@app.route('/usuarios/<int:usuario_id>/contactos/buscar', methods=['GET'])
def buscar_contactos(usuario_id):
    nombre = request.args.get('nombre')
    if not nombre:
        return jsonify({'error': 'Debes proporcionar un nombre para buscar'}), 400

    contactos = Contacto.query.filter(
        Contacto.usuario_id == usuario_id,
        Contacto.name.ilike(f"%{nombre}%") 
    ).all()

    if not contactos:
        return jsonify({'mensaje': 'No se encontraron contactos con ese nombre'}), 404

    resultado = []
    for c in contactos:
        resultado.append({
            'id': c.id,
            'nombre': c.name,
            'apellido': c.last_name,
            'telefono': c.telefono,
            'email': c.email
        })

    return jsonify(resultado), 200


#Exportacion de contactos en un CSV o en un PDF
@app.route('/usuarios/<int:usuario_id>/contactos/export', methods=['GET'])
def exportar_contactos(usuario_id):
    formato = request.args.get('formato', 'csv')  # por defecto CSV
    
    # Obtener los contactos del usuario
    contactos = Contacto.query.filter_by(usuario_id=usuario_id).all()
    
    if not contactos:
        return jsonify({"El usuario no tiene contactos"}), 404
    
    if formato == 'csv':
        # Generar CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Contactos del usuario'])
        writer.writerow(['Nombre', 'Apellido', 'Telefono', 'Correo'])
        
        for c in contactos:
            writer.writerow([c.name, c.last_name, c.telefono, c.email])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename=contactos_{usuario_id}.csv"}
        )
    
    elif formato == 'pdf':
        # Generar PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(200, height - 50, f"Contactos del Usuario")
        
        y = height - 100
        p.setFont("Helvetica", 10)
        p.drawString(50, y, "Nombre")
        p.drawString(150, y, "Apellido")
        p.drawString(250, y, "Teléfono")
        p.drawString(350, y, "Correo")
        
        y -= 20
        for c in contactos:
            p.drawString(50, y, c.name)
            p.drawString(150, y, c.last_name)
            p.drawString(250, y, c.telefono)
            if (c.email == None):
                p.drawString(350, y, "No disponible")
            else:
                p.drawString(350, y, c.email)
            y -= 20
            if y < 50:  
                p.showPage()
                y = height - 50
        
        p.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"contactos_{usuario_id}.pdf",
            mimetype='application/pdf'
        )
    
    else:
        return jsonify({"error": "Formato no soportado. Use csv o pdf"}), 400


# -------------------
# Obtener un contacto por id
# -------------------
@app.route('/contactos/<int:id>', methods=['GET'])
def obtener_contacto(id):
    contacto = Contacto.query.get_or_404(id)
    return jsonify({
        'id': contacto.id,
        'nombre': contacto.name,
        'apellido': contacto.last_name,
        'telefono': contacto.telefono, 
        'email': contacto.email,
        'agregado en': contacto.creado_en
    }), 200
    

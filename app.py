from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://agenda_user:agenda_pass@localhost/agenda_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Tabla Usuario
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    contactos = db.relationship('Contacto', backref='usuario', lazy=True)

# Tabla Categoría
class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    
    contactos = db.relationship('Contacto', backref='categoria', lazy=True)

# Tabla Contacto
class Contacto(db.Model):
    __tablename__ = 'contactos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)

# -------------------
# Crear un usuario
# -------------------
@app.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.get_json()
    if not data or not all(k in data for k in ('nombre', 'email', 'password')):
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    
    # Encriptar password
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    
    nuevo_usuario = Usuario(
        nombre=data['nombre'],
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
            'nombre': u.nombre,
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
        'nombre': usuario.nombre,
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
    
    if 'nombre' in data:
        usuario.nombre = data['nombre']
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

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


# -------------------
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

    # Verificar que exista la categoría
    categoria_id = data.get("categoria_id")
    if categoria_id:
        categoria = Categoria.query.get(categoria_id)
        if not categoria:
            return jsonify({"error": "Categoría no encontrada"}), 404

    # Crear contacto
    nuevo_contacto = Contacto(
        nombre=data.get("nombre"),
        telefono=data.get("telefono"),
        email=data.get("email"),
        usuario_id=usuario_id,
        categoria_id=categoria_id
    )

    db.session.add(nuevo_contacto)
    db.session.commit()

    return jsonify({
        "mensaje": "Contacto agregado exitosamente",
        "contacto": {
            "id": nuevo_contacto.id,
            "nombre": nuevo_contacto.nombre,
            "telefono": nuevo_contacto.telefono,
            "email": nuevo_contacto.email,
            "categoria_id": nuevo_contacto.categoria_id,
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
    contacto.nombre = data.get("nombre", contacto.nombre)
    contacto.telefono = data.get("telefono", contacto.telefono)
    contacto.email = data.get("email", contacto.email)
    
    # VERIFICAR Y ACTUALIZAR CATEGORÍA SI SE PROPORCIONA
    if "categoria_id" in data:
        categoria_id = data["categoria_id"]
        if categoria_id:
            categoria = Categoria.query.get(categoria_id)
            if not categoria:
                return jsonify({"error": "Categoría no encontrada"}), 404
            contacto.categoria_id = categoria_id
        else:
            contacto.categoria_id = None

    db.session.commit()

    return jsonify({
        "mensaje": "Contacto actualizado exitosamente",
        "contacto": {
            "id": contacto.id,
            "nombre": contacto.nombre,
            "telefono": contacto.telefono,
            "email": contacto.email,
            "categoria_id": contacto.categoria_id,
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
            "nombre": c.nombre,
            "telefono": c.telefono,
            "email": c.email,
            "categoria_id": c.categoria_id
        })

    return jsonify(resultado), 200
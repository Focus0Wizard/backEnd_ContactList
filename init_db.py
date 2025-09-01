from app import app, db

with app.app_context():
    app.run(debug = True)
    db.create_all()
    print("Base de datos inicializada")
    
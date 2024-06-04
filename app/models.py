from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(64), unique=False, nullable=False)
    weigth = db.Column(db.Integer, unique=False, nullable=False)
    height = db.Column(db.Integer, unique=False, nullable=False)
    sex = db.Column(db.String(64), unique=False, nullable=False)
    customer_id = db.Column(db.String(128), unique=True, nullable=False)
    age = db.Column(db.Integer, unique=False, nullable=False)
    bmr = db.Column(db.Integer, unique=False, nullable=False)
    line_id = db.Column(db.String(128), unique=True, nullable=True)
    encrypcustomer_id = db.Column(db.String(256), unique=True, nullable=True)
    keydecrypt = db.Column(db.String(256), unique=True, nullable=True)

    def __repr__(self):
        return f'<User {self.keyword}>'
    
class AdditionalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),unique=False, nullable=False)
    problem = db.Column(db.String(256), nullable=False)
    calday = db.Column(db.String(256), nullable=False)
    
    user = db.relationship('User', backref=db.backref('additional_info', lazy=True))

    def __repr__(self):
        return f'<AdditionalInfo {self.id} - User {self.user_id}>'
    

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Author(db.Model):
    __tablename__ = 'authors'
    author_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return f"<Author {self.author_id}: {self.name}>"

class Publisher(db.Model):
    __tablename__ = 'publishers'
    publisher_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return f"<Publisher {self.publisher_id}: {self.name}>"

class Book(db.Model):
    __tablename__ = 'books'
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    genre = db.Column(db.String(100))
    published_date = db.Column(db.DateTime)
    
    author_id = db.Column(db.Integer, db.ForeignKey('authors.author_id'))
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.publisher_id'))
    
    author = db.relationship('Author', backref=db.backref('books', lazy=True))
    publisher = db.relationship('Publisher', backref=db.backref('books', lazy=True))

    def __repr__(self):
        return f"<Book {self.book_id}: {self.title} by {self.author.name}>"

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return f"<User {self.user_id}: {self.name}>"

class Loan(db.Model):
    __tablename__ = 'loans'
    loan_id = db.Column(db.Integer, primary_key=True)
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime, nullable=True)
    
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    
    book = db.relationship('Book', backref=db.backref('loans', lazy=True))
    user = db.relationship('User', backref=db.backref('loans', lazy=True))

    def __repr__(self):
        return f"<Loan {self.loan_id}: {self.book.title} to {self.user.name} (Due: {self.due_date})>"

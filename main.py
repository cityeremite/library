# -*- coding: utf-8 -*-
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from config import DevConfig
import json, time

from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from flask_httpauth import HTTPBasicAuth
from flask_debugtoolbar import DebugToolbarExtension


app = Flask(__name__)
app.secret_key = "super secret key"
app.config.from_object(DevConfig)

db = SQLAlchemy(app)
auth = HTTPBasicAuth()
toolbar = DebugToolbarExtension(app)




@app.route('/')
def index():
    return "Hello, World!"


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(256))
    create_date = db.Column(db.Date)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def dumps(self):
        return {
            'username': self.username,
            'create_date': self.create_date,
        }


@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    else:
        return (jsonify({
                        'username': user.username,
                         'create_date': user.create_date
                         }), 200)


@app.route('/api/users')
def get_users():
    users = User.query.all()
    if not users:
        return (jsonify({'users':'null'}),200)
    else:
        return jsonify( [u.dumps() for u in users])


@app.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    user.create_date = time.strftime("%Y-%m-%d", time.localtime())
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_users', _external=True)})


@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if user is not None:
        db.session.delete(user)
        db.session.commit()
        return (jsonify({'user deleted': user.username}), 201,
            {'Location': url_for('get_users', _external=True)})
    else:
        abort(400)


@app.route('/api/users/<int:id>', methods=['PUT'])
def change_user(id):
    user = User.query.get(id)
    if user is not None:
        password = request.json.get('password')
        user.hash_password(password)
        db.session.commit()
        return (jsonify({'user updated': user.username}), 201)
    else:
        abort(400)



@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


class Book(db.Model):
    __tablename__ = 'books'
    book_no = db.Column(db.String(30), primary_key=True)
    book_name = db.Column(db.String(100))
    intro_addr = db.Column(db.String(300))

    def dumps(self):
        return {
            'book_no': self.book_no,
            'book_name': self.book_name,
            'intro_addr': self.intro_addr,
        }


@app.route('/api/books/<string:book_no>')
def get_book(book_no):
    book = Book.query.get(book_no)
    if not book:
        abort(400)
    else:
        return (jsonify({
                        'book_no': book_no,
                        'book_name': book.username,
                         'intro_addr': book.intro_addr
                         }), 200)


@app.route('/api/books')
def get_books():
    books = Book.query.all()

    if not books:
        return (jsonify({'books':'null'}),200)
    else:
        return jsonify( [u.dumps() for u in books])



@app.route('/api/books', methods=['POST'])
def new_book():
    book_no = request.json.get('book_no')
    book_name = request.json.get('book_name')
    intro_addr = request.json.get('intro_addr')
    if book_name is None or book_no is None:
        abort(400)    # missing arguments
    if Book.query.filter_by(book_name=book_name).first() is not None:
        abort(400)    # existing book
    if Book.query.filter_by(book_no=book_no).first() is not None:
        abort(400)    # existing book

    book = Book(book_no=book_no)
    book.book_name = book_name
    book.intro_addr = intro_addr
    db.session.add(book)
    db.session.commit()
    return (jsonify({'book_name': book.book_name}), 201,
            {'Location': url_for('get_books', _external=True)})


@app.route('/api/books/<string:book_no>', methods=['DELETE'])
def delete_book(book_no):
    book = Book.query.get(book_no)
    if book is not None:
        db.session.delete(book)
        db.session.commit()
        return (jsonify({'book deleted': book.book_name}), 201,
            {'Location': url_for('get_books', _external=True)})
    else:
        abort(400)


@app.route('/api/books/<string:book_no>', methods=['PUT'])
def change_book(book_no):
    book = Book.query.get(book_no)
    if book is not None:
        book_name = request.json.get('book_name')
        intro_addr = request.json.get('intro_addr')
        book.book_name = book_name
        book.intro_addr = intro_addr
        db.session.commit()
        return (jsonify({'book updated': book.book_no}), 201)
    else:
        abort(400)







if __name__ == '__main__':
    app.run(debug=True)

# class Book(db.Model):
#     book_no = db.Column(db.String(30), primary_key=True)
#     book_name = db.Column(db.String(100))
#     intro_addr = db.Column(db.String(300))
#     borrow_rec = db.relationship(
#         'BorrowRec',
#         backref = 'book',
#         lazy = 'dynamic'
#     )
#
#     def __init__(self, book_no, book_name, intro_addr):
#         self.book_no = book_no
#         self.book_name = book_name
#         self.intro_addr = intro_addr
#
#     def __repr__(self):
#         return u"<Book '{0}'>".format(self.book_name.encode('utf-8'))
#
# class BorrowRec(db.Model):
#     id = db.Column(db.Integer(), primary_key=True)
#     reader = db.Column(db.String(50))
#     borrow_date = db.Column(db.DateTime())
#     book_no = db.Column(db.String(30), db.ForeignKey('book.book_no'))
#
#     def __init__(self):
#         pass
#
#     def __repr__(self):
#         return "<Borrow: '{}'>".format(self.book_no)

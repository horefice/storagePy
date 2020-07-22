#!/usr/bin/env python

# Libs
from dotenv import load_dotenv
from flask import Flask, jsonify, abort, request, make_response
from pymongo import MongoClient, ReturnDocument
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from string import hexdigits
from hashlib import md5
from functools import wraps
from datetime import datetime
import os
import re

# Env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# App and add-ons
app = Flask(__name__)
auth = HTTPBasicAuth()
limiter = Limiter(app,key_func=get_remote_address,global_limits=["10000 per day", "100 per minute"])

# MongoDB
client = MongoClient(os.environ.get("DATABASE_URL"))
db = client[os.environ.get("DATABASE_DB")]
collection = db[os.environ.get("DATABASE_COLLECTION")]

# Errors
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

@app.errorhandler(401)
def unauthorized_access(error):
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}),404)

@app.errorhandler(413)
def payload_too_large(error):
    return make_response(jsonify({'error': 'Payload too large'}),413)

@app.errorhandler(429)
def too_many_requests(error):
    return make_response(jsonify({'error': 'Too many requests'}),429)

# Helpers
@auth.get_password
def get_password(username):
    if username == os.environ.get("DATABASE_USER"):
        return os.environ.get("DATABASE_PASSWORD")
    return None

def validate_userid(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = kwargs['user_id']
        if not all(c in hexdigits for c in user_id) or not len(user_id) == 32:
            abort(400)
        if collection.find_one_and_update({'hash': user_id}, {'$set': {'last-Request': datetime.utcnow()}}) is None:
            abort(404)
        return f(*args, **kwargs)
    return wrapper

def validate_item(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = kwargs['user_id']
        item = kwargs['item']
        data = collection.find_one({'hash': user_id})['data']
        if item not in data:
            abort(404)
        return f(*args, **kwargs)
    return wrapper

def limit_content_length(max_length, accumulative = False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cl = request.content_length
            if accumulative is True:
                user_id = kwargs['user_id']
                item = kwargs['item']
                data = collection.find_one({'hash': user_id})['data']
                free_space = max_length - len(data) + len(data[item] if item in data else "")
            else:
            	free_space = max_length
            if cl is not None and cl > free_space:
                abort(413)
            return f(*args, **kwargs)
        return wrapper
    return decorator

def make_public_data(data, item = 'data'):
    return {item: data[item]}

def make_public_user(user):
    new_user = {}
    for field in user:
        if field == '_id':
            new_user[field] = str(user[field])
        else:
            new_user[field] = user[field]
    return new_user

# Admin
@app.route('/admin/', methods = ['GET'])
@auth.login_required
def get_all():
    cursor = collection.find({})
    all_data = [make_public_user(user) for user in cursor]
    return jsonify({'collection': all_data})

@app.route('/admin/', methods = ['DELETE'])
@auth.login_required
def delete_all():
    result = collection.update_many({}, {'$set': {'data': {}}})
    return jsonify({'result': True, 'deleted': result.modified_count})

@app.route('/admin/destroy', methods = ['DELETE'])
@auth.login_required
def reset_all():
    result = collection.delete_many({})
    return jsonify({'result': True, 'deleted': result.deleted_count})

# Public
@app.route('/', methods = ['GET'], defaults={'user_id': '4bd19e518d90d816fb283cf09d6498bf'})
@app.route('/<user_id>', methods = ['GET'])
@validate_userid
def get_data(user_id):
    user = collection.find_one({'hash': user_id})
    return jsonify(make_public_data(user))

@app.route('/<user_id>/<item>', methods = ['GET'])
@validate_userid
@validate_item
def get_item(user_id,item):
    data = collection.find_one({'hash': user_id})['data']
    return jsonify(make_public_data(data,item))

@app.route('/', methods = ['POST', 'PUT'], defaults={'user_id': '4bd19e518d90d816fb283cf09d6498bf'})
@app.route('/<user_id>', methods = ['POST', 'PUT'])
@validate_userid
@limit_content_length(5 * 1024 * 1024)
def update_data(user_id):
    user = collection.find_one_and_update({'hash': user_id}, {'$set': {'data': request.json}}, return_document = ReturnDocument.AFTER)
    status = 201 if request.method == "POST" else 200
    return jsonify(make_public_data(user)), status

@app.route('/<user_id>/<item>', methods = ['POST', 'PUT'])
@validate_userid
@limit_content_length(5 * 1024 * 1024, True)
def update_item(user_id,item):
    data = collection.find_one_and_update({'hash': user_id}, {'$set': {'data.' + item: request.json}}, return_document = ReturnDocument.AFTER)['data']
    status = 201 if request.method == "POST" else 200
    return jsonify(make_public_data(data,item)), status

@app.route('/', methods = ['DELETE'], defaults={'user_id': '4bd19e518d90d816fb283cf09d6498bf'})
@app.route('/<user_id>', methods = ['DELETE'])
@validate_userid
def delete_data(user_id):
    collection.find_one_and_update({'hash': user_id}, {'$set': {'data': {}}})
    return jsonify({'result': True})

@app.route('/<user_id>/<item>', methods = ['DELETE'])
@validate_userid
@validate_item
def delete_item(user_id,item):
    collection.find_one_and_update({'hash': user_id}, {'$unset': {'data.' + item: ""}})
    return jsonify({'result': True})

# Signup
@app.route('/signup', methods = ['POST'])
@limit_content_length(1024)
def create_user():
    user = {}
    user['email'] = request.form['email']
    if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", user['email']):
        abort(400)
    hash = md5(user['email'].encode('utf-8')).hexdigest()
    user['hash'] = hash
    if not collection.find_one({'hash': hash}):
        user['data'] = {}
        user['created-At'] = datetime.utcnow()
        collection.insert_one(user)
    return jsonify({'hash': hash}), 201, {'Access-Control-Allow-Origin': '*'} 

# Run
if __name__ == '__main__':
    app.run(debug = True)
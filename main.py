import json
import pdb

from bson import json_util
from bson.objectid import ObjectId
from pymongo import MongoClient
from flask import Flask, request, jsonify, Response
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import datetime
import hashlib

app = Flask(__name__)

mongo_url = "mongodb+srv://usmanhidral:uob#15026436@cluster0.oyjdpoe.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(mongo_url)

db = client.get_database('templates_db')

jwt = JWTManager(app)  # initialize JWTManager
app.config['JWT_SECRET_KEY'] = 'Your_Secret_Key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)  # define the life span of the token


@app.route("/register", methods=['post'])
def register():
    users_collection = db.users
    new_user = request.get_json()  # store the json body request
    new_user["password"] = hashlib.sha256(new_user["password"].encode("utf-8")).hexdigest()  # encrpt password
    doc = users_collection.find_one({"email": new_user["email"]})
    print(doc)
    if not doc:
        users_collection.insert_one(new_user)
        return json.dumps({'message': 'User Record Inserted Successfully'})
    else:
        return json.dumps({'message': 'User Already Exist'})


@app.route("/login", methods=["POST"])
def login():
    users_collection = db.users
    login_details = request.get_json()  # store the json body request
    user_from_db = users_collection.find_one({'email': login_details['email']})  # search for user in database

    if user_from_db:
        encrpted_password = hashlib.sha256(login_details['password'].encode("utf-8")).hexdigest()
        if encrpted_password == user_from_db['password']:
            access_token = create_access_token(identity=user_from_db['email'])  # create jwt token
            return jsonify(access_token=access_token), 200

    return jsonify({'msg': 'The username or password is incorrect'}), 401


@app.route("/user", methods=["GET"])
@jwt_required()
def profile():
    users_collection = db.users
    current_user = get_jwt_identity()  # Get the identity of the current user
    user_from_db = users_collection.find_one({'email': current_user})
    if user_from_db:
        del user_from_db['_id'], user_from_db['password']  # delete data we don't want to return
        return jsonify({'profile': user_from_db}), 200
    else:
        return jsonify({'msg': 'Profile not found'}), 404


@app.route("/template", methods=['post', 'get', 'delete', 'put'])
@jwt_required()
def template():
    if request.method == 'POST':
        templates_collection = db.templates
        new_template = request.get_json()  # store the json body request
        templates_collection.insert_one(new_template)
        return json.dumps({'message': 'Template Inserted Successfully'})

    elif request.method == 'GET':
        if request.args.get('id'):

            custom_id = request.args.get('id')

            single_template = db.templates.find_one(ObjectId(custom_id))
            single_template = json.loads(json_util.dumps(single_template))
            if single_template:
                single_template.pop("_id")
                return Response(response=json.dumps(single_template),
                                status=200,
                                mimetype='application/json')
            else:
                return jsonify({'msg': 'No item found with the given ID '}), 200

        else:

            templates_collection = db.templates.find()
            output = [{item: data[item] for item in data if item != '_id'} for data in templates_collection]
            return Response(response=json.dumps(output),
                            status=200,
                            mimetype='application/json')

    elif request.method == "PUT":
        if request.args.get('id'):
            # pdb.set_trace()
            custom_id = request.args.get('id')
            new_template = request.get_json()  # store the json body request
            print(new_template)
            db.templates.find_one_and_update(
                {"_id": ObjectId(custom_id)},
                {"$set":
                     new_template
                 }, upsert=True
            )
            return jsonify({'msg': 'item updated with the given ID '}), 200



    elif request.method == "DELETE":
        if request.args.get('id'):
            custom_id = request.args.get('id')
            single_template = db.templates.find_one(ObjectId(custom_id))
            if single_template:
                result = db.templates.delete_one({'_id': ObjectId(custom_id)})
                return jsonify({'msg': 'Template Deleted'}), 200
            else:
                return jsonify({'msg': 'No item found with the given ID '}), 200


if __name__ == '__main__':
    app.run(debug=True)

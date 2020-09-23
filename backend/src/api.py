import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc, and_
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

"""
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
"""
#db_drop_and_create_all()

## ROUTES
"""
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks", methods=["GET"])
def get_drinks():
    drinks = Drink.query.all()
    if not drinks:
        return (jsonify({"success": True, "drinks": []}), 200)
    short_drinks = [drink.short() for drink in drinks]
    return (jsonify({"success": True, "drinks": short_drinks}), 200)


"""
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks-detail", methods=["GET"])
@requires_auth("get:drinks-detail")
def get_drinks_detail(header):
    drinks = Drink.query.all()
    if not drinks:
        return (jsonify({"success": True, "drinks": []}), 200)
    drinks_detail = [drink.long() for drink in drinks]
    return (jsonify({"success": True, "drinks": drinks_detail}), 200)


"""
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def add_new_drink(payload):
    new_drink = request.get_json()
    if not new_drink["title"]:
        abort(422)
    drink_excited = Drink.query.filter(Drink.title == new_drink["title"]).all()
    if drink_excited:
        abort(409)
    for ingredient in new_drink["recipe"]:
        if not ingredient["name"]:
            abort(422)
    title = new_drink["title"]
    recipe = new_drink["recipe"]
    drink = Drink(title=title, recipe=json.dumps(recipe))
    try:
        drink.insert()
    except Exception:
        abort(500)
    return (jsonify({"success": True, "drinks": [drink.long()]}), 200)


"""
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(drink_id):
    drink_info = request.get_json()
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if not drink:
        abort(400)
    if "title" in drink_info:
        if not drink_info["title"]:
            abort(422)
        drink_excited = Drink.query.filter(
            and_(Drink.title == drink_info["title"], Drink.id != drink_id)
        ).all()
        if drink_excited:
            abort(409)
        drink.title = drink_info["title"]
    if "recipe" in drink_info:
        for ingrediet in drink_info["recipe"]:
            if not ingrediet["name"]:
                abort(422)
        drink.recipe = json.dumps(drink_info["recipe"])
    try:
        drink.update()
    except Exception:
        abort(500)
    return (jsonify({"success": True, "drinks": [drink.long()]}), 200)


"""
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
"""

@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if not drink:
        abort(404)
    try:
        drink.delete()
    except Exception:
        abort(500)
    return (jsonify({"success": True, "delete": drink_id}), 200)




## Error Handling
"""
Example error handling for unprocessable entity
"""


@app.errorhandler(422)
def unprocessable(error):
    return (
        jsonify({"success": False, "error": 422, "message": "unprocessable"}),
        422,
    )


"""
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

"""

"""
@TODO implement error handler for 404
    error handler should conform to general task above 
"""


@app.errorhandler(400)
def bad_request(error):
    return (
        jsonify(
            {"success": False, "error": 400, "message": "Bad request"}
        ),
        400,
    )


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify(
            {"success": False, "error": 404, "message": "Resouce not found"}
        ),
        404,
    )


@app.errorhandler(409)
def drink_conflict(error):
    return (
        jsonify({"success": False, "error": 409, "message": "Drink existed."}),
        409,
    )


@app.errorhandler(500)
def internal_server_error(error):
    return (
        jsonify(
            {
                "success": False,
                "error": 500,
                "message": "Internal server error",
            }
        ),
        500,
    )


"""
@TODO implement error handler for AuthError
    error handler should conform to general task above 
"""


@app.errorhandler(AuthError)
def autherror(error):
    json_error = error.error
    json_error["success"] = False
    return (jsonify(json_error), error.status_code)

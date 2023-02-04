import string

from functools import wraps
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from pymongo import MongoClient

client = MongoClient('localhost', 27017)

db = client.short_db

app = Flask(__name__)

def json_key(key,
             min: int = 1,
             max: int = 4096,
             var_type: type = str,
             required: bool = True,
             printable: bool = True):

    def wrapper(f):
        @wraps(f)
        def wrapper_function(*args, **kwargs):
            if request.json:
                value = request.json.get(key)
                if not value and required:
                    return {"text": f"Please specify a value for '{key}'!",
                            "error": f"invalid_{key}"}, 400
                elif not required:
                    value = value or None
            else:
                if required:
                    return {"text": "Bad request!",
                            "error": "bad_request"}, 400
                else:
                    value = None

            if value:
                if not isinstance(value, var_type):
                    try:
                        value = var_type(value)
                    except ValueError:
                        return {"text": (f"Value for '{key}' must be type "
                                         f"{var_type.__name__}!"),
                                "error": f"invalid_{key}"}, 400

                if len(str(value)) < min:
                    return {"text": (f"Value for '{key}' must be at least "
                                     f"{min} characters!"),
                            "error": f"invalid_{key}"}, 400

                if len(str(value)) > max:
                    return {"text": (f"Value for '{key}' must be at most "
                                     f"{max} characters!"),
                            "error": f"invalid_{key}"}, 400

                if printable and isinstance(value, str):
                    for chr in value:
                        if chr not in string.printable:
                            return {"text": f"Value for '{key}' uses invalid characters!",
                                    "error": f"invalid_{key}"}, 400

            return f(**{key: value}, **kwargs)
        return wrapper_function
    return wrapper


@app.route("/")
def index():
    return send_file("./index.html")


if __name__ == "__main__":
    app.run()
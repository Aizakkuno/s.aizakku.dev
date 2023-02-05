import string
import random

from functools import wraps
from flask import Flask, request, render_template, redirect
from pymongo import MongoClient

client = MongoClient('localhost', 27017)

db = client.short_db

app = Flask(__name__, template_folder="./static", static_url_path="/content", static_folder="./static/content")

def generate_code(n = 6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def validate_key(value,
                 key,
                 min: int = 1,
                 max: int = 4096,
                 var_type: type = str,
                 required: bool = True,
                 printable: bool = True):

    if not value and required:
        return {"text": f"Please specify a value for '{key}'!",
                "error": f"invalid_{key}"}, 400
    elif not required:
        value = value or None

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

    return True


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
    return render_template("index.html")


@app.route("/<string:code>")
def redirect_code(code):
    error = validate_key(code, "code")
    if error is not True:
        return error

    db_url = db.urls.find_one({"code": code})
    if not db_url:
        return redirect("/")

    return redirect(db_url["url"])


@app.route("/api/generate", methods=["POST"])
@json_key("url")
def api_generate(url):
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    db_url = db.urls.find_one({"url": url})
    if db_url:
        return {"code": db_url["code"]}

    code = generate_code()
    while db.urls.find({"code": code}):
        code = generate_code()

    db.urls.insert_one({"url": url, "code": code})

    return {"code": code}


if __name__ == "__main__":
    app.run()
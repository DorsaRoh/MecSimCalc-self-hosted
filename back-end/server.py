from contextlib import redirect_stdout
import importlib
import tempfile
from flask import Flask, jsonify, request
import os, json, io
import traceback


server = Flask(__name__)
APPS_PATH = "../apps"


@server.route("/apps", methods=["GET"])
def apps():
    # Load and return all json files from `apps` folder
    json_files = sorted([file for file in os.listdir(APPS_PATH) if file.endswith(".json")])
    response = []
    for json_file in json_files:
        try:
            with open(os.path.join(APPS_PATH, json_file), "r") as f:
                data = json.load(f)
            metadata = {key: data.get(key) for key in ["name", "description", "category", "tags", "primary_image"]}
            metadata["app_id"] = json_file  # the filename is the ID
            response.append(metadata)
        except json.JSONDecodeError as e:
            print(e)
            return f'"{json_file}" is not in a valid JSON format. Please fix this file', 500

    return jsonify(response), 200


@server.route("/app/<string:app_id>", methods=["GET", "POST"])
def app(app_id):
    try:
        with open(os.path.join(APPS_PATH, app_id + ".json"), "r") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(e)
        return f'"{app_id}" does not exist', 404

    if request.method == "GET":
        response = {
            key: data.get(key)
            for key in [
                "name",
                "description",
                "author",
                "category",
                "tags",
                "created_on",
                "updated_at",
                "primary_image",
                "favicon_image",
                "input_sections",
                "input_inputs",
                "input_layout",
                "output_html",
            ]
        }
    elif request.method == "POST":
        response = run_code(data.get("code"))
    return jsonify(response), 200


def run_code(code):
    response = {}
    # (1) Get user inputs as json
    inputs = request.get_json(force=True)
    with tempfile.NamedTemporaryFile(mode="w") as code_file:
        # (2) Write code to a temp file
        code_file.write(code)
        # (3) Capture stdout
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            # (4) Compile and run the app code
            try:
                # https://stackoverflow.com/a/67692
                # Compile the functions
                spec = importlib.util.spec_from_file_location("app_module", code_file.name)
                print("code_file.name", code_file.name)
                print("spec:", spec)
                script = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(script)
                # Execute the main() function
                response["outputs"] = script.main(inputs)
            except Exception as e:
                response["error"] = traceback.format_exc()
        response["stdout"] = stdout.getvalue()
    return response


if __name__ == "__main__":
    server.run(debug=True)
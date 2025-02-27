import io
import json
import os
import traceback
from contextlib import redirect_stdout

from flask import Flask, jsonify, request
from flask_cors import CORS

server = Flask(__name__)
CORS(server)

APPS_PATH = "../apps"


# GET: fetch all apps in `apps` folder
@server.route("/apps", methods=["GET"])
def apps():
    # Load and return all json files from `apps` folder
    json_files = sorted(
        [file for file in os.listdir(APPS_PATH) if file.endswith(".json")]
    )
    response = []
    for json_file in json_files:
        try:
            with open(os.path.join(APPS_PATH, json_file), "r") as f:
                data = json.load(f)
            metadata = {
                key: data.get(key)
                for key in [
                    "name",
                    "description",
                    "author",
                    "category",
                    "tags",
                    "favicon_image",
                    "primary_image",
                ]
            }
            metadata = {
                k: v for k, v in metadata.items() if v is not None
            }  # Remove None values
            metadata["app_id"] = os.path.splitext(json_file)[
                0
            ]  # the filename is the ID with `.json`
            response.append(metadata)
        except json.JSONDecodeError as e:
            print(f'"{json_file}" is not in a valid JSON format. Please fix this file')

    return jsonify(response), 200


# Run the python code and return its outputs and stdout
def run_code(code):

    response = {}
    # (1) Get user inputs as json
    inputs = request.get_json(force=True)
    # (3) Capture stdout
    stdout = io.StringIO()
    # with redirect_stdout(stdout):
        # (4) Compile and run the app code
    try:
        
        # note: have to do frontend on actual website, download json file, replace the hello_world.json
        # code here
        # Import necessary libraries
        import os 
        import openai

        from langchain.chains import ConversationalRetrievalChain, RetrievalQA
        from langchain.chat_models import ChatOpenAI
        from langchain.document_loaders import DirectoryLoader, TextLoader
        from langchain.embeddings import OpenAIEmbeddings
        from langchain.indexes import VectorstoreIndexCreator
        from langchain.indexes.vectorstore import VectorStoreIndexWrapper
        from langchain.llms import OpenAI
        from langchain.vectorstores import Chroma

        import streamlit as st 
        from langchain.llms import OpenAI
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain, SequentialChain 
        from langchain.memory import ConversationBufferMemory
        from langchain.utilities import WikipediaAPIWrapper 

        from pdfreader import PDFDocument, SimplePDFViewer
        

        response["outputs"] = clean_json(outputs)
    except Exception as e:
        response["error"] = traceback.format_exc()
    response["stdout"] = stdout.getvalue()
    return response


# Handles TypeError: not JSON serializable
def clean_json(dirty_json):
    def set_default(obj):
        import numpy as np
        import pandas as pd

        if isinstance(obj, (set, pd.core.series.Series, np.ndarray)):
            return list(obj)  # convert list
        else:
            try:
                return str(obj)  # As last resort, cast to string
            except Exception as e:
                raise TypeError

    return json.loads(json.dumps(dirty_json, default=set_default))


# GET: get a specific app with `app_id`
# POST: run the code of the specific app with inputs and returns the outputs
@server.route("/app/<string:app_id>", methods=["GET", "POST"])
def app(app_id):
    print("IN APP/")
    try:
        with open(os.path.join(APPS_PATH, app_id + ".json"), "r") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(e)
        return f'"{app_id}" does not exist', 404
    except json.JSONDecodeError as e:
        return (
            f'"{app_id}.json" is not in a valid JSON format. Please fix this file',
            500,
        )

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
        response = {
            k: v for k, v in response.items() if v is not None
        }  # Remove None values
        response["app_id"] = app_id
    elif request.method == "POST":
        print("working")
        response = run_code(data.get("code"))
    return jsonify(response), 200


if __name__ == "__main__":
    # Start Flask server
    # Set DEBUG to False in production!
    server.run(debug=True)

import os
import uuid
import boto3
import requests
from flask import *
from flask_cors import CORS
from flask_cors import cross_origin
from module.AWS import Aws
from module.video import *
from threading import Thread

app = Flask(
    __name__, static_folder="static", static_url_path="/", template_folder="templates"
)

CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploadvideo", methods=["PUT"])
# @cross_origin(origins=["https://www.leo145x.com"])
def upload():
    file = request.files["file"]

    if not file:
        return make_response({"ok": False, "message": "沒有檔案被上傳"}, 400)

    client_file_name = file.filename
    id = request.form.get("id")

    # save file by uuid
    filename = str(uuid.uuid4())
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename + ".mp4")
    file.save(file_path)

    # Solving video detection by thread
    thread = Thread(
        target=async_video_porcessing, args=(file_path, filename, client_file_name, id)
    )
    thread.start()

    return make_response({"ok": True, "message": "影片處理中"}, 200)


def async_video_porcessing(file_path, filename, client_file_name, id):
    with app.app_context():
        result_path, label_path = make_video(file_path, filename)
        try:
            # upload video to s3 bucket
            with open(result_path, "rb") as f:
                s3.upload_fileobj(f, aws.get_bucket_name(), f"{filename}.mp4")

            # transmit file info to ec2 sever
            with open(label_path, "rb") as f:
                s3.upload_fileobj(f, aws.get_bucket_name(), f"{filename}.csv")

            file_size = convert_size(os.path.getsize(result_path))

            url = "https://leo145x.com/fileAdmin/fileInfoPort"
            info = {
                "ok": True,
                "client_file_name": client_file_name,
                "file_uuid": aws.get_origin_url() + filename + ".mp4",
                "file_size": file_size,
                "file_label": aws.get_origin_url() + filename + ".csv",
                "id": id,
            }
            headers = {"Content-Type": "application/json"}
            requests.put(url, data=json.dumps(info), headers=headers)

        except Exception as e:
            requests.put(
                url, data=json.dumps({"ok": False, "message": str(e)}), headers=headers
            )


if __name__ == "__main__":
    aws = Aws()
    session = boto3.Session(
        aws_access_key_id=aws.get_access_key(),
        aws_secret_access_key=aws.get_secret_key(),
        region_name=aws.get_bucket_region(),
    )
    s3 = session.client("s3")
    app.json.ecsure_ascii = False
    app.config["UPLOAD_FOLDER"] = "temp_video"
    app.config["RESULT_FOLDER"] = "detect_video"
    app.config["LABEL_FOLDER"] = "labels"
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["JSON_SORT_KEYS"] = False
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["RESULT_FOLDER"], exist_ok=True)
    os.makedirs(app.config["LABEL_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=3000, debug=True)

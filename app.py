import argparse
import os

from flask import *
from flask_cors import CORS
from waitress import serve

from crawler.playwright_crawler import playwright_main
from crawler.wget_crawler import wget_main

app = Flask(__name__)
# Jsonで日本語が使えるようにする
app.config["JSON_AS_ASCII"] = False
CORS(app)


# 保存されている一覧を返す
@app.route("/saved", methods=["GET"])
def saved():
    print(request.environ["REMOTE_ADDR"])
    try:
        # Saved内のディレクトリ一覧
        dirs: list[str] = os.listdir("./Saved/")

        # Saved内の各ディレクトリのinfo.txtの読み取り
        response = {"saved": [], "cnt": 0}
        for directory in dirs:
            with open(f"./Saved/{directory}/info.txt") as f:
                date = f.readline().replace("\n", "").replace("発見：", "")
                url = f.readline().replace("\n", "").replace("URL：", "")
                target = f.readline().replace("\n", "").replace("対象：", "")
                gsb = f.readline().replace("\n", "").replace("GSB：", "")
                response["saved"].append({"dir": directory, "date": date, "url": url, "target": target, "gsb": gsb})
                response["cnt"] += 1

        return jsonify(response)
    except FileNotFoundError as e:
        return jsonify({"saved": ["Saved directory is not found"]})


# 保存されているzipのダウンロード
@app.route("/saved/download", methods=["GET"])
def saved_download():
    file = request.args.get("name")
    return send_file(f"./Saved/{file}/{file}.zip")


# 保存
@app.route("/save", methods=["POST"])
async def save():
    mode = request.json["mode"]
    url = request.json["url"]
    target = request.json["target"]
    gsb = request.json["gsb"]

    if mode == "wget":
        filename = await wget_main(url=url, target=target, gsb=gsb)
    elif mode == "playwright":
        filename = await playwright_main(url=url, target=target, gsb=gsb)
    else:
        filename = "error"

    return filename


def arg_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", action='store_true')
    parsed = parser.parse_args()
    return parsed


if __name__ == '__main__':
    if arg_parser().d:
        print("http://127.0.0.1:8000")

    serve(app, host='0.0.0.0', port=8000)

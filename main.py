from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import os
import math
from collections import Counter
import re

app = Flask(__name__)
app.secret_key = "sk"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def proc_text(filename):

    with open(
        os.path.join(app.config["UPLOAD_FOLDER"], filename), "r", encoding="utf-8"
    ) as file:
        text = file.read().lower()

    words = re.findall(r"\b\w+\b", text)

    word_counts = Counter(words)
    total_words = len(words)

    unique_words = len(word_counts)

    results = []
    for word, count in word_counts.items():
        tf = count / total_words

        idf = math.log(unique_words / 1)

        tfidf = tf * idf

        results.append(
            {
                "word": word.lower(),
                "tf": count,
                "idf": round(idf, 4),
                "tfidf": round(tfidf, 4),
            }
        )

    results.sort(key=lambda x: x["idf"], reverse=True)

    return results[:50], total_words


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("Файл не выбран")
            return render_template("index.html")

        files = request.files.getlist("file")
        if not files or files[0].filename == "":
            flash("Файл не выбран")
            return render_template("index.html")

        all_results = []
        total_words_count = 0
        processed_filenames = []

        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            try:
                results, total_words = proc_text(filename)
                processed_filenames.append(filename)

                for r in results:
                    r["filename"] = filename

                all_results.extend(results)
                total_words_count += total_words

                os.remove(file_path)
            except Exception as e:
                flash(f"Ошибка при обработке файла {filename}: {str(e)}")

                if os.path.exists(file_path):
                    os.remove(file_path)

        if all_results:

            all_results.sort(key=lambda x: x["idf"], reverse=True)

            all_results = all_results[:50]
            return render_template(
                "index.html",
                results=all_results,
                filenames=processed_filenames,
                total_words=total_words_count,
            )
        else:
            return render_template("index.html")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=2222)

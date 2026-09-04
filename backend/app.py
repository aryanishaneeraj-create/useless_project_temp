from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import tempfile
from pathlib import Path

from backend.detect import inspect_image

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
#                    FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder=str(BASE_DIR),
    static_url_path=""
)

CORS(app)


# Maximum upload size: 10 MB

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ============================================================
#                    HOME / HEALTH CHECK / UI
# ============================================================

@app.route("/", methods=["GET"])
def home():
    # If accessed from a web browser, serve index.html
    if request.accept_mimetypes.accept_html and not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        index_file = BASE_DIR / "index.html"
        if index_file.exists() and index_file.stat().st_size > 10:
            return send_from_directory(str(BASE_DIR), "index.html")

    return jsonify({
        "status": "online",
        "message": "SADYA AUDITOR BACKEND IS RUNNING 🚨"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "message": "SADYA AUDITOR BACKEND IS RUNNING 🚨"
    })


# ============================================================
#                    AUDIT ENDPOINT
# ============================================================

@app.route("/audit", methods=["POST"])
def audit():

    # Check whether an image was uploaded.

    if "image" not in request.files:

        return jsonify({

            "error":
                "No image uploaded."

        }), 400


    image = request.files["image"]


    # Check filename.

    if image.filename == "":

        return jsonify({

            "error":
                "No image selected."

        }), 400


    # --------------------------------------------------------
    # Create temporary file
    # --------------------------------------------------------

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".jpg"
    )

    temp_path = temp_file.name

    # IMPORTANT:
    # Close the file immediately.
    #
    # Windows does not allow os.remove() on a file
    # that is still open by this process.

    temp_file.close()


    try:

        # Save uploaded image.

        image.save(temp_path)


        print("\n")
        print("=" * 50)

        print(
            "NEW SADYA AUDIT REQUEST"
        )

        print("=" * 50)


        # ----------------------------------------------------
        # Run YOLOE + Sadya Auditor
        # ----------------------------------------------------

        result = inspect_image(
            temp_path
        )


        print(
            f"Score: {result['score']}/100"
        )

        print(
            f"Dishes: "
            f"{result['dishes_detected']}"
        )

        print(
            f"Verdict: "
            f"{result['verdict']}"
        )


        # ----------------------------------------------------
        # Send result to frontend
        # ----------------------------------------------------

        return jsonify(result)


    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )


        return jsonify({

            "error":
                "Something went wrong "
                "while auditing the Sadya.",

            "details":
                str(e)

        }), 500


    finally:

        # ----------------------------------------------------
        # Delete temporary uploaded image
        # ----------------------------------------------------

        if os.path.exists(temp_path):

            try:

                os.remove(temp_path)

            except PermissionError:

                print(
                    "Warning: Could not delete "
                    "temporary image immediately."
                )


# ============================================================
#                    START SERVER
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
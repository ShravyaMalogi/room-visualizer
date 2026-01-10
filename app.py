from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    send_from_directory,
    abort
)
from PIL import Image
import os
import cv2
import numpy as np

from room_processing import *
from texture_mapping import (
    get_wall_corners,
    map_texture,
    load_texture,
    image_resize
)
from wall_segmentation.segmenation import wall_segmenting, build_model
from wall_estimation.estimation import wall_estimation


# --------------------------------------------------
# App init
# --------------------------------------------------
app = Flask(__name__)

# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMG_FOLDER = os.path.join(BASE_DIR, "static", "IMG")
DATA_FOLDER = os.path.join(BASE_DIR, "static", "data")
TEXTURE_LIBRARY = os.path.join(BASE_DIR, "test_images", "textures")

ROOM_IMAGE = os.path.join(IMG_FOLDER, "room.jpg")
TEXTURED_ROOM_PATH = os.path.join(IMG_FOLDER, "textured_room.jpg")

MASK_PATH = os.path.join(DATA_FOLDER, "image_mask.npy")
CORNERS_PATH = os.path.join(DATA_FOLDER, "corners_estimation.npy")


# --------------------------------------------------
# Load model once
# --------------------------------------------------
model = build_model()


# --------------------------------------------------
# Home
# --------------------------------------------------
@app.route("/")
def main():
    return redirect("/room")


# --------------------------------------------------
# Upload room image + segmentation
# --------------------------------------------------
@app.route("/prediction", methods=["POST"])
def predict_image_room():
    try:
        if "file" in request.files and request.files["file"].filename != "":
            img_stream = request.files["file"].stream

            img = Image.open(img_stream)
            img = np.asarray(img)

            if img.shape[0] > 600:
                img = image_resize(img, height=600)

            img = Image.fromarray(img)

            # ✅ SAVE ONLY ROOM IMAGE
            img.save(ROOM_IMAGE)

            # Wall segmentation
            mask1 = wall_segmenting(model, ROOM_IMAGE)

            estimation_map = wall_estimation(ROOM_IMAGE)
            corners = get_wall_corners(estimation_map)

            mask2 = np.zeros(mask1.shape, dtype=np.uint8)
            for pts in corners:
                cv2.fillPoly(mask2, [np.array(pts)], 255)

            mask = mask1 & np.bool_(mask2)

            np.save(MASK_PATH, mask)
            np.save(CORNERS_PATH, np.array(corners))

        return redirect("/room")

    except Exception as e:
        print(e)
        return "Error", 500


# --------------------------------------------------
# Room visualizer
# --------------------------------------------------
@app.route("/room")
def room():
    textures = [
        f for f in os.listdir(TEXTURE_LIBRARY)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    # ✅ SHOW UPLOADED IMAGE FIRST
    if os.path.isfile(TEXTURED_ROOM_PATH):
        room_image = "/static/IMG/textured_room.jpg"
    elif os.path.isfile(ROOM_IMAGE):
        room_image = "/static/IMG/room.jpg"
    else:
        room_image = ""

    return render_template(
        "index.html",
        room=room_image,
        textures=textures
    )


# --------------------------------------------------
# Apply texture (CLICK)
# --------------------------------------------------
@app.route("/result_textured", methods=["POST"])
def result_textured():

    data = request.get_json()
    texture_name = os.path.basename(data["texture"])
    texture_path = os.path.join(TEXTURE_LIBRARY, texture_name)

    if not os.path.isfile(ROOM_IMAGE):
        return jsonify({"state": "error", "msg": "Upload room first"}), 400

    img = load_img(ROOM_IMAGE)
    corners = np.load(CORNERS_PATH)
    mask = np.load(MASK_PATH)

    texture = load_texture(texture_path, 6, 6)
    textured = map_texture(texture, img, corners, mask)
    out = brightness_transfer(img, textured, mask)

    # ✅ TEXTURED IMAGE CREATED ONLY HERE
    save_image(out, TEXTURED_ROOM_PATH)

    return jsonify({
        "state": "success",
        "room_path": "/static/IMG/textured_room.jpg"
    })


# --------------------------------------------------
# Serve textures
# --------------------------------------------------
@app.route("/textures/<path:filename>")
def serve_texture(filename):
    return send_from_directory(TEXTURE_LIBRARY, filename)


# --------------------------------------------------
# Run
# --------------------------------------------------
if __name__ == "__main__":
    app.run(port=9000, debug=True)

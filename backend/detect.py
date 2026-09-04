from ultralytics import YOLOE

from backend.auditor import (
    get_zone,
    audit_item,
    generate_roast
)


import os
from pathlib import Path
import torch

# ============================================================
#                    MODEL SETUP
# ============================================================

# Resolve model path dynamically from project root or environment
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "yoloe-11s-seg.pt"
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    str(DEFAULT_MODEL_PATH) if DEFAULT_MODEL_PATH.exists() else "yoloe-11s-seg.pt"
)
EMBEDDINGS_FILE = Path(__file__).resolve().parent / "dish_embeddings.pt"



# ============================================================
#                    DISH PROMPTS
# ============================================================

DISH_PROMPTS = {

    "avial": [
        "Kerala avial",
        "avial vegetable curry"
    ],

    "thoran": [
        "Kerala thoran",
        "vegetable thoran"
    ],

    "pachadi": [
        "Kerala pachadi",
        "yogurt coconut pachadi"
    ],

    "kichadi": [
        "Kerala kichadi",
        "coconut yogurt kichadi"
    ],

    "olan": [
        "Kerala olan",
        "ash gourd olan curry"
    ],

    "kalan": [
        "Kerala kalan",
        "yogurt coconut kalan curry"
    ],

    "sambar": [
        "Kerala sambar",
        "South Indian sambar"
    ],

    "parippu": [
        "Kerala parippu curry",
        "dal curry"
    ],

    "pickle": [
        "Kerala pickle",
        "Indian pickle"
    ],

    "payasam": [
        "Kerala payasam",
        "Indian rice pudding"
    ],

    "papad": [
        "papad",
        "papadum"
    ],

    "banana": [
        "banana",
        "banana slices"
    ],

    "rice": [
        "steamed rice",
        "white rice"
    ]
}


# ============================================================
#              CREATE YOLOE PROMPT LIST
# ============================================================

PROMPTS = []

PROMPT_TO_DISH = {}


for dish, descriptions in DISH_PROMPTS.items():

    for description in descriptions:

        PROMPTS.append(description)

        PROMPT_TO_DISH[description] = dish


# ============================================================
#                 LAZY MODEL LOADER
# ============================================================

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading Sadya Auditor model from {MODEL_PATH}...", flush=True)
        m = YOLOE(MODEL_PATH)
        if EMBEDDINGS_FILE.exists():
            print(f"Loading precomputed dish embeddings from {EMBEDDINGS_FILE}...", flush=True)
            pe = torch.load(str(EMBEDDINGS_FILE), weights_only=True)
            m.set_classes(PROMPTS, pe)
        else:
            print("Warning: precomputed embeddings not found, computing via text encoder...", flush=True)
            m.set_classes(PROMPTS)
        _model = m
        print("Sadya Auditor model ready!", flush=True)
    return _model


# ============================================================
#                    INSPECT IMAGE
# ============================================================

def inspect_image(image_path):

    print(f"Inspecting image: {image_path}", flush=True)

    # --------------------------------------------------------
    # Run YOLOE
    # --------------------------------------------------------

    model = get_model()

    results = model.predict(
        source=image_path,
        conf=0.15,
        imgsz=1024,
        max_det=50,
        verbose=False,
        save=False
    )


    all_results = []


    # --------------------------------------------------------
    # Process results
    # --------------------------------------------------------

    for result in results:

        width = result.orig_shape[1]
        height = result.orig_shape[0]


        # Keep only the strongest detection
        # for each dish.

        best_detections = {}


        for box in result.boxes:

            class_id = int(box.cls[0])

            confidence = float(box.conf[0])

            raw_name = result.names[class_id]


            # Convert the YOLOE prompt back
            # into our normal dish name.

            name = PROMPT_TO_DISH.get(
                raw_name,
                raw_name
            )


            # Get bounding box coordinates.

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )


            # Calculate center of the detected object.

            center_x = (x1 + x2) / 2

            center_y = (y1 + y2) / 2


            # Determine where the dish is
            # on the banana leaf.

            zone = get_zone(
                center_x,
                center_y,
                width,
                height
            )


            detection = {

                "name": name,

                "confidence": confidence,

                "x": round(center_x),

                "y": round(center_y),

                "zone": zone
            }


            # ------------------------------------------------
            # Remove duplicate detections
            # ------------------------------------------------

            if name not in best_detections:

                best_detections[name] = detection

            else:

                if (
                    confidence
                    >
                    best_detections[name]["confidence"]
                ):

                    best_detections[name] = detection


        # Convert dictionary to list.

        detected_items = list(
            best_detections.values()
        )


        # Round confidence values
        # only after selecting the best detection.

        for item in detected_items:

            item["confidence"] = round(
                item["confidence"],
                2
            )


        # ====================================================
        #                 AUDIT EACH DISH
        # ====================================================

        for item in detected_items:

            audit_result = audit_item(

                item["name"],

                item["x"],

                item["y"],

                width,

                height

            )


            item["status"] = (
                audit_result["status"]
            )

            item["message"] = (
                audit_result["message"]
            )


        # ====================================================
        #                 FINAL SADYA AUDIT
        # ====================================================

        final_report = generate_roast(
            detected_items
        )


        # ====================================================
        #                 JSON RESPONSE
        # ====================================================

        response = {

            "score":
                final_report["score"],

            "dishes_detected":
                len(detected_items),

            "dishes":
                detected_items,

            "violations":
                final_report["violations"],

            "verdict":
                final_report["verdict"]
        }


        all_results.append(response)


    # ========================================================
    #              NO RESULT FALLBACK
    # ========================================================

    if len(all_results) == 0:

        return {

            "score": 0,

            "dishes_detected": 0,

            "dishes": [],

            "violations": [

                "The auditor found absolutely nothing."

            ],

            "verdict":
                "This banana leaf has defeated artificial intelligence."

        }


    # Return the result for the uploaded image.

    return all_results[0]
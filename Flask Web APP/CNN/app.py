import io
import json
import base64
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# Global variable to hold the model
model = None

def load_model_function():
    global model
    try:
        import os
        from keras.layers import Dropout
        from keras.models import load_model
        from keras.utils import custom_object_scope

        # Define your FixedDropout class
        class FixedDropout(Dropout):
            def __init__(self, rate, **kwargs):
                super(FixedDropout, self).__init__(rate, **kwargs)
    
            def _get_noise_shape(self, inputs):
                return (inputs.shape[0], 1, 1, 1)

        # Load the model with custom objects
        model = load_model("B:\OneDrive - Amity University\Desktop\FLASK WEB APP\CNN\efficientnet-b0-Plant Village Disease-99.73.h5", 
                           custom_objects={'FixedDropout': FixedDropout})
        print("* Model Loaded!")
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None

# Load the model when the application starts
print("Loading Model...")
load_model_function()

# Ensure image size is 125x125 for compatibility with the model
def preprocess_image(image, target_size=(125, 125)):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)  # Resize to the correct target size (125x125)
    image = np.array(image)
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image

@app.route("/predict", methods=["POST","GET"])
def predict():
    print("Received POST request")
    global model
    if model is None:
        return jsonify({"error": "Model not loaded. Please try again later."}), 503
    
    try:
        message = request.get_json(force=True)
        encoded = message['image']
        decoded = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(decoded))
        processed_image = preprocess_image(image, target_size=(125, 125))  # Resize to 125x125
        
        # Make the prediction
        prediction = model.predict(processed_image).tolist()[0]  # Get the list of predictions
        
        # Filter out predictions with confidence less than 0.30
        disease_labels = [
            'Apple___Apple_scab',
            'Apple___Black_rot',
            'Apple___Cedar_apple_rust',
            'Apple___healthy',
            'Blueberry___healthy',
            'Cherry_including_sour___healthy',
            'Cherry_including_sour___Powdery_mildew',
            'Corn_maize___Cercospora_leaf_spot_Gray_leaf_spot',
            'Corn_maize___Common_rust_',
            'Corn_maize___Northern_Leaf_Blight',
            'Corn_maize___healthy',
            'Grape___Black_rot',
            'Grape___Esca_Black_Measles',
            'Grape___Leaf_blight_Isariopsis_Leaf_Spot',
            'Grape___healthy',
            'Orange___Haunglongbing_Citrus_greening',
            'Peach___Bacterial_spot',
            'Peach___healthy',
            'Pepper_bell___Bacterial_spot',
            'Pepper_bell___healthy',
            'Potato___Early_blight',
            'Potato___Late_blight',
            'Potato___healthy',
            'Raspberry___healthy',
            'Rice__Bacterial_blight',
            'Rice__Blast',
            'Rice__Brownspot',
            'Rice__Healthy',
            'Rice__Tungro',
            'Soybean___healthy',
            'Squash___Powdery_mildew',
            'Strawberry___Leaf_scorch',
            'Strawberry___healthy',
            'Sugarcane__Healthy',
            'Sugarcane__Mosaic',
            'Sugarcane__RedRot',
            'Sugarcane__Rust',
            'Sugarcane__Yellow',
            'Tomato___Bacterial_spot',
            'Tomato___Early_blight',
            'Tomato___Late_blight',
            'Tomato___Leaf_Mold',
            'Tomato___Septoria_leaf_spot',
            'Tomato___Spider_mites_Two-spotted_spider_mite',
            'Tomato___Target_Spot',
            'Tomato___Tomato_mosaic_virus',
            'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
            'Tomato___healthy'
        ]

        
        response = {
            'prediction': {
                label: pred for label, pred in zip(disease_labels, prediction) if pred >= 0.30
            }
        }
        
        # If no prediction is >= 0.30, provide a warning
        if not response['prediction']:
            response['warning'] = "No predictions with confidence higher than 0.30"
        
        return jsonify(response)
    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400
from flask_cors import CORS
CORS(app)

@app.route('/')
def home():
    return redirect('/static/plantdisease.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8000)


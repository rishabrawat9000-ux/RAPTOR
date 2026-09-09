import pickle
import tensorflow as tf


MODEL_PATH = r"C:\code\inference\models\world_model.keras"
SCALER_PATH = r"C:\code\inference\models\state_scaler.pkl"
ENCODER_PATH = r"C:\code\inference\models\stage_encoder.pkl"


print("=" * 60)
print("RAPTOR MODEL INSPECTION")
print("=" * 60)


# --------------------------------------------------
# 1. Load model
# --------------------------------------------------

print("\n[1] Loading world model...")

model = tf.keras.models.load_model(MODEL_PATH)

print("Model loaded successfully.")
print("\nModel summary:\n")

model.summary()


# --------------------------------------------------
# 2. Model input/output information
# --------------------------------------------------

print("\n" + "=" * 60)
print("MODEL INPUT / OUTPUT")
print("=" * 60)

print("\nInput:")
print(model.input)

print("\nInput shape:")
print(model.input_shape)

print("\nOutputs:")
print(model.output)

print("\nOutput shapes:")
print(model.output_shape)


# --------------------------------------------------
# 3. Load scaler
# --------------------------------------------------

print("\n" + "=" * 60)
print("STATE SCALER")
print("=" * 60)

import joblib

scaler = joblib.load(SCALER_PATH)

print("Scaler type:", type(scaler))

if hasattr(scaler, "n_features_in_"):
    print("Features:", scaler.n_features_in_)

if hasattr(scaler, "mean_"):
    print("Mean shape:", scaler.mean_.shape)

if hasattr(scaler, "scale_"):
    print("Scale shape:", scaler.scale_.shape)


# --------------------------------------------------
# 4. Load stage encoder
# --------------------------------------------------

# --------------------------------------------------
# 4. Load stage encoder
# --------------------------------------------------

print("\n" + "=" * 60)
print("STAGE ENCODER")
print("=" * 60)

encoder = joblib.load(ENCODER_PATH)

print("Encoder type:", type(encoder))

if hasattr(encoder, "classes_"):
    print("Classes:")
    print(encoder.classes_)

if hasattr(encoder, "categories_"):
    print("Categories:")
    print(encoder.categories_)


print("\n" + "=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)
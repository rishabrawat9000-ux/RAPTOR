import os
import numpy as np
import joblib
import tensorflow as tf


# ============================================================
# Paths
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "inference",
    "models",
    "world_model.keras"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "inference",
    "models",
    "state_scaler.pkl"
)

ENCODER_PATH = os.path.join(
    BASE_DIR,
    "inference",
    "models",
    "stage_encoder.pkl"
)


# ============================================================
# Load RAPTOR artifacts
# ============================================================

print("Loading RAPTOR model...")

model = tf.keras.models.load_model(MODEL_PATH)

scaler = joblib.load(SCALER_PATH)

stage_encoder = joblib.load(ENCODER_PATH)

print("RAPTOR model loaded.")
print("Scaler:", type(scaler).__name__)
print("Stage classes:", stage_encoder.classes_)


# ============================================================
# Prediction function
# ============================================================

def predict_state(sequence):
    """
    Predict the next network state and attack-related outputs.

    Parameters
    ----------
    sequence : array-like
        Shape must be (20, 27)

    Returns
    -------
    dict
        RAPTOR prediction results.
    """

    sequence = np.asarray(sequence, dtype=np.float32)

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if sequence.shape != (20, 27):
        raise ValueError(
            f"Expected sequence shape (20, 27), "
            f"got {sequence.shape}"
        )

    # --------------------------------------------------------
    # Scale each temporal state
    # --------------------------------------------------------

    original_shape = sequence.shape

    sequence_2d = sequence.reshape(-1, 27)

    sequence_scaled = scaler.transform(sequence_2d)

    sequence_scaled = sequence_scaled.reshape(original_shape)

    # --------------------------------------------------------
    # Add batch dimension
    # --------------------------------------------------------

    model_input = np.expand_dims(sequence_scaled, axis=0)

    # Shape:
    # (1, 20, 27)

    # --------------------------------------------------------
    # Model inference
    # --------------------------------------------------------

    outputs = model.predict(
        model_input,
        verbose=0
    )

    next_state = outputs[0][0]

    attack_probability = float(
        outputs[1][0][0]
    )

    attack_ratio = float(
        outputs[2][0][0]
    )

    stage_probabilities = outputs[3][0]

    # --------------------------------------------------------
    # Stage prediction
    # --------------------------------------------------------

    stage_index = int(
        np.argmax(stage_probabilities)
    )

    stage_label = stage_encoder.inverse_transform(
        [stage_index]
    )[0]

    stage_confidence = float(
        stage_probabilities[stage_index]
    )

    # --------------------------------------------------------
    # Return results
    # --------------------------------------------------------

    return {
        "next_state": next_state.tolist(),

        "attack_probability": attack_probability,

        "attack_ratio": attack_ratio,

        "attack_stage": stage_label,

        "stage_confidence": stage_confidence,

        "stage_probabilities": (
            stage_probabilities.tolist()
        )
    }
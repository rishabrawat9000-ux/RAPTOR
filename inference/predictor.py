import os
import numpy as np
import joblib
import tensorflow as tf


# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

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


# =====================================================
# LOAD RAPTOR MODEL
# =====================================================

print("Loading RAPTOR model...")

model = tf.keras.models.load_model(
    MODEL_PATH
)


# =====================================================
# LOAD SCALER
# =====================================================

scaler = joblib.load(
    SCALER_PATH
)


# =====================================================
# LOAD STAGE ENCODER
# =====================================================

stage_encoder = joblib.load(
    ENCODER_PATH
)


print("RAPTOR model loaded.")

print(
    "Scaler:",
    type(scaler).__name__
)

print(
    "Scaler features:",
    scaler.n_features_in_
)

print(
    "Stage classes:",
    stage_encoder.classes_
)


# =====================================================
# SINGLE STATE PREDICTION
# =====================================================

def predict_state(sequence):

    sequence = np.asarray(
        sequence,
        dtype=np.float32
    )


    if sequence.shape != (20, 27):

        raise ValueError(
            f"Expected sequence shape (20,27), "
            f"got {sequence.shape}"
        )


    # -------------------------------------------------
    # SCALE
    # -------------------------------------------------

    original_shape = sequence.shape

    sequence_2d = sequence.reshape(
        -1,
        27
    )

    sequence_scaled = scaler.transform(
        sequence_2d
    )

    sequence_scaled = (
        sequence_scaled
        .reshape(original_shape)
    )


    # -------------------------------------------------
    # MODEL INPUT
    # -------------------------------------------------

    model_input = np.expand_dims(
        sequence_scaled,
        axis=0
    )


    outputs = model.predict(
        model_input,
        verbose=0
    )


    # -------------------------------------------------
    # NEXT STATE
    # -------------------------------------------------

    next_state = outputs[0][0]


    # -------------------------------------------------
    # ATTACK PROBABILITY
    # -------------------------------------------------

    attack_probability = float(
        np.clip(
            outputs[1][0][0],
            0.0,
            1.0
        )
    )


    # -------------------------------------------------
    # ATTACK RATIO
    # -------------------------------------------------

    attack_ratio = float(
        np.clip(
            outputs[2][0][0],
            0.0,
            1.0
        )
    )


    # -------------------------------------------------
    # ATTACK STAGE
    # -------------------------------------------------

    stage_probabilities = (
        outputs[3][0]
    )

    stage_index = int(
        np.argmax(
            stage_probabilities
        )
    )

    stage_label = (
        stage_encoder
        .inverse_transform(
            [stage_index]
        )[0]
    )

    stage_confidence = float(
        stage_probabilities[
            stage_index
        ]
    )


    return {

        "next_state":
            next_state.tolist(),

        "attack_probability":
            attack_probability,

        "attack_ratio":
            attack_ratio,

        "attack_stage":
            str(stage_label),

        "stage_confidence":
            stage_confidence,

        "stage_probabilities":
            stage_probabilities.tolist()

    }


# =====================================================
# FIVE-STEP RECURSIVE FORECAST
# =====================================================

def forecast_future_states(
    sequence,
    steps=5
):

    """
    Recursively forecast future network states.

    Input:
        sequence -> (20, 27)

    Output:
        t+1 ... t+steps
    """


    sequence = np.asarray(
        sequence,
        dtype=np.float32
    )


    # -------------------------------------------------
    # VALIDATE
    # -------------------------------------------------

    if sequence.shape != (20, 27):

        raise ValueError(
            f"Expected sequence shape (20,27), "
            f"got {sequence.shape}"
        )


    # -------------------------------------------------
    # SCALE INITIAL WINDOW
    # -------------------------------------------------

    sequence_scaled = scaler.transform(
        sequence
    ).astype(
        np.float32
    )


    predictions = []


    # =================================================
    # RECURSIVE LOOP
    # =================================================

    for step in range(steps):


        # ---------------------------------------------
        # MODEL INPUT
        # ---------------------------------------------

        model_input = np.expand_dims(
            sequence_scaled,
            axis=0
        ).astype(
            np.float32
        )


        # ---------------------------------------------
        # MODEL PREDICTION
        # ---------------------------------------------

        outputs = model.predict(
            model_input,
            verbose=0
        )


        # ---------------------------------------------
        # NEXT STATE
        # ---------------------------------------------

        next_state = np.asarray(
            outputs[0][0],
            dtype=np.float32
        )


        # ---------------------------------------------
        # ATTACK PROBABILITY
        # ---------------------------------------------

        attack_probability = float(
            np.clip(
                np.asarray(
                    outputs[1]
                ).reshape(-1)[0],
                0.0,
                1.0
            )
        )


        # ---------------------------------------------
        # ATTACK RATIO
        # ---------------------------------------------

        attack_ratio = float(
            np.clip(
                np.asarray(
                    outputs[2]
                ).reshape(-1)[0],
                0.0,
                1.0
            )
        )


        # ---------------------------------------------
        # STAGE
        # ---------------------------------------------

        stage_probabilities = np.asarray(
            outputs[3][0],
            dtype=np.float32
        ).reshape(-1)


        stage_index = int(
            np.argmax(
                stage_probabilities
            )
        )


        stage_label = (
            stage_encoder
            .inverse_transform(
                [stage_index]
            )[0]
        )


        stage_confidence = float(
            stage_probabilities[
                stage_index
            ]
        )


        # ---------------------------------------------
        # STORE
        # ---------------------------------------------

        predictions.append({

            "step":
                step + 1,

            "attack_probability":
                attack_probability,

            "attack_ratio":
                attack_ratio,

            "attack_stage":
                str(stage_label),

            "stage_confidence":
                stage_confidence,

            "stage_probabilities":
                stage_probabilities.tolist()

        })


        # ---------------------------------------------
        # ROLL WINDOW
        # ---------------------------------------------

        sequence_scaled = np.vstack([

            sequence_scaled[1:],

            next_state

        ]).astype(
            np.float32
        )


    return predictions
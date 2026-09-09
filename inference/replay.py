import os
import sys
import pandas as pd

# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, BASE_DIR)

from inference.predictor import predict_state


# =========================================================
# DATA PATH
# =========================================================

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "procesed",
    "02-14-2018_temporal_states.csv"
)


# =========================================================
# RAPTOR FEATURES
# Exact 27 features used by the trained model
# =========================================================

RAPTOR_FEATURES = [
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "TotLen Fwd Pkts",
    "TotLen Bwd Pkts",
    "Flow Byts/s",
    "Flow Pkts/s",
    "Flow Duration",
    "Fwd Pkt Len Mean",
    "Bwd Pkt Len Mean",
    "Fwd Pkt Len Std",
    "Bwd Pkt Len Std",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "SYN Flag Cnt",
    "ACK Flag Cnt",
    "RST Flag Cnt",
    "FIN Flag Cnt",
    "PSH Flag Cnt",
    "Pkt Len Min",
    "Pkt Len Max",
    "Pkt Len Mean",
    "Pkt Len Std",
    "Pkt Size Avg",
    "Dst Port",
    "Protocol"
]


# =========================================================
# LOAD TEMPORAL STATES
# =========================================================

def load_temporal_states():

    print("Loading temporal states...")

    df = pd.read_csv(DATA_PATH)

    missing = [
        col
        for col in RAPTOR_FEATURES
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing RAPTOR features: {missing}"
        )

    df["time_window"] = pd.to_datetime(
        df["time_window"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["time_window"]
    )

    df = df.sort_values(
        "time_window"
    ).reset_index(drop=True)

    return df


# =========================================================
# RUN ROLLING REPLAY
# =========================================================

def run_replay(
    df=None,
    max_predictions=None
):

    """
    Chronological one-step-ahead RAPTOR replay.

    For every temporal window:

        Previous 20 observed states
                    ↓
               RAPTOR LSTM
                    ↓
        Predict next network state
        Predict attack probability
        Predict attack ratio
        Predict attack stage

    The predicted state is NOT fed back into
    the following prediction.
    """

    if df is None:
        df = load_temporal_states()

    results = []

    total = len(df)

    # -----------------------------------------------------
    # First prediction requires 20 previous states
    # -----------------------------------------------------

    start_index = 20

    if max_predictions is not None:

        end_index = min(
            start_index + max_predictions,
            total
        )

    else:

        end_index = total

    prediction_count = (
        end_index - start_index
    )

    print(
        f"Temporal states loaded: {total}"
    )

    print(
        f"Running predictions: {prediction_count}"
    )

    print()


    # =====================================================
    # ROLL THROUGH THE DAY
    # =====================================================

    for i in range(
        start_index,
        end_index
    ):

        # -------------------------------------------------
        # Previous 20 observed states
        # -------------------------------------------------

        sequence_df = df.iloc[
            i - 20:i
        ]

        sequence = sequence_df[
            RAPTOR_FEATURES
        ].values


        # -------------------------------------------------
        # RAPTOR prediction
        # -------------------------------------------------

        prediction = predict_state(
            sequence
        )


        # -------------------------------------------------
        # Actual state at prediction time
        # -------------------------------------------------

        actual_row = df.iloc[i]


        # -------------------------------------------------
        # Store prediction
        # -------------------------------------------------

        result = {

            "time_window":
                str(
                    actual_row["time_window"]
                ),

            "attack_probability":
                prediction[
                    "attack_probability"
                ],

            "attack_ratio":
                prediction[
                    "attack_ratio"
                ],

            "attack_stage":
                prediction[
                    "attack_stage"
                ],

            "stage_confidence":
                prediction[
                    "stage_confidence"
                ],

            "actual_is_attack":
                int(
                    actual_row["IsAttack"]
                ),

            "actual_attack_ratio":
                float(
                    actual_row["attack_ratio"]
                ),

            "actual_attack_stage":
                str(
                    actual_row["AttackStage"]
                )
        }

        results.append(result)


        # -------------------------------------------------
        # Progress
        # -------------------------------------------------

        processed = len(results)

        if (
            processed % 100 == 0
            or processed == prediction_count
        ):

            print(
                f"Processed "
                f"{processed} / "
                f"{prediction_count}"
            )


    return pd.DataFrame(
        results
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("RAPTOR TEMPORAL REPLAY")
    print("=" * 60)

    print()


    # -----------------------------------------------------
    # RUN FULL DAY
    # -----------------------------------------------------

    results = run_replay(
        max_predictions=None
    )


    # =====================================================
    # SHOW FIRST 10
    # =====================================================

    print()

    print("=" * 60)
    print("FIRST 10 PREDICTIONS")
    print("=" * 60)

    print(
        results[
            [
                "time_window",
                "attack_probability",
                "attack_ratio",
                "attack_stage",
                "stage_confidence",
                "actual_is_attack",
                "actual_attack_stage"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


    # =====================================================
    # SAVE RESULTS
    # =====================================================

    output_path = os.path.join(
        BASE_DIR,
        "outputs",
        "raptor_replay.csv"
    )

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    results.to_csv(
        output_path,
        index=False
    )


    # =====================================================
    # SUMMARY
    # =====================================================

    print()

    print("=" * 60)
    print("REPLAY COMPLETE")
    print("=" * 60)

    print(
        f"Total predictions: {len(results)}"
    )

    print(
        f"Attack predictions: "
        f"{(results['attack_probability'] >= 0.5).sum()}"
    )

    print(
        f"Actual attack windows: "
        f"{results['actual_is_attack'].sum()}"
    )

    print()

    print(
        "Replay saved to:"
    )

    print(output_path)
import os
import numpy as np
import pandas as pd

from flask import Flask, render_template, jsonify

from inference.predictor import forecast_future_states


# =====================================================
# FLASK
# =====================================================

app = Flask(__name__)


# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TEMPORAL_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "02-14-2018_temporal_states.csv"
)

REPLAY_PATH = os.path.join(
    BASE_DIR,
    "outputs",
    "raptor_replay.csv"
)


# =====================================================
# EXACT 27 MODEL FEATURES
# =====================================================

FEATURES = [

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


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html"
    )


# =====================================================
# STATUS
# =====================================================

@app.route("/api/status")
def status():

    return jsonify({

        "system": "RAPTOR",

        "status": "online",

        "mode": "replay",

        "model": "LSTM"

    })


# =====================================================
# REPLAY DATA
# =====================================================

@app.route("/api/replay")
def replay():

    try:

        if not os.path.exists(
            REPLAY_PATH
        ):

            return jsonify({

                "error":
                    "Replay file not found",

                "path":
                    REPLAY_PATH

            }), 404


        df = pd.read_csv(
            REPLAY_PATH
        )


        # Convert NaN / inf safely
        df = df.replace(
            [np.inf, -np.inf],
            np.nan
        )

        df = df.fillna(0)


        # Convert timestamp to string
        if "time_window" in df.columns:

            df["time_window"] = (
                df["time_window"]
                .astype(str)
            )


        predictions = df.to_dict(orient="records")


        return jsonify({

            "predictions":
                predictions

        })


    except Exception as e:

        import traceback

        traceback.print_exc()


        return jsonify({

            "error":
                str(e)

        }), 500


# =====================================================
# FIVE-STEP FORECAST
# =====================================================

@app.route("/api/forecast/<int:index>")
def forecast(index):

    try:

        print()
        print(
            "=========================================="
        )

        print(
            f"RAPTOR FORECAST REQUEST: {index}"
        )

        print(
            "=========================================="
        )


        # -------------------------------------------------
        # CHECK INDEX
        # -------------------------------------------------

        if index < 0:

            return jsonify({

                "error":
                    "Index cannot be negative"

            }), 400


        # -------------------------------------------------
        # CHECK TEMPORAL DATASET
        # -------------------------------------------------

        if not os.path.exists(
            TEMPORAL_PATH
        ):

            raise FileNotFoundError(

                "Temporal state file not found:\n"
                + TEMPORAL_PATH

            )


        # -------------------------------------------------
        # LOAD TEMPORAL STATES
        # -------------------------------------------------

        df = pd.read_csv(
    TEMPORAL_PATH,
    engine="python",
    on_bad_lines="warn"
)


        print(
            "Temporal states:",
            len(df)
        )


        # -------------------------------------------------
        # CHECK FEATURES
        # -------------------------------------------------

        missing_features = [

            feature

            for feature in FEATURES

            if feature not in df.columns

        ]


        if missing_features:

            raise ValueError(

                "Missing model features: "
                + str(missing_features)

            )


        # -------------------------------------------------
        # 20-STATE INPUT WINDOW
        # -------------------------------------------------

        start_index = index

        end_index = index + 20


        if end_index > len(df):

            return jsonify({

                "error":
                    "Not enough temporal states "

                    f"for index {index}",

                "available_states":
                    len(df),

                "required_end":
                    end_index

            }), 400


        # -------------------------------------------------
        # EXTRACT 20 × 27
        # -------------------------------------------------

        sequence_df = (

            df[
                FEATURES
            ]

            .iloc[
                start_index:end_index
            ]

            .copy()

        )


        print(
            "Sequence dataframe shape:",
            sequence_df.shape
        )


        # -------------------------------------------------
        # NUMERIC CONVERSION
        # -------------------------------------------------

        sequence_df = (

            sequence_df

            .apply(
                pd.to_numeric,
                errors="coerce"
            )

            .replace(
                [np.inf, -np.inf],
                np.nan
            )

            .fillna(0)

        )


        sequence = (

            sequence_df

            .values

            .astype(
                np.float32
            )

        )


        print(
            "Model sequence shape:",
            sequence.shape
        )


        # -------------------------------------------------
        # SAFETY CHECK
        # -------------------------------------------------

        if sequence.shape != (
            20,
            27
        ):

            raise ValueError(

                "Invalid model input shape: "

                + str(sequence.shape)

            )


        # -------------------------------------------------
        # FIVE-STEP RECURSIVE FORECAST
        # -------------------------------------------------

        forecasts = forecast_future_states(

            sequence,

            steps=5

        )


        # -------------------------------------------------
        # ADD FUTURE TIMESTAMPS
        # -------------------------------------------------

        for prediction in forecasts:

            step = int(
                prediction["step"]
            )


            # The observed sequence occupies:
            #
            # index ... index + 19
            #
            # Therefore:
            #
            # t+1 = index + 20
            # t+2 = index + 21
            # ...
            # t+5 = index + 24

            future_index = (
                index + 19 + step
            )


            if future_index < len(df):

                timestamp = (

                    df.iloc[
                        future_index
                    ]["time_window"]

                )

                prediction[
                    "time_window"
                ] = str(
                    timestamp
                )

            else:

                prediction[
                    "time_window"
                ] = None


        # -------------------------------------------------
        # PRINT FORECAST
        # -------------------------------------------------

        print()

        print(
            "FIVE-STEP FORECAST"
        )

        print(
            "-------------------"
        )


        for prediction in forecasts:

            print(

                f"t+{prediction['step']} | "

                f"Probability: "
                f"{prediction['attack_probability']:.6f} | "

                f"Ratio: "
                f"{prediction['attack_ratio']:.6f} | "

                f"Stage: "
                f"{prediction['attack_stage']} | "

                f"Confidence: "
                f"{prediction['stage_confidence']:.6f}"

            )


        print()

        print(
            "Forecast successful."
        )


        return jsonify({

            "index":
                index,

            "forecast":
                forecasts

        })


    except Exception as e:

        import traceback


        print()

        print(
            "=========================================="
        )

        print(
            "RAPTOR FORECAST ERROR"
        )

        print(
            "=========================================="
        )


        traceback.print_exc()


        print(
            "=========================================="
        )

        print()


        return jsonify({

            "error":
                str(e)

        }), 500


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )

    print(
        "        RAPTOR PREDICTIVE CYBER DEFENCE"
    )

    print(
        "=========================================="
    )

    print(
        "Temporal data:",
        TEMPORAL_PATH
    )

    print(
        "Replay data:",
        REPLAY_PATH
    )

    print(
        "=========================================="
    )

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )
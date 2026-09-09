import pandas as pd

from predictor import predict_state


DATA_PATH = (
    r"C:\code\data\procesed"
    r"\02-14-2018_temporal_states.csv"
)


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
    "Protocol",
]


# ============================================================
# Load temporal states
# ============================================================

df = pd.read_csv(DATA_PATH)

print("Temporal states:", df.shape)


# ============================================================
# Verify features
# ============================================================

missing = [
    col for col in RAPTOR_FEATURES
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing RAPTOR features: {missing}"
    )


print("\nRAPTOR features:", len(RAPTOR_FEATURES))


# ============================================================
# Extract feature matrix
# ============================================================

features = df[RAPTOR_FEATURES].copy()

print("Feature matrix:", features.shape)


# ============================================================
# Take 20 consecutive temporal states
# ============================================================

sequence = features.iloc[
    0:20
].to_numpy()


print("\nSequence shape:", sequence.shape)


# ============================================================
# Run RAPTOR prediction
# ============================================================

prediction = predict_state(sequence)


# ============================================================
# Display result
# ============================================================

print("\n" + "=" * 60)
print("RAPTOR PREDICTION")
print("=" * 60)

print(
    f"\nAttack Probability : "
    f"{prediction['attack_probability']:.4f}"
)

print(
    f"Attack Ratio       : "
    f"{prediction['attack_ratio']:.4f}"
)

print(
    f"Attack Stage       : "
    f"{prediction['attack_stage']}"
)

print(
    f"Stage Confidence   : "
    f"{prediction['stage_confidence']:.4f}"
)

print(
    "\nStage Probabilities:"
)

print(
    prediction["stage_probabilities"]
)

print(
    "\nNext State shape:",
    len(prediction["next_state"])
)

print("\nNext State:")
print(prediction["next_state"])
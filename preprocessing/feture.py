import pandas as pd
import numpy as np



RAPTOR_FEATURES = [
    "Dst Port",
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "TotLen Fwd Pkts",
    "TotLen Bwd Pkts",
    "Flow Byts/s",
    "Flow Pkts/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd Pkt Len Mean",
    "Fwd Pkt Len Std",
    "Bwd Pkt Len Mean",
    "Bwd Pkt Len Std",
    "Pkt Len Min",
    "Pkt Len Max",
    "Pkt Len Mean",
    "Pkt Len Std",
    "Pkt Size Avg",
    "FIN Flag Cnt",
    "SYN Flag Cnt",
    "RST Flag Cnt",
    "ACK Flag Cnt",
    "Flow Duration",
    "Fwd Pkt Len Max",
    "Bwd Pkt Len Max"
]


def prepare_raptor_data(df):
    

    df = df.copy()

    print("Original shape:", df.shape)

    df.columns = df.columns.str.strip()

    required_columns = ["Timestamp", "Label"] + RAPTOR_FEATURES

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns:\n{missing}"
        )

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        dayfirst=True,
        errors="coerce"
    )

    before = len(df)

    df = df.dropna(subset=["Timestamp"]).copy()

    print(
        "Removed invalid timestamps:",
        before - len(df)
    )

    X = df[RAPTOR_FEATURES].copy()

    X = X.apply(
        pd.to_numeric,
        errors="coerce"
    )

    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )


    missing_before = X.isna().sum().sum()

    X = X.fillna(X.median())

    missing_after = X.isna().sum().sum()

    print("Missing feature values before:", missing_before)
    print("Missing feature values after:", missing_after)

    non_negative_features = [
        "Flow Duration",
        "Flow Byts/s",
        "Flow Pkts/s",
        "Flow IAT Mean",
        "Flow IAT Std",
        "Flow IAT Max",
        "Flow IAT Min",
        "Tot Fwd Pkts",
        "Tot Bwd Pkts",
        "TotLen Fwd Pkts",
        "TotLen Bwd Pkts"
    ]

    for col in non_negative_features:
        if col in X.columns:
            X.loc[X[col] < 0, col] = 0

    df[RAPTOR_FEATURES] = X

    df["IsAttack"] = (
        df["Label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .ne("benign")
        .astype(int)
    )

    df = df.sort_values(
        "Timestamp"
    ).reset_index(drop=True)

    X = df[RAPTOR_FEATURES].copy()

    print("\nFinal shape:", df.shape)
    print("Feature matrix:", X.shape)
    print("Number of RAPTOR features:", len(RAPTOR_FEATURES))

    print("\nAttack distribution:")
    print(df["IsAttack"].value_counts())

    print("\nLabel distribution:")
    print(df["Label"].value_counts())

    return df, X
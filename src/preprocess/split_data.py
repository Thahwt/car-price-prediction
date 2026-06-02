import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)

    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train_ratio", type=float, default=0.8)
    parser.add_argument("--val_ratio", type=float, default=0.1)
    parser.add_argument("--test_ratio", type=float, default=0.1)

    parser.add_argument("--target", type=str, default="price_log")
    parser.add_argument("--price_bins", type=int, default=5)
    parser.add_argument("--age_bins", type=int, default=5)  # CẬP NHẬT: Thay year_bins bằng age_bins
    parser.add_argument("--min_stratum_count", type=int, default=10)

    return parser.parse_args()


def check_ratio(train_ratio, val_ratio, test_ratio):
    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise ValueError("train_ratio + val_ratio + test_ratio must equal 1.0")


def cap_rare_values(series, min_count=20):
    counts = series.value_counts(dropna=False)
    valid_values = counts[counts >= min_count].index
    return series.where(series.isin(valid_values), "OTHER")


def make_bins(series, n_bins):
    return pd.qcut(series, q=n_bins, duplicates="drop").astype(str)


def build_stratify_column(df, args):
    brand = cap_rare_values(df["brand"].astype(str), args.min_stratum_count)

    model_key = (
            df["brand"].astype(str)
            + "__"
            + df["model"].astype(str)
    )
    model = cap_rare_values(model_key, args.min_stratum_count)

    price_bin = make_bins(df[args.target], args.price_bins)
    age_bin = make_bins(df["age"], args.age_bins)  # CẬP NHẬT: Dùng cột age

    stratify_col = (
            brand
            + "|"
            + model
            + "|"
            + price_bin
            + "|"
            + age_bin  # CẬP NHẬT: Ghép tuổi vào chuỗi stratify
    )

    counts = stratify_col.value_counts()
    rare_strata = counts[counts < args.min_stratum_count].index

    stratify_col = stratify_col.where(
        ~stratify_col.isin(rare_strata),
        brand + "|OTHER_MODEL|" + price_bin + "|" + age_bin  # CẬP NHẬT: Fallback với age_bin
    )

    counts = stratify_col.value_counts()
    rare_strata = counts[counts < args.min_stratum_count].index

    stratify_col = stratify_col.where(
        ~stratify_col.isin(rare_strata),
        brand + "|OTHER_MODEL|" + price_bin
    )

    counts = stratify_col.value_counts()
    rare_strata = counts[counts < args.min_stratum_count].index

    stratify_col = stratify_col.where(
        ~stratify_col.isin(rare_strata),
        "OTHER_BRAND|OTHER_MODEL|" + price_bin
    )

    return stratify_col


def split_data(df, stratify_col, args):
    train_df, temp_df = train_test_split(
        df,
        train_size=args.train_ratio,
        random_state=args.seed,
        stratify=stratify_col
    )

    temp_stratify = stratify_col.loc[temp_df.index]

    val_size = args.val_ratio / (args.val_ratio + args.test_ratio)

    val_df, test_df = train_test_split(
        temp_df,
        train_size=val_size,
        random_state=args.seed,
        stratify=temp_stratify
    )

    return train_df, val_df, test_df


def summarize_split(df, name, target):
    lines = []

    lines.append(f"===== {name.upper()} =====")
    lines.append(f"Rows: {len(df)}")
    lines.append(f"Columns: {len(df.columns)}")
    lines.append("")

    lines.append("[Target]")
    lines.append(str(df[target].describe()))
    lines.append("")

    # Thay "year" bằng "age" trong vòng lặp tóm tắt
    for col in ["brand", "model", "age"]:
        if col in df.columns:
            lines.append(f"[{col}]")
            lines.append(f"Unique: {df[col].nunique()}")
            lines.append("Top 20:")
            lines.append(str(df[col].value_counts().head(20)))
            lines.append("")

    lines.append("[Missing values]")
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    lines.append(str(missing if len(missing) else "No missing values"))
    lines.append("")

    return "\n".join(lines)


def save_split_summary(train_df, val_df, test_df, out_dir, target):
    content = []

    content.append(summarize_split(train_df, "train", target))
    content.append(summarize_split(val_df, "val", target))
    content.append(summarize_split(test_df, "test", target))

    with open(out_dir / "split_summary.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(content))


def save_schema(df, out_dir, args):
    schema = {
        "target": args.target,
        "categorical_features": [
            col for col in [
                "brand", "model", "trim", "status", "origin", "style",
                "transmission", "engine", "exterior_color",
                "interior_color", "drive"
            ]
            if col in df.columns
        ],
        "numerical_features": [
            col for col in [
                "age", "volume", "seats", "doors", "odo",  # CẬP NHẬT: Thay year bằng age
                "province", "lat", "lon"
            ]
            if col in df.columns
        ],
        "drop_features": [
            col for col in ["url", "date", "price_log"]
            if col in df.columns
        ],
        "split_logic": [
            "Stratify by brand",
            "Stratify by model inside brand",
            "Stratify by target price quantile bins",
            "Stratify by age quantile bins",  # CẬP NHẬT: Sửa nội dung log
            "Rare groups are collapsed into OTHER"
        ]
    }

    pd.Series(schema).to_json(
        out_dir / "schema.json",
        force_ascii=False,
        indent=4
    )


def main():
    args = parse_args()
    check_ratio(args.train_ratio, args.val_ratio, args.test_ratio)

    input_path = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)

    # Yêu cầu có cột "age" thay vì "year"
    required_cols = ["brand", "model", "age", args.target]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    stratify_col = build_stratify_column(df, args)

    train_df, val_df, test_df = split_data(df, stratify_col, args)

    train_df.to_csv(out_dir / "train.csv", index=False)
    val_df.to_csv(out_dir / "val.csv", index=False)
    test_df.to_csv(out_dir / "test.csv", index=False)

    save_schema(df, out_dir, args)
    save_split_summary(train_df, val_df, test_df, out_dir, args.target)

    print("Done.")
    print(f"Train: {len(train_df)}")
    print(f"Val:   {len(val_df)}")
    print(f"Test:  {len(test_df)}")
    print(f"Saved to: {out_dir}")


if __name__ == "__main__":
    main()
import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd


DRIVE_TOKENS = {
    "awd", "rwd", "fwd", "4wd", "2wd", "4x4", "4x2", "2x4", "4x", "2x",
    "rfd"  # dataset typo/variant seen in drive column
}

VI_TRANSLATE = {
    "tiêu chuẩn": "base",
    "dac biet": "special",
    "đặc biệt": "special",
    "cao cấp": "premium",
    "nâng cao": "advanced",
    "cửa trượt": "sliding door",
    "thùng bạt": "canvas box",
    "thùng kín": "closed box",
    "cứu thương": "ambulance",
    "trước": "fwd",
    "sau": "rwd",
    "số tay": "mt",
    "số tự động": "at",
}


def normalize_space(text: object) -> str:
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def replace_vi_terms(text: str) -> str:
    text = normalize_space(text)
    for vi, en in sorted(VI_TRANSLATE.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(vi)}(?!\w)", en, text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_drive_tokens(text: str) -> str:
    text = normalize_space(text)
    pattern = r"(?<!\w)(" + "|".join(re.escape(x) for x in sorted(DRIVE_TOKENS, key=len, reverse=True)) + r")(?!\w)"
    text = re.sub(pattern, " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_part(text: object, translate_vi: bool = False, remove_drive: bool = False) -> str:
    text = normalize_space(text)
    if translate_vi:
        text = replace_vi_terms(text)
    if remove_drive:
        text = remove_drive_tokens(text)
    return text


def should_replace_model_by_trim(model: str, trim: str) -> bool:
    if not model or not trim:
        return False
    return bool(re.search(r"\b(\d+\s*series|[a-z]{1,4}\s*class)\b$", model))


def build_name(row: pd.Series) -> str:
    brand = clean_part(row.get("brand", ""))
    model = clean_part(row.get("model", ""), remove_drive=True)
    trim = clean_part(row.get("trim", ""), translate_vi=True, remove_drive=True)

    if should_replace_model_by_trim(model, trim):
        parts = [brand, trim]
    else:
        parts = [brand, model, trim]

    name = " ".join(p for p in parts if p)
    return re.sub(r"\s+", " ", name).strip()


def fix_transmission(row: pd.Series) -> str:
    transmission = clean_part(row.get("transmission", ""), translate_vi=True)
    raw = " ".join([
        clean_part(row.get("model", "")),
        clean_part(row.get("trim", ""), translate_vi=True),
        transmission,
    ])
    if re.search(r"(?<!\w)cvt(?!\w)", raw):
        return "cvt"
    if transmission in {"manual", "mt"}:
        return "manual"
    if transmission in {"automatic", "at", "auto"}:
        return "automatic"
    return transmission


def transform(input_path: str, output_path: str) -> pd.DataFrame:
    df = pd.read_csv(input_path)

    required = {"brand", "model", "trim", "transmission"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["brand_clean"] = df["brand"].apply(clean_part)
    df["model_clean"] = df["model"].apply(lambda x: clean_part(x, remove_drive=True))
    df["trim_clean"] = df["trim"].apply(lambda x: clean_part(x, translate_vi=True, remove_drive=True))
    df["name"] = df.apply(build_name, axis=1)
    df["transmission"] = df.apply(fix_transmission, axis=1)
    df.drop(columns=["brand_clean", "model_clean", "trim_clean", "trim"], inplace=True)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    transform(args.input, args.output)


if __name__ == "__main__":
    main()

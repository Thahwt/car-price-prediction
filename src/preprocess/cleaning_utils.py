import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
import os
import matplotlib.pyplot as plt
import seaborn as sns

def duplicates_remv (df):
    """
    Hàm này dùng để loại bỏ trùng lặp.
    """
    df.drop_duplicates(inplace = True)
    return df

def impute_missing_fuel(df):
    """
    Sử dụng Random Forest để điền khuyết cột Fuel
    """

    # 1. Chuẩn bị các đặc trưng
    #---------------------------

    df_out = df.copy()

    # Chọn các đặc trưng cần
    FEATURES = ["brand", "model", "year", "odo"]
    TARGET = "fuel"

    # Điền các dòng bị khuyết tên xe thành "Unknown" để encoding không bị lỗi.
    df_out["model"] = df_out["model"].fillna("Unknown")

    # Chia train và test: train chứa các row đã có fuel, test chứa các row chưa có fuel.
    train_set = df_out[TARGET].notna()
    test_set = df_out[TARGET].isna()

    # optional
    print(f"Rows with known fuel  (train)  : {train_set.sum()}")
    print(f"Rows with missing fuel (predict): {test_set.sum()}")

    if test_set.sum() == 0:
        print("Không có giá trị khuyết ở cột Fuel.")
        return df_out

    # Encode brand và model
    le_brand = LabelEncoder()
    le_model = LabelEncoder()

    df_out["brand_enc"] = le_brand.fit_transform(df["brand"])
    df_out["model_enc"] = le_model.fit_transform(df["model"])

    # Feature matrix
    X = df_out[["brand_enc", "model_enc", "year", "odo"]]

    # Encode fuel:
    le_fuel = LabelEncoder()

    y_train = le_fuel.fit_transform(df_out.loc[train_set, TARGET]) # Target answer

    print(f"\nFuel classes detected: {list(le_fuel.classes_)}")


    # 2. Train model
    #----------------

    X_train = X[train_set]
    X_predict = X[test_set]

    # Khởi tạo model
    clf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    print(f"n_estimators : 50")
    print(f"Training rows: {X_train.shape[0]}")
    print(f"Features used: {X_train.shape[1]}  {FEATURES}")

    # Cross-validation:

    # Chia train thành 5 phần: 4 train/ 1 test
    cv_scores = cross_val_score(clf, X_train, y_train, cv=5, scoring="accuracy")

    # Accuracy trung bình
    print(f"Avg accuracy (5-Fold CV): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    # Accuracy từng phần
    print(f"Per-fold scores : {[round(float(s), 4) for s in cv_scores]}")


    # 3. Dự đoán & điền missing values
    #----------------------------------

    # Dự đoán
    y_pred = clf.predict(X_predict)

    # Decode ngược lại thành labels chữ
    predicted_labels = le_fuel.inverse_transform(y_pred)

    # Điền vào test_set của dataframe
    df_out.loc[test_set, TARGET] = predicted_labels

    print(f"\nMissing 'fuel' values remaining: {df_out[TARGET].isna().sum()}")

    # 4. Output
    # --------------

    df_out.drop(columns=["brand_enc", "model_enc"], inplace=True)
    return df_out


def handle_price_outliers(df, column='prices', apply_log=True):
    """
    Hàm này dùng để xử lý các outliers của biến price (VD: các xe trị giá cao như 66 tỷ...)
    Phát hiện bằng IQR và biến đổi Logarit.
    """
    df_out = df.copy()

    Q1 = df_out[column].quantile(0.25)
    Q3 = df_out[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    #Giữ lại outliers và biến đổi logarit
    if apply_log:
        df_out[f'{column}_log'] = np.log1p(df_out[column])
    return df_out


def noisy_inconsistent_logic(df):
    """
    Hàm này dùng để:
     + Xử lý data không đồng nhất (chuẩn hóa về chữ thường trong brand, model, location).
     + Loại bỏ Noisy data do lỗi nhập người dùng.
    """
    df_out = df.copy()

    # Chuẩn hóa chữ thường
    for col in ['brand', 'model', 'location']:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).str.lower().str.strip()

    # Lọc các thông số vật lý phi logic (odo, seat, door)
    df_out = df_out[df_out['odo'] <= 1000000]
    df_out = df_out[(df_out['seats'] > 0) & (df_out['doors'] > 0) & (df_out['seats'] <= 16)]

    return df_out

def clean_emoji_text(text):
    """
    Hàm này dùng để làm sạch dấu câu, icon và khoảng trắng thừa trong văn bản.
    """
    if not isinstance(text, str):
        return ""

    # Bỏ thẻ HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    # Bỏ ký tự đặc biệt/icon
    text = re.sub(r'[^\w\s]', ' ', text)
    # Thu gọn khoảng trắng
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def save_csv(df, path):
    full_path = os.path.join(path, 'cleaned_vietnamese-car-prices-dataset.csv')
    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    print(f"Saved: {full_path}")



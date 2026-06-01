import pandas as pd
import numpy as np
import re
import glob
import os

def duplicates_remv (df):
    """
    Hàm này dùng để loại bỏ trùng lặp.
    """
    df.drop_duplicates(inplace = True)
    return df

def impute_missing_odo(df):
    """
    Fill odo:
        status = new --> odo = 0
        others: impute by median group
    """
    df_out = df.copy()

    df_out.loc[
        (df_out["status"] == "new") & (df_out["odo"].isnull()),
        "odo"
    ] = 0
    df_out["odo"] = df_out.groupby(
        ["brand", "model", "year"]
    )["odo"].transform(
        lambda x: x.fillna(x.median())
    )
    return df_out

def handle_volume(df):
    """
    Hàm xử lý điền khuyết (impute) cho cột 'volume' dựa trên các đặc trưng liên quan.
    """
    df_out = df.copy()

    # Kiểm tra xem có bao nhiêu null trước khi xử lý
    null_before = df_out['volume'].isnull().sum()
    print(f"Số lượng null ban đầu ở cột volume: {null_before}")

    # LỚP 1: Điền theo trung vị của nhóm (brand, model)
    # Ví dụ: Mất volume của xe Toyota Vios -> lấy trung vị volume của các xe Toyota Vios khác
    df_out['volume'] = df_out.groupby(['brand', 'model'])['volume'].transform(
        lambda x: x.fillna(x.median())
    )

    # LỚP 2: Điền theo trung vị của 'style'
    # Phòng trường hợp một model xe nào đó bị thiếu volume ở TẤT CẢ các dòng
    df_out['volume'] = df_out.groupby('style')['volume'].transform(
        lambda x: x.fillna(x.median())
    )

    # LỚP 3: Điền bằng trung vị của toàn bộ cột volume
    # Dành cho trường hợp cực hiếm khi toàn bộ xe trong một 'style' đều bị thiếu volume
    global_median = df_out['volume'].median()
    df_out['volume'] = df_out['volume'].fillna(global_median)

    # Kiểm tra lại số lượng null sau xử lý
    null_after = df_out['volume'].isnull().sum()
    print(f"Số lượng null sau khi xử lý: {null_after}")

    return df_out

def handle_price_outliers(df, column='price', apply_log=True):
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

def handle_trim_advanced(df):
    df_out = df.copy()

    brands = df_out['brand'].fillna('').astype(str).str.lower().str.strip()
    trims = df_out['trim'].fillna('').astype(str).str.lower().str.strip()

    # Xóa từ khóa
    keywords = [
        # Từ khóa tiếng Anh
        'luxury line', 'luxury', 'premium', 'platinum','pure excellence', 'signature',
        'dynamic', 'performance', 'exclusive','titanium','sport','sportback','quattro','edition',

        # Từ khóa tiếng Việt phổ biến trong tin đăng xe
        'thùng bạt', 'thùng kín', 'nhập khẩu', 'lắp ráp', 'trong nước','thùng lửng',
        'bản đủ', 'bản thiếu', 'mới', 'cũ', 'nhập', 'form mới', 'form cũ', 'cao cấp', 'đặc biệt','tiêu chuẩn',

        # Hộp số (Transmission)
        r'\bat\b', r'\bmt\b', r'\bcvt\b', r'\bautomatic\b', r'\bmanual\b',

        # Hệ dẫn động (Drive)
        r'\b4x4\b', r'\b4x2\b', r'\bawd\b', r'\b4wd\b', r'\bfwd\b', r'\brwd\b', r'\b2wd\b',
        r'\b4matic\b', r'\bxdrive\b', r'\bsdrive\b',  # Các thuật ngữ AWD riêng của hãng

        # Color
        r'\bwhite\b', r'\bblack\b', r'\bred\b', r'\bblue\b', r'\bgray\b', r'\bgrey\b',
        r'\bsilver\b', r'\bbrown\b', r'\bgreen\b', r'\byellow\b',
        r'\btrắng\b', r'\bđen\b', r'\bđỏ\b', r'\bxanh\b', r'\bvàng\b', r'\bcam\b',
        r'\bxám\b', r'\bbạc\b', r'\bnâu\b', r'\bghi\b', r'\bhồng\b', r'\btím\b',

        # Kiểu dáng xe (Style)
        r'\bsuv\b', r'\bsedan\b', r'\bcoupe\b', r'\bhatchback\b', r'\bcabriolet\b',
        r'\bconvertible\b', r'\bmpv\b', r'\bvan\b', r'\bpickup\b', r'\bcuv\b',

        # Dung tích động cơ (Volume)
        r'\b\d\.\d[a-z]*\b',
        r'\bv6\b', r'\bv8\b'
    ]

    # Bọc \b cho các từ thông thường để tránh xóa nhầm
    keywords = [kw if kw.startswith(r'\b') else rf'\b{kw}\b' for kw in keywords]
    pattern = '|'.join(keywords)

    # Xóa từ khóa khi các dấu tiếng Việt VẪN CÒN NGUYÊN
    trims = trims.str.replace(pattern, '', regex=True)

    # Xóa ký tự đặc biệt
    # Bây giờ chữ "thùng bạt" đã bị xóa sạch sẽ, ta mới dọn dẹp các dấu phẩy, ngoặc, v.v.
    trims = trims.str.replace(r'[^a-z0-9\s\.\-]', ' ', regex=True)

    # Dọn dẹp khoảng trắng và nối brand
    trims = trims.str.replace(r'\s+', ' ', regex=True).str.strip()

    cleaned_trims = [
        f"{b} {t}".strip() if b and (b not in t) else t
        for b, t in zip(brands, trims)
    ]

    df_out['trim'] = pd.Series(cleaned_trims, index=df_out.index)
    return df_out

def noisy_inconsistent_logic(df):
    """
    Hàm này dùng để:
     + Xử lý data không đồng nhất (chuẩn hóa về chữ thường trong brand, model, location).
     + Loại bỏ Noisy data do lỗi nhập người dùng.
    """
    df_out = df.copy()

    # Chuẩn hóa chữ thường
    for col in ['brand', 'model']:
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
    full_path = os.path.join(path, 'cleaned_bonbanh.csv')
    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    print(f"Saved: {full_path}")



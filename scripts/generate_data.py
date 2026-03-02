"""
Foodex Buyer Agent デモデータ生成スクリプト
商品マスタ(~200件)、顧客マスタ(~2000人)、ID-POS(~10万件)、在庫データを生成
"""

import os
import random
import uuid
from datetime import datetime, timedelta, date, time
from pathlib import Path

import numpy as np
import pandas as pd

from product_data import PRODUCTS, STORE_DATA, CROSS_SELL_PATTERNS, NEW_PRODUCT_NAMES

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

NUM_CUSTOMERS = 2000
NUM_POS_RECORDS = 100000
POS_START_DATE = date(2024, 3, 1)
POS_END_DATE = date(2026, 2, 28)
INVENTORY_DATE = date(2026, 2, 28)
NEW_PRODUCT_CUTOFF = date(2025, 12, 1)

PREFECTURES = [
    ("東京都", ["新宿区", "渋谷区", "世田谷区", "練馬区", "大田区", "杉並区", "板橋区", "江東区", "足立区", "中野区"], 0.20),
    ("神奈川県", ["横浜市", "川崎市", "相模原市", "藤沢市", "横須賀市"], 0.12),
    ("大阪府", ["大阪市", "堺市", "東大阪市", "枚方市", "豊中市"], 0.12),
    ("埼玉県", ["さいたま市", "川口市", "川越市", "所沢市", "越谷市"], 0.08),
    ("千葉県", ["千葉市", "船橋市", "松戸市", "市川市", "柏市"], 0.08),
    ("愛知県", ["名古屋市", "豊田市", "岡崎市", "一宮市", "豊橋市"], 0.07),
    ("北海道", ["札幌市", "旭川市", "函館市"], 0.05),
    ("福岡県", ["福岡市", "北九州市", "久留米市"], 0.05),
    ("兵庫県", ["神戸市", "姫路市", "西宮市", "尼崎市"], 0.05),
    ("宮城県", ["仙台市", "石巻市"], 0.03),
    ("広島県", ["広島市", "福山市"], 0.03),
    ("京都府", ["京都市", "宇治市"], 0.03),
    ("静岡県", ["静岡市", "浜松市"], 0.03),
    ("茨城県", ["水戸市", "つくば市"], 0.02),
    ("新潟県", ["新潟市", "長岡市"], 0.02),
    ("岡山県", ["岡山市", "倉敷市"], 0.02),
]

OCCUPATIONS = [
    ("会社員", 0.35), ("パート・アルバイト", 0.15), ("主婦・主夫", 0.15),
    ("自営業", 0.08), ("公務員", 0.07), ("学生", 0.05),
    ("年金生活", 0.08), ("その他", 0.07),
]

WEEKDAY_JP = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}

# 季節性重み: 月ごとの販売傾向倍率 (key = category_large)
SEASONAL_WEIGHTS = {
    "飲料": [0.7, 0.7, 0.8, 0.9, 1.0, 1.3, 1.5, 1.5, 1.2, 0.9, 0.8, 0.8],
    "菓子": [1.0, 1.2, 1.0, 0.9, 0.9, 0.9, 1.0, 1.0, 1.0, 1.1, 1.1, 1.3],
    "調味料": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2],
    "即席食品": [1.3, 1.2, 1.1, 0.9, 0.8, 0.7, 0.7, 0.7, 0.8, 1.0, 1.2, 1.3],
    "缶詰・レトルト": [1.1, 1.1, 1.0, 1.0, 0.9, 0.9, 0.9, 0.9, 1.0, 1.0, 1.1, 1.2],
    "乳製品": [0.9, 0.9, 1.0, 1.0, 1.1, 1.1, 1.2, 1.2, 1.1, 1.0, 0.9, 0.9],
    "冷凍食品": [1.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1],
    "パン・シリアル": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
}


def generate_product_master():
    """商品マスタ CSV 生成"""
    print("商品マスタを生成中...")
    rows = []
    for i, p in enumerate(PRODUCTS, start=1):
        product_id = f"P{i:04d}"
        jan_code = f"49{random.randint(10000, 99999):05d}{random.randint(1000, 9999):04d}"
        name, brand, mfr, cat_l, cat_m, cat_s, price, vol, measure, desc = p
        cost = int(price * random.uniform(0.55, 0.72))
        is_new = name in NEW_PRODUCT_NAMES
        if is_new:
            launch = random.choice([
                date(2025, 12, random.randint(1, 28)),
                date(2026, 1, random.randint(1, 28)),
                date(2026, 2, random.randint(1, 15)),
            ])
        else:
            launch = date(
                random.randint(2000, 2024),
                random.randint(1, 12),
                random.randint(1, 28),
            )
        rows.append({
            "product_id": product_id,
            "jan_code": jan_code,
            "product_name": name,
            "brand_name": brand,
            "manufacturer_name": mfr,
            "category_large": cat_l,
            "category_medium": cat_m,
            "category_small": cat_s,
            "unit_price": price,
            "cost_price": cost,
            "unit_volume": vol,
            "unit_measure": measure,
            "launch_date": launch.isoformat(),
            "product_description": desc,
            "is_new_product": is_new,
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "product_master.csv", index=False, encoding="utf-8-sig")
    print(f"  -> {len(df)} 商品を出力")
    return df


def generate_store_master():
    """店舗マスタ CSV 生成"""
    print("店舗マスタを生成中...")
    rows = []
    for s in STORE_DATA:
        rows.append({
            "store_id": s[0],
            "store_name": s[1],
            "prefecture": s[2],
            "city": s[3],
            "store_format": s[4],
            "sales_floor_area": s[5],
            "opening_date": s[6],
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "store_master.csv", index=False, encoding="utf-8-sig")
    print(f"  -> {len(df)} 店舗を出力")
    return df


def generate_customer_master():
    """顧客マスタ CSV 生成"""
    print("顧客マスタを生成中...")
    pref_names = [p[0] for p in PREFECTURES]
    pref_cities = {p[0]: p[1] for p in PREFECTURES}
    pref_weights = [p[2] for p in PREFECTURES]
    occ_names = [o[0] for o in OCCUPATIONS]
    occ_weights = [o[1] for o in OCCUPATIONS]

    age_groups = ["10代", "20代", "30代", "40代", "50代", "60代", "70代以上"]
    age_weights = [0.03, 0.12, 0.20, 0.22, 0.18, 0.15, 0.10]

    rows = []
    for i in range(1, NUM_CUSTOMERS + 1):
        cid = f"C{i:05d}"
        gender = random.choice(["男性", "女性"])
        age_grp = random.choices(age_groups, weights=age_weights, k=1)[0]
        age_min_map = {"10代": 15, "20代": 20, "30代": 30, "40代": 40, "50代": 50, "60代": 60, "70代以上": 70}
        age_max_map = {"10代": 19, "20代": 29, "30代": 39, "40代": 49, "50代": 59, "60代": 69, "70代以上": 85}
        age = random.randint(age_min_map[age_grp], age_max_map[age_grp])
        birth_year = 2026 - age
        birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
        pref = random.choices(pref_names, weights=pref_weights, k=1)[0]
        city = random.choice(pref_cities[pref])
        tier_r = random.random()
        if tier_r < 0.50:
            tier = "レギュラー"
        elif tier_r < 0.80:
            tier = "シルバー"
        elif tier_r < 0.95:
            tier = "ゴールド"
        else:
            tier = "プラチナ"
        reg_date = POS_START_DATE - timedelta(days=random.randint(0, 1800))
        family_size = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.25, 0.25, 0.25, 0.10], k=1)[0]
        has_children = family_size >= 3 and age >= 25 and random.random() < 0.7
        occupation = random.choices(occ_names, weights=occ_weights, k=1)[0]
        if age_grp == "10代":
            occupation = "学生"
        elif age_grp in ("60代", "70代以上") and random.random() < 0.5:
            occupation = "年金生活"

        rows.append({
            "customer_id": cid,
            "gender": gender,
            "birth_date": birth_date.isoformat(),
            "age_group": age_grp,
            "prefecture": pref,
            "city": city,
            "membership_tier": tier,
            "registration_date": reg_date.isoformat(),
            "family_size": family_size,
            "has_children": has_children,
            "occupation": occupation,
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "customer_master.csv", index=False, encoding="utf-8-sig")
    print(f"  -> {len(df)} 顧客を出力")
    return df


def _pick_hour():
    """買い物時間帯の分布"""
    r = random.random()
    if r < 0.05:
        return random.randint(7, 8)
    elif r < 0.20:
        return random.randint(9, 10)
    elif r < 0.40:
        return random.randint(11, 13)
    elif r < 0.55:
        return random.randint(14, 15)
    elif r < 0.75:
        return random.randint(16, 18)
    elif r < 0.92:
        return random.randint(19, 20)
    else:
        return random.randint(21, 22)


def generate_pos_data(product_df, customer_df, store_df):
    """ID-POSトランザクション CSV 生成"""
    print("ID-POSデータを生成中...")

    product_ids = product_df["product_id"].tolist()
    product_names = product_df["product_name"].tolist()
    product_prices = dict(zip(product_df["product_id"], product_df["unit_price"]))
    product_categories = dict(zip(product_df["product_id"], product_df["category_large"]))
    product_launch = dict(zip(product_df["product_id"], pd.to_datetime(product_df["launch_date"]).dt.date))
    name_to_id = {}
    for pid, pname in zip(product_ids, product_names):
        name_to_id[pname] = pid
        for word in pname.split():
            if word not in name_to_id:
                name_to_id[word] = pid

    customer_ids = customer_df["customer_id"].tolist()
    customer_ages = dict(zip(customer_df["customer_id"], customer_df["age_group"]))
    customer_children = dict(zip(customer_df["customer_id"], customer_df["has_children"]))
    store_ids = store_df["store_id"].tolist()

    # 商品名キーワード → product_id マッピング（併売パターン用）
    def find_product_ids_by_keywords(keywords):
        matched = []
        for kw in keywords:
            for pname, pid in name_to_id.items():
                if kw in pname:
                    matched.append(pid)
        return list(set(matched))

    cross_sell_resolved = []
    for pattern_name, groups, prob in CROSS_SELL_PATTERNS:
        resolved_groups = []
        for group_keywords in groups:
            pids = find_product_ids_by_keywords(group_keywords)
            if pids:
                resolved_groups.append(pids)
        if len(resolved_groups) >= 2:
            cross_sell_resolved.append((pattern_name, resolved_groups, prob))

    # 人気商品重み（価格帯低い方が売れやすい + ランダム性）
    base_weights = []
    for pid in product_ids:
        price = product_prices[pid]
        w = max(0.3, 1.0 - (price - 100) / 800) + random.uniform(0, 0.3)
        base_weights.append(w)
    base_weights = np.array(base_weights)

    total_days = (POS_END_DATE - POS_START_DATE).days + 1
    all_dates = [POS_START_DATE + timedelta(days=d) for d in range(total_days)]

    # 日付ごとの重み（曜日効果）
    dow_mult = {0: 0.8, 1: 0.8, 2: 0.9, 3: 0.9, 4: 1.0, 5: 1.3, 6: 1.2}

    rows = []
    basket_count = 0
    txn_count = 0

    target_baskets = NUM_POS_RECORDS // 4  # 平均4アイテム/バスケット

    print(f"  目標: {NUM_POS_RECORDS} トランザクション, 約{target_baskets} バスケット")

    while txn_count < NUM_POS_RECORDS:
        tx_date = random.choice(all_dates)
        month_idx = tx_date.month - 1
        dow = tx_date.weekday()

        basket_count += 1
        basket_id = f"B{basket_count:08d}"
        customer_id = random.choice(customer_ids)
        store_id = random.choice(store_ids)
        hour = _pick_hour()
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        tx_time = time(hour, minute, second)

        # バスケット内アイテム数
        num_items = max(1, int(np.random.lognormal(mean=1.0, sigma=0.5)))
        num_items = min(num_items, 12)

        # 季節重み調整
        weights = base_weights.copy()
        for j, pid in enumerate(product_ids):
            cat = product_categories[pid]
            s_w = SEASONAL_WEIGHTS.get(cat, [1.0] * 12)
            weights[j] *= s_w[month_idx]
            weights[j] *= dow_mult.get(dow, 1.0)
            launch = product_launch[pid]
            if launch > tx_date:
                weights[j] = 0.0

        # 顧客属性による嗜好調整
        age_grp = customer_ages[customer_id]
        has_child = customer_children[customer_id]
        for j, pid in enumerate(product_ids):
            cat = product_categories[pid]
            if has_child and cat in ("菓子", "乳製品", "パン・シリアル"):
                weights[j] *= 1.5
            if age_grp in ("60代", "70代以上") and cat in ("缶詰・レトルト", "調味料"):
                weights[j] *= 1.3
            if age_grp in ("10代", "20代") and cat in ("菓子", "飲料"):
                weights[j] *= 1.3

        w_sum = weights.sum()
        if w_sum == 0:
            continue
        probs = weights / w_sum

        basket_items = set()

        # 併売パターン適用
        cross_sell_applied = False
        for pattern_name, groups, prob in cross_sell_resolved:
            if random.random() < prob and not cross_sell_applied:
                for group_pids in groups:
                    valid = [p for p in group_pids if product_launch.get(p, date(2000, 1, 1)) <= tx_date]
                    if valid:
                        basket_items.add(random.choice(valid))
                cross_sell_applied = True
                break

        remaining = num_items - len(basket_items)
        if remaining > 0:
            chosen = np.random.choice(len(product_ids), size=min(remaining, len(product_ids)), replace=False, p=probs)
            for idx in chosen:
                basket_items.add(product_ids[idx])

        for pid in basket_items:
            txn_count += 1
            txn_id = f"T{txn_count:09d}"
            price = product_prices[pid]
            qty = 1 if random.random() < 0.85 else random.randint(2, 3)
            discount = 0
            if random.random() < 0.08:
                discount = int(price * random.choice([0.05, 0.10, 0.15, 0.20]))
            sales = (price - discount) * qty

            rows.append({
                "transaction_id": txn_id,
                "basket_id": basket_id,
                "transaction_date": tx_date.isoformat(),
                "transaction_time": tx_time.strftime("%H:%M:%S"),
                "customer_id": customer_id,
                "store_id": store_id,
                "product_id": pid,
                "quantity": qty,
                "unit_selling_price": price - discount,
                "discount_amount": discount,
                "sales_amount": sales,
                "day_of_week": WEEKDAY_JP[dow],
            })

            if txn_count >= NUM_POS_RECORDS:
                break

        if txn_count % 20000 == 0:
            print(f"  ... {txn_count}/{NUM_POS_RECORDS} トランザクション生成済み")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "id_pos_transactions.csv", index=False, encoding="utf-8-sig")
    print(f"  -> {len(df)} トランザクション, {basket_count} バスケットを出力")
    return df


def generate_inventory(product_df, store_df, pos_df):
    """在庫データ CSV 生成"""
    print("在庫データを生成中...")

    recent_pos = pos_df[pos_df["transaction_date"] >= (INVENTORY_DATE - timedelta(days=30)).isoformat()]
    daily_sales = (
        recent_pos.groupby(["store_id", "product_id"])["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"quantity": "monthly_sales"})
    )
    daily_sales["avg_daily_sales"] = daily_sales["monthly_sales"] / 30.0

    rows = []
    for _, store in store_df.iterrows():
        sid = store["store_id"]
        for _, prod in product_df.iterrows():
            pid = prod["product_id"]
            match = daily_sales[
                (daily_sales["store_id"] == sid) & (daily_sales["product_id"] == pid)
            ]
            if len(match) > 0:
                avg_daily = match.iloc[0]["avg_daily_sales"]
            else:
                avg_daily = random.uniform(0.1, 0.5)

            safety = max(1, int(avg_daily * random.uniform(2, 4)))
            reorder = max(safety + 1, int(avg_daily * random.uniform(4, 7)))
            stock = max(0, int(avg_daily * random.uniform(1, 14)))

            # 一部商品を欠品気味にする
            if random.random() < 0.05:
                stock = random.randint(0, safety)

            dos = round(stock / max(avg_daily, 0.01), 1) if avg_daily > 0 else 999.0
            dos = min(dos, 999.0)

            last_rep = INVENTORY_DATE - timedelta(days=random.randint(0, 10))

            rows.append({
                "inventory_date": INVENTORY_DATE.isoformat(),
                "store_id": sid,
                "product_id": pid,
                "stock_quantity": stock,
                "reorder_point": reorder,
                "safety_stock": safety,
                "days_of_supply": dos,
                "last_replenishment_date": last_rep.isoformat(),
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "inventory.csv", index=False, encoding="utf-8-sig")
    print(f"  -> {len(df)} 在庫レコードを出力")
    return df


def main():
    print("=" * 60)
    print("Foodex Buyer Agent デモデータ生成")
    print("=" * 60)

    product_df = generate_product_master()
    store_df = generate_store_master()
    customer_df = generate_customer_master()
    pos_df = generate_pos_data(product_df, customer_df, store_df)
    generate_inventory(product_df, store_df, pos_df)

    print("=" * 60)
    print("完了！ CSVファイルは data/ ディレクトリに出力されました。")
    print("=" * 60)


if __name__ == "__main__":
    main()

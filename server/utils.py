import json
import sys
from typing import Dict, Any, List
from datetime import datetime

# 假设 FoodPriceDB 类已定义（可从原文件导入）
# from your_module import FoodPriceDB

def load_data_from_json(db: 'FoodPriceDB', json_path: str) -> bool:
    """
    从 JSON 文件加载数据到数据库
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取 JSON 文件失败: {e}")
        return False

    success = True

    # 1. 导入用户
    for user in data.get("users", []):
        ok, msg = db.register_user(
            username=user["username"],
            email=user["email"],
            password=user["password"]
        )
        if not ok:
            print(f"⚠️ 用户 {user['username']} 导入失败: {msg}")
            success = False

    # 2. 导入平台
    for plat in data.get("platforms", []):
        ok, msg = db.add_platform(plat["platform_name"])
        if not ok and "已存在" not in msg:
            print(f"⚠️ 平台 {plat['platform_name']} 导入失败: {msg}")
            success = False

    # 3. 导入店铺
    shop_key_to_id: Dict[tuple, int] = {}  # (platform_name, shop_name) -> shop_id
    for shop in data.get("shops", []):
        ok, msg, shop_id = db.add_shop(
            platform_name=shop["platform_name"],
            shop_name=shop["shop_name"],
            delivery_distance=shop.get("delivery_distance", 0),
            rating=shop.get("rating", 0),
            delivery_time=shop.get("delivery_time"),
            delivery_fee=shop.get("delivery_fee", 0),
            monthly_sales=shop.get("monthly_sales", 0),
            min_order=shop.get("min_order", 0),
            avg_consumption=shop.get("avg_consumption", 0)
        )
        if ok and shop_id is not None:
            shop_key_to_id[(shop["platform_name"], shop["shop_name"])] = shop_id
        else:
            print(f"⚠️ 店铺 {shop['shop_name']} ({shop['platform_name']}) 导入失败: {msg}")
            success = False

    # 4. 导入菜品
    for dish in data.get("dishes", []):
        key = (dish["platform_name"], dish["shop_name"])
        if key not in shop_key_to_id:
            # 尝试从数据库查询（可能之前已存在）
            cursor = db._get_thread_cursor()
            cursor.execute("""
                SELECT s.shop_id 
                FROM shops s 
                JOIN platforms p ON s.platform_id = p.platform_id 
                WHERE s.shop_name = ? AND p.platform_name = ?
            """, (dish["shop_name"], dish["platform_name"]))
            row = cursor.fetchone()
            if row:
                shop_id = row["shop_id"]
                shop_key_to_id[key] = shop_id
            else:
                print(f"⚠️ 菜品 {dish['dish_name']} 所属店铺未找到: {key}")
                success = False
                continue
        else:
            shop_id = shop_key_to_id[key]

        ok, msg = db.add_dish(shop_id, dish["dish_name"], dish["price"])
        if not ok:
            print(f"⚠️ 菜品 {dish['dish_name']} 导入失败: {msg}")
            success = False

    # 5. 导入优惠券
    for coupon in data.get("coupons", []):
        key = (coupon["platform_name"], coupon["shop_name"])
        if key not in shop_key_to_id:
            cursor = db._get_thread_cursor()
            cursor.execute("""
                SELECT s.shop_id 
                FROM shops s 
                JOIN platforms p ON s.platform_id = p.platform_id 
                WHERE s.shop_name = ? AND p.platform_name = ?
            """, (coupon["shop_name"], coupon["platform_name"]))
            row = cursor.fetchone()
            if row:
                shop_id = row["shop_id"]
            else:
                print(f"⚠️ 优惠券所属店铺未找到: {key}")
                success = False
                continue
        else:
            shop_id = shop_key_to_id[key]

        ok, msg = db.add_coupon(
            shop_id=shop_id,
            condition_amount=coupon["condition_amount"],
            discount_amount=coupon["discount_amount"],
            valid_from=coupon.get("valid_from"),
            valid_to=coupon.get("valid_to")
        )
        if not ok:
            print(f"⚠️ 优惠券导入失败: {msg}")
            success = False

    return success


# ======================
# 使用示例
# ======================
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python load_data.py <data.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    db = FoodPriceDB()

    if not db.initialize("food_price.db"):
        print("❌ 数据库初始化失败")
        sys.exit(1)

    if load_data_from_json(db, json_file):
        print("✅ 所有数据导入完成")
    else:
        print("⚠️ 部分数据导入失败，请检查日志")

    db.close_thread_resources()
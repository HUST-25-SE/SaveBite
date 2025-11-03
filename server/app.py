# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from FoodPriceDB import FoodPriceDB
import os, random
from utils import load_data_from_json
app = Flask(__name__)
CORS(app)  # 允许跨域（开发阶段）


# if not db.initialize_test_data():
#     print("测试数据初始化失败")
#     exit(1)

# 工具函数：从请求头获取用户 ID（简化版，正式应使用 JWT）
def get_user_id_from_request():
    user_id = request.headers.get("X-User-ID")
    if not user_id or not user_id.isdigit():
        return None
    return int(user_id)

# ========== 认证接口 ==========

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not all([username, email, password]):
        return jsonify({"success": False, "message": "缺少必要字段"}), 400

    success, user_id, msg = db.register_user(username, email, password) 
    if success:
        _, user_info = db.get_user_by_id(user_id) 
        return jsonify({"success": True, "user": user_info})
    else:
        return jsonify({"success": False, "message": msg}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"success": False, "message": "用户名或密码为空"}), 400
    success, user_id, msg = db.login_user(username, password)
    if success:
        _, user_info = db.get_user_by_id(user_id)
        return jsonify({
            "success": True,
            "token": f"mock_jwt_{user_id}",  # 实际应生成 JWT
            "user": user_info
        })
    else:
        return jsonify({"success": False, "message": msg}), 401

@app.route('/api/auth/me', methods=['GET'])
def me():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"success": False, "message": "未登录"}), 401
    success, user_info = db.get_user_by_id(user_id)
    if success:
        return jsonify({"success": True, "user": user_info})
    else:
        return jsonify({"success": False, "message": "用户不存在"}), 404

# ========== 收藏接口 ==========
@app.route('/api/user/favorites', methods=['GET'])
def get_favorites():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"success": False, "message": "未登录"}), 401

    success, favorites = db.get_user_favorites(user_id)
    if not success:
        return jsonify({"success": False, "message": "获取收藏失败"}), 500

    if not favorites:
        return jsonify({"success": True, "favorites": []})

    conn = db._get_thread_connection()
    cursor = conn.cursor()

    # Step 1: 收集所有收藏的 shop_id 和对应的 shop_name
    favorite_shop_ids = [fav["shop_id"] for fav in favorites]
    favorite_shop_names = list(set(fav["shop_name"] for fav in favorites))

    # Step 2: 查询这些 shop_name 对应的所有平台店铺（用于聚合）
    placeholders = ','.join('?' * len(favorite_shop_names))
    cursor.execute(f"""
        SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
               s.delivery_distance, s.delivery_time,
               p.platform_name
        FROM shops s
        JOIN platforms p ON s.platform_id = p.platform_id
        WHERE s.shop_name IN ({placeholders})
        ORDER BY s.shop_name, p.platform_name
    """, favorite_shop_names)

    all_shops = cursor.fetchall()

    # 按 shop_name 分组
    from collections import defaultdict
    grouped_shops = defaultdict(list)
    for row in all_shops:
        grouped_shops[row["shop_name"]].append(row)

    # Step 3: 批量查询所有相关店铺的 dishes
    all_shop_ids = [row["shop_id"] for row in all_shops]
    dish_map = {}
    if all_shop_ids:
        placeholders_dish = ','.join('?' * len(all_shop_ids))
        cursor.execute(f"""
            SELECT dish_id, shop_id, dish_name, price
            FROM dishes
            WHERE shop_id IN ({placeholders_dish})
            ORDER BY dish_name
        """, all_shop_ids)

        for dish in cursor.fetchall():
            shop_id = dish["shop_id"]
            if shop_id not in dish_map:
                dish_map[shop_id] = []
            dish_map[shop_id].append({
                "name": dish["dish_name"],
                "price": round(dish["price"], 2)
            })

    # Step 4: 构建合并后的结果
    result = []
    for shop_name, platforms in grouped_shops.items():
        meituan_data = next((p for p in platforms if p["platform_name"] == "美团"), None)
        ele_data = next((p for p in platforms if p["platform_name"] == "饿了么"), None)

        main_shop = meituan_data or ele_data
        if not main_shop:
            continue

        # 评分 & 月销量
        rating = max(
            meituan_data["rating"] if meituan_data else 0,
            ele_data["rating"] if ele_data else 0
        ) or 4.5

        monthly_sales = (meituan_data["monthly_sales"] if meituan_data else 0) + \
                        (ele_data["monthly_sales"] if ele_data else 0) or 100

        # 起送价
        min_order_meituan = meituan_data["min_order"] if meituan_data else None
        min_order_ele = ele_data["min_order"] if ele_data else None

        # 菜品均价
        avg_meituan = None
        avg_ele = None

        if meituan_data:
            mt_dishes = dish_map.get(meituan_data["shop_id"], [])
            if mt_dishes:
                avg_meituan = round(sum(d["price"] for d in mt_dishes) / len(mt_dishes), 2)

        if ele_data:
            ele_dishes = dish_map.get(ele_data["shop_id"], [])
            if ele_dishes:
                avg_ele = round(sum(d["price"] for d in ele_dishes) / len(ele_dishes), 2)

        # 距离 & 配送时间（取主店铺）
        distance_val = main_shop["delivery_distance"] or 1.2
        distance_str = f"{distance_val:.1f}km"

        delivery_time_val = main_shop["delivery_time"]
        delivery_time_str = f"{max(10, delivery_time_val - 5)}-{(delivery_time_val or 35) + 5}分钟" \
            if delivery_time_val else "30-40分钟"

        # 聚合 dishes
        dish_name_to_platforms = defaultdict(dict)
        shop_ids = []
        if meituan_data:
            shop_ids.append(meituan_data["shop_id"])
        if ele_data:
            shop_ids.append(ele_data["shop_id"])

        for shop_id in shop_ids:
            platform_name = "meituan" if meituan_data and shop_id == meituan_data["shop_id"] else "ele"
            dishes = dish_map.get(shop_id, [])
            for d in dishes:
                dish_name_to_platforms[d["name"]][platform_name] = d["price"]

        dishes_list = []
        for name, prices in dish_name_to_platforms.items():
            dish_entry = {"name": name}
            if "meituan" in prices:
                dish_entry["meituan"] = prices["meituan"]
            if "ele" in prices:
                dish_entry["ele"] = prices["ele"]
            dishes_list.append(dish_entry)

        # 构造最终对象
        result.append({
            "id": main_shop["shop_id"],
            "name": shop_name,
            "rating": rating,
            "reviews": monthly_sales,
            "distance": distance_str,
            "deliveryTime": delivery_time_str,
            "deliveryFee": f"¥{((meituan_data['delivery_fee'] if meituan_data else 0) + (ele_data['delivery_fee'] if ele_data else 0)) / 2:.1f}",
            "minimumOrder": {
                "meituan": min_order_meituan,
                "ele": min_order_ele
            },
            "image": f"https://via.placeholder.com/300x160?text={shop_name}",
            "prices": {
                "meituan": {"current": avg_meituan} if avg_meituan is not None else None,
                "ele": {"current": avg_ele} if avg_ele is not None else None
            },
            "isFavorite": True,
            "dishes": dishes_list
        })

    return jsonify({"success": True, "favorites": result})

@app.route('/api/favorite/toggle', methods=['POST'])
def toggle_favorite():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"success": False, "message": "未登录"}), 401

    data = request.json
    shop_name = data.get('shop_name')  # ✅ 改为 shop_name
    if not shop_name or not isinstance(shop_name, str) or not shop_name.strip():
        return jsonify({"success": False, "message": "无效店铺名"}), 400

    shop_name = shop_name.strip()
    conn = db._get_thread_connection()
    cursor = conn.cursor()

    # Step 1: 查找所有平台下该 shop_name 对应的 shop_id
    cursor.execute("""
        SELECT shop_id FROM shops s
        JOIN platforms p ON s.platform_id = p.platform_id
        WHERE s.shop_name = ?
    """, (shop_name,))
    same_name_shop_ids = [row["shop_id"] for row in cursor.fetchall()]

    if not same_name_shop_ids:
        return jsonify({"success": False, "message": "店铺不存在"}), 404

    # Step 2: 检查这些 shop_id 中是否任意一个已被收藏
    placeholders = ','.join('?' * len(same_name_shop_ids))
    cursor.execute(f"""
        SELECT shop_id FROM user_favorites 
        WHERE user_id = ? AND shop_id IN ({placeholders})
    """, [user_id] + same_name_shop_ids)

    already_favorited = cursor.fetchall()
    has_any_favorite = len(already_favorited) > 0

    if has_any_favorite:
        # 取消收藏：删除所有同名店铺的收藏记录
        removed_count = 0
        for sid in same_name_shop_ids:
            success, msg = db.remove_favorite(user_id, sid)
            if success:
                removed_count += 1
        is_favorite = False
        message = "取消收藏成功"
    else:
        # 收藏：添加所有同名店铺的收藏记录
        added_count = 0
        for sid in same_name_shop_ids:
            success, msg = db.add_favorite(user_id, sid)
            if success:
                added_count += 1
        is_favorite = True
        message = "收藏成功"

    return jsonify({"success": True, "isFavorite": is_favorite})

# ========== 搜索接口 ==========
@app.route('/api/restaurants/search', methods=['GET'])
def search_restaurants():
    keyword = request.args.get('keyword', '').strip()
    
    # 获取当前用户 ID（可能为 None）
    user_id = get_user_id_from_request()

    conn = db._get_thread_connection()
    cursor = conn.cursor()

    if keyword:
        cursor.execute("""
            SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
                   s.delivery_distance, s.delivery_time,
                   p.platform_name
            FROM shops s
            JOIN platforms p ON s.platform_id = p.platform_id
            WHERE s.shop_name LIKE ?
            ORDER BY s.shop_name, p.platform_name
        """, (f"%{keyword}%",))
    else:
        cursor.execute("""
            SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
                   s.delivery_distance, s.delivery_time,
                   p.platform_name
            FROM shops s
            JOIN platforms p ON s.platform_id = p.platform_id
            ORDER BY s.monthly_sales DESC, s.rating DESC
            LIMIT 50
        """)

    shop_rows = cursor.fetchall()

    from collections import defaultdict
    grouped_shops = defaultdict(list)
    for row in shop_rows:
        grouped_shops[row["shop_name"]].append(row)

    # 所有 shop_id（用于查菜品 和 收藏状态）
    all_shop_ids = [row["shop_id"] for row in shop_rows]
    dish_map = {}

    # 批量查菜品
    if all_shop_ids:
        placeholders = ','.join('?' * len(all_shop_ids))
        cursor.execute(f"""
            SELECT dish_id, shop_id, dish_name, price
            FROM dishes
            WHERE shop_id IN ({placeholders})
            ORDER BY dish_name
        """, all_shop_ids)

        for dish in cursor.fetchall():
            shop_id = dish["shop_id"]
            if shop_id not in dish_map:
                dish_map[shop_id] = []
            dish_map[shop_id].append({
                "name": dish["dish_name"],
                "price": round(dish["price"], 2)
            })

    # === 新增：查询用户的收藏 shop_id 集合 ===
    user_favorite_shop_ids = set()
    if user_id:
        cursor.execute("""
            SELECT shop_id FROM user_favorites WHERE user_id = ?
        """, (user_id,))
        user_favorite_shop_ids = {row["shop_id"] for row in cursor.fetchall()}

    results = []
    for shop_name, platforms in grouped_shops.items():
        meituan_data = next((p for p in platforms if p["platform_name"] == "美团"), None)
        ele_data = next((p for p in platforms if p["platform_name"] == "饿了么"), None)

        main_shop = meituan_data or ele_data
        if not main_shop:
            continue

        rating = max(
            meituan_data["rating"] if meituan_data else 0,
            ele_data["rating"] if ele_data else 0
        ) or 4.5

        monthly_sales = (meituan_data["monthly_sales"] if meituan_data else 0) + \
                        (ele_data["monthly_sales"] if ele_data else 0) or 100

        min_order_meituan = meituan_data["min_order"] if meituan_data else None
        min_order_ele = ele_data["min_order"] if ele_data else None

        avg_meituan = None
        avg_ele = None

        if meituan_data:
            mt_dishes = dish_map.get(meituan_data["shop_id"], [])
            if mt_dishes:
                avg_meituan = round(sum(d["price"] for d in mt_dishes) / len(mt_dishes), 2)

        if ele_data:
            ele_dishes = dish_map.get(ele_data["shop_id"], [])
            if ele_dishes:
                avg_ele = round(sum(d["price"] for d in ele_dishes) / len(ele_dishes), 2)

        distance_val = main_shop["delivery_distance"] or 1.2
        distance_str = f"{distance_val:.1f}km"

        delivery_time_val = main_shop["delivery_time"]
        delivery_time_str = f"{max(10, delivery_time_val - 5)}-{(delivery_time_val or 35) + 5}分钟" \
            if delivery_time_val else "30-40分钟"

        dish_name_to_platforms = defaultdict(dict)
        shop_ids = []
        if meituan_data:
            shop_ids.append(meituan_data["shop_id"])
        if ele_data:
            shop_ids.append(ele_data["shop_id"])

        for shop_id in shop_ids:
            platform_name = "meituan" if meituan_data and shop_id == meituan_data["shop_id"] else "ele"
            dishes = dish_map.get(shop_id, [])
            for d in dishes:
                dish_name_to_platforms[d["name"]][platform_name] = d["price"]

        dishes_list = []
        for name, prices in dish_name_to_platforms.items():
            dish_entry = {"name": name}
            if "meituan" in prices:
                dish_entry["meituan"] = prices["meituan"]
            if "ele" in prices:
                dish_entry["ele"] = prices["ele"]
            dishes_list.append(dish_entry)

        # === 新增：判断是否收藏 ===
        is_favorite = False
        if user_id:
            # 只要任一平台的 shop_id 被收藏，就算收藏
            for sid in shop_ids:
                if sid in user_favorite_shop_ids:
                    is_favorite = True
                    break

        results.append({
            "id": main_shop["shop_id"],
            "name": shop_name,
            "rating": rating,
            "reviews": monthly_sales,
            "distance": distance_str,
            "deliveryTime": delivery_time_str,
            "deliveryFee": f"¥{((meituan_data['delivery_fee'] if meituan_data else 0) + (ele_data['delivery_fee'] if ele_data else 0)) / 2:.1f}",
            "minimumOrder": {
                "meituan": min_order_meituan,
                "ele": min_order_ele
            },
            "image": f"https://via.placeholder.com/300x160?text={shop_name}",
            "prices": {
                "meituan": {"current": avg_meituan} if avg_meituan is not None else None,
                "ele": {"current": avg_ele} if avg_ele is not None else None
            },
            "isFavorite": is_favorite,
            "dishes": dishes_list
        })

    # 首页随机选 6 个
    if not keyword and len(results) > 6:
        results = random.sample(results, 6)

    return jsonify({"success": True, "restaurants": results})
# ========== 比价接口（可选） ==========

@app.route('/api/dish/compare', methods=['GET'])
def compare_dish():
    dish_name = request.args.get('dish_name')
    shop_name = request.args.get('shop_name')
    if not dish_name:
        return jsonify({"success": False, "message": "缺少菜品名"}), 400
    success, results = db.compare_dish_price(dish_name=dish_name, shop_name=shop_name, exact=False)
    return jsonify({"success": success, "results": results if success else str(results)})

# ========== 启动 ==========

if __name__ == '__main__':
    # 初始化数据库
    db = FoodPriceDB()
    db_path = os.getenv("DB_PATH", "food_price.db")
    if not db.initialize(db_path):
        raise RuntimeError("数据库初始化失败")
    db.clear_all_data()

    load_data_from_json(db, "./data.json")
    app.run(host='0.0.0.0', port=5000, debug=True)
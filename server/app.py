# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from FoodPriceDB import FoodPriceDB
import os
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
    if success:
        # 转换为前端需要的格式（模拟 mockRestaurants 结构）
        result = []
        for fav in favorites:
            # 简化：假设每个店铺在两个平台都有（实际需查 dishes/shops）
            result.append({
                "id": fav["shop_id"],
                "name": fav["shop_name"],
                "rating": fav["rating"] or 4.5,
                "reviews": fav["monthly_sales"] or 100,
                "distance": "1.5km",
                "deliveryTime": "30-40分钟",
                "deliveryFee": f"¥{fav['delivery_fee']}",
                "minimumOrder": {
                    "meituan": fav["min_order"],
                    "ele": fav["min_order"]
                },
                "image": "https://via.placeholder.com/300x160?text=" + fav["shop_name"],
                "prices": {
                    "meituan": {"current": fav["min_order"] + 10},
                    "ele": {"current": fav["min_order"] + 8}
                },
                "isFavorite": True,
                "dishes": []  # 可后续扩展
            })
        return jsonify({"success": True, "favorites": result})
    else:
        return jsonify({"success": False, "message": "获取收藏失败"}), 500

@app.route('/api/favorite/toggle', methods=['POST'])
def toggle_favorite():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"success": False, "message": "未登录"}), 401
    data = request.json
    shop_id = data.get('shop_id')
    if not shop_id or not isinstance(shop_id, int):
        return jsonify({"success": False, "message": "无效店铺ID"}), 400
    # 检查是否已收藏
    conn = db._get_thread_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM user_favorites WHERE user_id = ? AND shop_id = ?", (user_id, shop_id))
    exists = cursor.fetchone()
    if exists:
        success, msg = db.remove_favorite(user_id, shop_id)
        is_favorite = False
    else:
        success, msg = db.add_favorite(user_id, shop_id)
        is_favorite = True
    if success:
        return jsonify({"success": True, "isFavorite": is_favorite})
    else:
        return jsonify({"success": False, "message": msg}), 400

# ========== 搜索接口 ==========

@app.route('/api/restaurants/search', methods=['GET'])
def search_restaurants():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({"success": True, "restaurants": []})

    conn = db._get_thread_connection()
    cursor = conn.cursor()

    # 第一步：获取匹配的店铺（含 delivery_distance, delivery_time）
    cursor.execute("""
        SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
               s.delivery_distance, s.delivery_time,
               p.platform_name
        FROM shops s
        JOIN platforms p ON s.platform_id = p.platform_id
        WHERE s.shop_name LIKE ?
        ORDER BY s.shop_name, p.platform_name
    """, (f"%{keyword}%",))

    shop_rows = cursor.fetchall()

    from collections import defaultdict
    grouped_shops = defaultdict(list)
    for row in shop_rows:
        grouped_shops[row["shop_name"]].append(row)

    # 提前收集所有 shop_id，用于批量查询菜品
    all_shop_ids = [row["shop_id"] for row in shop_rows]
    dish_map = {}  # shop_id -> list of dishes

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

    results = []
    for shop_name, platforms in grouped_shops.items():
        meituan_data = next((p for p in platforms if p["platform_name"] == "美团"), None)
        ele_data = next((p for p in platforms if p["platform_name"] == "饿了么"), None)

        # 主店铺用于 distance / deliveryTime
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

        price_meituan = min_order_meituan + 10 if min_order_meituan else None
        price_ele = min_order_ele + 8 if min_order_ele else None

        distance_val = main_shop["delivery_distance"] or 1.2
        distance_str = f"{distance_val:.1f}km"

        delivery_time_val = main_shop["delivery_time"]
        delivery_time_str = f"{max(10, delivery_time_val - 5)}-{(delivery_time_val or 35) + 5}分钟" \
            if delivery_time_val else "30-40分钟"

        # === 构建 dishes 列表 ===
        # 按菜品名聚合，记录各平台价格
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

        # 转为列表格式
        dishes_list = []
        for name, prices in dish_name_to_platforms.items():
            dish_entry = {"name": name}
            if "meituan" in prices:
                dish_entry["meituan"] = prices["meituan"]
            if "ele" in prices:
                dish_entry["ele"] = prices["ele"]
            dishes_list.append(dish_entry)

        # 限制菜品数量（可选，比如最多显示10个）
        dishes_list = dishes_list[:10]

        results.append({
            "id": main_shop["shop_id"],
            "name": shop_name,
            "rating": rating,
            "reviews": monthly_sales,
            "distance": distance_str,
            "deliveryTime": delivery_time_str,
            "deliveryFee": {
                "meituan": f"¥{meituan_data['delivery_fee']}" if meituan_data else "0.0",
                "ele": f"¥{ele_data['delivery_fee']}" if ele_data else "0.0"
            },
            "minimumOrder": {
                "meituan": min_order_meituan,
                "ele": min_order_ele
            },
            "image": f"https://via.placeholder.com/300x160?text={shop_name}",
            "prices": {
                "meituan": {"current": price_meituan} if price_meituan is not None else "0.0",
                "ele": {"current": price_ele} if price_ele is not None else "0.0"
            },
            "isFavorite": False,
            "dishes": dishes_list
        })

    results.sort(key=lambda x: (-x["rating"], -x["reviews"]))
    results = results[:20]

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
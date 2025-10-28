# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from FoodPriceDB import FoodPriceDB
import os

app = Flask(__name__)
CORS(app)  # 允许跨域（开发阶段）

# 初始化数据库
db = FoodPriceDB()
db_path = os.getenv("DB_PATH", "food_price.db")
if not db.initialize(db_path):
    raise RuntimeError("数据库初始化失败")

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
    success, msg = db.register_user(username, email, password)
    if success:
        _, user_info = db.get_user_by_id(db._get_thread_cursor().lastrowid)
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
    cursor.execute("""
        SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
               p.platform_name
        FROM shops s
        JOIN platforms p ON s.platform_id = p.platform_id
        WHERE s.shop_name LIKE ?
        ORDER BY s.rating DESC
        LIMIT 20
    """, (f"%{keyword}%",))
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            "id": row["shop_id"],
            "name": row["shop_name"],
            "rating": row["rating"] or 4.5,
            "reviews": row["monthly_sales"] or 100,
            "distance": "1.2km",
            "deliveryTime": "30-40分钟",
            "deliveryFee": f"¥{row['delivery_fee']}",
            "minimumOrder": {
                "meituan": row["min_order"],
                "ele": row["min_order"]
            },
            "image": "https://via.placeholder.com/300x160?text=" + row["shop_name"],
            "prices": {
                "meituan": {"current": row["min_order"] + 10},
                "ele": {"current": row["min_order"] + 8}
            },
            "isFavorite": False,  # 前端可后续调用收藏状态接口
            "dishes": []
        })
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
    app.run(host='0.0.0.0', port=5000, debug=True)
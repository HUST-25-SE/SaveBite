from flask import Flask, request, jsonify
from flask_cors import CORS
from .FoodPriceDB import FoodPriceDB
import os, random
from .utils import load_data_from_json
from flask import send_from_directory

app = Flask(__name__)
CORS(app)  # 允许跨域

# 全局 db 实例
db = None

# 初始化数据库（Vercel 适配）
def init_db():
    global db
    if db is None:
        db = FoodPriceDB()
        db_path = os.getenv("DB_PATH", "/tmp/food_price.db")  # Vercel 使用 /tmp 目录
        if not db.initialize(db_path):
            # 如果初始化失败，尝试使用内存数据库
            db_path = ":memory:"
            if not db.initialize(db_path):
                raise RuntimeError("数据库初始化失败")
        
        # 只在数据库为空时加载数据
        conn = db._get_thread_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM shops")
        count = cursor.fetchone()["count"]
        if count == 0:
            # 尝试从环境变量或默认路径加载数据
            data_path = os.getenv("DATA_PATH", "./data.json")
            if os.path.exists(data_path):
                load_data_from_json(db, data_path)

# 确保在应用启动时初始化数据库
init_db()

# 工具函数：从请求头获取用户 ID
def get_user_id_from_request():
    user_id = request.headers.get("X-User-ID")
    if not user_id or not user_id.isdigit():
        return None
    return int(user_id)

# ========== Vercel Serverless 适配器 ==========

def vercel_handler(request):
    """Vercel Serverless 函数处理器"""
    from flask import Request, Response
    import json
    
    # 确保数据库已初始化
    init_db()
    
    # 创建 Flask 请求上下文
    with app.test_request_context(
        path=request['path'],
        method=request['method'],
        headers=request.get('headers', {}),
        query_string=request.get('query', {}),
        json=request.get('body') if request.get('body') and request.get('headers', {}).get('content-type') == 'application/json' else None,
        data=request.get('body') if not request.get('headers', {}).get('content-type') == 'application/json' else None
    ):
        try:
            # 执行 Flask 路由处理
            response = app.full_dispatch_request()
            
            # 构建 Vercel 响应格式
            vercel_response = {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': response.content_type,
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, X-User-ID'
                },
                'body': response.get_data(as_text=True)
            }
            
            return vercel_response
            
        except Exception as e:
            # 错误处理
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'message': f'服务器错误: {str(e)}'
                })
            }

# ========== 健康检查接口 ==========

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"success": True, "message": "服务正常运行"})

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
            "token": f"mock_jwt_{user_id}",
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

def get_image_url(meituan_data, ele_data):
    """优先使用美团图片，其次饿了么，最后回退到 placeholder"""
    def safe_image(row):
        if row is None:
            return None
        url = row["image_url"]
        return url if url not in (None, "") else None

    mt_url = safe_image(meituan_data)
    ele_url = safe_image(ele_data)

    if mt_url:
        return mt_url
    if ele_url:
        return ele_url

    shop_name = (meituan_data or ele_data)["shop_name"]
    return f"https://via.placeholder.com/300x160?text={shop_name}"

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

    favorite_shop_names = list(set(fav["shop_name"] for fav in favorites))

    placeholders = ','.join('?' * len(favorite_shop_names))
    cursor.execute(f"""
        SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
               s.delivery_distance, s.delivery_time, s.image_url,
               p.platform_name
        FROM shops s
        JOIN platforms p ON s.platform_id = p.platform_id
        WHERE s.shop_name IN ({placeholders})
        ORDER BY s.shop_name, p.platform_name
    """, favorite_shop_names)

    all_shops = cursor.fetchall()

    from collections import defaultdict
    grouped_shops = defaultdict(list)
    for row in all_shops:
        grouped_shops[row["shop_name"]].append(row)

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

    result = []
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

        # 使用真实 image_url
        image_url = get_image_url(meituan_data, ele_data)

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
            "image": image_url,
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
    shop_name = data.get('shop_name')
    if not shop_name or not isinstance(shop_name, str) or not shop_name.strip():
        return jsonify({"success": False, "message": "无效店铺名"}), 400

    shop_name = shop_name.strip()
    conn = db._get_thread_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT shop_id FROM shops s
        JOIN platforms p ON s.platform_id = p.platform_id
        WHERE s.shop_name = ?
    """, (shop_name,))
    same_name_shop_ids = [row["shop_id"] for row in cursor.fetchall()]

    if not same_name_shop_ids:
        return jsonify({"success": False, "message": "店铺不存在"}), 404

    placeholders = ','.join('?' * len(same_name_shop_ids))
    cursor.execute(f"""
        SELECT shop_id FROM user_favorites 
        WHERE user_id = ? AND shop_id IN ({placeholders})
    """, [user_id] + same_name_shop_ids)

    already_favorited = cursor.fetchall()
    has_any_favorite = len(already_favorited) > 0

    if has_any_favorite:
        removed_count = 0
        for sid in same_name_shop_ids:
            success, msg = db.remove_favorite(user_id, sid)
            if success:
                removed_count += 1
        is_favorite = False
        message = "取消收藏成功"
    else:
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
    user_id = get_user_id_from_request()

    conn = db._get_thread_connection()
    cursor = conn.cursor()

    if keyword:
        cursor.execute("""
            SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
                   s.delivery_distance, s.delivery_time, s.image_url,
                   p.platform_name
            FROM shops s
            JOIN platforms p ON s.platform_id = p.platform_id
            WHERE s.shop_name LIKE ?
            ORDER BY s.shop_name, p.platform_name
        """, (f"%{keyword}%",))
    else:
        cursor.execute("""
            SELECT s.shop_id, s.shop_name, s.rating, s.delivery_fee, s.min_order, s.monthly_sales,
                   s.delivery_distance, s.delivery_time, s.image_url,
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

    all_shop_ids = [row["shop_id"] for row in shop_rows]
    dish_map = {}

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

    user_favorite_shop_ids = set()
    if user_id:
        cursor.execute("SELECT shop_id FROM user_favorites WHERE user_id = ?", (user_id,))
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

        is_favorite = False
        if user_id:
            for sid in shop_ids:
                if sid in user_favorite_shop_ids:
                    is_favorite = True
                    break

        # 使用真实 image_url
        image_url = get_image_url(meituan_data, ele_data)

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
            "image": image_url,
            "prices": {
                "meituan": {"current": avg_meituan} if avg_meituan is not None else None,
                "ele": {"current": avg_ele} if avg_ele is not None else None
            },
            "isFavorite": is_favorite,
            "dishes": dishes_list
        })

    if not keyword and len(results) > 6:
        results = random.sample(results, 6)

    return jsonify({"success": True, "restaurants": results})

# ========== 比价接口 ==========

@app.route('/api/dish/compare', methods=['GET'])
def compare_dish():
    dish_name = request.args.get('dish_name')
    shop_name = request.args.get('shop_name')
    if not dish_name:
        return jsonify({"success": False, "message": "缺少菜品名"}), 400
    success, results = db.compare_dish_price(dish_name=dish_name, shop_name=shop_name, exact=False)
    return jsonify({"success": success, "results": results if success else str(results)})

# ========== Vercel 启动配置 ==========

# Vercel Serverless 函数入口点
def handler(request, context):
    return vercel_handler(request)

# 本地开发启动
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
import sqlite3
import hashlib
import threading
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional

class FoodPriceDB:
    def __init__(self):
        self.initialized = False
        self.db_path = None
        self.lock = threading.Lock()
        self.local = threading.local()

    def initialize(self, db_path: str = "food_price.db") -> bool:
        with self.lock:
            if self.initialized:
                return True
            
            self.db_path = db_path
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 用户表（不变）
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # 平台表（不变）
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS platforms (
                    platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # 店铺表：添加 image_url 字段
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS shops (
                    shop_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_id INTEGER NOT NULL,
                    shop_name TEXT NOT NULL,
                    delivery_distance REAL DEFAULT 0,
                    rating REAL DEFAULT 0,
                    delivery_time INTEGER,
                    delivery_fee REAL DEFAULT 0,
                    monthly_sales INTEGER DEFAULT 0,
                    min_order REAL DEFAULT 0,
                    avg_consumption REAL DEFAULT 0,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id) ON DELETE CASCADE,
                    UNIQUE(platform_id, shop_name)
                )
                ''')

                # 兼容旧数据库：如果 shops 表已存在但无 image_url，则添加
                cursor.execute("PRAGMA table_info(shops)")
                columns = [info[1] for info in cursor.fetchall()]
                if 'image_url' not in columns:
                    cursor.execute("ALTER TABLE shops ADD COLUMN image_url TEXT")

                # 优惠券表（不变）
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS coupons (
                    coupon_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER NOT NULL,
                    condition_amount REAL NOT NULL,
                    discount_amount REAL NOT NULL,
                    valid_from TIMESTAMP,
                    valid_to TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (shop_id) REFERENCES shops(shop_id) ON DELETE CASCADE
                )
                ''')

                # 菜品表（不变）
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS dishes (
                    dish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER NOT NULL,
                    dish_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (shop_id) REFERENCES shops(shop_id) ON DELETE CASCADE,
                    UNIQUE(shop_id, dish_name)
                )
                ''')

                # 收藏表（不变）
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_favorites (
                    user_id INTEGER NOT NULL,
                    shop_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, shop_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (shop_id) REFERENCES shops(shop_id) ON DELETE CASCADE
                )
                ''')

                # 插入默认平台
                default_platforms = ["美团", "饿了么"]
                for name in default_platforms:
                    cursor.execute("SELECT platform_id FROM platforms WHERE platform_name = ?", (name,))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO platforms (platform_name) VALUES (?)", (name,))

                conn.commit()
                self.initialized = True
                return True
            except Exception as e:
                print(f"初始化数据库失败: {e}")
                return False
            finally:
                if 'conn' in locals():
                    conn.close()

    def _get_thread_connection(self) -> sqlite3.Connection:
        if not hasattr(self.local, 'conn'):
            if not self.initialized:
                raise RuntimeError("数据库未初始化，请先调用 initialize()")
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn

    def _get_thread_cursor(self) -> sqlite3.Cursor:
        return self._get_thread_connection().cursor()

    def close_thread_resources(self) -> None:
        if hasattr(self.local, 'conn'):
            self.local.conn.close()
            del self.local.conn

    def _retry_operation(self, operation, max_retries: int = 3, delay: float = 0.1) -> Any:
        for i in range(max_retries):
            try:
                return operation()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and i < max_retries - 1:
                    import time
                    time.sleep(delay * (i + 1))
                    continue
                raise
            except Exception as e:
                raise

    def _hash_password(self, password: str) -> str:
        """对密码进行 SHA256 哈希（课程作业简化版）"""
        return hashlib.sha256(password.encode()).hexdigest()

    # ======================
    # 用户管理
    # ======================
    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, Optional[int], str]:
        """用户注册，返回 (成功, user_id, 消息)"""
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", (username, email))
                if cursor.fetchone():
                    return (False, None, "用户名或邮箱已存在")

                hashed_pwd = self._hash_password(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, hashed_pwd)
                )
                user_id = cursor.lastrowid
                self._get_thread_connection().commit()
                return (True, user_id, "注册成功")
            except Exception as e:
                return (False, None, f"注册失败: {e}")
        return self._retry_operation(operation)

    def login_user(self, username: str, password: str) -> Tuple[bool, Optional[int], str]:
        """用户登录，返回 (成功, user_id, 消息)"""
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT user_id, password FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                if not user:
                    return (False, None, "用户不存在")

                if self._hash_password(password) == user['password']:
                    return (True, user['user_id'], "登录成功")
                else:
                    return (False, None, "密码错误")
            except Exception as e:
                return (False, None, f"登录异常: {e}")
        return self._retry_operation(operation)

    def get_user_by_id(self, user_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """根据 user_id 获取用户信息（不含密码）"""
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT user_id, username, email, created_at FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if not row:
                    return (False, None)
                return (True, {
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "email": row["email"],
                    "created_at": row["created_at"]
                })
            except Exception as e:
                return (False, None)
        return self._retry_operation(operation)

    # ======================
    # 收藏管理
    # ======================
    def add_favorite(self, user_id: int, shop_id: int) -> Tuple[bool, str]:
        """收藏店铺"""
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                if not cursor.fetchone():
                    return (False, "用户不存在")

                cursor.execute("SELECT shop_id FROM shops WHERE shop_id = ?", (shop_id,))
                if not cursor.fetchone():
                    return (False, "店铺不存在")

                cursor.execute("SELECT 1 FROM user_favorites WHERE user_id = ? AND shop_id = ?", (user_id, shop_id))
                if cursor.fetchone():
                    return (False, "已收藏该店铺")

                cursor.execute(
                    "INSERT INTO user_favorites (user_id, shop_id) VALUES (?, ?)",
                    (user_id, shop_id)
                )
                self._get_thread_connection().commit()
                return (True, "收藏成功")
            except Exception as e:
                return (False, f"收藏失败: {e}")
        return self._retry_operation(operation)

    def remove_favorite(self, user_id: int, shop_id: int) -> Tuple[bool, str]:
        """取消收藏"""
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute(
                    "DELETE FROM user_favorites WHERE user_id = ? AND shop_id = ?",
                    (user_id, shop_id)
                )
                if cursor.rowcount == 0:
                    return (False, "未收藏该店铺或店铺/用户不存在")
                self._get_thread_connection().commit()
                return (True, "取消收藏成功")
            except Exception as e:
                return (False, f"取消收藏失败: {e}")
        return self._retry_operation(operation)

    def get_user_favorites(self, user_id: int) -> Tuple[bool, List[Dict[str, Any]]]:
        """获取用户收藏的店铺列表（含平台、评分、image_url 等信息）"""
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                if not cursor.fetchone():
                    return (False, [])

                query = '''
                SELECT 
                    s.shop_id,
                    s.shop_name,
                    s.rating,
                    s.delivery_fee,
                    s.min_order,
                    s.monthly_sales,
                    s.image_url,
                    p.platform_name
                FROM user_favorites uf
                JOIN shops s ON uf.shop_id = s.shop_id
                JOIN platforms p ON s.platform_id = p.platform_id
                WHERE uf.user_id = ?
                ORDER BY s.rating DESC, s.monthly_sales DESC
                '''
                cursor.execute(query, (user_id,))
                favorites = []
                for row in cursor.fetchall():
                    favorites.append({
                        "shop_id": row["shop_id"],
                        "shop_name": row["shop_name"],
                        "platform": row["platform_name"],
                        "rating": row["rating"],
                        "delivery_fee": row["delivery_fee"],
                        "min_order": row["min_order"],
                        "monthly_sales": row["monthly_sales"],
                        "image_url": row["image_url"] or ""
                    })
                return (True, favorites)
            except Exception as e:
                return (False, [])
        return self._retry_operation(operation)

    # ======================
    # 平台、店铺、优惠券、菜品管理
    # ======================
    def add_platform(self, platform_name: str) -> Tuple[bool, str]:
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT platform_id FROM platforms WHERE platform_name = ?", (platform_name,))
                if cursor.fetchone():
                    return (False, "平台已存在")
                cursor.execute("INSERT INTO platforms (platform_name) VALUES (?)", (platform_name,))
                self._get_thread_connection().commit()
                return (True, "平台添加成功")
            except Exception as e:
                return (False, f"添加失败: {e}")
        return self._retry_operation(operation)

    def add_shop(
        self,
        platform_name: str,
        shop_name: str,
        delivery_distance: float = 0,
        rating: float = 0,
        delivery_time: Optional[int] = None,
        delivery_fee: float = 0,
        monthly_sales: int = 0,
        min_order: float = 0,
        avg_consumption: float = 0,
        image_url: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT platform_id FROM platforms WHERE platform_name = ?", (platform_name,))
                platform = cursor.fetchone()
                if not platform:
                    return (False, "平台不存在", None)

                cursor.execute(
                    """INSERT INTO shops (
                        platform_id, shop_name, delivery_distance, rating,
                        delivery_time, delivery_fee, monthly_sales,
                        min_order, avg_consumption, image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        platform['platform_id'], shop_name, delivery_distance, rating,
                        delivery_time, delivery_fee, monthly_sales,
                        min_order, avg_consumption, image_url
                    )
                )
                shop_id = cursor.lastrowid
                self._get_thread_connection().commit()
                return (True, "店铺添加成功", shop_id)
            except Exception as e:
                return (False, f"添加失败: {e}", None)
        return self._retry_operation(operation)

    def add_coupon(
        self,
        shop_id: int,
        condition_amount: float,
        discount_amount: float,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None
    ) -> Tuple[bool, str]:
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT shop_id FROM shops WHERE shop_id = ?", (shop_id,))
                if not cursor.fetchone():
                    return (False, "店铺不存在")

                cursor.execute(
                    """INSERT INTO coupons (shop_id, condition_amount, discount_amount, valid_from, valid_to)
                       VALUES (?, ?, ?, ?, ?)""",
                    (shop_id, condition_amount, discount_amount, valid_from, valid_to)
                )
                self._get_thread_connection().commit()
                return (True, "满减优惠添加成功")
            except Exception as e:
                return (False, f"添加失败: {e}")
        return self._retry_operation(operation)

    def add_dish(self, shop_id: int, dish_name: str, price: float) -> Tuple[bool, str]:
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("SELECT shop_id FROM shops WHERE shop_id = ?", (shop_id,))
                if not cursor.fetchone():
                    return (False, "店铺不存在")

                cursor.execute(
                    "INSERT INTO dishes (shop_id, dish_name, price) VALUES (?, ?, ?)",
                    (shop_id, dish_name, price)
                )
                self._get_thread_connection().commit()
                return (True, "菜品添加成功")
            except Exception as e:
                return (False, f"添加失败: {e}")
        return self._retry_operation(operation)

    def compare_dish_price(
        self, 
        dish_name: str, 
        shop_name: Optional[str] = None,
        exact: bool = True
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        比价指定菜品（可选指定店铺名）
        """
        def operation():
            cursor = self._get_thread_cursor()
            try:
                conditions = []
                params = []

                if exact:
                    conditions.append("d.dish_name = ?")
                    params.append(dish_name)
                else:
                    conditions.append("d.dish_name LIKE ?")
                    params.append(f"%{dish_name}%")

                if shop_name:
                    conditions.append("s.shop_name = ?")
                    params.append(shop_name)

                where_clause = " AND ".join(conditions)

                query = f'''
                SELECT 
                    d.dish_name,
                    d.price AS dish_price,
                    s.shop_name,
                    s.delivery_fee,
                    s.min_order,
                    p.platform_name,
                    c.condition_amount,
                    c.discount_amount
                FROM dishes d
                JOIN shops s ON d.shop_id = s.shop_id
                JOIN platforms p ON s.platform_id = p.platform_id
                LEFT JOIN coupons c ON s.shop_id = c.shop_id
                WHERE {where_clause}
                ORDER BY 
                    CASE 
                        WHEN (d.price + s.delivery_fee) >= IFNULL(c.condition_amount, 999999)
                        THEN (d.price + s.delivery_fee - c.discount_amount)
                        ELSE (d.price + s.delivery_fee)
                    END ASC
                '''
                cursor.execute(query, params)
                results = []
                for row in cursor.fetchall():
                    total = row['dish_price'] + row['delivery_fee']
                    condition = row['condition_amount']
                    discount = row['discount_amount'] or 0

                    if condition is not None and total >= condition:
                        final_price = total - discount
                        saved = discount
                        meets = True
                    else:
                        final_price = total
                        saved = 0
                        meets = False

                    results.append({
                        "platform": row["platform_name"],
                        "shop": row["shop_name"],
                        "dish": row["dish_name"],
                        "dish_price": round(row["dish_price"], 2),
                        "delivery_fee": round(row["delivery_fee"], 2),
                        "total_before_discount": round(total, 2),
                        "final_price": round(final_price, 2),
                        "saved": round(saved, 2),
                        "meets_discount": meets
                    })
                return (True, results)
            except Exception as e:
                return (False, f"比价失败: {e}")

        return self._retry_operation(operation)

    def clear_all_data(self) -> bool:
        """
        清空所有业务数据（保留表结构）
        """
        def operation():
            cursor = self._get_thread_cursor()
            try:
                cursor.execute("DELETE FROM user_favorites")
                cursor.execute("DELETE FROM dishes")
                cursor.execute("DELETE FROM coupons")
                cursor.execute("DELETE FROM shops")
                cursor.execute("DELETE FROM users")
                self._get_thread_connection().commit()
                print("✅ 所有业务数据已清空")
                return True
            except Exception as e:
                print(f"清空数据失败: {e}")
                return False

        try:
            return self._retry_operation(operation)
        except Exception as e:
            print(f"清空操作异常: {e}")
            return False

    def initialize_test_data(self) -> bool:
        def operation():
            self.register_user("alice", "alice@example.com", "123456")
            self.register_user("bob", "bob@example.com", "123456")

            cursor = self._get_thread_cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = 'alice'")
            alice_id = cursor.fetchone()['user_id']

            self.add_shop(
                "美团", "张亮麻辣烫(中关村店)",
                rating=4.7, delivery_fee=3.0, min_order=20.0,
                monthly_sales=1200, avg_consumption=35.0,
                image_url="https://example.com/meituan_zhangliang.jpg"
            )
            self.add_shop(
                "饿了么", "张亮麻辣烫(中关村店)",
                rating=4.6, delivery_fee=2.5, min_order=20.0,
                monthly_sales=980, avg_consumption=32.0,
                image_url="https://example.com/eleme_zhangliang.jpg"
            )

            cursor.execute("""
                SELECT s.shop_id 
                FROM shops s 
                JOIN platforms p ON s.platform_id = p.platform_id 
                WHERE s.shop_name = ? AND p.platform_name = ?
            """, ("张亮麻辣烫(中关村店)", "美团"))
            shop1_id = cursor.fetchone()['shop_id']

            cursor.execute("""
                SELECT s.shop_id 
                FROM shops s 
                JOIN platforms p ON s.platform_id = p.platform_id 
                WHERE s.shop_name = ? AND p.platform_name = ?
            """, ("张亮麻辣烫(中关村店)", "饿了么"))
            shop2_id = cursor.fetchone()['shop_id']

            self.add_dish(shop1_id, "麻辣烫（微辣）", 28.0)
            self.add_dish(shop2_id, "麻辣烫（微辣）", 29.5)

            self.add_coupon(shop1_id, 30, 5)
            self.add_coupon(shop2_id, 25, 6)

            self.add_favorite(alice_id, shop1_id)
            self.add_favorite(alice_id, shop2_id)

            print("测试数据已确保存在（重复插入被数据库阻止）")
            return True

        try:
            return self._retry_operation(operation)
        except Exception as e:
            print(f"测试数据初始化异常: {e}")
            return False

# ======================
# 使用示例
# ======================
if __name__ == "__main__":
    db = FoodPriceDB()
    
    if not db.initialize("food_price.db"):
        print("数据库初始化失败")
        exit(1)
        
    db.clear_all_data()

    if not db.initialize_test_data():
        print("测试数据初始化失败")
        exit(1)

    success, user_id, msg = db.login_user("alice", "123456")
    if success:
        print(f"\n✅ {msg}，用户ID: {user_id}")

        ok, favorites = db.get_user_favorites(user_id)
        if ok:
            print(f"\n【{db.get_user_by_id(user_id)[1]['username']} 的收藏】")
            for fav in favorites:
                print(f"- {fav['shop_name']} ({fav['platform']}) ⭐{fav['rating']} | 月销{fav['monthly_sales']} | 图片: {fav['image_url']}")

    print("\n" + "="*60)
    success, results = db.compare_dish_price("麻辣烫", shop_name='张亮麻辣烫(中关村店)', exact=False)
    if success:
        print("\n【麻辣烫比价结果】")
        for r in results:
            status = "✅ 满减后" if r['meets_discount'] else "❌ 未满减"
            print(f"{r['platform']} | {r['shop']} | {status}: ¥{r['final_price']}")

    db.close_thread_resources()
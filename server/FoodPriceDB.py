import sqlite3
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
        """初始化数据库，创建表"""
        with self.lock:
            if self.initialized:
                return True
            
            self.db_path = db_path
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 平台表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS platforms (
                    platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # 店铺表
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id) ON DELETE CASCADE
                )
                ''')

                # 优惠券表（满减）
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

                # 菜品表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS dishes (
                    dish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id INTEGER NOT NULL,
                    dish_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

    # ======================
    # 平台管理
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

    # ======================
    # 店铺管理
    # ======================
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
        avg_consumption: float = 0
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
                        min_order, avg_consumption
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        platform['platform_id'], shop_name, delivery_distance, rating,
                        delivery_time, delivery_fee, monthly_sales,
                        min_order, avg_consumption
                    )
                )
                shop_id = cursor.lastrowid
                self._get_thread_connection().commit()
                return (True, "店铺添加成功", shop_id)
            except Exception as e:
                return (False, f"添加失败: {e}", None)
        return self._retry_operation(operation)

    # ======================
    # 优惠券（满减）管理
    # ======================
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

    # ======================
    # 菜品管理
    # ======================
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

    # ======================
    # 核心功能：菜品比价（含满减）
    # ======================
    def compare_dish_price(self, dish_name: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        比价指定菜品在各平台的价格（含满减优惠后价格）
        简化假设：用户只买这一份菜 + 配送费，计算是否满足满减
        """
        def operation():
            cursor = self._get_thread_cursor()
            try:
                # 查询菜品、店铺、平台、优惠信息
                query = '''
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
                WHERE d.dish_name LIKE ?
                ORDER BY 
                    CASE 
                        WHEN (d.price + s.delivery_fee) >= IFNULL(c.condition_amount, 999999)
                        THEN (d.price + s.delivery_fee - c.discount_amount)
                        ELSE (d.price + s.delivery_fee)
                    END ASC
                '''
                cursor.execute(query, (f"%{dish_name}%",))
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

    # ======================
    # 测试数据初始化
    # ======================
    def initialize_test_data(self) -> bool:
        """添加测试数据用于演示比价功能"""
        def operation():
            # 美团 - 张亮麻辣烫
            success, msg, shop1_id = self.add_shop(
                platform_name="美团",
                shop_name="张亮麻辣烫(中关村店)",
                delivery_distance=2.1,
                rating=4.7,
                delivery_time=30,
                delivery_fee=3.0,
                monthly_sales=1200,
                min_order=20.0,
                avg_consumption=35.0
            )
            if not success:
                print(f"添加美团店铺失败: {msg}")
                return False

            # 满30减5
            success, msg = self.add_coupon(shop1_id, 30, 5)
            if not success:
                print(f"添加美团满减失败: {msg}")
                return False

            success, msg = self.add_dish(shop1_id, "麻辣烫（微辣）", 28.0)
            if not success:
                print(f"添加美团菜品失败: {msg}")
                return False

            # 饿了么 - 张亮麻辣烫（同名不同价）
            success, msg, shop2_id = self.add_shop(
                platform_name="饿了么",
                shop_name="张亮麻辣烫(中关村店)",
                delivery_distance=2.0,
                rating=4.6,
                delivery_time=28,
                delivery_fee=2.5,
                monthly_sales=980,
                min_order=20.0,
                avg_consumption=32.0
            )
            if not success:
                print(f"添加饿了么店铺失败: {msg}")
                return False

            # 满25减6（更激进）
            success, msg = self.add_coupon(shop2_id, 25, 6)
            if not success:
                print(f"添加饿了么满减失败: {msg}")
                return False

            success, msg = self.add_dish(shop2_id, "麻辣烫（微辣）", 29.5)
            if not success:
                print(f"添加饿了么菜品失败: {msg}")
                return False

            # 沙县小吃（无满减）
            success, msg, shop3_id = self.add_shop(
                platform_name="美团",
                shop_name="沙县小吃(学院路店)",
                delivery_distance=1.5,
                rating=4.3,
                delivery_time=20,
                delivery_fee=2.0,
                monthly_sales=800,
                min_order=15.0,
                avg_consumption=22.0
            )
            if not success:
                return False
            success, msg = self.add_dish(shop3_id, "鸡腿饭", 18.0)
            if not success:
                return False
            # 不添加优惠券，测试无满减场景

            print("测试数据添加成功！")
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

    if not db.initialize_test_data():
        print("测试数据初始化失败")
        exit(1)

    # 比价演示
    success, results = db.compare_dish_price("麻辣烫")
    if success:
        print("\n【麻辣烫比价结果】")
        for r in results:
            print(f"平台: {r['platform']} | 店铺: {r['shop']}")
            print(f"  菜品: {r['dish']} | 价格: ¥{r['dish_price']}")
            print(f"  配送费: ¥{r['delivery_fee']} | 小计: ¥{r['total_before_discount']}")
            if r['meets_discount']:
                print(f"  ✅ 满减后实付: ¥{r['final_price']} (省 ¥{r['saved']})")
            else:
                print(f"  ❌ 未达满减，实付: ¥{r['final_price']}")
            print("-" * 50)
    else:
        print("比价失败:", results)

    db.close_thread_resources()
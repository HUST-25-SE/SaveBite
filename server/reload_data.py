import os
import sys
sys.path.append(os.path.dirname(__file__))

from FoodPriceDB import FoodPriceDB
from utils import load_data_from_json

def main():
    db = FoodPriceDB()
    db_path = os.getenv("DB_PATH", "food_price.db")
    if not db.initialize(db_path):
        print("❌ 数据库初始化失败")
        return False

    print("🧹 清空现有数据...")
    db.clear_all_data()

    print("📥 从 JSON 重新加载数据...")
    success = load_data_from_json(db, "./data.json")  # 确保 data.json 路径正确
    
    if success:
        print("✅ 数据重载成功！")
    else:
        print("❌ 数据加载失败，请检查 data.json 格式和路径")

    return success

if __name__ == '__main__':
    main()
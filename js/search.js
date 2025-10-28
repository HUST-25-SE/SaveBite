// 搜索页面功能
document.getElementById('searchBtn').addEventListener('click', function () {
  performSearch();
});

document.getElementById('searchInput').addEventListener('keypress', function (e) {
  if (e.key === 'Enter') {
    performSearch();
  }
});

function performSearch() {
  /* 
  【正式版需要后端支持】
  功能：餐厅搜索
  接口：GET /api/restaurants/search
  参数：keyword (搜索关键词), page (页码), size (每页数量), filters (筛选条件)
  响应：{ restaurants: [...], pagination: { page, size, total } }
  
  实现说明：
  1. 获取搜索关键词和筛选条件
  2. 调用后端搜索接口
  3. 处理分页逻辑
  4. 渲染搜索结果
  5. 处理空结果和错误情况
  */

  const searchTerm = document.getElementById('searchInput').value.trim();
  const searchResults = document.getElementById('searchResults');

  if (!searchTerm) {
    searchResults.innerHTML = '<div class="empty-state"><i class="fas fa-search"></i><p>请输入搜索关键词</p></div>';
    return;
  }

  searchResults.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>搜索中...</p></div>';

  // 模拟API调用
  setTimeout(() => {
    const filtered = window.mockRestaurants.filter(restaurant =>
      restaurant.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (filtered.length === 0) {
      searchResults.innerHTML = '<div class="empty-state"><i class="fas fa-search"></i><p>没有找到相关结果</p></div>';
      return;
    }

    searchResults.innerHTML = '<div class="recommend-list" id="searchResultList"></div>';
    const resultContainer = document.getElementById('searchResultList');

    filtered.forEach(restaurant => {
      renderSearchRestaurantCard(restaurant, resultContainer);
    });
  }, 800);
}

// 专门为搜索页面渲染餐厅卡片（确保收藏功能正常）
function renderSearchRestaurantCard(restaurant, container) {
  const restaurantCard = document.createElement('div');
  restaurantCard.className = 'restaurant-card';
  restaurantCard.setAttribute('data-id', restaurant.id);

  // 确定推荐平台（价格更低的）
  const meituanPrice = restaurant.prices.meituan.current;
  const elePrice = restaurant.prices.ele.current;
  const recommendedPlatform = meituanPrice <= elePrice ? 'meituan' : 'ele';

  restaurantCard.innerHTML = `
        <div class="restaurant-image" style="background-image: url('${restaurant.image}')"></div>
        <div class="restaurant-info">
            <div class="restaurant-name">
                ${restaurant.name}
                <button class="favorite-btn ${restaurant.isFavorite ? 'active' : ''}" data-id="${restaurant.id}">
                    <i class="fas fa-heart"></i>
                </button>
            </div>
            <div class="restaurant-meta">
                <div class="restaurant-rating">
                    <span class="stars">${window.generateStars(restaurant.rating)}</span>
                    <span>${restaurant.rating}</span>
                    <span>(${restaurant.reviews})</span>
                </div>
                <div>${restaurant.distance}</div>
            </div>
            <div class="restaurant-meta">
                <div>${restaurant.deliveryTime}</div>
                <div>配送费${restaurant.deliveryFee}</div>
            </div>
            <div class="platform-comparison">
                <div class="platform-info ${recommendedPlatform === 'meituan' ? 'recommended' : ''}">
                    <div class="platform-name">美团</div>
                    <div class="price">¥${restaurant.prices.meituan.current}</div>
                    <div class="minimum-order">起送¥${restaurant.minimumOrder.meituan}</div>
                </div>
                <div class="platform-info ${recommendedPlatform === 'ele' ? 'recommended' : ''}">
                    <div class="platform-name">饿了么</div>
                    <div class="price">¥${restaurant.prices.ele.current}</div>
                    <div class="minimum-order">起送¥${restaurant.minimumOrder.ele}</div>
                </div>
            </div>
        </div>
    `;

  container.appendChild(restaurantCard);

  // 添加收藏按钮事件
  const favoriteBtn = restaurantCard.querySelector('.favorite-btn');
  favoriteBtn.addEventListener('click', function (e) {
    e.preventDefault();
    e.stopPropagation(); // 防止事件冒泡

    // 检查登录状态
    const userData = localStorage.getItem('currentUser');
    if (!userData) {
      alert('请先登录');
      window.navigateTo('login');
      return;
    }

    // 切换收藏状态 - 使用全局函数
    const restaurantId = parseInt(this.getAttribute('data-id'));
    window.toggleFavorite(restaurantId);
  });

  // 添加卡片点击事件，显示商家详情 - 使用全局函数
  restaurantCard.addEventListener('click', function (e) {
    // 排除收藏按钮的点击
    if (!e.target.closest('.favorite-btn')) {
      // 直接调用全局函数，不要重复定义本地函数
      if (typeof window.showRestaurantDetails === 'function') {
        window.showRestaurantDetails(restaurant);
      } else {
        console.error('showRestaurantDetails function not available');
      }
    }
  });
}

// 监听收藏状态变化，同步更新搜索页面的UI
window.addEventListener('favoriteUpdated', function (e) {
  const { restaurantId, isFavorite } = e.detail;

  // 更新搜索页面中的所有对应餐厅的收藏按钮
  const favoriteBtns = document.querySelectorAll(`.favorite-btn[data-id="${restaurantId}"]`);
  favoriteBtns.forEach(btn => {
    if (isFavorite) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
});
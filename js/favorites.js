// 收藏页面功能
function renderFavoritesPage() {
  /* 
  【正式版需要后端支持】
  功能：获取用户收藏列表
  接口：GET /api/user/favorites
  请求头：Authorization: Bearer {token}
  响应：{ favorites: [{ id, restaurant: {...} }] }
  
  实现说明：
  1. 检查用户登录状态，未登录显示登录提示
  2. 调用后端获取收藏列表接口
  3. 渲染收藏的餐厅
  4. 处理空收藏列表情况
  */

  const favoritesList = document.getElementById('favoritesList');

  // 检查用户是否已登录
  const userData = localStorage.getItem('currentUser');
  if (!userData) {
    favoritesList.innerHTML = '<div class="empty-state"><i class="fas fa-lock"></i><p>请先登录查看收藏</p><button class="submit-btn" id="goToLogin">立即登录</button></div>';

    document.getElementById('goToLogin')?.addEventListener('click', function () {
      window.navigateTo('login');
    });
    return;
  }

  // 模拟实现 - 实际应该调用后端API
  const favorites = window.mockRestaurants.filter(restaurant => restaurant.isFavorite);

  if (favorites.length === 0) {
    favoritesList.innerHTML = '<div class="empty-state"><i class="far fa-heart"></i><p>您还没有收藏任何餐厅</p></div>';
    return;
  }

  favoritesList.innerHTML = '<div class="recommend-list" id="favoritesResultList"></div>';
  const resultContainer = document.getElementById('favoritesResultList');

  favorites.forEach(restaurant => {
    renderFavoriteRestaurantCard(restaurant, resultContainer);
  });
}

// 专门为收藏页面渲染餐厅卡片
function renderFavoriteRestaurantCard(restaurant, container) {
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
                <button class="favorite-btn active" data-id="${restaurant.id}">
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
    e.stopPropagation();

    const restaurantId = parseInt(this.getAttribute('data-id'));
    window.toggleFavorite(restaurantId);

    // 从收藏页面移除该卡片
    restaurantCard.remove();

    // 如果收藏列表为空，显示空状态
    const favorites = window.mockRestaurants.filter(restaurant => restaurant.isFavorite);
    if (favorites.length === 0) {
      document.getElementById('favoritesList').innerHTML = '<div class="empty-state"><i class="far fa-heart"></i><p>您还没有收藏任何餐厅</p></div>';
    }
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

// 监听收藏状态变化，当有餐厅被取消收藏时重新渲染收藏页面
window.addEventListener('favoriteUpdated', function (e) {
  const { restaurantId, isFavorite } = e.detail;

  // 如果当前在收藏页面并且有餐厅被取消收藏，重新渲染页面
  if (document.getElementById('favorites').classList.contains('active') && !isFavorite) {
    renderFavoritesPage();
  }
});

// 全局函数
window.renderFavoritesPage = renderFavoritesPage;
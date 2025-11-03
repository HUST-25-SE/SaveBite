// search.js
document.getElementById('searchBtn').addEventListener('click', performSearch);
document.getElementById('searchInput').addEventListener('keypress', e => {
  if (e.key === 'Enter') performSearch();
});

async function performSearch() {
  const term = document.getElementById('searchInput').value.trim();
  const container = document.getElementById('searchResults');
  if (!term) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-search"></i><p>请输入关键词</p></div>';
    return;
  }
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>搜索中...</p></div>';
  try {
    const res = await fetch(`/api/restaurants/search?keyword=${encodeURIComponent(term)}`);
    const data = await res.json();
    if (data.success && data.restaurants?.length > 0) {
      container.innerHTML = '<div class="recommend-list" id="searchResultList"></div>';
      const list = document.getElementById('searchResultList');
      data.restaurants.forEach(r => renderSearchRestaurantCard(r, list));
    } else {
      container.innerHTML = '<div class="empty-state"><i class="fas fa-search"></i><p>未找到结果</p></div>';
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>搜索失败</p></div>';
  }
}

function renderSearchRestaurantCard(restaurant, container) {
  const meituanPrice = restaurant.prices.meituan.current;
  const elePrice = restaurant.prices.ele.current;
  const recommendedPlatform = meituanPrice <= elePrice ? 'meituan' : 'ele';
  const card = document.createElement('div');
  card.className = 'restaurant-card';
  card.setAttribute('data-name', restaurant.name);
  // 👇 关键修改
  const isFavorite = userFavorites.has(restaurant.name);
  card.innerHTML = `
    <div class="restaurant-image" style="background-image: url('${restaurant.image}')"></div>
    <div class="restaurant-info">
      <div class="restaurant-name">
        ${restaurant.name}
        <button class="favorite-btn ${isFavorite ? 'active' : ''}" data-name="${restaurant.name}">
          <i class="fas fa-heart"></i>
        </button>
      </div>
      <div class="restaurant-meta">
        <div class="restaurant-rating">
          <span class="stars">${generateStars(restaurant.rating)}</span>
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
  container.appendChild(card);
  card.querySelector('.favorite-btn').addEventListener('click', e => {
    e.stopPropagation();
    const user = localStorage.getItem('currentUser');
    if (!user) {
      alert('请先登录');
      window.navigateTo('login');
      return;
    }
    toggleFavorite(restaurant.name);
  });
  card.addEventListener('click', () => {
    if (typeof window.showRestaurantDetails === 'function') {
      window.showRestaurantDetails(restaurant);
    }
  });
}

// 已有监听器，保留即可（它会更新所有按钮）
// favorites.js
async function renderFavoritesPage() {
  const container = document.getElementById('favoritesList');
  const user = localStorage.getItem('currentUser');
  if (!user) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-lock"></i>
        <p>请先登录查看收藏</p>
        <button class="submit-btn" id="goToLogin">立即登录</button>
      </div>
    `;
    document.getElementById('goToLogin').addEventListener('click', () => window.navigateTo('login'));
    return;
  }
  const userData = JSON.parse(user);
  try {
    const res = await fetch('/api/user/favorites', {
      headers: { 'X-User-ID': userData.user_id }
    });
    const data = await res.json();
    if (data.success && data.favorites?.length > 0) {
      container.innerHTML = '<div class="recommend-list" id="favoritesResultList"></div>';
      const list = document.getElementById('favoritesResultList');
      data.favorites.forEach(r => {
        renderFavoriteRestaurantCard(r, list);
      });
    } else {
      container.innerHTML = '<div class="empty-state"><i class="far fa-heart"></i><p>您还没有收藏任何餐厅</p></div>';
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>加载失败</p></div>';
  }
}

function renderFavoriteRestaurantCard(restaurant, container) {
  const meituanPrice = restaurant.prices.meituan.current;
  const elePrice = restaurant.prices.ele.current;
  const recommendedPlatform = meituanPrice <= elePrice ? 'meituan' : 'ele';
  const card = document.createElement('div');
  card.className = 'restaurant-card';
  card.setAttribute('data-name', restaurant.name);
  // 可保留 active，但为了统一也判断（其实一定是 true）
  const isFavorite = userFavorites.has(restaurant.name); // 实际必为 true
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
    toggleFavorite(restaurant.name);
    card.remove();
    if (document.querySelectorAll('#favoritesResultList .restaurant-card').length === 0) {
      document.getElementById('favoritesList').innerHTML = '<div class="empty-state"><i class="far fa-heart"></i><p>您还没有收藏任何餐厅</p></div>';
    }
  });
  card.addEventListener('click', () => {
    if (typeof window.showRestaurantDetails === 'function') {
      window.showRestaurantDetails(restaurant);
    }
  });
}

// 监听收藏状态变化（已有逻辑，保留）
window.addEventListener('favoriteUpdated', e => {
  const { restaurantName, isFavorite } = e.detail;
  const allFavoriteBtns = document.querySelectorAll(`.favorite-btn[data-name="${restaurantName}"]`);
  allFavoriteBtns.forEach(btn => {
    btn.classList.toggle('active', isFavorite);
  });
  const modalBtn = document.getElementById('modalFavoriteBtn');
  if (modalBtn && modalBtn.dataset.restaurantName === restaurantName) {
    modalBtn.classList.toggle('active', isFavorite);
    modalBtn.innerHTML = isFavorite ?
      '<i class="fas fa-heart"></i> 已收藏' :
      '<i class="fas fa-heart"></i> 收藏';
  }
  if (document.getElementById('favorites').classList.contains('active') && !isFavorite) {
    renderFavoritesPage();
  }
});

window.renderFavoritesPage = renderFavoritesPage;
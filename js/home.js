// home.js

// 轮播图（无需后端）
function initCarousel() {
  const slides = document.querySelectorAll('.carousel-slide');
  const dots = document.querySelectorAll('.carousel-dot');
  const prevBtn = document.querySelector('.carousel-prev');
  const nextBtn = document.querySelector('.carousel-next');
  let currentSlide = 0;
  let slideInterval;

  function showSlide(index) {
    slides.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    slides[index].classList.add('active');
    dots[index].classList.add('active');
    currentSlide = index;
  }

  function nextSlide() {
    showSlide((currentSlide + 1) % slides.length);
  }

  function prevSlide() {
    showSlide((currentSlide - 1 + slides.length) % slides.length);
  }

  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => {
      showSlide(i);
      resetInterval();
    });
  });

  prevBtn.addEventListener('click', () => {
    prevSlide();
    resetInterval();
  });
  nextBtn.addEventListener('click', () => {
    nextSlide();
    resetInterval();
  });

  function startInterval() {
    slideInterval = setInterval(nextSlide, 5000);
  }
  function resetInterval() {
    clearInterval(slideInterval);
    startInterval();
  }
  startInterval();

  const carousel = document.querySelector('.carousel');
  carousel.addEventListener('mouseenter', () => clearInterval(slideInterval));
  carousel.addEventListener('mouseleave', () => startInterval());
}

// 星级
function generateStars(rating) {
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    stars += i <= Math.floor(rating) ? '★' : '☆';
  }
  return stars;
}

// 切换收藏（调用后端，使用店铺名称）
async function toggleFavorite(restaurantName) {
  const user = localStorage.getItem('currentUser');
  if (!user) {
    alert('请先登录');
    window.navigateTo('login');
    return;
  }
  const userData = JSON.parse(user);
  try {
    const res = await fetch('http://localhost:5000/api/favorite/toggle', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userData.user_id
      },
      body: JSON.stringify({ shop_name: restaurantName }) // 改为使用店铺名称
    });
    const data = await res.json();
    if (data.success) {
      const btns = document.querySelectorAll(`.favorite-btn[data-name="${restaurantName}"]`);
      btns.forEach(btn => {
        btn.classList.toggle('active', data.isFavorite);
      });
      // 更新模态框按钮（如果打开）
      const modalBtn = document.getElementById('modalFavoriteBtn');
      if (modalBtn && modalBtn.dataset.restaurantName == restaurantName) {
        modalBtn.classList.toggle('active', data.isFavorite);
        modalBtn.innerHTML = data.isFavorite ?
          '<i class="fas fa-heart"></i> 已收藏' :
          '<i class="fas fa-heart"></i> 收藏';
      }
      // 触发事件供其他页面监听
      window.dispatchEvent(new CustomEvent('favoriteUpdated', {
        detail: { restaurantName, isFavorite: data.isFavorite } // 改为 restaurantName
      }));
    } else {
      alert('操作失败: ' + data.message);
    }
  } catch (err) {
    alert('网络错误: ' + err.message);
  }
}

// 渲染卡片（通用）
function renderRestaurantCard(restaurant, container) {
  const meituanPrice = restaurant.prices.meituan.current;
  const elePrice = restaurant.prices.ele.current;
  const recommendedPlatform = meituanPrice <= elePrice ? 'meituan' : 'ele';

  const card = document.createElement('div');
  card.className = 'restaurant-card';
  card.setAttribute('data-name', restaurant.name); // 改为使用店铺名称
  card.innerHTML = `
    <div class="restaurant-image" style="background-image: url('${restaurant.image}')"></div>
    <div class="restaurant-info">
      <div class="restaurant-name">
        ${restaurant.name}
        <button class="favorite-btn ${restaurant.isFavorite ? 'active' : ''}" data-name="${restaurant.name}">
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
    toggleFavorite(restaurant.name); // 传递店铺名称
  });
  card.addEventListener('click', () => {
    showRestaurantDetails(restaurant);
  });
}

// 显示详情模态框
function showRestaurantDetails(restaurant) {
  const modal = document.getElementById('restaurantModal');
  document.getElementById('modalRestaurantName').textContent = restaurant.name;
  document.getElementById('modalStars').textContent = generateStars(restaurant.rating);
  document.getElementById('modalRating').textContent = restaurant.rating;
  document.getElementById('modalReviews').textContent = `(${restaurant.reviews})`;
  document.getElementById('modalDistance').textContent = restaurant.distance;
  document.getElementById('modalDeliveryTime').textContent = restaurant.deliveryTime;
  document.getElementById('modalDeliveryFee').textContent = restaurant.deliveryFee;

  const meituanPrice = restaurant.prices.meituan.current;
  const elePrice = restaurant.prices.ele.current;
  const recommendedPlatform = meituanPrice <= elePrice ? '美团' : '饿了么';
  document.getElementById('modalRecommendedPlatform').textContent = recommendedPlatform;

  const dishesList = document.getElementById('dishesList');
  dishesList.innerHTML = '';
  (restaurant.dishes || []).forEach(dish => {
    const dishMeituan = dish.meituan != null ? parseFloat(dish.meituan) : Infinity;
    const dishEle = dish.ele != null ? parseFloat(dish.ele) : Infinity;

    // 如果两个平台都没有价格，跳过
    if (dishMeituan === Infinity && dishEle === Infinity) {
      return;
    }

    const bestPrice = Math.min(dishMeituan, dishEle);
    const plat = dishMeituan <= dishEle ? '美团' : '饿了么';

    const dishEl = document.createElement('div');
    dishEl.className = 'dish-item';
    dishEl.innerHTML = `
      <div class="dish-info">
        <div class="dish-name">${dish.name}</div>
        <div class="dish-recommendation">推荐在 <span class="platform-tag">${plat}</span> 购买</div>
      </div>
      <div class="dish-price">¥${bestPrice.toFixed(2)}</div>
    `;
    dishesList.appendChild(dishEl);
  });

  const modalBtn = document.getElementById('modalFavoriteBtn');
  modalBtn.className = `favorite-btn-modal ${restaurant.isFavorite ? 'active' : ''}`;
  modalBtn.innerHTML = restaurant.isFavorite ?
    '<i class="fas fa-heart"></i> 已收藏' :
    '<i class="fas fa-heart"></i> 收藏';
  modalBtn.dataset.restaurantName = restaurant.name; // 改为使用店铺名称
  modalBtn.onclick = () => toggleFavorite(restaurant.name);

  modal.style.display = 'block';
}

// 首页初始化
function initHomePage() {
  initCarousel();
  renderHomeRecommendations();
  document.getElementById('refreshBtn')?.addEventListener('click', renderHomeRecommendations);
}

// 获取推荐（调用搜索接口，关键词为空）
async function renderHomeRecommendations() {
  const container = document.getElementById('recommendList');
  container.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>加载中...</p></div>';
  try {
    const res = await fetch('http://localhost:5000/api/restaurants/search');
    const data = await res.json();
    container.innerHTML = '';
    if (data.success && data.restaurants) {
      data.restaurants.slice(0, 6).forEach(r => renderRestaurantCard(r, container));
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>加载失败</p></div>';
  }
}

// 模态框关闭
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('restaurantModal');
  document.getElementById('modalClose').addEventListener('click', () => {
    modal.style.display = 'none';
  });
  window.addEventListener('click', e => {
    if (e.target === modal) modal.style.display = 'none';
  });
});

// 全局暴露
window.initHomePage = initHomePage;
window.renderRestaurantCard = renderRestaurantCard;
window.toggleFavorite = toggleFavorite;
window.generateStars = generateStars;
window.showRestaurantDetails = showRestaurantDetails;
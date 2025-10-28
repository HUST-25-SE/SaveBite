// 模拟数据（在没有后端时使用）
const mockRestaurants = [
  {
    id: 1,
    name: "川味小厨",
    rating: 4.8,
    reviews: 128,
    distance: "1.2km",
    deliveryTime: "30-40分钟",
    deliveryFee: "¥3",
    minimumOrder: {
      meituan: 20,
      ele: 25
    },
    image: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&h=160&q=80",
    prices: {
      meituan: { current: 28 },
      ele: { current: 26 }
    },
    isFavorite: false,
    dishes: [
      { name: "麻婆豆腐", prices: { meituan: 28, ele: 30 } },
      { name: "宫保鸡丁", prices: { meituan: 32, ele: 35 } },
      { name: "水煮鱼", prices: { meituan: 45, ele: 48 } },
      { name: "回锅肉", prices: { meituan: 36, ele: 38 } },
      { name: "担担面", prices: { meituan: 18, ele: 20 } }
    ]
  },
  {
    id: 2,
    name: "披萨先生",
    rating: 4.5,
    reviews: 96,
    distance: "0.8km",
    deliveryTime: "25-35分钟",
    deliveryFee: "¥5",
    minimumOrder: {
      meituan: 30,
      ele: 28
    },
    image: "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&h=160&q=80",
    prices: {
      meituan: { current: 45 },
      ele: { current: 42 }
    },
    isFavorite: false,
    dishes: [
      { name: "玛格丽特披萨", prices: { meituan: 45, ele: 48 } },
      { name: "意大利香肠披萨", prices: { meituan: 52, ele: 55 } },
      { name: "海鲜披萨", prices: { meituan: 68, ele: 65 } },
      { name: "芝士披萨", prices: { meituan: 48, ele: 45 } },
      { name: "蔬菜沙拉", prices: { meituan: 25, ele: 28 } }
    ]
  },
  {
    id: 3,
    name: "日式料理屋",
    rating: 4.9,
    reviews: 210,
    distance: "2.1km",
    deliveryTime: "35-45分钟",
    deliveryFee: "¥4",
    minimumOrder: {
      meituan: 40,
      ele: 35
    },
    image: "https://images.unsplash.com/photo-1553621042-f6e147245754?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&h=160&q=80",
    prices: {
      meituan: { current: 68 },
      ele: { current: 65 }
    },
    isFavorite: false,
    dishes: [
      { name: "寿司拼盘", prices: { meituan: 68, ele: 70 } },
      { name: "刺身拼盘", prices: { meituan: 88, ele: 85 } },
      { name: "天妇罗", prices: { meituan: 45, ele: 42 } },
      { name: "拉面", prices: { meituan: 35, ele: 38 } },
      { name: "照烧鸡排", prices: { meituan: 42, ele: 45 } }
    ]
  },
  {
    id: 4,
    name: "汉堡王",
    rating: 4.3,
    reviews: 75,
    distance: "1.5km",
    deliveryTime: "20-30分钟",
    deliveryFee: "¥0",
    minimumOrder: {
      meituan: 25,
      ele: 20
    },
    image: "https://images.unsplash.com/photo-1571091718767-18b5b1457add?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&h=160&q=80",
    prices: {
      meituan: { current: 35 },
      ele: { current: 32 }
    },
    isFavorite: false,
    dishes: [
      { name: "经典汉堡", prices: { meituan: 35, ele: 38 } },
      { name: "双层牛肉汉堡", prices: { meituan: 48, ele: 45 } },
      { name: "炸鸡桶", prices: { meituan: 42, ele: 40 } },
      { name: "薯条", prices: { meituan: 15, ele: 18 } },
      { name: "可乐", prices: { meituan: 8, ele: 10 } }
    ]
  },
  {
    id: 5,
    name: "甜品时光",
    rating: 4.7,
    reviews: 142,
    distance: "0.9km",
    deliveryTime: "25-35分钟",
    deliveryFee: "¥2",
    minimumOrder: {
      meituan: 15,
      ele: 18
    },
    image: "https://images.unsplash.com/photo-1551024506-0bccd828d307?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&h=160&q=80",
    prices: {
      meituan: { current: 25 },
      ele: { current: 22 }
    },
    isFavorite: false,
    dishes: [
      { name: "提拉米苏", prices: { meituan: 25, ele: 28 } },
      { name: "巧克力蛋糕", prices: { meituan: 28, ele: 30 } },
      { name: "水果塔", prices: { meituan: 22, ele: 20 } },
      { name: "冰淇淋", prices: { meituan: 18, ele: 20 } },
      { name: "奶茶", prices: { meituan: 15, ele: 18 } }
    ]
  },
  {
    id: 6,
    name: "烧烤夜宵",
    rating: 4.6,
    reviews: 89,
    distance: "1.8km",
    deliveryTime: "40-50分钟",
    deliveryFee: "¥6",
    minimumOrder: {
      meituan: 30,
      ele: 35
    },
    image: "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&h=160&q=80",
    prices: {
      meituan: { current: 58 },
      ele: { current: 55 }
    },
    isFavorite: false,
    dishes: [
      { name: "羊肉串", prices: { meituan: 58, ele: 60 } },
      { name: "烤鸡翅", prices: { meituan: 35, ele: 38 } },
      { name: "烤茄子", prices: { meituan: 18, ele: 15 } },
      { name: "烤玉米", prices: { meituan: 12, ele: 10 } },
      { name: "啤酒", prices: { meituan: 15, ele: 18 } }
    ]
  }
];

// 轮播图功能
function initCarousel() {
  const slides = document.querySelectorAll('.carousel-slide');
  const dots = document.querySelectorAll('.carousel-dot');
  const prevBtn = document.querySelector('.carousel-prev');
  const nextBtn = document.querySelector('.carousel-next');
  let currentSlide = 0;
  let slideInterval;

  function showSlide(index) {
    // 移除所有active类
    slides.forEach(slide => slide.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));

    // 添加active类到当前幻灯片
    slides[index].classList.add('active');
    dots[index].classList.add('active');

    currentSlide = index;
  }

  function nextSlide() {
    let nextIndex = currentSlide + 1;
    if (nextIndex >= slides.length) {
      nextIndex = 0;
    }
    showSlide(nextIndex);
  }

  function prevSlide() {
    let prevIndex = currentSlide - 1;
    if (prevIndex < 0) {
      prevIndex = slides.length - 1;
    }
    showSlide(prevIndex);
  }

  // 点击指示点切换幻灯片
  dots.forEach(dot => {
    dot.addEventListener('click', function () {
      const index = parseInt(this.getAttribute('data-index'));
      showSlide(index);
      resetInterval();
    });
  });

  // 上一张/下一张按钮
  prevBtn.addEventListener('click', function () {
    prevSlide();
    resetInterval();
  });

  nextBtn.addEventListener('click', function () {
    nextSlide();
    resetInterval();
  });

  // 自动轮播
  function startInterval() {
    slideInterval = setInterval(nextSlide, 5000);
  }

  function resetInterval() {
    clearInterval(slideInterval);
    startInterval();
  }

  // 开始自动轮播
  startInterval();

  // 鼠标悬停时暂停轮播
  const carousel = document.querySelector('.carousel');
  carousel.addEventListener('mouseenter', () => {
    clearInterval(slideInterval);
  });

  carousel.addEventListener('mouseleave', () => {
    startInterval();
  });
}

// 生成星级评分
function generateStars(rating) {
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    if (i <= Math.floor(rating)) {
      stars += '★';
    } else {
      stars += '☆';
    }
  }
  return stars;
}

// 切换收藏状态
function toggleFavorite(restaurantId) {
  // 检查登录状态
  const userData = localStorage.getItem('currentUser');
  if (!userData) {
    alert('请先登录');
    window.navigateTo('login');
    return;
  }

  const restaurant = mockRestaurants.find(r => r.id === restaurantId);
  if (restaurant) {
    // 模拟实现 - 实际应该调用后端API
    restaurant.isFavorite = !restaurant.isFavorite;

    // 更新UI
    const favoriteBtns = document.querySelectorAll(`.favorite-btn[data-id="${restaurantId}"]`);
    favoriteBtns.forEach(btn => {
      btn.classList.toggle('active');
    });

    // 更新模态框收藏按钮状态（如果模态框打开）
    const modalFavoriteBtn = document.getElementById('modalFavoriteBtn');
    if (modalFavoriteBtn && modalFavoriteBtn.onclick) {
      const currentRestaurant = getCurrentModalRestaurant();
      if (currentRestaurant && currentRestaurant.id === restaurantId) {
        modalFavoriteBtn.classList.toggle('active');
        modalFavoriteBtn.innerHTML = restaurant.isFavorite ?
          '<i class="fas fa-heart"></i> 已收藏' :
          '<i class="fas fa-heart"></i> 收藏';
      }
    }

    // 触发自定义事件，通知其他页面收藏状态变化
    window.dispatchEvent(new CustomEvent('favoriteUpdated', {
      detail: {
        restaurantId: restaurantId,
        isFavorite: restaurant.isFavorite
      }
    }));

    // 如果当前在收藏页面，更新收藏列表
    if (document.getElementById('favorites').classList.contains('active')) {
      if (typeof renderFavoritesPage === 'function') {
        renderFavoritesPage();
      }
    }
  }
}

// 辅助函数：获取当前模态框显示的餐厅
function getCurrentModalRestaurant() {
  const modalRestaurantName = document.getElementById('modalRestaurantName').textContent;
  return mockRestaurants.find(r => r.name === modalRestaurantName);
}

// 渲染餐厅卡片
function renderRestaurantCard(restaurant, container, isFavoritePage = false) {
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

  container.appendChild(restaurantCard);

  // 添加收藏按钮事件
  const favoriteBtn = restaurantCard.querySelector('.favorite-btn');
  favoriteBtn.addEventListener('click', function (e) {
    e.stopPropagation(); // 防止触发卡片点击事件
    toggleFavorite(restaurant.id);
  });

  // 添加卡片点击事件，显示商家详情
  restaurantCard.addEventListener('click', function () {
    showRestaurantDetails(restaurant);
  });
}

// 显示商家详情模态框
function showRestaurantDetails(restaurant) {
  const modal = document.getElementById('restaurantModal');
  const modalRestaurantName = document.getElementById('modalRestaurantName');
  const modalStars = document.getElementById('modalStars');
  const modalRating = document.getElementById('modalRating');
  const modalReviews = document.getElementById('modalReviews');
  const modalDistance = document.getElementById('modalDistance');
  const modalDeliveryTime = document.getElementById('modalDeliveryTime');
  const modalDeliveryFee = document.getElementById('modalDeliveryFee');
  const dishesList = document.getElementById('dishesList');
  const modalFavoriteBtn = document.getElementById('modalFavoriteBtn');

  // 填充餐厅基本信息
  modalRestaurantName.textContent = restaurant.name;
  modalStars.textContent = generateStars(restaurant.rating);
  modalRating.textContent = restaurant.rating;
  modalReviews.textContent = `(${restaurant.reviews})`;
  modalDistance.textContent = restaurant.distance;
  modalDeliveryTime.textContent = restaurant.deliveryTime;
  modalDeliveryFee.textContent = restaurant.deliveryFee;

  // 确定推荐平台（价格更低的）
  const meituanPrice = restaurant.prices.meituan.current;
  const elePrice = restaurant.prices.ele.current;

  let recommendedPlatform;
  if (meituanPrice <= elePrice) {
    recommendedPlatform = '美团';
  } else {
    recommendedPlatform = '饿了么';
  }

  // 设置推荐平台名称
  document.getElementById('modalRecommendedPlatform').textContent = recommendedPlatform;

  // 填充菜品列表
  dishesList.innerHTML = '';
  restaurant.dishes.forEach(dish => {
    const dishItem = document.createElement('div');
    dishItem.className = 'dish-item';

    // 确定每道菜的推荐平台
    const dishMeituanPrice = dish.prices.meituan;
    const dishElePrice = dish.prices.ele;
    const dishRecommendedPlatform = dishMeituanPrice <= dishElePrice ? '美团' : '饿了么';
    const dishBestPrice = Math.min(dishMeituanPrice, dishElePrice);

    dishItem.innerHTML = `
      <div class="dish-info">
        <div class="dish-name">${dish.name}</div>
        <div class="dish-recommendation">推荐在 <span class="platform-tag">${dishRecommendedPlatform}</span> 购买</div>
      </div>
      <div class="dish-price">¥${dishBestPrice}</div>
    `;
    dishesList.appendChild(dishItem);
  });

  // 更新收藏按钮状态
  modalFavoriteBtn.className = restaurant.isFavorite ? 'favorite-btn-modal active' : 'favorite-btn-modal';
  modalFavoriteBtn.innerHTML = restaurant.isFavorite ?
    '<i class="fas fa-heart"></i> 已收藏' :
    '<i class="fas fa-heart"></i> 收藏';

  // 模态框收藏按钮事件
  modalFavoriteBtn.onclick = function () {
    toggleFavorite(restaurant.id);
    modalFavoriteBtn.classList.toggle('active');
    modalFavoriteBtn.innerHTML = restaurant.isFavorite ?
      '<i class="fas fa-heart"></i> 已收藏' :
      '<i class="fas fa-heart"></i> 收藏';
  };

  // 显示模态框
  modal.style.display = 'block';
}

// 首页初始化
function initHomePage() {
  initCarousel();
  renderHomeRecommendations();

  // 换一批按钮事件
  document.getElementById('refreshBtn').addEventListener('click', function () {
    renderHomeRecommendations();
  });
}

// 渲染首页推荐
function renderHomeRecommendations() {
  const recommendList = document.getElementById('recommendList');

  // 模拟实现 - 实际应该调用后端API
  // 随机选择6个餐厅显示
  const shuffled = [...mockRestaurants].sort(() => 0.5 - Math.random());
  const selected = shuffled.slice(0, 6);

  recommendList.innerHTML = '';
  selected.forEach(restaurant => {
    renderRestaurantCard(restaurant, recommendList);
  });
}

// 模态框关闭逻辑
document.addEventListener('DOMContentLoaded', function () {
  const modal = document.getElementById('restaurantModal');
  const modalClose = document.getElementById('modalClose');

  // 关闭模态框
  modalClose.addEventListener('click', function () {
    modal.style.display = 'none';
  });

  // 点击模态框外部关闭
  window.addEventListener('click', function (event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
});

// 全局函数
window.initHomePage = initHomePage;
window.renderRestaurantCard = renderRestaurantCard;
window.toggleFavorite = toggleFavorite;
window.mockRestaurants = mockRestaurants;
window.generateStars = generateStars;
window.showRestaurantDetails = showRestaurantDetails;
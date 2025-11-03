// app.js
let currentUser = null;
let userFavorites = new Set(); // 👈 新增：全局维护用户收藏集合

document.addEventListener('DOMContentLoaded', function () {
  const pages = document.querySelectorAll('.page');
  const navLinks = document.querySelectorAll('.nav-link');
  const homeLink = document.getElementById('homeLink');
  const loginLink = document.getElementById('loginLink');
  document.getElementById('logoutLink').addEventListener('click', function (e) {
    e.preventDefault();
    logout();
  });
  window.navigateTo = function (pageId) {
    pages.forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    navLinks.forEach(link => {
      link.classList.toggle('active', link.getAttribute('data-page') === pageId);
    });
    if (pageId === 'home' && typeof initHomePage === 'function') {
      initHomePage();
    } else if (pageId === 'favorites' && typeof renderFavoritesPage === 'function') {
      renderFavoritesPage();
    }
  };
  navLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      window.navigateTo(this.getAttribute('data-page'));
    });
  });
  homeLink.addEventListener('click', e => {
    e.preventDefault();
    window.navigateTo('home');
  });
  loginLink.addEventListener('click', e => {
    e.preventDefault();
    window.navigateTo('login');
  });
  checkLoginStatus();
  if (document.getElementById('home').classList.contains('active')) {
    initHomePage();
  }
});

async function checkLoginStatus() {
  const user = localStorage.getItem('currentUser');
  const token = localStorage.getItem('authToken');
  if (!user || !token) {
    logoutUI();
    return;
  }
  const userData = JSON.parse(user);
  try {
    const res = await fetch('http://localhost:5000/api/auth/me', {
      headers: { 'X-User-ID': userData.user_id }
    });
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      document.getElementById('userInfo').textContent = `欢迎，${currentUser.username}`;
      document.getElementById('userInfo').style.display = 'inline';
      document.getElementById('loginLink').style.display = 'none';
      document.getElementById('logoutLink').style.display = 'inline';

      // 👇 登录后加载收藏列表
      await loadUserFavorites();
    } else {
      logoutUI();
    }
  } catch {
    logoutUI();
  }
}

// 👇 新增：加载用户收藏
async function loadUserFavorites() {
  const user = localStorage.getItem('currentUser');
  if (!user) {
    userFavorites.clear();
    return;
  }
  const userData = JSON.parse(user);
  try {
    const res = await fetch('http://localhost:5000/api/user/favorites', {
      headers: { 'X-User-ID': userData.user_id }
    });
    const data = await res.json();
    userFavorites.clear();
    if (data.success && Array.isArray(data.favorites)) {
      data.favorites.forEach(r => userFavorites.add(r.name));
    }
  } catch (err) {
    userFavorites.clear();
  }
}

function logoutUI() {
  localStorage.removeItem('currentUser');
  localStorage.removeItem('authToken');
  currentUser = null;
  userFavorites.clear(); // 👈 清空收藏
  document.getElementById('userInfo').style.display = 'none';
  document.getElementById('loginLink').style.display = 'inline';
  document.getElementById('logoutLink').style.display = 'none';
}

function logout() {
  logoutUI();
  window.navigateTo('home');
  alert('已成功退出登录');
}

window.logout = logout;
window.userFavorites = userFavorites; // 暴露给其他模块使用
window.loadUserFavorites = loadUserFavorites;
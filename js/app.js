// 全局变量
let currentUser = null;

// 页面导航逻辑
document.addEventListener('DOMContentLoaded', function () {
  // 获取所有页面和导航链接
  const pages = document.querySelectorAll('.page');
  const navLinks = document.querySelectorAll('.nav-link');
  const homeLink = document.getElementById('homeLink');
  const loginLink = document.getElementById('loginLink');
  // 退出登录按钮点击事件
  document.getElementById('logoutLink').addEventListener('click', function (e) {
    e.preventDefault();
    logout();
  });

  // 导航函数 - 设为全局
  window.navigateTo = function (pageId) {
    // 隐藏所有页面
    pages.forEach(page => page.classList.remove('active'));

    // 显示目标页面
    document.getElementById(pageId).classList.add('active');

    // 更新导航链接状态
    navLinks.forEach(link => {
      if (link.getAttribute('data-page') === pageId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // 页面特定初始化
    if (pageId === 'home' && typeof initHomePage === 'function') {
      initHomePage();
    } else if (pageId === 'favorites' && typeof renderFavoritesPage === 'function') {
      renderFavoritesPage();
    }
  };

  // 导航链接点击事件
  navLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const pageId = this.getAttribute('data-page');
      window.navigateTo(pageId);
    });
  });

  // 首页logo点击事件
  homeLink.addEventListener('click', function (e) {
    e.preventDefault();
    window.navigateTo('home');
  });

  // 登录链接点击事件
  loginLink.addEventListener('click', function (e) {
    e.preventDefault();
    window.navigateTo('login');
  });

  // 检查用户登录状态
  checkLoginStatus();

  // 初始化首页
  if (document.getElementById('home').classList.contains('active')) {
    initHomePage();
  }
});

// 检查用户登录状态
function checkLoginStatus() {
  /* 
  【正式版需要后端支持】
  功能：检查用户登录状态
  接口：GET /api/auth/me
  请求头：Authorization: Bearer {token}
  响应：{ user: { id, username, email } }
  
  实现说明：
  1. 从localStorage获取token
  2. 调用后端接口验证token有效性
  3. 如果有效，设置currentUser并更新UI
  4. 如果无效，清除本地存储的token
  */

  // 模拟实现 - 实际应该调用后端API
  const userData = localStorage.getItem('currentUser');
  if (userData) {
    currentUser = JSON.parse(userData);
    document.getElementById('userInfo').textContent = `欢迎，${currentUser.username}`;
    document.getElementById('userInfo').style.display = 'inline';
    document.getElementById('loginLink').style.display = 'none';
    // 显示退出登录按钮
    document.getElementById('logoutLink').style.display = 'inline';
  } else {
    // 确保未登录时隐藏退出按钮
    document.getElementById('logoutLink').style.display = 'none';
  }
}

// 登出功能
function logout() {
  /* 
  【正式版需要后端支持】
  功能：用户登出
  实现说明：
  1. 可以调用后端登出接口（如果有的话）
  2. 清除本地存储的用户信息
  3. 清除前端状态
  4. 重定向到首页
  */

  // 模拟实现 - 实际应该调用后端API
  
  localStorage.removeItem('currentUser');
  localStorage.removeItem('authToken');
  currentUser = null;

  // 更新UI状态
  document.getElementById('userInfo').style.display = 'none';
  document.getElementById('loginLink').style.display = 'inline';
  document.getElementById('logoutLink').style.display = 'none';

  // 跳转到首页
  window.navigateTo('home');

  // 显示退出成功提示
  alert('已成功退出登录');
}

// 全局登出函数
window.logout = logout;
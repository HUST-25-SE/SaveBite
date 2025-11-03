// auth.js
document.addEventListener('DOMContentLoaded', function () {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const authForms = document.querySelectorAll('.auth-form');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const tabName = this.getAttribute('data-tab');
      tabBtns.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      authForms.forEach(f => {
        f.classList.toggle('active', f.id === `${tabName}Form`);
      });
    });
  });

  // 登录
  document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    if (!username || !password) {
      alert('请输入用户名和密码');
      return;
    }
    const submitBtn = this.querySelector('.submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = '登录中...';
    try {
      const res = await fetch('http://localhost:5000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('currentUser', JSON.stringify(data.user));
        localStorage.setItem('authToken', data.token);
        document.getElementById('userInfo').textContent = `欢迎，${username}`;
        document.getElementById('userInfo').style.display = 'inline';
        document.getElementById('loginLink').style.display = 'none';
        document.getElementById('logoutLink').style.display = 'inline';

        // 👇 新增
        await loadUserFavorites();

        window.navigateTo('home');
        this.reset();
      } else {
        alert('登录失败: ' + data.message);
      }
    } catch (err) {
      alert('网络错误: ' + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '登录';
    }
  });

  // 注册
  document.getElementById('registerForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    if (!username || !email || !password || !confirmPassword) {
      alert('请填写所有字段');
      return;
    }
    if (password !== confirmPassword) {
      alert('密码不一致');
      return;
    }
    if (password.length < 6) {
      alert('密码至少6位');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert('邮箱格式无效');
      return;
    }
    const submitBtn = this.querySelector('.submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = '注册中...';
    try {
      const res = await fetch('http://localhost:5000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('currentUser', JSON.stringify(data.user));
        localStorage.setItem('authToken', data.token);
        document.getElementById('userInfo').textContent = `欢迎，${username}`;
        document.getElementById('userInfo').style.display = 'inline';
        document.getElementById('loginLink').style.display = 'none';
        document.getElementById('logoutLink').style.display = 'inline';

        // 👇 新增
        await loadUserFavorites();

        alert('注册成功！已自动登录');
        window.navigateTo('home');
        this.reset();
      } else {
        alert('注册失败: ' + data.message);
      }
    } catch (err) {
      alert('网络错误: ' + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '注册';
    }
  });
});

window.registerUser = async function (username, email, password) {
  const res = await fetch('http://localhost:5000/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  });
  return await res.json();
};
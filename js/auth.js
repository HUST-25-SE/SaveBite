// 登录/注册页面功能
document.addEventListener('DOMContentLoaded', function () {
  // 标签页切换功能
  const tabBtns = document.querySelectorAll('.tab-btn');
  const authForms = document.querySelectorAll('.auth-form');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const tabName = this.getAttribute('data-tab');

      // 更新标签按钮状态
      tabBtns.forEach(tab => tab.classList.remove('active'));
      this.classList.add('active');

      // 显示对应的表单
      authForms.forEach(form => {
        form.classList.remove('active');
        if (form.id === `${tabName}Form`) {
          form.classList.add('active');
        }
      });
    });
  });

  // 登录表单提交
  document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault();

    /* 
    【正式版需要后端支持】
    功能：用户登录
    接口：POST /api/auth/login
    请求体：{ username, password }
    响应：{ 
        success: true, 
        token: "jwt_token_string",
        user: { id, username, email } 
    }
    
    实现说明：
    1. 获取表单数据并进行基本验证
    2. 调用后端登录接口
    3. 保存token和用户信息到localStorage
    4. 更新UI状态
    5. 跳转到首页或原请求页面
    6. 处理登录失败情况（显示错误信息）
    */

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // 基本表单验证
    if (!username || !password) {
      alert('请输入用户名和密码');
      return;
    }

    // 显示加载状态
    const submitBtn = this.querySelector('.submit-btn');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '登录中...';
    submitBtn.disabled = true;

    // 模拟API调用 - 实际应该调用后端API
    setTimeout(() => {
      try {
        // 模拟登录成功
        const userData = {
          id: Date.now(),
          username: username,
          email: `${username}@example.com`
        };

        // 保存用户信息和token到localStorage
        localStorage.setItem('currentUser', JSON.stringify(userData));
        localStorage.setItem('authToken', 'mock_jwt_token_' + Date.now()); // 正式版应该使用后端返回的token

        // 更新UI
        document.getElementById('userInfo').textContent = `欢迎，${username}`;
        document.getElementById('userInfo').style.display = 'inline';
        document.getElementById('loginLink').style.display = 'none';

        // 跳转到首页
        window.navigateTo('home');

        // 重置表单
        this.reset();
      } catch (error) {
        alert('登录失败: ' + error.message);
      } finally {
        // 恢复按钮状态
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    }, 1000);
  });

  // 注册表单提交
  document.getElementById('registerForm').addEventListener('submit', function (e) {
    e.preventDefault();

    /* 
    【正式版需要后端支持】
    功能：用户注册
    接口：POST /api/auth/register
    请求体：{ username, password, email }
    响应：{ 
        success: true, 
        message: "注册成功",
        user: { id, username, email } 
    }
    
    实现说明：
    1. 获取表单数据并进行验证（用户名格式、密码强度、邮箱格式等）
    2. 检查密码和确认密码是否匹配
    3. 调用后端注册接口
    4. 注册成功后自动登录或跳转到登录页
    5. 处理注册失败情况（用户名已存在、邮箱已注册等）
    */

    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    // 表单验证
    if (!username || !email || !password || !confirmPassword) {
      alert('请填写所有必填字段');
      return;
    }

    if (password !== confirmPassword) {
      alert('两次输入的密码不一致');
      return;
    }

    if (password.length < 6) {
      alert('密码长度至少6位');
      return;
    }

    // 简单的邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert('请输入有效的邮箱地址');
      return;
    }

    // 显示加载状态
    const submitBtn = this.querySelector('.submit-btn');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '注册中...';
    submitBtn.disabled = true;

    // 模拟API调用 - 实际应该调用后端API
    setTimeout(() => {
      try {
        /* 
        实际后端调用示例：
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || '注册失败');
        }
        
        // 注册成功处理
        */

        // 模拟注册成功
        const userData = {
          id: Date.now(),
          username: username,
          email: email
        };

        // 保存用户信息和token到localStorage（模拟自动登录）
        localStorage.setItem('currentUser', JSON.stringify(userData));
        localStorage.setItem('authToken', 'mock_jwt_token_' + Date.now()); // 正式版应该使用后端返回的token

        // 更新UI
        document.getElementById('userInfo').textContent = `欢迎，${username}`;
        document.getElementById('userInfo').style.display = 'inline';
        document.getElementById('loginLink').style.display = 'none';

        // 显示成功消息
        alert('注册成功！已自动登录');

        // 跳转到首页
        window.navigateTo('home');

        // 重置表单
        this.reset();
      } catch (error) {
        alert('注册失败: ' + error.message);
      } finally {
        // 恢复按钮状态
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    }, 1500);
  });
});

// 全局注册函数（供其他模块调用）
window.registerUser = async function (username, email, password) {
  /* 
  【正式版需要后端支持】
  功能：用户注册（程序化调用）
  接口：POST /api/auth/register
  请求体：{ username, email, password }
  响应：{ success: true, user: { id, username, email } }
  
  实现说明：
  1. 调用后端注册接口
  2. 返回注册结果
  3. 可以用于第三方注册或程序化注册场景
  */

  // 模拟实现
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 模拟成功注册
      resolve({
        success: true,
        user: {
          id: Date.now(),
          username: username,
          email: email
        }
      });
    }, 1000);
  });
};
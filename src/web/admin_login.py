"""
Admin Login Page - 管理后台登录界面
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.services.auth_service import AuthService
from src.core.security import generate_token

router = APIRouter(prefix="/admin", tags=["Admin Login"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page():
    """管理后台登录页面."""
    html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signal Transceiver - 管理后台登录</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      background-attachment: fixed;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    /* 动态背景 */
    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3), transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(252, 70, 107, 0.3), transparent 50%),
        radial-gradient(circle at 40% 20%, rgba(99, 179, 237, 0.3), transparent 50%);
      animation: float 20s ease-in-out infinite;
      z-index: -1;
    }
    @keyframes float {
      0%, 100% { transform: translate(0, 0); }
      25% { transform: translate(10px, -10px); }
      50% { transform: translate(-5px, 5px); }
      75% { transform: translate(5px, 10px); }
    }
    .login-container {
      background: rgba(255, 255, 255, 0.25);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 20px;
      padding: 3rem;
      box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
      width: 100%;
      max-width: 450px;
      animation: slideIn 0.5s ease-out;
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(30px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .logo {
      text-align: center;
      margin-bottom: 2rem;
    }
    .logo h1 {
      color: white;
      font-size: 2rem;
      font-weight: 700;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 0.5rem;
    }
    .logo p {
      color: rgba(255, 255, 255, 0.9);
      font-size: 0.875rem;
    }
    .form-group {
      margin-bottom: 1.5rem;
    }
    label {
      display: block;
      color: white;
      font-weight: 600;
      margin-bottom: 0.5rem;
      font-size: 0.875rem;
    }
    input {
      width: 100%;
      padding: 0.875rem 1rem;
      background: rgba(255, 255, 255, 0.9);
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 10px;
      font-size: 1rem;
      transition: all 0.3s;
    }
    input:focus {
      outline: none;
      background: white;
      border-color: rgba(255, 255, 255, 0.8);
      box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    .btn {
      width: 100%;
      padding: 0.875rem;
      background: rgba(255, 255, 255, 0.3);
      backdrop-filter: blur(10px);
      color: white;
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 10px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s;
      text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .btn:hover {
      background: rgba(255, 255, 255, 0.4);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .btn:active {
      transform: translateY(0);
    }
    .error {
      background: rgba(239, 68, 68, 0.9);
      color: white;
      padding: 0.75rem 1rem;
      border-radius: 10px;
      margin-bottom: 1rem;
      font-size: 0.875rem;
      display: none;
    }
    .error.show {
      display: block;
      animation: shake 0.5s;
    }
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-10px); }
      75% { transform: translateX(10px); }
    }
    .footer {
      margin-top: 2rem;
      text-align: center;
      color: rgba(255, 255, 255, 0.8);
      font-size: 0.875rem;
    }
    .footer a {
      color: white;
      text-decoration: none;
      font-weight: 600;
    }
    .loading {
      display: none;
      text-align: center;
      margin-top: 1rem;
    }
    .spinner {
      border: 3px solid rgba(255, 255, 255, 0.3);
      border-top-color: white;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 0.8s linear infinite;
      margin: 0 auto;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="login-container">
    <div class="logo">
      <h1>🚀 Signal Transceiver</h1>
      <p>管理后台登录</p>
    </div>
    
    <div id="error" class="error"></div>
    
    <form id="loginForm" onsubmit="handleLogin(event)">
      <div class="form-group">
        <label for="username">用户名</label>
        <input 
          type="text" 
          id="username" 
          name="username" 
          required 
          autocomplete="username"
          placeholder="请输入用户名"
        />
      </div>
      
      <div class="form-group">
        <label for="password">密码</label>
        <input 
          type="password" 
          id="password" 
          name="password" 
          required 
          autocomplete="current-password"
          placeholder="请输入密码"
        />
      </div>
      
      <button type="submit" class="btn">登录</button>
      
      <div class="loading" id="loading">
        <div class="spinner"></div>
      </div>
    </form>
    
    <div class="footer">
      <p>还没有账号？请联系管理员</p>
      <p><a href="/docs" target="_blank">API 文档</a> | <a href="/health" target="_blank">系统状态</a></p>
    </div>
  </div>

  <script>
    async function handleLogin(event) {
      event.preventDefault();
      
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const errorDiv = document.getElementById('error');
      const loading = document.getElementById('loading');
      const btn = event.target.querySelector('.btn');
      
      // 隐藏错误
      errorDiv.classList.remove('show');
      errorDiv.textContent = '';
      
      // 显示加载
      btn.disabled = true;
      btn.textContent = '登录中...';
      loading.style.display = 'block';
      
      try {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
          // 登录成功，保存 API Key
          if (data.data && data.data.api_key) {
            localStorage.setItem('adminApiKey', data.data.api_key);
            localStorage.setItem('adminUsername', username);
            
            // 跳转到管理界面
            window.location.href = '/admin/ui';
          } else {
            showError('登录成功但未返回 API Key');
          }
        } else {
          showError(data.message || '登录失败，请检查用户名和密码');
        }
      } catch (error) {
        showError('网络错误：' + error.message);
      } finally {
        btn.disabled = false;
        btn.textContent = '登录';
        loading.style.display = 'none';
      }
    }
    
    function showError(message) {
      const errorDiv = document.getElementById('error');
      errorDiv.textContent = '❌ ' + message;
      errorDiv.classList.add('show');
    }
    
    // 检查是否已登录
    window.onload = function() {
      const apiKey = localStorage.getItem('adminApiKey');
      if (apiKey) {
        // 已登录，跳转到管理界面
        window.location.href = '/admin/ui';
      }
    };
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/logout")
async def admin_logout():
    """退出登录."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
  <title>退出登录</title>
  <script>
    localStorage.removeItem('adminApiKey');
    localStorage.removeItem('adminUsername');
    window.location.href = '/admin/login';
  </script>
</head>
<body>
  <p>正在退出...</p>
</body>
</html>
""")

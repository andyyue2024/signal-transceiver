"""
Enhanced admin UI with beautiful, interactive management interface.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin/ui", tags=["Admin UI"])


@router.get("", response_class=HTMLResponse)
async def admin_ui_home():
    """Admin UI entry point with enhanced interface."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signal Transceiver Admin Console</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      background-attachment: fixed;
      min-height: 100vh;
      padding: 2rem;
      color: #1f2937;
      position: relative;
      overflow-x: hidden;
    }
    /* 动态背景效果 */
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
    .container { max-width: 1400px; margin: 0 auto; }
    /* 毛玻璃效果 Header */
    header { 
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      padding: 2rem;
      border-radius: 20px;
      box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    h1 { 
      color: white;
      font-size: 2.5rem;
      font-weight: 700;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .status { display: flex; gap: 1rem; align-items: center; }
    .status-badge { 
      padding: 0.5rem 1.2rem;
      background: rgba(16, 185, 129, 0.9);
      backdrop-filter: blur(10px);
      color: white;
      border-radius: 25px;
      font-size: 0.875rem;
      font-weight: 600;
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
      animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }
    /* 毛玻璃效果卡片 */
    .card { 
      background: rgba(255, 255, 255, 0.25);
      backdrop-filter: blur(15px);
      -webkit-backdrop-filter: blur(15px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      padding: 1.5rem;
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .card:hover { 
      transform: translateY(-5px) scale(1.02);
      box-shadow: 0 12px 40px rgba(31, 38, 135, 0.2);
      background: rgba(255, 255, 255, 0.35);
    }
    .card h2 { 
      color: white;
      font-size: 1.25rem;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 2px solid rgba(255, 255, 255, 0.3);
      text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .grid { 
      display: grid;
      gap: 1.5rem;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      margin-bottom: 1.5rem;
    }
    /* 毛玻璃 API Key 区域 */
    .api-key-section {
      background: rgba(102, 126, 234, 0.2);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      color: white;
      padding: 2rem;
      border-radius: 20px;
      margin-bottom: 2rem;
      box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
    }
    .api-key-section h2 { color: white; border-bottom-color: rgba(255,255,255,0.3); }
    input { 
      width: 100%;
      padding: 0.75rem 1rem;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(10px);
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 10px;
      font-size: 1rem;
      transition: all 0.3s;
    }
    input:focus { 
      outline: none;
      border-color: rgba(255, 255, 255, 0.8);
      background: rgba(255, 255, 255, 1);
      box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    button { 
      padding: 0.75rem 1.5rem;
      background: rgba(255, 255, 255, 0.25);
      backdrop-filter: blur(10px);
      color: white;
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      font-size: 0.875rem;
      text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    button:hover { 
      background: rgba(255, 255, 255, 0.4);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    button:active { transform: translateY(0); }
    button.secondary { background: rgba(107, 114, 128, 0.3); }
    button.secondary:hover { background: rgba(75, 85, 99, 0.4); }
    button.danger { background: rgba(239, 68, 68, 0.3); }
    button.danger:hover { background: rgba(220, 38, 38, 0.4); }
    .button-group { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1rem; }
    pre { 
      background: rgba(31, 41, 55, 0.8);
      backdrop-filter: blur(10px);
      color: #e5e7eb;
      padding: 1rem;
      border-radius: 12px;
      overflow: auto;
      max-height: 300px;
      margin-top: 1rem;
      font-size: 0.875rem;
      line-height: 1.5;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .muted { color: rgba(255, 255, 255, 0.8); font-size: 0.875rem; margin-top: 0.5rem; }
    /* 毛玻璃标签页 */
    .tabs { 
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(15px);
      border-radius: 15px;
      padding: 0.5rem;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .tab { 
      padding: 0.75rem 1.5rem;
      background: transparent;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.7);
      transition: all 0.3s;
    }
    .tab:hover {
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }
    .tab.active { 
      background: rgba(255, 255, 255, 0.3);
      backdrop-filter: blur(10px);
      color: white;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.4s; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .metric { 
      background: rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      padding: 1rem;
      border-radius: 12px;
      text-align: center;
      transition: all 0.3s;
    }
    .metric:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: scale(1.05);
    }
    .metric-value { 
      font-size: 2.5rem;
      font-weight: 700;
      color: white;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-label { 
      font-size: 0.875rem;
      color: rgba(255, 255, 255, 0.9);
      margin-top: 0.25rem;
      font-weight: 500;
    }
    .loading { 
      display: inline-block;
      width: 1rem;
      height: 1rem;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .empty-state {
      text-align: center;
      padding: 3rem;
      color: rgba(255, 255, 255, 0.7);
    }
    .links { 
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
      flex-wrap: wrap;
    }
    .links a {
      color: white;
      text-decoration: none;
      font-weight: 600;
      padding: 0.5rem 1rem;
      background: rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(10px);
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.3);
      transition: all 0.3s;
    }
    .links a:hover { 
      background: rgba(255, 255, 255, 0.3);
      transform: translateY(-2px);
    }
    /* 通知样式 */
    .notification {
      position: fixed;
      top: 2rem;
      right: 2rem;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(20px);
      padding: 1rem 1.5rem;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
      z-index: 1000;
      border: 1px solid rgba(255, 255, 255, 0.3);
      animation: slideIn 0.4s ease-out;
    }
    @keyframes slideIn {
      from { transform: translateX(400px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    /* 告警卡片 */
    .alert-item {
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      padding: 1rem;
      border-radius: 10px;
      margin-bottom: 0.5rem;
      transition: all 0.3s;
    }
    .alert-item:hover {
      background: rgba(255, 255, 255, 0.25);
      transform: translateX(5px);
    }
    .alert-badge {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-right: 0.5rem;
    }
    .alert-badge.info { background: rgba(59, 130, 246, 0.8); color: white; }
    .alert-badge.warning { background: rgba(245, 158, 11, 0.8); color: white; }
    .alert-badge.error { background: rgba(239, 68, 68, 0.8); color: white; }
    .alert-badge.critical { background: rgba(153, 27, 27, 0.9); color: white; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>🚀 Signal Transceiver</h1>
        <p class="muted">Admin Console v1.0</p>
      </div>
      <div class="status">
        <span class="status-badge">● Online</span>
      </div>
    </header>

    <div class="api-key-section">
      <h2>🔐 API Authentication</h2>
      <input id="apiKey" type="password" placeholder="Enter your API Key" />
      <div class="button-group">
        <button onclick="saveKey()">💾 Save Key</button>
        <button class="secondary" onclick="toggleKeyVisibility()">👁️ Show/Hide</button>
        <button class="danger" onclick="clearKey()">🗑️ Clear</button>
      </div>
      <p class="muted">Your API key is stored locally and never sent to external servers.</p>
    </div>

    <div class="tabs">
      <button class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</button>
      <button class="tab" onclick="switchTab('users')">👥 Users</button>
      <button class="tab" onclick="switchTab('clients')">🔌 Clients</button>
      <button class="tab" onclick="switchTab('strategies')">📈 Strategies</button>
      <button class="tab" onclick="switchTab('subscriptions')">📬 Subscriptions</button>
      <button class="tab" onclick="switchTab('permissions')">🔒 Permissions</button>
      <button class="tab" onclick="switchTab('alerts')">🚨 Alerts</button>
      <button class="tab" onclick="switchTab('config')">⚙️ Config</button>
      <button class="tab" onclick="switchTab('logs')">📝 Logs</button>
    </div>

    <div id="dashboard" class="tab-content active">
      <div class="grid">
        <div class="card">
          <h2>System Metrics</h2>
          <div class="button-group">
            <button onclick="loadMetrics()">🔄 Refresh</button>
          </div>
          <div id="metricsGrid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;">
            <div class="metric">
              <div class="metric-value" id="metricUsers">-</div>
              <div class="metric-label">Users</div>
            </div>
            <div class="metric">
              <div class="metric-value" id="metricClients">-</div>
              <div class="metric-label">Clients</div>
            </div>
            <div class="metric">
              <div class="metric-value" id="metricData">-</div>
              <div class="metric-label">Data Records</div>
            </div>
            <div class="metric">
              <div class="metric-value" id="metricSubs">-</div>
              <div class="metric-label">Subscriptions</div>
            </div>
          </div>
        </div>
        <div class="card">
          <h2>System Health</h2>
          <div class="button-group">
            <button onclick="loadHealth()">🔄 Check Health</button>
          </div>
          <pre id="healthOut">Click "Check Health" to load system status</pre>
        </div>
      </div>
    </div>

    <div id="users" class="tab-content">
      <div class="card">
        <h2>User Management</h2>
        <div class="button-group">
          <button onclick="loadData('/api/v1/auth/me', 'usersOut')">Load Current User</button>
        </div>
        <pre id="usersOut">No data loaded</pre>
        <p class="muted">Full user list available via CLI: <code>python -m src.cli user list</code></p>
      </div>
    </div>

    <div id="clients" class="tab-content">
      <div class="card">
        <h2>Client Management</h2>
        <div class="button-group">
          <button onclick="loadData('/api/v1/clients', 'clientsOut')">📋 Load All Clients</button>
          <button onclick="showCreateClient()">➕ Create Client</button>
        </div>
        <pre id="clientsOut">No data loaded</pre>
      </div>
    </div>

    <div id="strategies" class="tab-content">
      <div class="card">
        <h2>Strategy Management</h2>
        <div class="button-group">
          <button onclick="loadData('/api/v1/strategies', 'strategiesOut')">📋 Load All Strategies</button>
        </div>
        <pre id="strategiesOut">No data loaded</pre>
      </div>
    </div>

    <div id="subscriptions" class="tab-content">
      <div class="card">
        <h2>Subscription Management</h2>
        <div class="button-group">
          <button onclick="loadData('/api/v1/subscriptions', 'subsOut')">📋 Load All Subscriptions</button>
        </div>
        <pre id="subsOut">No data loaded</pre>
      </div>
    </div>

    <div id="permissions" class="tab-content">
      <div class="grid">
        <div class="card">
          <h2>Roles</h2>
          <div class="button-group">
            <button onclick="loadData('/api/v1/admin/roles', 'rolesOut')">📋 Load Roles</button>
          </div>
          <pre id="rolesOut">No data loaded</pre>
        </div>
        <div class="card">
          <h2>Permissions</h2>
          <div class="button-group">
            <button onclick="loadData('/api/v1/admin/permissions', 'permsOut')">📋 Load Permissions</button>
          </div>
          <pre id="permsOut">No data loaded</pre>
        </div>
      </div>
    </div>

    <div id="alerts" class="tab-content">
      <div class="grid">
        <div class="card">
          <h2>🚨 Active Alerts</h2>
          <div class="button-group">
            <button onclick="loadAlerts('active')">📋 Load Active</button>
            <button onclick="loadAlerts('all')">📚 Load All</button>
            <button onclick="testAlert()">🧪 Send Test Alert</button>
          </div>
          <pre id="alertsOut">No alerts loaded</pre>
        </div>

        <div class="card">
          <h2>⚙️ Alert Configuration</h2>
          <div style="margin-top: 1rem;">
            <label style="color: white; display: block; margin-bottom: 0.5rem;">Alert Level</label>
            <select id="alertLevel" style="width: 100%; padding: 0.75rem; border-radius: 10px; background: rgba(255,255,255,0.9); border: 2px solid rgba(255,255,255,0.3);">
              <option value="info">ℹ️ Info</option>
              <option value="warning">⚠️ Warning</option>
              <option value="error">❌ Error</option>
              <option value="critical">🔥 Critical</option>
            </select>
          </div>
          <div style="margin-top: 1rem;">
            <label style="color: white; display: block; margin-bottom: 0.5rem;">Title</label>
            <input id="alertTitle" placeholder="Alert title" />
          </div>
          <div style="margin-top: 1rem;">
            <label style="color: white; display: block; margin-bottom: 0.5rem;">Message</label>
            <input id="alertMessage" placeholder="Alert message" />
          </div>
          <div class="button-group">
            <button onclick="createTestAlert()">📤 Create Test Alert</button>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>📊 Alert Statistics</h2>
        <div class="button-group">
          <button onclick="loadData('/api/v1/monitor/dashboard', 'alertStatsOut')">📈 Load Stats</button>
        </div>
        <div id="alertStatsGrid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 1rem;">
          <div class="metric">
            <div class="metric-value" id="alertTotal">0</div>
            <div class="metric-label">Total Alerts</div>
          </div>
          <div class="metric">
            <div class="metric-value" id="alertActive">0</div>
            <div class="metric-label">Active</div>
          </div>
          <div class="metric">
            <div class="metric-value" id="alertResolved">0</div>
            <div class="metric-label">Resolved</div>
          </div>
          <div class="metric">
            <div class="metric-value" id="alertCritical">0</div>
            <div class="metric-label">Critical</div>
          </div>
        </div>
        <pre id="alertStatsOut" style="margin-top: 1rem;">Click "Load Stats" to view alert statistics</pre>
      </div>
    </div>

    <div id="config" class="tab-content">
      <div class="card">
        <h2>System Configuration</h2>
        <div class="button-group">
          <button onclick="loadData('/api/v1/config', 'configOut')">📋 Load Config</button>
        </div>
        <pre id="configOut">No data loaded</pre>
        <p class="muted">⚠️ Admin permissions required</p>
      </div>
    </div>

    <div id="logs" class="tab-content">
      <div class="card">
        <h2>System Logs</h2>
        <div class="button-group">
          <button onclick="loadData('/api/v1/logs?hours=24&limit=50', 'logsOut')">📋 Last 24h</button>
          <button onclick="loadData('/api/v1/logs?level=ERROR&hours=168', 'logsOut')">🚨 Errors (7d)</button>
          <button onclick="loadData('/api/v1/logs/stats', 'logsOut')">📊 Statistics</button>
        </div>
        <pre id="logsOut">No data loaded</pre>
      </div>
    </div>

    <div class="card">
      <h2>📚 Quick Links</h2>
      <div class="links">
        <a href="/docs" target="_blank">API Documentation</a>
        <a href="/api/v1/monitor/metrics" target="_blank">Prometheus Metrics</a>
        <a href="/health" target="_blank">Health Check</a>
      </div>
    </div>
  </div>

  <script>
    const keyInput = document.getElementById('apiKey');
    const storedKey = localStorage.getItem('adminApiKey');
    if (storedKey) keyInput.value = storedKey;

    function saveKey() {
      localStorage.setItem('adminApiKey', keyInput.value || '');
      showNotification('✅ API Key saved successfully');
    }

    function clearKey() {
      if (confirm('Clear saved API key?')) {
        localStorage.removeItem('adminApiKey');
        keyInput.value = '';
        showNotification('🗑️ API Key cleared');
      }
    }

    function toggleKeyVisibility() {
      keyInput.type = keyInput.type === 'password' ? 'text' : 'password';
    }

    function switchTab(tabName) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById(tabName).classList.add('active');
    }

    async function loadData(url, outId) {
      const out = document.getElementById(outId);
      out.innerHTML = '<div class="loading"></div> Loading...';
      const key = keyInput.value || localStorage.getItem('adminApiKey');
      const headers = key ? { 'X-API-Key': key } : {};
      
      try {
        const res = await fetch(url, { headers });
        const text = await res.text();
        let formatted;
        try {
          formatted = JSON.stringify(JSON.parse(text), null, 2);
        } catch {
          formatted = text;
        }
        out.textContent = formatted;
      } catch (e) {
        out.textContent = '❌ Error: ' + e.message;
      }
    }

    async function loadMetrics() {
      const key = keyInput.value || localStorage.getItem('adminApiKey');
      const headers = key ? { 'X-API-Key': key } : {};
      
      try {
        const res = await fetch('/api/v1/admin/stats', { headers });
        const data = await res.json();
        
        if (data.success && data.data) {
          document.getElementById('metricUsers').textContent = data.data.total_users || '-';
          document.getElementById('metricClients').textContent = data.data.total_clients || '-';
          document.getElementById('metricData').textContent = data.data.total_data || '-';
          document.getElementById('metricSubs').textContent = data.data.total_subscriptions || '-';
        }
      } catch (e) {
        console.error('Failed to load metrics:', e);
      }
    }

    async function loadHealth() {
      await loadData('/health/detailed', 'healthOut');
    }

    function showNotification(message) {
      const notif = document.createElement('div');
      notif.className = 'notification';
      notif.textContent = message;
      document.body.appendChild(notif);
      setTimeout(() => notif.remove(), 3000);
    }

    async function loadAlerts(type) {
      const url = type === 'all' 
        ? '/api/v1/monitor/alerts?active_only=false'
        : '/api/v1/monitor/alerts?active_only=true';
      await loadData(url, 'alertsOut');
    }

    async function testAlert() {
      const key = keyInput.value || localStorage.getItem('adminApiKey');
      if (!key) {
        showNotification('⚠️ Please set API Key first');
        return;
      }

      const url = '/api/v1/monitor/alerts/test?title=Test+Alert&message=This+is+a+test+alert&level=info';
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'X-API-Key': key }
        });
        const data = await res.json();
        showNotification(data.success ? '✅ Test alert sent!' : '❌ Failed to send alert');
      } catch (e) {
        showNotification('❌ Error: ' + e.message);
      }
    }

    async function createTestAlert() {
      const key = keyInput.value || localStorage.getItem('adminApiKey');
      if (!key) {
        showNotification('⚠️ Please set API Key first');
        return;
      }

      const level = document.getElementById('alertLevel').value;
      const title = document.getElementById('alertTitle').value || 'Test Alert';
      const message = document.getElementById('alertMessage').value || 'This is a test alert';

      const url = `/api/v1/monitor/alerts/test?title=${encodeURIComponent(title)}&message=${encodeURIComponent(message)}&level=${level}`;
      
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'X-API-Key': key }
        });
        const data = await res.json();
        if (data.success) {
          showNotification('✅ Alert created successfully!');
          loadAlerts('active');
        } else {
          showNotification('❌ Failed: ' + data.message);
        }
      } catch (e) {
        showNotification('❌ Error: ' + e.message);
      }
    }

    function showCreateClient() {
      alert('Create Client form - implement as needed');
    }

    // Auto-load metrics on dashboard
    if (localStorage.getItem('adminApiKey')) {
      loadMetrics();
    }
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/health", response_class=HTMLResponse)
async def admin_ui_health():
    """Admin UI health page."""
    return HTMLResponse(content="<p>Admin UI is running.</p>")

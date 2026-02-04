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
      min-height: 100vh;
      padding: 2rem;
      color: #1f2937;
    }
    .container { max-width: 1400px; margin: 0 auto; }
    header { 
      background: white;
      padding: 2rem;
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    h1 { color: #667eea; font-size: 2rem; font-weight: 700; }
    .status { display: flex; gap: 1rem; align-items: center; }
    .status-badge { 
      padding: 0.5rem 1rem;
      background: #10b981;
      color: white;
      border-radius: 20px;
      font-size: 0.875rem;
      font-weight: 600;
    }
    .card { 
      background: white;
      padding: 1.5rem;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover { 
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    .card h2 { 
      color: #667eea;
      font-size: 1.25rem;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 2px solid #f3f4f6;
    }
    .grid { 
      display: grid;
      gap: 1.5rem;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      margin-bottom: 1.5rem;
    }
    .api-key-section {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 2rem;
      border-radius: 12px;
      margin-bottom: 2rem;
    }
    .api-key-section h2 { color: white; border-bottom-color: rgba(255,255,255,0.3); }
    input { 
      width: 100%;
      padding: 0.75rem 1rem;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
      font-size: 1rem;
      transition: border-color 0.2s;
    }
    input:focus { 
      outline: none;
      border-color: #667eea;
    }
    button { 
      padding: 0.75rem 1.5rem;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, transform 0.1s;
      font-size: 0.875rem;
    }
    button:hover { 
      background: #5568d3;
      transform: translateY(-1px);
    }
    button:active { transform: translateY(0); }
    button.secondary { background: #6b7280; }
    button.secondary:hover { background: #4b5563; }
    button.danger { background: #ef4444; }
    button.danger:hover { background: #dc2626; }
    .button-group { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1rem; }
    pre { 
      background: #1f2937;
      color: #e5e7eb;
      padding: 1rem;
      border-radius: 8px;
      overflow: auto;
      max-height: 300px;
      margin-top: 1rem;
      font-size: 0.875rem;
      line-height: 1.5;
    }
    .muted { color: #6b7280; font-size: 0.875rem; margin-top: 0.5rem; }
    .tabs { 
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
      border-bottom: 2px solid #e5e7eb;
    }
    .tab { 
      padding: 0.75rem 1.5rem;
      background: transparent;
      border: none;
      border-bottom: 3px solid transparent;
      cursor: pointer;
      font-weight: 600;
      color: #6b7280;
      transition: all 0.2s;
    }
    .tab.active { 
      color: #667eea;
      border-bottom-color: #667eea;
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .metric { 
      background: #f9fafb;
      padding: 1rem;
      border-radius: 8px;
      text-align: center;
    }
    .metric-value { 
      font-size: 2rem;
      font-weight: 700;
      color: #667eea;
    }
    .metric-label { 
      font-size: 0.875rem;
      color: #6b7280;
      margin-top: 0.25rem;
    }
    .loading { 
      display: inline-block;
      width: 1rem;
      height: 1rem;
      border: 2px solid #e5e7eb;
      border-top-color: #667eea;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .empty-state {
      text-align: center;
      padding: 3rem;
      color: #9ca3af;
    }
    .links { 
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
    }
    .links a {
      color: #667eea;
      text-decoration: none;
      font-weight: 600;
      transition: color 0.2s;
    }
    .links a:hover { color: #5568d3; }
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
      notif.style.cssText = 'position:fixed;top:2rem;right:2rem;background:white;padding:1rem 1.5rem;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:1000;';
      notif.textContent = message;
      document.body.appendChild(notif);
      setTimeout(() => notif.remove(), 3000);
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

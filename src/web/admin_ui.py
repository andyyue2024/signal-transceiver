"""
Minimal admin UI backend routes.
Provides a simple HTML admin dashboard shell.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin/ui", tags=["Admin UI"])


@router.get("", response_class=HTMLResponse)
async def admin_ui_home():
    """Admin UI entry point."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signal Transceiver Admin</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; color: #1f2937; }
    header { margin-bottom: 1.5rem; }
    .card { border: 1px solid #e5e7eb; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    code { background: #f3f4f6; padding: 0.1rem 0.3rem; border-radius: 4px; }
  </style>
</head>
<body>
  <header>
    <h1>Signal Transceiver Admin</h1>
    <p>Backend management UI shell. Use the API endpoints below for data.</p>
  </header>
  <div class="card">
    <h2>Quick Links</h2>
    <ul>
      <li><a href="/docs" target="_blank">API Docs</a></li>
      <li><a href="/api/v1/monitor/dashboard" target="_blank">System Dashboard API</a></li>
      <li><a href="/api/v1/admin/stats" target="_blank">System Stats API</a></li>
      <li><a href="/api/v1/logs" target="_blank">Log Search API</a></li>
      <li><a href="/api/v1/config" target="_blank">Config API</a></li>
    </ul>
  </div>
  <div class="card">
    <h2>Health</h2>
    <p>Basic: <code>/health</code> | Detailed: <code>/health/detailed</code></p>
  </div>
  <div class="card">
    <h2>Notes</h2>
    <p>This is a minimal admin UI shell. Add frontend assets as needed.</p>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/health", response_class=HTMLResponse)
async def admin_ui_health():
    """Admin UI health page."""
    return HTMLResponse(content="<p>Admin UI is running.</p>")

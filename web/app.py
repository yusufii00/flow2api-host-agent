"""Flow2API Host Agent - Web UI"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))
from core import load_config, read_json, health_report  # noqa: E402

CFG_PATH = str(BASE / 'agent.toml')
VENV_PYTHON = str(BASE / '.venv' / 'bin' / 'python')
DEFAULT_NOVNC = 'http://localhost:6080/vnc.html?autoconnect=true&resize=scale&quality=6'
app = FastAPI(title='Flow2API Host Agent')
templates = Jinja2Templates(directory=str(BASE / 'web' / 'templates'))


def _run_cmd(cmd: str) -> dict:
    python_bin = VENV_PYTHON if Path(VENV_PYTHON).exists() else sys.executable
    result = subprocess.run(
        [python_bin, str(BASE / 'scripts' / 'agent.py'), '--config', CFG_PATH, cmd],
        capture_output=True, text=True
    )
    stdout = (result.stdout or '').strip().splitlines()
    candidate = stdout[-1] if stdout else ''
    try:
        return json.loads(candidate)
    except Exception:
        return {
            'ok': False,
            'error': (result.stderr[:800] if result.stderr else 'no output'),
            'raw_stdout': result.stdout[:1500] if result.stdout else ''
        }


def _write_config(cfg: dict) -> None:
    lines = []
    for k, v in cfg.items():
        if isinstance(v, bool):
            lines.append(f'{k} = {str(v).lower()}')
        elif isinstance(v, (int, float)):
            lines.append(f'{k} = {v}')
        else:
            escaped = str(v).replace('"', '\\"')
            lines.append(f'{k} = "{escaped}"')
    Path(CFG_PATH).write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _validate_config_input(flow2api_url: str, connection_token: str, novnc_url: str) -> list[str]:
    errors: list[str] = []
    token = (connection_token or '').strip()
    if token.startswith('http://') or token.startswith('https://'):
        errors.append('Connection Token 必须填写 token 字符串，不能填写 URL。')
    if '/api/plugin/update-token' in token:
        errors.append('Connection Token 不能填写 /api/plugin/update-token 接口地址。')

    flow = (flow2api_url or '').strip()
    if flow:
        parsed = urlparse(flow)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            errors.append('Flow2API 地址格式不正确，需要是 http(s)://host:port 形式。')

    novnc = (novnc_url or '').strip()
    if novnc.startswith('http://localhost') or novnc.startswith('https://localhost'):
        errors.append('noVNC 地址不要填写 localhost；如果从外部设备访问，请填写服务器实际可访问地址。')

    return errors


def _get_context():
    cfg = load_config(CFG_PATH)
    cfg.setdefault('novnc_url', DEFAULT_NOVNC)
    state = read_json(cfg['state_file']) or {}
    status = _run_cmd('status')
    health = health_report(cfg, status=status, state=state)
    last_update_display = '—'
    if state.get('time'):
        try:
            last_update_display = datetime.fromtimestamp(state['time']).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    return cfg, state, status, health, last_update_display


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    cfg, state, status, health, last_update_display = _get_context()
    return templates.TemplateResponse('index.html', {
        'request': request,
        'cfg': cfg,
        'state': state,
        'status': status,
        'health': health,
        'last_update_display': last_update_display,
    })


@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request):
    cfg, _state, status, health, _ = _get_context()
    novnc_url = cfg.get('novnc_url', DEFAULT_NOVNC)
    return templates.TemplateResponse('login.html', {
        'request': request,
        'cfg': cfg,
        'status': status,
        'health': health,
        'novnc_url': novnc_url,
    })


@app.get('/api/status')
def api_status():
    return _run_cmd('status')


@app.get('/api/health')
def api_health():
    cfg = load_config(CFG_PATH)
    state = read_json(cfg['state_file']) or {}
    status = _run_cmd('status')
    return health_report(cfg, status=status, state=state)


@app.post('/action/launch-browser')
def action_launch_browser():
    _run_cmd('login')
    return RedirectResponse('/login', status_code=303)


@app.post('/action/run-once')
def action_run_once():
    result = _run_cmd('run-once')
    flag = '1' if result.get('success', False) else '0'
    return RedirectResponse(f'/?refreshed={flag}', status_code=303)


@app.post('/action/save')
def action_save(
    flow2api_url: str = Form(...),
    connection_token: str = Form(...),
    chrome_profile_dir: str = Form(...),
    remote_debugging_port: int = Form(...),
    display: str = Form(...),
    refresh_interval_minutes: int = Form(...),
    novnc_url: str = Form(''),
):
    errors = _validate_config_input(flow2api_url, connection_token, novnc_url)
    if errors:
        return RedirectResponse('/?saved=0&reason=config', status_code=303)

    cfg = load_config(CFG_PATH)
    cfg.update({
        'flow2api_url': flow2api_url.strip(),
        'connection_token': connection_token.strip(),
        'chrome_profile_dir': chrome_profile_dir.strip(),
        'remote_debugging_port': int(remote_debugging_port),
        'display': display.strip(),
        'refresh_interval_minutes': int(refresh_interval_minutes),
        'novnc_url': (novnc_url or DEFAULT_NOVNC).strip(),
    })
    _write_config(cfg)
    return RedirectResponse('/?saved=1', status_code=303)

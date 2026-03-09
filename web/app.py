"""Flow2API Host Agent - Web UI"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))
from core import load_config, read_json  # noqa: E402

CFG_PATH = str(BASE / 'agent.toml')
VENV_PYTHON = str(BASE / '.venv' / 'bin' / 'python')
DEFAULT_NOVNC = 'http://localhost:6080/vnc.html?autoconnect=true&resize=scale&quality=6'
DISPLAY_TZ = ZoneInfo('Asia/Shanghai')
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
            'error': (result.stderr[:500] if result.stderr else 'no output'),
            'raw_stdout': result.stdout[:1000] if result.stdout else ''
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


def _restart_daemon() -> None:
    subprocess.run(['systemctl', 'restart', 'flow2api-host-agent.service'], capture_output=True, text=True)


def _fmt_local(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=DISPLAY_TZ).strftime('%Y-%m-%d %H:%M:%S') + ' (UTC+8)'


def _get_context():
    cfg = load_config(CFG_PATH)
    cfg.setdefault('novnc_url', DEFAULT_NOVNC)
    state = read_json(cfg['state_file']) or {}
    status = _run_cmd('status')
    last_update_display = '—'
    next_refresh_display = '—'
    next_refresh_ts = None
    if state.get('time'):
        try:
            last_update_display = _fmt_local(int(state['time']))
            next_ts = int(state['time']) + int(cfg.get('refresh_interval_minutes', 30)) * 60
            next_refresh_ts = next_ts
            next_refresh_display = _fmt_local(next_ts)
        except Exception:
            pass
    return cfg, state, status, last_update_display, next_refresh_display, next_refresh_ts


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    cfg, state, status, last_update_display, next_refresh_display, next_refresh_ts = _get_context()
    return templates.TemplateResponse('index.html', {
        'request': request,
        'cfg': cfg,
        'state': state,
        'status': status,
        'last_update_display': last_update_display,
        'next_refresh_display': next_refresh_display,
        'next_refresh_ts': next_refresh_ts,
    })


@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request):
    cfg, _state, status, _, _, _ = _get_context()
    novnc_url = cfg.get('novnc_url', DEFAULT_NOVNC)
    health = _run_cmd('health')
    return templates.TemplateResponse('login.html', {
        'request': request,
        'cfg': cfg,
        'status': status,
        'novnc_url': novnc_url,
        'health': health,
    })


@app.get('/api/status')
def api_status():
    return _run_cmd('status')


def _restart_browser() -> None:
    subprocess.run(['systemctl', 'restart', 'flow2api-host-agent-browser.service'], capture_output=True, text=True)


@app.post('/action/launch-browser')
def action_launch_browser():
    _restart_browser()
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
    cfg = load_config(CFG_PATH)
    cfg.update({
        'flow2api_url': flow2api_url,
        'connection_token': connection_token,
        'chrome_profile_dir': chrome_profile_dir,
        'remote_debugging_port': int(remote_debugging_port),
        'display': display,
        'refresh_interval_minutes': int(refresh_interval_minutes),
        'novnc_url': novnc_url or DEFAULT_NOVNC,
    })
    _write_config(cfg)
    _restart_daemon()
    return RedirectResponse('/?saved=1', status_code=303)


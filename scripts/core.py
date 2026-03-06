import json
import os
import subprocess
import time
from pathlib import Path

try:
    import tomllib  # py311+
except Exception:
    import tomli as tomllib

import requests
from playwright.sync_api import sync_playwright


def load_config(path: str):
    with open(path, 'rb') as f:
        return tomllib.load(f)


def ensure_parent(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def save_json(path: str, data: dict):
    ensure_parent(path)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_json(path: str):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text('utf-8'))


def chrome_running(port: int) -> bool:
    try:
        r = requests.get(f'http://127.0.0.1:{port}/json/version', timeout=3)
        return r.ok
    except Exception:
        return False


def start_chrome(cfg: dict):
    Path(cfg['chrome_profile_dir']).mkdir(parents=True, exist_ok=True)
    ensure_parent(cfg['log_file'])
    log = open(cfg['log_file'], 'a', encoding='utf-8')
    env = os.environ.copy()
    env['DISPLAY'] = cfg['display']
    cmd = [
        cfg['chrome_binary'],
        f"--remote-debugging-port={cfg['remote_debugging_port']}",
        f"--user-data-dir={cfg['chrome_profile_dir']}",
        '--no-first-run', '--no-default-browser-check', '--no-sandbox',
        '--disable-dev-shm-usage', '--disable-gpu', '--disable-software-rasterizer',
        '--disable-background-networking', '--disable-default-apps',
        '--disable-extensions', '--disable-sync', '--disable-translate',
        '--metrics-recording-only', '--mute-audio', '--no-first-run',
        '--safebrowsing-disable-auto-update',
        cfg['start_url'],
    ]
    proc = subprocess.Popen(cmd, stdout=log, stderr=log, env=env)
    return proc.pid


def attach_and_get_st(cfg: dict):
    endpoint = f"http://127.0.0.1:{cfg['remote_debugging_port']}"
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        cookies = []
        for ctx in browser.contexts:
            try:
                cookies.extend(ctx.cookies())
            except Exception:
                pass
        st = None
        for c in cookies:
            if c.get('name') == '__Secure-next-auth.session-token':
                st = c.get('value')
                break
        browser.close()
        return st, cookies


def update_flow2api(cfg: dict, session_token: str):
    r = requests.post(
        cfg['flow2api_url'].rstrip('/') + '/api/plugin/update-token',
        headers={
            'Authorization': f"Bearer {cfg['connection_token']}",
            'Content-Type': 'application/json',
        },
        json={'session_token': session_token},
        timeout=60,
    )
    return r.status_code, r.text


def run_once(cfg: dict):
    started = time.time()
    st, cookies = attach_and_get_st(cfg)
    result = {
        'time': int(started),
        'cookie_count': len(cookies),
        'has_session_token': bool(st),
        'remote_debugging_port': cfg['remote_debugging_port'],
    }
    if st:
        status, body = update_flow2api(cfg, st)
        result['update_status'] = status
        result['update_body'] = body[:1000]
        result['success'] = status == 200
    else:
        result['success'] = False
        result['error'] = 'No session token found'
    save_json(cfg['state_file'], result)
    return result

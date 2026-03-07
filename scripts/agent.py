#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import load_config, start_chrome, chrome_running, run_once, read_json, health_report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('login')
    sub.add_parser('run-once')
    sub.add_parser('status')
    sub.add_parser('health')
    sub.add_parser('daemon')
    args = ap.parse_args()

    cfg = load_config(args.config)

    if args.cmd == 'login':
        pid = start_chrome(cfg)
        print(json.dumps({'started': True, 'pid': pid, 'debug_port': cfg['remote_debugging_port'], 'start_url': cfg['start_url']}, ensure_ascii=False))
        return

    if args.cmd == 'run-once':
        print(json.dumps(run_once(cfg), ensure_ascii=False))
        return

    if args.cmd == 'status':
        state = read_json(cfg['state_file'])
        print(json.dumps({
            'chrome_running': chrome_running(cfg['remote_debugging_port']),
            'debug_port': cfg['remote_debugging_port'],
            'profile_dir': cfg['chrome_profile_dir'],
            'last_state': state,
        }, ensure_ascii=False))
        return

    if args.cmd == 'health':
        state = read_json(cfg['state_file']) or {}
        status = {
            'chrome_running': chrome_running(cfg['remote_debugging_port']),
            'debug_port': cfg['remote_debugging_port'],
            'profile_dir': cfg['chrome_profile_dir'],
            'last_state': state,
        }
        print(json.dumps(health_report(cfg, status=status, state=state), ensure_ascii=False))
        return

    if args.cmd == 'daemon':
        interval_sec = max(300, int(cfg.get('refresh_interval_minutes', 30)) * 60)
        print(json.dumps({'daemon_started': True, 'interval_sec': interval_sec, 'interval_min': interval_sec // 60}), flush=True)
        while True:
            try:
                if not chrome_running(cfg['remote_debugging_port']):
                    print(json.dumps({'event': 'chrome_not_running', 'action': 'starting_chrome'}), flush=True)
                    start_chrome(cfg)
                    time.sleep(5)
                result = run_once(cfg)
                result['next_run_in_sec'] = interval_sec
                print(json.dumps(result, ensure_ascii=False), flush=True)
            except Exception as e:
                err = {'success': False, 'error': repr(e), 'time': int(time.time())}
                Path(cfg['state_file']).write_text(json.dumps(err, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                print(json.dumps(err, ensure_ascii=False), flush=True)
            time.sleep(interval_sec)


if __name__ == '__main__':
    main()

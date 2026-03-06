# Deployment (Draft)

## 1. Install dependencies

```bash
cd extras/flow2api-host-agent
python3 -m pip install -r requirements.txt
```

> Note: Python 3.10 needs `tomli` from `requirements.txt`; Python 3.11+ can use built-in `tomllib`.

## 2. Prepare config

```bash
cp agent.example.toml agent.toml
# edit connection_token / flow2api_url / profile path / refresh interval
```

## 3. First login

```bash
python3 scripts/agent.py --config agent.toml login
```

Then open your X11/noVNC desktop and log into Google Labs Flow.

## 4. Test once

```bash
python3 scripts/agent.py --config agent.toml run-once
```

## 5. Start Web UI

```bash
uvicorn web.app:app --host 0.0.0.0 --port 38110 --app-dir .
```

## 6. Daemon mode

```bash
python3 scripts/agent.py --config agent.toml daemon
```

## 7. systemd

Copy templates from `systemd/` and adjust paths to your deployment directory.

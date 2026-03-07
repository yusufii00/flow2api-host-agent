# Flow2API Host Agent

> Flow2API 的 Linux 宿主机伴生服务：浏览器登录、Token 自动刷新、Web UI 与 systemd 常驻支持。

一个运行在 **Linux 宿主机** 上的独立 companion service，用来把 Google Labs / Flow 的登录态稳定同步回 **已有的 Flow2API** 实例。

适合这些场景：
- 你已经部署好了 `flow2api`
- 你不想依赖 Chrome 扩展
- 你希望在服务器上自动刷新 token
- 你需要 Web UI / systemd / 定时维护能力

---

## 界面预览

### 仪表盘

![Dashboard](assets/dashboard.png)

### 登录向导

![Login Guide](assets/login-guide.png)

---

## 成熟版改进点

这个版本额外做了几件对生产更友好的事：

- **统一 Python 运行时**：Web UI / daemon / one-shot 命令全部走项目内 `.venv`
- **新增健康检查**：提供 `/api/health`，把 Chrome、最近刷新、Connection Token 配置分层展示
- **配置防呆**：阻止把 `Connection Token` 错填成 URL
- **安装更稳**：`install-systemd.sh` 自动创建 `.venv` 并为 systemd 固定解释器路径
- **日志更清晰**：Chrome 日志和 daemon 日志拆分

---

## 3 分钟上手

### 1. 克隆仓库

```bash
git clone https://github.com/muyouzhi6/flow2api-host-agent.git
cd flow2api-host-agent
```

### 2. 安装 systemd 服务

```bash
bash install-systemd.sh
```

### 3. 配置 `agent.toml`

```bash
cp agent.example.toml agent.toml
nano agent.toml
```

最关键的几项：

```toml
flow2api_url = "http://127.0.0.1:38000"
connection_token = "从 Flow2API 管理后台复制的 token 字符串"
novnc_url = "http://你的服务器IP:6080/vnc.html?autoconnect=true&resize=scale&quality=6"
listen_host = "0.0.0.0"
listen_port = 38110
```

### 4. 打开登录向导

```bash
systemctl start flow2api-host-agent-browser
systemctl start flow2api-host-agent-ui
```

然后访问：

```text
http://你的服务器IP:38110/login
```

### 5. 登录 Google Labs 并手动刷新一次

- 在登录向导页面中完成 Google 登录
- 回到仪表盘点击 **立即刷新 Token**
- 看到成功即可

### 6. 启动自动刷新 daemon

```bash
systemctl start flow2api-host-agent
```

---

## 它和 Flow2API 的关系

- **Flow2API**：主体服务，负责模型路由、token 管理、API 能力
- **Flow2API Host Agent**：宿主机侧辅助服务，负责维护浏览器登录态并把最新 session token 推回 Flow2API

也就是说：

> 如果你已经有 Flow2API，这个项目安装好以后就能直接配合使用。

它不是 Flow2API 的替代品，而是外挂式 companion service。

---

## 核心能力

- 维护 Google Labs 登录浏览器 profile
- 通过 Chrome DevTools Protocol 读取 `__Secure-next-auth.session-token`
- 调用 Flow2API 的 `/api/plugin/update-token` 自动更新 token
- 提供 Web UI（仪表盘 / 登录向导 / 配置 / 帮助）
- 提供 `/api/status` 与 `/api/health`
- 支持 systemd 常驻
- 支持可选的每日维护性重启 timer

---

## Connection Token 怎么获取？

打开你的 Flow2API 管理后台：

1. 登录管理员账号
2. 进入 **设置**
3. 找到 **插件连接配置**
4. 复制 **连接 Token**

如果为空，就先生成一个再保存。

它的作用是：

> Host Agent 每次把 session token 推送回 Flow2API 时，Flow2API 用它验证“这个请求是不是你授权的来源”。

### 重要：这里填的是 token，不是 URL

**正确：**

```text
abc123xyz
```

**错误：**

```text
http://127.0.0.1:38000/api/plugin/update-token
```

---

## Web UI 页面说明

- **仪表盘**：看最近一次刷新结果和分层状态
- **登录向导**：首次使用 / 登录失效时用
- **配置**：修改 Flow2API 地址、Connection Token、noVNC 地址等
- **帮助 / 原理 / 稳定性**：解释它怎么工作、会不会越跑越重、为什么建议维护性重启

---

## API

### `GET /api/status`

返回当前 Chrome/CDP 状态和最近一次状态文件。

### `GET /api/health`

返回更适合排错的分层健康信息：

- Chrome / CDP 是否正常
- 最近一次刷新是否成功
- Connection Token 配置是否可疑
- Chrome binary 是否存在
- 当前运行时 Python 是哪个

---

## 可选：每日维护性重启

如果你希望进一步降低 Chrome 长时间运行的累积状态问题，可以开启：

```bash
systemctl enable --now flow2api-host-agent-daily-restart.timer
```

默认计划时间：

- **每天 04:30 UTC**

它会重启：
- browser
- daemon
- ui

这是一个偏稳妥的长期运行策略。

---

## 注意事项

### 不要把 noVNC 地址写成 localhost

如果你是用手机或另一台设备访问登录页，`novnc_url` 不能写成：

```toml
novnc_url = "http://localhost:6080/..."
```

因为这会让浏览器去访问**你自己设备的 localhost**，不是服务器。

正确方式应该是：

```toml
novnc_url = "http://你的服务器IP:6080/vnc.html?autoconnect=true&resize=scale&quality=6"
```

### 主要资源开销来自 Chrome

- Python daemon：轻
- Web UI：轻
- 大头是 Chrome / renderer / GPU 相关进程

所以如果长期运行，建议保留每日维护性重启方案。

---

## 常见问题

### 1）页面显示 Chrome 未运行，但 daemon 明明在跑

旧版本可能出现这个问题，原因通常是：

- Web UI 用了系统 `python3` 调子命令
- daemon 却跑在项目自己的虚拟环境里
- 导致 UI 自检失败，但底层服务其实是好的

新版本已经统一为项目内 `.venv` 运行时，避免这类假失败。

### 2）为什么会报 `Invalid connection token`

通常是因为你把 `Connection Token` 填成了 URL，而不是 token 字符串。

### 3）怎么快速自检

```bash
curl http://127.0.0.1:38110/api/health
```

---

## 适用前提

你需要先有：

1. **一台 Linux 服务器**
2. **已部署好的 Flow2API**
3. **Google Chrome / Chromium**
4. **Xvfb / noVNC**（用于服务器上的浏览器登录）

---

## 目录结构

- `scripts/`：CLI 与核心逻辑
- `web/`：Web UI
- `systemd/`：systemd service / timer 模板
- `docs/`：设计与部署文档
- `install-systemd.sh`：一键安装脚本

---

## License

MIT

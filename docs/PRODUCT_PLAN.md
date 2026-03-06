# Flow2API Host Agent 产品化方案

## 目标

将当前已验证成功的 PoC（Linux 宿主机 Chrome + CDP + `/api/plugin/update-token`）产品化为：

1. **别人从仓库下载就能用**
2. **不依赖 Chrome 扩展**
3. **支持首次人工登录**
4. **支持可自定义刷新频率**
5. **提供可操作界面**
6. **可作为 Flow2API 的 companion service 独立运行**

---

## 推荐产品形态

不是把浏览器自动化强塞进 Docker 容器，而是新增一个 companion project：

- 目录：`extras/flow2api-host-agent/`
- 运行位置：Linux 宿主机
- 与 Flow2API 的交互方式：HTTP API（复用 `/api/plugin/update-token`）

---

## 模块划分

### 1. Agent Core
- `run-once`：抓一次 ST 并推送
- `daemon`：按周期自动刷新
- `login`：打开登录浏览器 profile
- `status`：查看当前 profile / Chrome / 调试口状态

### 2. Browser Runtime
- 常驻 Chrome（固定 profile）
- 固定 remote debugging 端口
- 支持 Xvfb / noVNC 登录
- profile 持久化目录可配置

### 3. Config
- `agent.toml` / `.env`
- Flow2API URL
- connection token
- debug port
- profile path
- refresh interval
- display
- headful/headless 模式

### 4. UI
两层界面：

#### A. Agent 自带轻量 Web UI（推荐）
- 登录状态
- 最近刷新时间
- 下次刷新时间
- 调试口状态
- 立即刷新按钮
- 打开登录入口按钮
- 配置编辑（频率/路径/端口）

#### B. Flow2API 后台集成卡片（后续）
- 在 `manage.html` 的“插件连接配置”旁边新增“Host-Agent 自动刷新”卡片
- 只展示状态，不承担复杂浏览器操作

---

## 推荐交付阶段

### Phase 1
- 独立 host-agent CLI
- 独立 Web UI
- systemd 模板
- 首次登录流程
- 自定义刷新频率

### Phase 2
- Flow2API 后台集成状态卡片
- 与 `/api/plugin/config` 联动
- 一键生成 agent 配置

### Phase 3
- 失败告警
- 邮件/Bark/Telegram 通知
- 多 profile / 多账号支持

---

## 为什么做独立子项目而不是直接塞进 src/

1. 当前 Flow2API 主体跑 Docker
2. 浏览器自动化适合宿主机
3. 别人 clone 后也容易理解部署边界
4. 便于将来单独发布/维护
5. 不破坏上游主服务结构

---

## 推荐目录结构

```text
extras/flow2api-host-agent/
  README.md
  agent.example.toml
  requirements.txt
  scripts/
    agent.py
    login.py
    run_once.py
    daemon.py
  systemd/
    flow2api-host-agent-browser.service
    flow2api-host-agent.service
    flow2api-host-agent.timer
  web/
    app.py
    templates/
    static/
  docs/
    ARCHITECTURE.md
    DEPLOYMENT.md
```

---

## 界面需求（第一版）

### 页面 1：Dashboard
- 当前状态：已登录 / 未登录
- Chrome 状态：运行中 / 未运行
- Debug Port：9223
- 最近刷新结果
- 最近 token 更新时间
- 手动刷新按钮
- 打开登录入口说明

### 页面 2：Settings
- Flow2API URL
- Connection Token
- Chrome Profile 路径
- Remote Debug Port
- 刷新频率（分钟，可自定义）
- 是否开机自启说明

### 页面 3：Logs
- 最近刷新记录
- 是否成功
- 返回邮箱
- 接口响应

---

## 频率策略

### 默认建议
- 默认刷新：30 分钟

### 可配置范围建议
- 最小：5 分钟
- 默认：30 分钟
- 常规：60 分钟
- 最大：720 分钟

### 说明
刷新太慢会错过 session 更新；刷新太快会增加 Google 风控与无效操作。

---

## 第一版验收标准

1. clone 仓库后能按 README 独立跑起 host-agent
2. 能打开登录入口并完成 Google Labs 登录
3. 能自动抓取 ST 并更新 Flow2API token
4. 刷新频率可自定义
5. Web UI 能查看状态并手动触发刷新
6. systemd 模板可直接部署

---

## 当前已验证成功的核心链路

- Linux Host Chrome ✅
- Xvfb ✅
- CDP attach ✅
- 读取 `__Secure-next-auth.session-token` ✅
- `/api/plugin/update-token` 更新 token ✅

所以产品化不是从零开始，而是在成功 PoC 基础上收敛工程结构。

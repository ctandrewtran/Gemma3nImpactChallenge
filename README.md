# Gemma3n Impact Challenge: Hyper-Local RAG System

## Welcome!

This project helps your community get fast, local answers from your town or county website. It is designed for easy setup by anyone with minimal IT experience.

All processing takes place and all data is stored locally. Only egress it to scrape local town/county website to build a search index. Gemma 3n is used to generate answers.

---

## Recommended System Requirements

- **Operating System:**
  - Windows 10/11 (64-bit)
  - Ubuntu Linux 20.04+ (64-bit)
  - macOS 12+ (Intel or Apple Silicon)
- **Processor:** Dual-core or better (Intel i3/i5/i7, AMD Ryzen, Apple M1/M2, etc.)
- **Memory (RAM):** 8 GB minimum (16 GB recommended for best performance)
- **Storage:** 30 GB free disk space
- **Internet:** Required for first-time setup (downloads software and models)
- **Admin Rights:** You may need to approve software installation (especially on Windows)

---

## How to Set Up (No Experience Needed!)

**⚠️ IMPORTANT:**
- **Windows:** Right-click PowerShell and choose **"Run as administrator"** before running the script below.
- **Linux/macOS:** If you see a permission error, add `sudo` before the command (e.g., `sudo curl -s ... | bash`).
- **Docker running in Windows** may require extra setup/help. See the [docker system requirements](https://docs.docker.com/desktop/setup/install/windows-install/?uuid=97079F61-2695-4294-A290-A2101AC32837#system-requirements)

**1. Open your computer's terminal:**
- On **Windows**: Search for "PowerShell" in the Start menu and open it.
- On **Linux/macOS**: Open the "Terminal" app.

**2. Copy and paste ONE of these commands and press Enter:**

### For Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.ps1 | iex
```

### For Linux/macOS (Bash)

```bash
curl -s https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.sh | bash
```

**That's it!**
- The script will check your system, install Docker and everything else needed, and start the app for you.
- If you are on Windows and don't have Docker Desktop, the script will tell you how to install it.

---

## Windows: How to Update WSL (Windows Subsystem for Linux)

If you are using Docker Desktop on Windows, it relies on WSL (Windows Subsystem for Linux) to run Linux containers. Sometimes, updating WSL can fix compatibility or startup issues with Docker.

**To update WSL:**

1. Open PowerShell as Administrator (right-click and choose "Run as administrator").
2. Type the following command and press Enter:

   ```powershell
   wsl --update
   ```

**What does this do?**
- This command updates the WSL kernel and related components to the latest version.
- It can help resolve issues where Docker Desktop or Linux containers are not starting or behaving unexpectedly.
- After updating, you may need to restart your computer or Docker Desktop.

For more information, see the [official Microsoft WSL documentation](https://learn.microsoft.com/en-us/windows/wsl/).

---

## What Happens Next?
- The app will open at: [http://localhost:8050](http://localhost:8050)
- You can use your web browser to access the admin panel and chat interface.
- All data stays on your computer—nothing is sent to the cloud.

---

## Troubleshooting & Tips
- If you see a message about "permissions" or "admin rights," right-click PowerShell or Terminal and choose "Run as administrator." On Linux/macOS, add `sudo` before the command if needed.
- If you have questions, check the [official Docker documentation](https://docs.docker.com/get-docker/) or ask a local IT helper.
- You can always review the install scripts before running them by opening them in Notepad or any text editor.

---

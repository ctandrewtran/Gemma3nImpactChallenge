# Gemma3n Impact Challenge: Hyper-Local RAG System

## Welcome!

This project helps your community get fast, local answers from your town or county website. It is designed for easy setup by anyone—even if you have very little IT experience.

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

## Important Notes
- **No technical experience required!**
- The script will install everything for you.
- No `.bat` file is needed—use the PowerShell or Bash script above.
- The app runs on your computer, not in the cloud.

---

## Example: Run Bash Script from URL

```bash
curl -s https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.sh | bash
```

[More info](https://www.atlantic.net/vps-hosting/how-to-execute-a-bash-script-directly-from-a-url/) [[1]]

---

## Example: Run PowerShell Script from URL

```powershell
irm https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.ps1 | iex
```

---

## References
- [How to Execute a Bash Script Directly from a URL](https://www.atlantic.net/vps-hosting/how-to-execute-a-bash-script-directly-from-a-url/)
- [Microsoft Docs: PowerShell in Docker](https://learn.microsoft.com/en-ca/powershell/scripting/install/powershell-in-docker?view=powershell-7.4)

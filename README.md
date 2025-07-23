# Gemma3n Impact Challenge: Hyper-Local RAG System

## Quick Start for Rural IT Admins

This project is designed to be easy to install and run on Windows, Linux, or macOS. All you need is to run a single script—everything else (including Docker and Docker Compose) will be installed for you if needed.

---

## 1. Prerequisites

- **Windows:** No prerequisites. The script will prompt you to install Docker Desktop if it's not found.
- **Linux/macOS:** No prerequisites. The script will install Docker and Docker Compose if not found.

---

## 2. One-Click Startup (Recommended)

### Windows (PowerShell)

**Option 1: Download and run the script**

1. Download the installer script:
   ```powershell
   curl -o install.ps1 https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.ps1
   ```
2. Run the script in PowerShell:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\install.ps1
   ```

**Option 2: Run directly from URL (if allowed)**

> Note: PowerShell does not natively support piping remote scripts to PowerShell as simply as Bash, but you can use `iex` (Invoke-Expression) with `irm` (Invoke-RestMethod):

```powershell
irm https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.ps1 | iex
```

---

### Linux/macOS (Bash)

**Option 1: Download and run the script**

1. Download the installer script:
   ```bash
   curl -O https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.sh
   chmod +x install.sh
   ./install.sh
   ```

**Option 2: Run directly from URL**

```bash
curl -s https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.sh | bash
```

---

## 3. After Installation

- The app will be available at: [http://localhost:8050](http://localhost:8050)
- All services (Milvus, Ollama, and the app) will run in Docker containers.

---

## 4. Security Note

> **Always review scripts before running them from the internet.**
> You can open `install.sh` or `install.ps1` in a text editor to inspect the contents before executing.

---

## 5. Troubleshooting

- Make sure Docker and Docker Compose are running (the script will install them if missing).
- If you see permission errors, try running your terminal as Administrator (Windows) or with `sudo` (Linux/macOS).
- For more help, see the [official Docker documentation](https://docs.docker.com/get-docker/).

---

## 6. Notes

- There is no `.bat` script provided. Use `install.ps1` for Windows and `install.sh` for Linux/macOS.
- The installer will build the app Docker image locally and start all services.
- Minimal setup required—just run the script!

---

## Example: Run Bash Script from URL

You can run a bash script directly from a URL using:

```bash
curl -s https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.sh | bash
```

[More info](https://www.atlantic.net/vps-hosting/how-to-execute-a-bash-script-directly-from-a-url/) [[1]]

---

## Example: Run PowerShell Script from URL

You can run a PowerShell script directly from a URL using:

```powershell
irm https://raw.githubusercontent.com/ctandrewtran/Gemma3nImpactChallenge/main/install.ps1 | iex
```

---

## References
- [How to Execute a Bash Script Directly from a URL](https://www.atlantic.net/vps-hosting/how-to-execute-a-bash-script-directly-from-a-url/)
- [Microsoft Docs: PowerShell in Docker](https://learn.microsoft.com/en-ca/powershell/scripting/install/powershell-in-docker?view=powershell-7.4)

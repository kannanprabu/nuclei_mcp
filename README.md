# nuclei_mcp

A standalone Python MCP (Model Context Protocol) server that wraps [Nuclei](https://github.com/projectdiscovery/nuclei), enabling Claude Desktop to run real vulnerability scans through natural language.

> **Presented at BSides San Diego 2026**
> *"Build Your First MCP Server: Automate Security Scans with AI"*
> Kannan Prabu Ramamoorthy & Swarup Natukula

---

## Demo

Type this in Claude Desktop:

```
Run a nuclei scan on https://scanme.sh
```

**Expected output — 19 findings in ~7 seconds:**

```
[nuclei] 19 finding(s) on https://scanme.sh:
[INFO] OpenSSH Service - Detect | matched: scanme.sh:22 | template: openssh-detect
[INFO] SSH Server Software Enumeration | matched: scanme.sh:22 | template: ssh-server-enumeration
[INFO] SSH Password-based Authentication | matched: scanme.sh:22 | template: ssh-password-auth
[INFO] SSH SHA-1 HMAC Algorithms Enabled | matched: scanme.sh:22 | template: ssh-sha1-hmac-algo
[INFO] Deprecated TLS Detection | matched: scanme.sh:443 | template: deprecated-tls
[LOW]  Weak Cipher Suites Detection | matched: scanme.sh:443 | template: weak-cipher-suites
[LOW]  Self Signed SSL Certificate | matched: scanme.sh:443 | template: self-signed-ssl
[INFO] Mismatched SSL Certificate | matched: scanme.sh:443 | template: mismatched-ssl-certificate
[INFO] TLS Version - Detect | matched: scanme.sh:443 | template: tls-version
[INFO] CAA Record | matched: scanme.sh | template: caa-fingerprint
[INFO] NS Record Detection | matched: scanme.sh | template: nameserver-fingerprint
[INFO] AAAA Record - IPv6 Detection | matched: scanme.sh | template: aaaa-fingerprint
...
```

---

## MCP Tools

| Tool | Description | Speed |
|------|-------------|-------|
| `nuclei_scan` | Full scan with severity + template tag filters | ~7s (fast tags) |
| `nuclei_basic_scan` | Quick scan, fast defaults (ssl,ssh,dns) | ~7s |
| `nuclei_list_templates` | Browse templates by tag | instant |

---

## Requirements

- macOS (Apple Silicon M1/M2/M3/M4) — tested on M4 Pro, macOS Tahoe
- [Claude Desktop](https://claude.ai/download)
- Python 3.8+
- curl (pre-installed on macOS)

---

## Installation

### Option A — Automated (recommended)

```bash
git clone https://github.com/kannanprabu/nuclei_mcp.git
cd nuclei_mcp
chmod +x setup.sh
./setup.sh
```

The script will:
1. Install Nuclei binary (official arm64 binary — NOT brew)
2. Create Python venv and install MCP library
3. Print your exact Claude Desktop config to copy-paste

### Option B — Manual Step by Step

#### Step 1 — Install Nuclei

> ⚠️ **Do NOT use `brew install nuclei`** — the Homebrew bottle crashes on Apple Silicon with a SIGSEGV/cgo bug. Use the official binary:

```bash
# Download official arm64 binary
curl -L https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_macOS_arm64.zip -o /tmp/nuclei.zip

# Install
unzip /tmp/nuclei.zip -d /tmp/nuclei-bin/
chmod +x /tmp/nuclei-bin/nuclei
sudo mv /tmp/nuclei-bin/nuclei /usr/local/bin/nuclei

# Fix Gatekeeper if needed
xattr -d com.apple.quarantine /usr/local/bin/nuclei

# Verify
nuclei -version

# Update to latest + download templates
sudo nuclei -update
nuclei -update-templates
```

#### Step 2 — Clone repo and set up Python

```bash
git clone https://github.com/kannanprabu/nuclei_mcp.git
cd nuclei_mcp

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 3 — Get your exact Python path

```bash
source venv/bin/activate
which python3
# Example: /Users/yourname/nuclei_mcp/venv/bin/python3
```

#### Step 4 — Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nuclei-scanner": {
      "command": "/Users/yourname/nuclei_mcp/venv/bin/python3",
      "args": ["/Users/yourname/nuclei_mcp/nuclei-server.py"]
    }
  }
}
```

Replace `/Users/yourname` with your actual path from Step 3.

#### Step 5 — Restart Claude Desktop

```bash
pkill -x "Claude"
open -a Claude
```

#### Step 6 — Test it

In Claude Desktop, type:

```
Run a nuclei scan on https://scanme.sh
```

You should see 19 findings in ~7 seconds.

---

## Demo Prompts

```
# Quick scan
Run a nuclei basic scan on https://scanme.sh

# Scan with all severities
Run a nuclei scan on https://scanme.sh

# Target specific vulnerability classes
Run a nuclei scan on https://scanme.sh with templates ssl,ssh,dns

# Browse templates
List nuclei templates for tag "ssh"
List nuclei templates for tag "cve"

# Scan your own authorized target
Run a nuclei scan on https://yourauthorizedtarget.com
```

---

## Troubleshooting

### `SIGSEGV: segmentation violation` when running nuclei

This is the `go-m1cpu` cgo bug in Homebrew's nuclei bottle. Use the official binary from Step 1.

### `ModuleNotFoundError: No module named 'mcp'`

You're using system Python instead of the venv:

```bash
source venv/bin/activate
pip install -r requirements.txt
# Make sure config uses venv python path
```

### Tools don't appear in Claude Desktop

- Validate your JSON (no trailing commas)
- Confirm python path in config matches `which python3` inside the venv
- Fully quit Claude Desktop with `Cmd+Q`, then reopen
- Check logs: `~/Library/Logs/Claude/`

### Scan times out

The default `ssl,ssh,dns` tags finish in ~7 seconds. If you override with broader tags like `misconfig` or remove the tag filter, scans can take 3-4 minutes and will exceed Claude Desktop's MCP timeout. Stick to the fast tag set for demos.

### No findings returned

```bash
# Verify nuclei works standalone
nuclei -target https://scanme.sh -tags ssl,ssh,dns -no-color
# Should return 19 findings
```

---

## Related

- [BsidesMCPDemo](https://github.com/kannanprabu/BsidesMCPDemo) — main workshop repo with 7 pentest tools
- [Nuclei](https://github.com/projectdiscovery/nuclei) — ProjectDiscovery's vulnerability scanner
- [MCP Protocol](https://modelcontextprotocol.io) — Model Context Protocol docs
- [scanme.sh](https://scanme.sh) — Official ProjectDiscovery scan-me target

---

## License

MIT

---

*Tested on macOS Tahoe, Apple Silicon M4 Pro, March 2026.*

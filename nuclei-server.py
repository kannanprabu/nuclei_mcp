#!/usr/bin/env python3
"""
nuclei_mcp - Standalone Nuclei MCP Server
BSides San Diego 2026 - "Build Your First MCP Server: Automate Security Scans with AI"
Authors: Kannan Prabu Ramamoorthy & Swarup Natukula
Repo: https://github.com/kannanprabu/nuclei_mcp
"""

import subprocess
import json
import shutil
import tempfile
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nuclei-scanner")

NUCLEI_BIN = shutil.which("nuclei") or "/usr/local/bin/nuclei"

# Fast tags finish in ~7 seconds and produce real findings on most targets.
# ssl, ssh, dns cover TLS misconfigs, SSH fingerprinting, and DNS recon.
# Do NOT use -as (automatic scan) — it takes 3-4 mins and times out in Claude Desktop.
FAST_TAGS = "ssl,ssh,dns"


@mcp.tool()
def nuclei_scan(
    target: str,
    severity: str = "info,low,medium,high,critical",
    templates: str = "",
    timeout: int = 300
) -> str:
    """
    Run a Nuclei vulnerability scan against a target URL or IP.
    Detects CVEs, misconfigs, and exposures using community templates.
    Uses fast tags (ssl,ssh,dns) by default — completes in ~7 seconds.
    Pass templates= to override with specific tags (e.g. xss,sqli,http).

    Args:
        target: Target URL or IP (e.g. https://scanme.sh)
        severity: Comma-separated severity filter (info,low,medium,high,critical)
        templates: Optional template tags (e.g. xss,sqli,cve,http,network)
        timeout: Scan timeout in seconds (default 300)
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()

    cmd = [
        NUCLEI_BIN,
        "-target", target,
        "-severity", severity,
        "-timeout", str(timeout),
        "-json-export", tmp.name,
        "-no-color",
        "-silent",
        "-tags", templates if templates else FAST_TAGS,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout + 30
        )

        findings = []
        if os.path.exists(tmp.name) and os.path.getsize(tmp.name) > 0:
            with open(tmp.name, "r") as f:
                raw = f.read().strip()
            try:
                data = json.loads(raw)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    sev = item.get("info", {}).get("severity", "?").upper()
                    name = item.get("info", {}).get("name", "Unknown")
                    matched = item.get("matched-at", target)
                    tid = item.get("template-id", "?")
                    findings.append(
                        f"[{sev}] {name} | matched: {matched} | template: {tid}"
                    )
            except json.JSONDecodeError:
                for line in raw.splitlines():
                    try:
                        item = json.loads(line)
                        sev = item.get("info", {}).get("severity", "?").upper()
                        name = item.get("info", {}).get("name", "Unknown")
                        matched = item.get("matched-at", target)
                        tid = item.get("template-id", "?")
                        findings.append(
                            f"[{sev}] {name} | matched: {matched} | template: {tid}"
                        )
                    except json.JSONDecodeError:
                        if line.strip():
                            findings.append(line)

        if findings:
            return (
                f"[nuclei] {len(findings)} finding(s) on {target}:\n"
                + "\n".join(findings)
            )

        stderr_tail = result.stderr.strip().splitlines()
        debug = "\n".join(stderr_tail[-5:]) if stderr_tail else "none"
        return f"[nuclei] No findings for {target} (severity={severity})\n[debug] {debug}"

    except subprocess.TimeoutExpired:
        return f"[nuclei] Timed out after {timeout}s for {target}"
    except Exception as e:
        return f"[nuclei] Error: {str(e)}"
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


@mcp.tool()
def nuclei_basic_scan(target: str) -> str:
    """
    Quick Nuclei scan using fast tags (ssl,ssh,dns). Completes in ~7 seconds.
    Best for live demos and quick recon. Covers TLS, SSH, and DNS findings.

    Args:
        target: Target URL or IP (e.g. https://scanme.sh)
    """
    return nuclei_scan(target=target)


@mcp.tool()
def nuclei_list_templates(tag: str = "") -> str:
    """
    List available Nuclei templates, optionally filtered by tag.

    Args:
        tag: Optional tag to filter (e.g. xss, sqli, cve, ssh, ssl, wordpress)
    """
    cmd = [NUCLEI_BIN, "-tl"] + (["-tags", tag] if tag else [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        lines = result.stdout.strip().splitlines()
        if not lines:
            return "[nuclei] No templates found"
        summary = f"[nuclei] {len(lines)} templates"
        if tag:
            summary += f" matching tag '{tag}'"
        preview = "\n".join(lines[:50])
        suffix = f"\n... and {len(lines) - 50} more" if len(lines) > 50 else ""
        return f"{summary}:\n{preview}{suffix}"
    except Exception as e:
        return f"[nuclei] Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

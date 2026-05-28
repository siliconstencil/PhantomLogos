import os
import subprocess

from mcp.server.fastmcp import FastMCP

BROWSE_BIN = os.getenv("BROWSE_BIN", r"D:\Downloads\gstack-main\browse\dist\browse.exe")

mcp = FastMCP("browse")


def _run(*args: str, timeout: int = 30) -> str:
    r = subprocess.run(
        [BROWSE_BIN, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"browse exited with code {r.returncode}")
    return r.stdout.strip()


@mcp.tool(name="mcp_browse_goto", description="Navigate to a URL in the headless browser.")
def mcp_browse_goto(url: str) -> str:
    return _run("goto", url)


@mcp.tool(name="mcp_browse_click", description="Click an element matching the CSS selector.")
def mcp_browse_click(selector: str) -> str:
    return _run("click", selector)


@mcp.tool(name="mcp_browse_fill", description="Fill an input element with a value.")
def mcp_browse_fill(selector: str, value: str) -> str:
    return _run("fill", selector, value)


@mcp.tool(
    name="mcp_browse_text", description="Get visible text content. Omit selector for full page."
)
def mcp_browse_text(selector: str = "") -> str:
    args = ["text"] + ([selector] if selector else [])
    return _run(*args)


@mcp.tool(name="mcp_browse_html", description="Get raw HTML. Omit selector for full page.")
def mcp_browse_html(selector: str = "") -> str:
    args = ["html"] + ([selector] if selector else [])
    return _run(*args)


@mcp.tool(
    name="mcp_browse_js", description="Evaluate a JavaScript expression and return the result."
)
def mcp_browse_js(expr: str) -> str:
    return _run("js", expr)


@mcp.tool(
    name="mcp_browse_wait",
    description="Wait for a CSS selector, '--networkidle', or '--load'.",
)
def mcp_browse_wait(selector_or_mode: str) -> str:
    return _run("wait", selector_or_mode, timeout=60)


@mcp.tool(
    name="mcp_browse_press", description="Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape')."
)
def mcp_browse_press(key: str) -> str:
    return _run("press", key)


@mcp.tool(name="mcp_browse_url", description="Return the current page URL.")
def mcp_browse_url() -> str:
    return _run("url")


@mcp.tool(name="mcp_browse_links", description="Return all hyperlinks on the current page.")
def mcp_browse_links() -> str:
    return _run("links")


if __name__ == "__main__":
    mcp.run(transport="stdio")

"""System resource monitor. Run with: uv run python sysmon.py"""

import functools
import os
import select
import shutil
import subprocess
import sys
import termios
import time
import tty

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")

# Previous /proc/stat sample, so CPU usage is measured across refreshes instead of sleeping.
_prev_cpu_stats = None


def _read_cpu_stats():
    stats = {}
    with open("/proc/stat") as f:
        for line in f:
            if not line.startswith("cpu"):
                break
            parts = line.split()
            name = parts[0]
            vals = list(map(int, parts[1:]))
            total = sum(vals)
            idle = vals[3] + vals[4]
            key = "all" if name == "cpu" else int(name[3:])
            stats[key] = (total, idle)
    return stats


def cpu_usage(interval=0.5):
    global _prev_cpu_stats
    if _prev_cpu_stats is None:
        _prev_cpu_stats = _read_cpu_stats()
        time.sleep(interval)
    s1 = _prev_cpu_stats
    s2 = _read_cpu_stats()
    _prev_cpu_stats = s2

    per_core = {}
    for key in s2:
        if key not in s1:
            # CPU came online since the last sample.
            continue
        t1, i1 = s1[key]
        t2, i2 = s2[key]
        dt = t2 - t1
        di = i2 - i1
        pct = (1.0 - di / dt) * 100 if dt > 0 else 0.0
        per_core[key] = max(0.0, min(100.0, pct))

    overall = per_core.pop("all", 0.0)
    return overall, per_core


def mem_info():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            info[parts[0].rstrip(":")] = int(parts[1])
    total = info["MemTotal"] / 1024 / 1024
    available = info["MemAvailable"] / 1024 / 1024
    used = total - available
    swap_total = info.get("SwapTotal", 0) / 1024 / 1024
    swap_free = info.get("SwapFree", 0) / 1024 / 1024
    swap_used = swap_total - swap_free
    return total, used, swap_total, swap_used


def load_avg():
    with open("/proc/loadavg") as f:
        parts = f.read().split()
    return parts[0], parts[1], parts[2]


def uptime_info():
    with open("/proc/uptime") as f:
        secs = float(f.read().split()[0])
    days = int(secs // 86400)
    hours = int((secs % 86400) // 3600)
    mins = int((secs % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def disk_info():
    usage = shutil.disk_usage("/")
    total = usage.total / 1024**3
    used = usage.used / 1024**3
    return total, used


def net_info():
    with open("/proc/net/dev") as f:
        lines = f.readlines()
    skip_prefixes = ("lo", "veth", "br-", "docker", "virbr")
    interfaces = []
    for line in lines[2:]:
        parts = line.split()
        iface = parts[0].rstrip(":")
        if any(iface.startswith(p) for p in skip_prefixes):
            continue
        rx_bytes = int(parts[1])
        tx_bytes = int(parts[9])
        if rx_bytes == 0 and tx_bytes == 0:
            continue
        interfaces.append(
            {
                "name": iface,
                "rx": rx_bytes / 1024**3,
                "tx": tx_bytes / 1024**3,
            }
        )
    return interfaces


def _cmdline(pid):
    """Return cmdline argv list, or [] for kernel threads / dead processes."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            raw = f.read()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return []
    if not raw:
        return []
    return [p.decode("utf-8", errors="replace") for p in raw.split(b"\0") if p]


def _format_cmd(parts, comm, max_len=60):
    """btop-like compact cmdline: 'python script.py --flag', kernel threads in brackets."""
    if not parts:
        return f"[{comm}]"
    # Strip "uv run" / "uv run python" wrapper so the actual script is visible.
    if parts and os.path.basename(parts[0]) == "uv" and len(parts) > 1 and parts[1] == "run":
        parts = parts[2:]
    if not parts:
        return f"[{comm}]"
    out = [os.path.basename(parts[0])]
    for a in parts[1:]:
        # Show flags as-is, basename for paths to keep things short.
        if a.startswith("-") or "/" not in a:
            out.append(a)
        else:
            out.append(os.path.basename(a))
    cmd = " ".join(out)
    if len(cmd) > max_len:
        cmd = cmd[: max_len - 1] + "…"
    return cmd


def top_processes(n=5):
    procs = []
    try:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                with open(f"/proc/{pid}/stat") as f:
                    data = f.read()
                # comm may contain spaces and parens, so split around the outermost parens.
                close = data.rindex(")")
                comm = data[data.index("(") + 1 : close]
                rest = data[close + 2 :].split()  # rest[0] is field 3 (state)
                rss_mb = int(rest[21]) * PAGE_SIZE / 1024 / 1024
                procs.append({"pid": pid, "comm": comm, "rss_mb": rss_mb})
            except (FileNotFoundError, PermissionError, ProcessLookupError, IndexError, ValueError):
                continue
    except FileNotFoundError:
        return []
    procs.sort(key=lambda p: p["rss_mb"], reverse=True)
    top = procs[:n]
    for p in top:
        p["cmd"] = _format_cmd(_cmdline(p["pid"]), p["comm"])
    return top


def _num(s):
    """Parse an nvidia-smi numeric field; '[N/A]' / '[Not Supported]' become None."""
    try:
        return float(s)
    except ValueError:
        return None


@functools.cache
def _cuda_version():
    try:
        header = subprocess.check_output(["nvidia-smi"], stderr=subprocess.DEVNULL, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    for hline in header.split("\n"):
        if "CUDA Version:" in hline:
            return hline.split("CUDA Version:")[1].split()[0].strip()
    return ""


def gpu_info():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit,fan.speed,driver_version",
                "--format=csv,noheader,nounits",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    cuda_ver = _cuda_version()
    gpus = []
    for line in out.strip().split("\n"):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        gpus.append(
            {
                "name": parts[0],
                "util": _num(parts[1]),
                "mem_used": (_num(parts[2]) or 0.0) / 1024,
                "mem_total": (_num(parts[3]) or 0.0) / 1024,
                "temp": _num(parts[4]),
                "power": _num(parts[5]),
                "power_limit": _num(parts[6]),
                "fan": _num(parts[7]) if len(parts) > 7 else None,
                "driver": parts[8] if len(parts) > 8 else "",
                "cuda": cuda_ver,
            }
        )
    return gpus


def gpu_processes():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid,used_memory,name", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        procs = []
        for line in out.strip().split("\n"):
            if not line.strip():
                continue
            # maxsplit so a process name containing commas stays intact.
            parts = [p.strip() for p in line.split(",", 2)]
            if len(parts) < 3:
                continue
            pid = parts[0]
            cmd = _format_cmd(_cmdline(pid), os.path.basename(parts[2]))
            procs.append({"pid": pid, "mem_mb": parts[1], "cmd": cmd})
        return procs
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []


def fmt_gb(gb):
    if gb < 1:
        return f"{gb * 1024:.0f} MB"
    return f"{gb:.1f} GB"


def fmt_unit(v, unit):
    return f"{v:.0f}{unit}" if v is not None else "N/A"


def pct_color(pct):
    if pct >= 90:
        return "red bold"
    elif pct >= 70:
        return "yellow"
    elif pct >= 30:
        return "green"
    return "cyan"


def make_bar_text(label, pct, detail="", width=30):
    color = pct_color(pct)
    filled = int(width * pct / 100)
    bar_str = "█" * filled + "░" * (width - filled)
    text = Text()
    text.append(f" {label:>5}: ", style="bold")
    text.append("[", style="dim")
    text.append(bar_str[:filled], style=color)
    text.append(bar_str[filled:], style="dim")
    text.append("]", style="dim")
    text.append(f" {pct:5.1f}%", style=color)
    if detail:
        text.append(f"  {detail}", style="dim")
    return text


def make_core_text(core_id, pct, cw=2, bar_w=8):
    color = pct_color(pct)
    filled = int(bar_w * pct / 100)
    bar_str = "█" * filled + "░" * (bar_w - filled)
    text = Text()
    text.append(f"{core_id:>{cw}}", style="bold cyan")
    text.append(":", style="dim")
    text.append(bar_str[:filled], style=color)
    text.append(bar_str[filled:], style="dim")
    text.append(f"{pct:5.1f}%", style=color)
    return text


def build_display():
    """Build the full display as a rich Group for use with Live."""
    renderables = []

    # CPU — sample
    overall_cpu, per_core_cpu = cpu_usage()
    cores = len(per_core_cpu)
    load1, load5, load15 = load_avg()
    up = uptime_info()

    # Memory
    mem_total, mem_used, swap_total, swap_used = mem_info()
    mem_pct = mem_used / mem_total * 100

    # Disk
    disk_total, disk_used = disk_info()
    disk_pct = disk_used / disk_total * 100

    # === CPU Panel ===
    cpu_lines = []
    cpu_lines.append(
        Text.assemble(
            ("Load: ", "dim"),
            (f"{load1} {load5} {load15}", "bold"),
            ("  Up: ", "dim"),
            (up, "bold"),
        )
    )
    cpu_lines.append(make_bar_text("All", overall_cpu))
    cpu_group = Text("\n").join(cpu_lines)
    renderables.append(Panel(cpu_group, title=f"[bold]CPU [cyan]{cores}[/cyan] cores[/bold]", border_style="blue"))

    # Per-core grid
    core_ids = sorted(per_core_cpu.keys())
    cw = len(str(max(core_ids, default=0)))
    bar_w = 10 if cores <= 32 else 6 if cores <= 64 else 4
    core_renderables = []
    for c in core_ids:
        core_renderables.append(make_core_text(c, per_core_cpu[c], cw=cw, bar_w=bar_w))
    renderables.append(Columns(core_renderables, equal=True, expand=True))

    # === Memory Panel ===
    mem_lines = []
    mem_lines.append(make_bar_text("RAM", mem_pct, f"{mem_used:.1f} / {mem_total:.1f} GB"))
    if swap_total > 0:
        swap_pct = swap_used / swap_total * 100
        mem_lines.append(make_bar_text("Swap", swap_pct, f"{swap_used:.1f} / {swap_total:.1f} GB"))
    mem_lines.append(make_bar_text("Disk", disk_pct, f"{disk_used:.0f} / {disk_total:.0f} GB"))
    mem_group_text = Text("\n").join(mem_lines)
    renderables.append(Panel(mem_group_text, title="[bold]Memory & Disk[/bold]", border_style="green"))

    # === Network ===
    interfaces = net_info()
    if interfaces:
        net_table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
        net_table.add_column("Interface", style="cyan")
        net_table.add_column("RX", justify="right")
        net_table.add_column("TX", justify="right")
        for iface in interfaces:
            net_table.add_row(iface["name"], fmt_gb(iface["rx"]), fmt_gb(iface["tx"]))
        renderables.append(Panel(net_table, title="[bold]Network[/bold]", border_style="magenta"))

    # === GPU ===
    gpus = gpu_info()
    if gpus:
        for i, g in enumerate(gpus):
            gmem_pct = g["mem_used"] / g["mem_total"] * 100 if g["mem_total"] > 0 else 0.0
            gpu_lines = []

            info_parts = []
            if g.get("cuda"):
                info_parts.append(f"CUDA {g['cuda']}")
            if g.get("driver"):
                info_parts.append(f"Driver {g['driver']}")
            if info_parts:
                gpu_lines.append(Text.assemble(("  ", ""), (" | ".join(info_parts), "dim")))

            if g["util"] is not None:
                gpu_lines.append(make_bar_text("Use", g["util"]))
            gpu_lines.append(make_bar_text("VRAM", gmem_pct, f"{g['mem_used']:.1f} / {g['mem_total']:.1f} GB"))

            stats = Text.assemble(
                ("  Temp: ", "dim"),
                (fmt_unit(g["temp"], "C"), "bold"),
                ("  Power: ", "dim"),
                (fmt_unit(g["power"], "W"), "bold"),
                (f" / {fmt_unit(g['power_limit'], 'W')}", "dim"),
            )
            if g["fan"] is not None:
                stats.append("  Fan: ", style="dim")
                stats.append(fmt_unit(g["fan"], "%"), style="bold")
            gpu_lines.append(stats)

            gpu_group_text = Text("\n").join(gpu_lines)
            renderables.append(
                Panel(gpu_group_text, title=f"[bold]GPU {i}: [cyan]{g['name']}[/cyan][/bold]", border_style="yellow")
            )

        gprocs = gpu_processes()
        if gprocs:
            gp_table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
            gp_table.add_column("PID", justify="right", style="cyan")
            gp_table.add_column("VRAM (MB)", justify="right")
            gp_table.add_column("Command", overflow="ellipsis", no_wrap=True)
            for p in gprocs:
                gp_table.add_row(p["pid"], p["mem_mb"], p["cmd"])
            renderables.append(Panel(gp_table, title="[bold]GPU Processes[/bold]", border_style="yellow"))

    # === Top Processes ===
    top = top_processes(5)
    if top:
        proc_table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
        proc_table.add_column("PID", justify="right", style="cyan")
        proc_table.add_column("RAM (MB)", justify="right")
        proc_table.add_column("Command", overflow="ellipsis", no_wrap=True)
        for p in top:
            proc_table.add_row(p["pid"], f"{p['rss_mb']:.0f}", p["cmd"])
        renderables.append(Panel(proc_table, title="[bold]Top Processes by RAM[/bold]", border_style="red"))

    renderables.append(Text("Press q to quit", style="dim italic", justify="center"))

    return Group(*renderables)


def main():
    console = Console()

    fd = sys.stdin.fileno()
    try:
        old_settings = termios.tcgetattr(fd)
    except (termios.error, OSError):
        # stdin isn't a tty (piped/redirected) — fall back to plain sleep loop.
        old_settings = None

    try:
        if old_settings is not None:
            tty.setcbreak(fd)

        with Live(build_display(), console=console, auto_refresh=False, screen=True) as live:
            while True:
                if old_settings is not None:
                    rlist, _, _ = select.select([fd], [], [], 1.0)
                    # Read raw bytes: buffered sys.stdin can swallow multi-byte input (arrow keys) past select.
                    if rlist and b"q" in os.read(fd, 64).lower():
                        break
                else:
                    time.sleep(1)
                live.update(build_display(), refresh=True)
    finally:
        if old_settings is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

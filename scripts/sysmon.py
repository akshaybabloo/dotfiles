"""System resource monitor. Run with: uv run python sysmon.py

Click a process row (or select it and press Enter) to see its full command line.
"""

import functools
import os
import shlex
import shutil
import subprocess
import sys
import time

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual import events, work
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, LoadingIndicator, Static

PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
REFRESH_SECONDS = 1.0

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
    except FileNotFoundError, PermissionError, ProcessLookupError:
        return []
    if not raw:
        return []
    parts = [p.decode("utf-8", errors="replace") for p in raw.split(b"\0") if p]
    # Some programs (Electron, Chromium, setproctitle users) overwrite argv with one space-joined
    # string, so treat a lone argument containing spaces as the whole command line.
    if len(parts) == 1 and " " in parts[0]:
        parts = parts[0].split()
    return parts


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


def _full_cmd(parts, comm):
    """Full, shell-quoted command line suitable for copy/paste."""
    return shlex.join(parts) if parts else f"[{comm}]"


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
            except FileNotFoundError, PermissionError, ProcessLookupError, IndexError, ValueError:
                continue
    except FileNotFoundError:
        return []
    procs.sort(key=lambda p: p["rss_mb"], reverse=True)
    top = procs[:n]
    for p in top:
        argv = _cmdline(p["pid"])
        p["cmd"] = _format_cmd(argv, p["comm"])
        p["full_cmd"] = _full_cmd(argv, p["comm"])
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
    except FileNotFoundError, subprocess.CalledProcessError:
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
    except FileNotFoundError, subprocess.CalledProcessError:
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
        # nvidia-smi prints one line per GPU context, so a process using several GPUs appears more
        # than once. Merge by PID (summing VRAM) so each process gets a single row.
        procs = {}
        for line in out.strip().split("\n"):
            if not line.strip():
                continue
            # maxsplit so a process name containing commas stays intact.
            parts = [p.strip() for p in line.split(",", 2)]
            if len(parts) < 3:
                continue
            pid = parts[0]
            mem = _num(parts[1])
            if pid in procs:
                prev = procs[pid]["mem"]
                procs[pid]["mem"] = None if prev is None or mem is None else prev + mem
                continue
            argv = _cmdline(pid)
            procs[pid] = {
                "pid": pid,
                "comm": os.path.basename(parts[2]),
                "mem": mem,
                "cmd": _format_cmd(argv, os.path.basename(parts[2])),
                # nvidia-smi's name is the full exe path, a better fallback than comm.
                "full_cmd": _full_cmd(argv, parts[2]),
            }
        for p in procs.values():
            mem = p.pop("mem")
            p["mem_mb"] = f"{mem:.0f}" if mem is not None else "N/A"
        return list(procs.values())
    except FileNotFoundError, subprocess.CalledProcessError:
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


def render_cpu(overall_cpu, per_core_cpu):
    load1, load5, load15 = load_avg()
    cpu_lines = [
        Text.assemble(
            ("Load: ", "dim"),
            (f"{load1} {load5} {load15}", "bold"),
            ("  Up: ", "dim"),
            (uptime_info(), "bold"),
        ),
        make_bar_text("All", overall_cpu),
    ]
    cores = len(per_core_cpu)
    panel = Panel(Text("\n").join(cpu_lines), title=f"[bold]CPU [cyan]{cores}[/cyan] cores[/bold]", border_style="blue")

    core_ids = sorted(per_core_cpu.keys())
    cw = len(str(max(core_ids, default=0)))
    bar_w = 10 if cores <= 32 else 6 if cores <= 64 else 4
    grid = Columns([make_core_text(c, per_core_cpu[c], cw=cw, bar_w=bar_w) for c in core_ids], equal=True, expand=True)
    return Group(panel, grid)


def render_memory():
    mem_total, mem_used, swap_total, swap_used = mem_info()
    disk_total, disk_used = disk_info()
    mem_lines = [make_bar_text("RAM", mem_used / mem_total * 100, f"{mem_used:.1f} / {mem_total:.1f} GB")]
    if swap_total > 0:
        mem_lines.append(make_bar_text("Swap", swap_used / swap_total * 100, f"{swap_used:.1f} / {swap_total:.1f} GB"))
    mem_lines.append(make_bar_text("Disk", disk_used / disk_total * 100, f"{disk_used:.0f} / {disk_total:.0f} GB"))
    return Panel(Text("\n").join(mem_lines), title="[bold]Memory & Disk[/bold]", border_style="green")


def render_network():
    interfaces = net_info()
    if not interfaces:
        return None
    net_table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    net_table.add_column("Interface", style="cyan")
    net_table.add_column("RX", justify="right")
    net_table.add_column("TX", justify="right")
    for iface in interfaces:
        net_table.add_row(iface["name"], fmt_gb(iface["rx"]), fmt_gb(iface["tx"]))
    return Panel(net_table, title="[bold]Network[/bold]", border_style="magenta")


def render_gpus(gpus):
    if not gpus:
        return None
    panels = []
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

        panels.append(
            Panel(
                Text("\n").join(gpu_lines),
                title=f"[bold]GPU {i}: [cyan]{g['name']}[/cyan][/bold]",
                border_style="yellow",
            )
        )
    return Group(*panels)


def collect():
    """Sample everything. Runs in a worker thread so slow nvidia-smi calls don't block input."""
    overall_cpu, per_core_cpu = cpu_usage()
    gpus = gpu_info()
    return {
        "cpu": render_cpu(overall_cpu, per_core_cpu),
        "mem": render_memory(),
        "net": render_network(),
        "gpu": render_gpus(gpus),
        "gpu_procs": gpu_processes() if gpus else [],
        "top_procs": top_processes(5),
    }


class ProcessTable(DataTable):
    """DataTable that opens a row with a single click instead of highlight-then-click."""

    def _on_click(self, event: events.Click) -> None:
        # Runs before DataTable's own click handler. Moving the cursor to the clicked row first
        # makes DataTable treat the click as a click on the highlighted row and post RowSelected.
        meta = event.style.meta
        if meta.get("row", -1) >= 0 and "column" in meta:
            self.cursor_coordinate = Coordinate(meta["row"], meta["column"])


class CommandScreen(ModalScreen):
    """Popup showing a process's full command line."""

    BINDINGS = [("escape,q,enter", "dismiss", "Close"), ("c", "copy", "Copy")]

    DEFAULT_CSS = """
    CommandScreen {
        align: center middle;
    }
    #dialog {
        width: 90%;
        max-width: 140;
        height: auto;
        max-height: 80%;
        border: round $accent;
        border-title-style: bold;
        background: $surface;
        padding: 1 2;
    }
    #cmd-scroll {
        height: auto;
    }
    #cmd-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, pid, comm, command):
        super().__init__()
        self.pid = pid
        self.comm = comm
        self.command = command

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog") as dialog:
            dialog.border_title = f"PID {self.pid} · {self.comm}"
            with VerticalScroll(id="cmd-scroll"):
                yield Static(Text(self.command, overflow="fold"), id="cmd")
            yield Static("c copy · esc close", id="cmd-hint")

    def on_click(self, event: events.Click) -> None:
        # Clicking the dimmed backdrop closes the popup.
        if event.widget is self:
            self.dismiss()

    def action_copy(self) -> None:
        self.app.copy_to_clipboard(self.command)
        self.notify("Copied command to clipboard")


class SysMon(App):
    TITLE = "sysmon"
    BINDINGS = [("q", "quit", "Quit")]

    CSS = """
    #loading {
        align: center middle;
    }
    #loading LoadingIndicator {
        height: 1;
    }
    #loading-label {
        width: 100%;
        text-align: center;
        color: $text-muted;
    }
    #body {
        display: none;
        padding: 0 1;
    }
    ProcessTable {
        height: auto;
        max-height: 16;
        border: round red;
        border-title-style: bold;
        border-title-color: $text;
    }
    ProcessTable:focus {
        border: round red;
    }
    #gpu-procs, #gpu-procs:focus {
        border: round yellow;
    }
    #hint {
        color: $text-muted;
        text-style: italic;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        # Shown until the first sample lands; a cold nvidia-smi can take a few seconds.
        with Vertical(id="loading"):
            yield LoadingIndicator()
            yield Static("Sampling…", id="loading-label")
        with VerticalScroll(id="body"):
            yield Static(id="cpu")
            yield Static(id="mem")
            yield Static(id="net")
            yield Static(id="gpu")
            yield ProcessTable(id="gpu-procs", cursor_type="row", zebra_stripes=True)
            yield ProcessTable(id="top-procs", cursor_type="row", zebra_stripes=True)
            yield Static("Click a process (or select it and press Enter) to see its full command", id="hint")
        yield Footer()

    def on_mount(self) -> None:
        gpu_table = self.query_one("#gpu-procs", ProcessTable)
        gpu_table.border_title = "GPU Processes"
        gpu_table.add_columns("PID", "VRAM (MB)", "Command")

        top_table = self.query_one("#top-procs", ProcessTable)
        top_table.border_title = "Top Processes by RAM"
        top_table.add_columns("PID", "RAM (MB)", "Command")

        for wid in ("#net", "#gpu", "#gpu-procs"):
            self.query_one(wid).display = False

        # pid -> (comm, full command) for every process currently listed.
        self._commands = {}
        self._refreshing = False
        self._tick()
        self.set_interval(REFRESH_SECONDS, self._tick)

    def _tick(self) -> None:
        # Skip ticks while a sample is still in flight (a cold nvidia-smi can take seconds while
        # the GPU wakes up) rather than cancelling it, which would discard every slow sample.
        if not self._refreshing:
            self._refreshing = True
            self.refresh_stats()

    @work(thread=True, group="refresh")
    def refresh_stats(self) -> None:
        try:
            snapshot = collect()
        finally:
            self._refreshing = False
        self.call_from_thread(self._apply, snapshot)

    def _apply(self, snap) -> None:
        loading = self.query("#loading")
        if loading:
            loading.remove()
            self.query_one("#body").display = True

        self.query_one("#cpu", Static).update(snap["cpu"])
        self.query_one("#mem", Static).update(snap["mem"])
        for wid in ("net", "gpu"):
            widget = self.query_one(f"#{wid}", Static)
            widget.display = snap[wid] is not None
            if snap[wid] is not None:
                widget.update(snap[wid])

        # GPU entries go last so they win for a PID in both tables: their name is the full exe path
        # from nvidia-smi rather than the 15-char kernel comm.
        self._commands = {p["pid"]: (p["comm"], p["full_cmd"]) for p in snap["top_procs"] + snap["gpu_procs"]}

        gpu_table = self.query_one("#gpu-procs", ProcessTable)
        gpu_table.display = bool(snap["gpu_procs"])
        self._fill_table(
            gpu_table,
            [
                (
                    p["pid"],
                    (Text(p["pid"], style="cyan", justify="right"), Text(p["mem_mb"], justify="right"), p["cmd"]),
                )
                for p in snap["gpu_procs"]
            ],
        )
        self._fill_table(
            self.query_one("#top-procs", ProcessTable),
            [
                (
                    p["pid"],
                    (
                        Text(p["pid"], style="cyan", justify="right"),
                        Text(f"{p['rss_mb']:.0f}", justify="right"),
                        p["cmd"],
                    ),
                )
                for p in snap["top_procs"]
            ],
        )

    @staticmethod
    def _fill_table(table, rows) -> None:
        """Replace table rows, keeping the cursor on the same PID as rows re-sort."""
        selected = None
        if table.row_count:
            selected = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        table.clear()
        for key, cells in rows:
            table.add_row(*cells, key=key)
        if selected is not None and selected in table.rows:
            table.move_cursor(row=table.get_row_index(selected), animate=False)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        pid = event.row_key.value
        comm, command = self._commands.get(pid, ("?", _full_cmd(_cmdline(pid), "?")))
        self.push_screen(CommandScreen(pid, comm, command))


if __name__ == "__main__":
    SysMon().run()

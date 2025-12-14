#!/usr/bin/env python3

import curses
import time
import random
import psutil

# ---------------- CONFIG ---------------- #

GLITCH_CHARS = "!@#$%^&*()_+=-[]{};:,.<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

TOP_N_PROCS = 25
REFRESH_RATE = 0.85
MAX_LOG_LINES = 4  # Number of lines in scrolling log

# ---------------- STATUS LINE GLITCH SETTINGS ---------------- #
MIN_WAIT = 3
MAX_WAIT = 8
MIN_GLITCH_CHARS = 1
MAX_GLITCH_CHARS = 6
MIN_FRAMES = 3
MAX_FRAMES = 6
FRAME_DELAY = 0.12

HEADER = [
    "   _______  _____________________  ___   ____  __________  ____  ____  ______",
    "  / ___/\\ \\/ / ___/_  __/ ____/  |/  /  / __ \\/ ____/ __ \\/ __ \\/ __ \\/_  __/",
    "  \\__ \\  \\  /\\__ \\ / / / __/ / /|_/ /  / /_/ / __/ / /_/ / / / / /_/ / / /   ",
    " ___/ /  / /___/ // / / /___/ /  / /  / _, _/ /___/ ____/ /_/ / _, _/ / /    ",
    "/____/  /_//____//_/ /_____/_/  /_/  /_/ |_/_____/_/    \\____/_/ |_| /_/     ",
    " ",
    "==============================================================================",
    " "
]

# ---------------- UTILS ---------------- #

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_uptime():
    return format_time(time.time() - psutil.boot_time())

def get_system_status(cpu, mem):
    if cpu >= 80 or mem >= 85:
        return "CRITICAL"
    elif cpu >= 60 or mem >= 70:
        return "DEGRADED"
    elif cpu >= 40 or mem >= 60:
        return "MONITORING"
    else:
        return "NOMINAL"

def glitch_line(text, color, stdscr, row, x=4,
                min_chars=MIN_GLITCH_CHARS, max_chars=MAX_GLITCH_CHARS,
                min_frames=MIN_FRAMES, max_frames=MAX_FRAMES,
                frame_delay=FRAME_DELAY):
    """Glitch any line with multiple frames and random chars."""
    for _ in range(random.randint(min_frames, max_frames)):
        glitched = list(text)
        for _ in range(random.randint(min_chars, max_chars)):
            pos = random.randrange(len(glitched))
            glitched[pos] = random.choice(GLITCH_CHARS)
        stdscr.addstr(row, x, "".join(glitched).ljust(len(text)), color)
        stdscr.refresh()
        time.sleep(frame_delay)

# ---------------- MAIN DRAW LOOP ---------------- #

def draw(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    # ---------------- COLOR PAIRS ---------------- #
    curses.init_pair(1, 220, -1)  # Yellow/orange for status nominal
    curses.init_pair(2, 214, -1)  # Bright orange for CPU
    curses.init_pair(3, 109, -1)  # Teal/cyan for Memory
    curses.init_pair(4, 108, -1)  # Green for Uptime
    curses.init_pair(5, 167, -1)  # Red for Critical status
    curses.init_pair(6, 223, -1)  # Yellow for logs/process CPU
    curses.init_pair(7, 189, -1)  # Light green for process MEM
    curses.init_pair(8, 15, -1)   # Gruv-White for general/headers

    # ----- DRAW HEADER ONCE -----
    row = 1
    for line in HEADER:
        stdscr.addstr(row, 2, line, curses.color_pair(8))
        row += 1

    status_row = row
    base_row = status_row + 2
    last_status_glitch_time = time.time()

    # ----- LIVE DEVICE ID -----
    live_feed_row = status_row - 1
    def generate_device_id():
        return f"{random.randint(10000,99999)}-{random.randint(10000,99999)}-{random.randint(100000000000,999999999999)}"
    live_feed = generate_device_id()
    stdscr.addstr(live_feed_row, 4, f"DEVICE ID: {live_feed}", curses.color_pair(6))

    # ----- LOGS BUFFER -----
    log_lines = []

    while True:
        # ------ CHECK FOR EXIT KEY ------
        try:
            key = stdscr.getch()
            if key == ord('q'):
                break
        except Exception:
            pass

        # ----- SYSTEM INFO -----
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        load = psutil.getloadavg()[0]
        uptime = get_uptime()

        # ----- UPDATE LIVE DEVICE ID -----
        live_feed = generate_device_id()
        stdscr.addstr(live_feed_row, 4, f"HANDSHAKE ID: {live_feed}", curses.color_pair(6))

        # ----- STATUS LINE -----
        status_text_val = get_system_status(cpu, mem)
        STATUS_LINE = f"SYSTEM STATUS: {status_text_val}"
        if status_text_val == "CRITICAL":
            status_color = curses.color_pair(5) | curses.A_BOLD
        elif status_text_val == "DEGRADED":
            status_color = curses.color_pair(1) | curses.A_BOLD
        else:
            status_color = curses.color_pair(4)

        if time.time() - last_status_glitch_time > random.uniform(MIN_WAIT, MAX_WAIT):
            glitch_line(STATUS_LINE, status_color, stdscr, status_row)
            last_status_glitch_time = time.time()
        stdscr.addstr(status_row, 4, STATUS_LINE.ljust(40), status_color)

        # ----- SYSTEM OVERVIEW LINES (STABLE) -----
        system_lines = [
            f"---------------------- SYSTEM OVERVIEW ----------------------",
            f"CPU Usage : {cpu:5.1f}%",
            f"Memory    : {mem:5.1f}%",
            f"Load Avg  : {load:5.2f}",
            f"Uptime    : {uptime}",
            f" ",
            f"------------------------- PROCESSES -------------------------",
        ]
        for i, line in enumerate(system_lines):
            if "CPU" in line:
                clr = curses.color_pair(2)
            elif "Memory" in line:
                clr = curses.color_pair(3)
            elif "Load" in line:
                clr = curses.color_pair(6)
            elif "Uptime" in line:
                clr = curses.color_pair(4)
            else:
                clr = curses.color_pair(8)
            stdscr.addstr(base_row + i, 4, line.ljust(40), clr)

        # ----- PROCESS LIST -----
        processes = []
        for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_percent','cpu_times']):
            try:
                cpu_time = p.info['cpu_times']
                total_time = cpu_time.user + cpu_time.system
                processes.append({
                    'pid': p.info['pid'],
                    'user': p.info['username'][:8] if p.info['username'] else '?',
                    'cpu': p.info['cpu_percent'],
                    'mem': p.info['memory_percent'],
                    'time': format_time(total_time),
                    'name': p.info['name'][:20]
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        proc_start = base_row + len(system_lines) + 1

        # Table header
        stdscr.addstr(proc_start-1, 4, " PID   USER     CPU%   MEM%    TIME     COMMAND", curses.color_pair(8)|curses.A_BOLD)

        for i, p in enumerate(processes[:TOP_N_PROCS]):
            cpu_color = curses.color_pair(5)|curses.A_BOLD if p['cpu']>50 else curses.color_pair(6) if p['cpu']>20 else curses.color_pair(4)
            mem_color = curses.color_pair(5)|curses.A_BOLD if p['mem']>50 else curses.color_pair(7) if p['mem']>20 else curses.color_pair(4)
            line_parts = [
                (f"{p['pid']:5d} ", curses.color_pair(8)),
                (f"{p['user']:<8} ", curses.color_pair(8)),
                (f"{p['cpu']:5.1f} ", cpu_color),
                (f"{p['mem']:5.1f} ", mem_color),
                (f"{p['time']:>9} ", curses.color_pair(8)),
                (f"{p['name']:<20}", curses.color_pair(8))
            ]
            x = 4
            for text, color in line_parts:
                stdscr.addstr(proc_start+i, x, text, color)
                x += len(text)

        # ----- SEPARATOR -----
        separator_row = proc_start + TOP_N_PROCS + 1
        stdscr.addstr(separator_row, 4, "-"*60, curses.color_pair(8))

        # ----- LOGS -----
        log_start_row = separator_row + 1
        log_message = f"[{time.strftime('%H:%M:%S')}] CPU {cpu:.1f}%, MEM {mem:.1f}%"
        log_lines.append(log_message)
        if len(log_lines) > MAX_LOG_LINES:
            log_lines.pop(0)
        for i, line in enumerate(log_lines):
            stdscr.addstr(log_start_row + i, 4, line.ljust(60), curses.color_pair(6))

        stdscr.refresh()
        time.sleep(REFRESH_RATE)

# ---------------- ENTRY ---------------- #

def main():
    try:
        curses.wrapper(draw)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

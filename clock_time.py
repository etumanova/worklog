import sys
from datetime import datetime, timedelta
from pathlib import Path

# can change the path name if you want to name it something different
DATA_FILE = Path("clock_data.txt")
DATE_FMT = "%m-%d-%Y"
TIME_FMT = "%H:%M:%S"
DT_FMT = f"{DATE_FMT} {TIME_FMT}"

# -----------------------------
#           Helpers
# -----------------------------

def now():
    return datetime.now()

def read_entries():
    if not DATA_FILE.exists():
        return []

    entries = []
    with open(DATA_FILE, "r") as f:
        for line in f:
            date_str, time_str, status = line.strip().split()
            dt = datetime.strptime(f"{date_str} {time_str}", DT_FMT)
            entries.append((dt, status))
    return entries

def write_entry(dt, status):
    # checks if the file exists, otherwise it creates the file
    DATA_FILE.touch(exist_ok=True)

    with open(DATA_FILE, "a") as f:
        f.write(f"{dt.strftime(DATE_FMT)} {dt.strftime(TIME_FMT)} {status}\n")

def last_status(entries):
    return entries[-1][1] if entries else None

def clear_n_previous(n: int):
    if not DATA_FILE.exists():
        print("Error: no data file to clear.")
        return

    with open(DATA_FILE, "r") as f:
        lines = f.readlines()

    if n <= 0:
        print("Nothing to clear.")
        return

    if n >= len(lines):
        DATA_FILE.unlink()
        print("Cleared entire file.")
        return

    # keep everything except the last n lines
    remaining = lines[:-n]

    with open(DATA_FILE, "w") as f:
        f.writelines(remaining)

    print(f"Cleared last {n} entr{'y' if n == 1 else 'ies'}.")

def status():
    entries = read_entries()
    if not entries:
        print("No entries yet. You have not clocked in or out.")
        return

    last_dt, last_status = entries[-1]

    if last_status == "in":
        # we're currently clocked in
        elapsed = now() - last_dt
        days, remainder = divmod(elapsed.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        print("Status: CLOCKED IN")
        print(f"Started: {last_dt.strftime(DT_FMT)}")

        elapsed_str = ""
        if days > 0:
            elapsed_str += f"{days}d "
        elapsed_str += f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        print(f"Elapsed: {elapsed_str}")
    else:
        # currently clocked out
        print("Status: CLOCKED OUT")
        print(f"Last clock-out: {last_dt.strftime(DT_FMT)}")

# -----------------------------
#        Clock in / out
# -----------------------------

def clock_in():
    entries = read_entries()
    if last_status(entries) == "in":
        print("Error: already clocked in.")
        return

    write_entry(now(), "in")
    print("Clocked in.")

def clock_out():
    entries = read_entries()
    if last_status(entries) != "in":
        print("Error: cannot clock out unless clocked in.")
        return

    write_entry(now(), "out")
    print("Clocked out.")

# -----------------------------
#      Weekly calculations
# -----------------------------

def week_start(dt):
    # uses Monday as start of week
    return dt - timedelta(days=dt.weekday())

def compute_weekly_hours():
    entries = read_entries()
    weekly = {}

    i = 0
    while i < len(entries):
        dt, status = entries[i]
        if status == "in":
            start = dt
            # determine if this session was ended
            if (i + 1) < len(entries) and entries[i + 1][1] == "out":
                end = entries[i + 1][0]
                i += 1 # skip entry since there was an out
            else:
                # open session
                end = now()
            # compute duration in hours
            duration = (end - start).total_seconds() / 3600

            # assign to week (Monday-Sunday)
            wk_start = week_start(start).date()
            weekly[wk_start] = weekly.get(wk_start, 0.0) + duration
        i += 1

    return dict(sorted(weekly.items()))

def print_weekly(limit=None):
    weekly = compute_weekly_hours()
    weeks = list(weekly.items())

    if limit:
        weeks = weeks[-limit:]

    print(f"{'WEEK':<30}{'HOURS':>8}")
    for wk_start, hours in weeks:
        wk_end = wk_start + timedelta(days=6)
        label = f"{wk_start.strftime(DATE_FMT)} to {wk_end.strftime(DATE_FMT)}"
        print(f"{label:<30}{hours:>8.1f}")

# -----------------------------
#             Main
# -----------------------------

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else None

    if cmd in {"in", "out", "weekly", "all"} and len(sys.argv) != 2:
        print("Usage: python3 clock_time.py [in|out|status|weekly|all]")
        return
    elif cmd == "clear" and len(sys.argv) != 3:
        print("Usage: python3 clock_time.py clear n")
        return
    
    if cmd == "in":
        clock_in()
    elif cmd == "out":
        clock_out()
    elif cmd == "weekly":
        print_weekly(limit=10)
    elif cmd == "all":
        print_weekly()
    elif cmd == "clear":
        if len(sys.argv) != 3 or not sys.argv[2].isdigit():
            print("Usage: python3 clock_time.py clear n")
            return
        clear_n_previous(int(sys.argv[2]))
    elif cmd == "status":
        status()
    else:
        print("Unknown command.")

if __name__ == "__main__":
    main()

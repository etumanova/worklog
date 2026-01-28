import sys
from datetime import datetime, timedelta
from pathlib import Path

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
    # Ensure file exists before appending
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

    # Keep everything except the last n lines
    remaining = lines[:-n]

    with open(DATA_FILE, "w") as f:
        f.writelines(remaining)

    print(f"Cleared last {n} entr{'y' if n == 1 else 'ies'}.")

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
    if not DATA_FILE.exists():
        print("Error: no existing data file.")
        return

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
    # Monday as start of week
    return dt - timedelta(days=dt.weekday())

def compute_weekly_hours():
    entries = read_entries()
    weekly = {}

    i = 0
    while i < len(entries) - 1:
        dt_in, status_in = entries[i]
        dt_out, status_out = entries[i + 1]

        if status_in == "in" and status_out == "out":
            duration = (dt_out - dt_in).total_seconds() / 3600
            wk = week_start(dt_in).date()
            weekly[wk] = weekly.get(wk, 0.0) + duration
            i += 2
        else:
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
    if len(sys.argv) != 2 | len(sys.argv) != 3:
        print("Usage: python3 clock_time.py [in|out|weekly|all|(clear n)]")
        return

    cmd = sys.argv[1]

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
    else:
        print("Unknown command.")

if __name__ == "__main__":
    main()

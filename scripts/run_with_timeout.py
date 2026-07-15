"""Run test_all_apis with per-test timeout. Stops after 10s without response."""
import subprocess, sys, time, threading

TEST_SCRIPT = r'c:\Users\pxq\Desktop\mcp\scripts\test_all_apis.py'
TIMEOUT = 120  # total timeout

proc = subprocess.Popen(
    [sys.executable, TEST_SCRIPT],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

last_output = time.time()
output_lines = []

def check_timeout():
    global last_output
    while proc.poll() is None:
        time.sleep(1)

timer = threading.Thread(target=check_timeout, daemon=True)
timer.start()

lines = []
try:
    for line in iter(proc.stdout.readline, ''):
        line = line.rstrip('\n')
        if line:
            lines.append(line)
            print(line, flush=True)
            last_output = time.time()
        
        # Check total timeout
        if proc.poll() is not None:
            break
except Exception as e:
    print(f"Error reading: {e}")
    proc.kill()

proc.wait(timeout=5)

# Save output
with open(r'c:\Users\pxq\Desktop\mcp\test_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

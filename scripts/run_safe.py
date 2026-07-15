"""Run the complete test suite with progress saving."""
import subprocess, sys, time

TEST_SCRIPT = r'c:\Users\pxq\Desktop\mcp\scripts\test_all_apis.py'
OUTPUT_FILE = r'c:\Users\pxq\Desktop\mcp\test_output.txt'

proc = subprocess.Popen(
    [sys.executable, '-u', TEST_SCRIPT],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

start = time.time()
line_count = 0
all_lines = []

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for line in iter(proc.stdout.readline, ''):
        line = line.rstrip('\n')
        all_lines.append(line)
        f.write(line + '\n')
        f.flush()
        line_count += 1
        
        if line_count % 20 == 0:
            elapsed = time.time() - start
            print(f"[{elapsed:.0f}s] {line_count} lines processed")
        
        if time.time() - start > 360:
            print("TIMEOUT after 6 minutes")
            proc.kill()
            break

proc.wait()
elapsed = time.time() - start

# Check results
summary_lines = [l for l in all_lines if 'PASSED' in l or 'FAILED' in l or 'TOTAL' in l or 'RATE' in l]
for s in summary_lines:
    print(s)

print(f"\nDone in {elapsed:.0f}s. {line_count} lines written to {OUTPUT_FILE}")

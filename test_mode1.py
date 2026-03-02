import subprocess
import sys

# 测试模式1：总检索
result = subprocess.run([
    sys.executable, 'main.py', 'crawl', 
    '--pages', '2'
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)

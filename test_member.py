import subprocess
import sys

# 测试池田 瑛紗
result = subprocess.run([
    sys.executable, 'main.py', 'member', 
    '--name', '池田 瑛紗',
    '--pages', '3'
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)

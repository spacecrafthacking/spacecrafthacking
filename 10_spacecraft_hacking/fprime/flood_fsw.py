import subprocess

CMD = ["fprime-cli", "command-send", "cmdDisp.CMD_NO_OP"]

for i in range(1000):
    print(f"Sending NO_OP #{i+1}")
    result = subprocess.run(CMD, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Call #{i+1} failed with code {result.returncode}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        break

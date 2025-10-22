# === VNLT REV ===
# file: shell_util.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:shell
# note: r2c — shell pipeline support
# === /VNLT REV ===
import subprocess
def run_shell(script:str, stdin_text:str='') -> tuple[str,int,str]:
 p=subprocess.Popen(['/bin/sh','-c',script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
 out,err=p.communicate(stdin_text)
 return out, p.returncode, err

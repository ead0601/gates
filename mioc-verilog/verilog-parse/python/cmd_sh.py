# REV:r2
# cmd_sh.py — run a shell command via /bin/sh -c
# Usage:
#   sh [--print|--tty] <command...>
# Examples:
#   sh ls -ltr                # returns stdout as a single string (good for pipes/redirects)
#   sh --print ls -ltr        # prints lines directly to the screen (like a real shell)
#   sh 'printf "a\nb\nc\n"' | grep b
#
# Behavior:
#   - Default: capture stdout and RETURN it (so vnlt pipes/redirects work).
#   - --print/--tty: write stdout/stderr directly to terminal (multi-line display), return "".
#   - On non-zero exit, stderr is appended (default) or printed (with --print).

import sys
import subprocess

def register(reg):
    def _sh(args, _interp=None):
        if not args:
            return "sh: usage: sh [--print|--tty] <command...>"
        echo_direct = False
        if args[0] in ("--print", "--tty"):
            echo_direct = True
            args = args[1:]
            if not args:
                return "sh: usage: sh [--print|--tty] <command...>"
        cmd = " ".join(args)
        proc = subprocess.Popen(
            ['/bin/sh', '-c', cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, err = proc.communicate()
        rc = proc.returncode
        if echo_direct:
            if out:
                sys.stdout.write(out)
            if rc != 0 and err:
                sys.stdout.write(err)
            return ""
        if rc != 0 and err:
            if out and not out.endswith("\n"):
                out += "\n"
            out += err
        return out
    reg.add_command("sh", _sh, "sh [--print|--tty] <command...> — execute a shell command via /bin/sh -c")

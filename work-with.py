
import sys
import os

def proc_arg(p):
  curr_dir = os.getcwd()
  a = p.split(":")
  if len(a)== 1:
    a.append(a[0])
  return f"-v{curr_dir}/{a[0]}/:/work/{a[1]}"

volumes = list(map(proc_arg, sys.argv[2:]))
# privileged is used for strace
# todo: specific caps
os.execvp("/usr/bin/docker", [ "/usr/bin/docker", "run", "--privileged", "--rm", "-it" ] + volumes + [ sys.argv[1], "bash" ])

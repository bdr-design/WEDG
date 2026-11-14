import sys, subprocess, time, resource
t = time.time(); r = subprocess.run(sys.argv[1:]); 
u = resource.getrusage(resource.RUSAGE_CHILDREN)
print(f'TIMED wall {time.time()-t:.0f} s  user {u.ru_utime:.0f} s  peak RSS {u.ru_maxrss/1024:.0f} MiB  exit {r.returncode}', flush=True)
sys.exit(r.returncode)

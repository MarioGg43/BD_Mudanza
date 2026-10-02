# Captura cada vista (#vista-<id>) a 390x844 con Edge sin ventana, una por una.
import subprocess, time, pathlib, re, shutil, sys, tempfile
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
base = pathlib.Path(__file__).resolve().parent.parent
out = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else base / "shots").resolve()
url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8765/local.html"
out.mkdir(parents=True, exist_ok=True)
ids = re.findall(r"id: '([a-z0-9-]+)'", (base / "gallery.js").read_text(encoding="utf-8"))
faltan = []
solo = sys.argv[3].split(',') if len(sys.argv) > 3 else None
for i, vid in enumerate(ids, 1):
    if solo and vid not in solo: continue
    destino = out / f"{i:02d}-{vid}.png"
    if destino.exists(): destino.unlink()
    perfil = tempfile.mkdtemp(prefix="edge-")
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
           f"--user-data-dir={perfil}", "--force-device-scale-factor=2", "--window-size=390,844",
           "--virtual-time-budget=6000", f"--screenshot={destino}", f"{url}#vista-{vid}"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    for _ in range(40):
        if destino.exists() and destino.stat().st_size > 0: break
        time.sleep(0.25)
    shutil.rmtree(perfil, ignore_errors=True)
    if not destino.exists(): faltan.append(vid)
print(len(solo or ids) - len(faltan), "de", len(solo or ids), "capturas", "| faltan:", faltan)

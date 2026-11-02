"""usage: python shots.py OUTPREFIX WIDTH HEIGHT scheme(light|dark) page..."""
import subprocess, sys, os
from PIL import Image
CH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
S = os.path.dirname(os.path.abspath(__file__))
pre, w, h, scheme, pages = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:]
for p in pages:
    name = os.path.splitext(os.path.basename(p))[0]
    out = os.path.join(S, f"{pre}-{name}.png")
    subprocess.run([CH, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=6000",
                    f"--blink-settings=preferredColorScheme={1 if scheme == 'light' else 0}", f"--window-size={w},{h}",
                    f"--user-data-dir={S}\chrome-{name}", f"--screenshot={out}", "file:///" + p.replace(" ", "%20")],
                   capture_output=True)
    im = Image.open(out); im.thumbnail((720, 4000)); im.save(out.replace(".png", "-s.png")); print(out, im.size)

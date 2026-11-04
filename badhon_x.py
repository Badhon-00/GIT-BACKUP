#!/usr/bin/env python3
from __future__ import annotations
import argparse, getpass, json, os, shutil, subprocess, sys, time, zipfile
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip install requests")
    sys.exit(1)

VERSION = "4.0.0"

LOGO = r"""
   ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗   ██╗  ██╗
   ██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔═══██╗████╗  ██║   ╚██╗██╔╝
   ██████╔╝███████║██║  ██║███████║██║   ██║██╔██╗ ██║    ╚███╔╝
   ██╔══██╗██╔══██║██║  ██║██╔══██║██║   ██║██║╚██╗██║    ██╔██╗
   ██████╔╝██║  ██║██████╔╝██║  ██║╚██████╔╝██║ ╚████║   ██╔╝ ██╗
   ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝  ╚═╝
"""

TAGLINE = f"       ★  Premium GitHub Backup  ·  Termux  ·  v{VERSION}  ★\n"

HELP_BANNER = r"""
 ┌──────────────────────────────────────────────────────────────────────┐
 │                        BADHON-X  COMMANDS                            │
 ├──────────────────────────────────────────────────────────────────────┤
 │  badhon-x                    →  Full backup of every repo            │
 │  badhon-x --update           →  Pull latest, no re-clone             │
 │  badhon-x --upgrade          →  Pull latest and re-zip all           │
 │  badhon-x --new              →  Only new, forked or missing repos    │
 │  badhon-x --update --new     →  Daily driver                         │
 │  badhon-x --verify           →  Validate every zip                   │
 │  badhon-x --status           →  Show backup stats                    │
 │  badhon-x --set-path         →  Choose a custom storage folder       │
 │  badhon-x --where            →  Print current storage folder         │
 │  badhon-x --login            →  Save or replace token                │
 │  badhon-x --logout           →  Delete token from device             │
 └──────────────────────────────────────────────────────────────────────┘
"""

class C:
    R="\033[0m"; B="\033[1m"; D="\033[2m"
    RED="\033[31m"; GRN="\033[32m"; YEL="\033[33m"
    BLU="\033[34m"; MAG="\033[35m"; CYN="\033[36m"; WHT="\033[37m"

def col(t,c): return f"{c}{t}{C.R}"
def ok(m):    print(col("  ✔ ",C.GRN)+m, flush=True)
def warn(m):  print(col("  ⚠ ",C.YEL)+m, flush=True)
def err(m):   print(col("  ✖ ",C.RED)+m, flush=True)
def info(m):  print(col("  › ",C.CYN)+m, flush=True)
def head(m):  print("\n"+col(m,C.B+C.CYN), flush=True)
def rule():   print(col("─"*70,C.D), flush=True)

def banner():
    print(col(LOGO, C.CYN))
    print(col(TAGLINE, C.D))

def progress_bar(current, total, label="", width=34, unit="repos"):
    if total <= 0:
        return
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    pct_str = f"{pct*100:5.1f}%"
    line = f"  {label:>14}  [{col(bar, C.CYN)}] {pct_str}  {current}/{total} {unit}"
    print("\r" + line, end="", flush=True)
    if current >= total:
        print()

def mini_progress(current, total, label="", width=22):
    if total <= 0:
        return
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    print("\r     " + col(bar, C.MAG) + f" {int(pct*100):3d}%  {label[:40]}",
          end="", flush=True)
    if current >= total:
        print()

HOME = Path.home()
CONFIG_DIR  = HOME / ".config" / "badhon-x"
CONFIG_FILE = CONFIG_DIR / "config.json"

def default_base() -> Path:
    if Path("/sdcard").exists():
        return Path("/sdcard/GitHubBackup")
    return HOME / "GitHubBackup"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text())
        except Exception: return {}
    return {}

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    CONFIG_FILE.chmod(0o600)

def base_path() -> Path:
    cfg = load_config()
    p = cfg.get("base_path")
    return Path(p) if p else default_base()

def dirs():
    b = base_path()
    return {
        "root":    b,
        "repos":   b / "repos",
        "working": b / "working",
        "logs":    b / "logs",
        "state":   b / "state.json",
    }

INCLUDE_FORKS    = True
INCLUDE_ARCHIVED = True

def do_login():
    head("GitHub login")
    info("Create a token at https://github.com/settings/tokens")
    info("Required scope: " + col("repo", C.B))
    try:
        tok = getpass.getpass("  Paste token (hidden): ").strip()
    except (KeyboardInterrupt, EOFError):
        print(); return None
    if not (tok.startswith("ghp_") or tok.startswith("github_pat_")):
        err("Token must start with ghp_ or github_pat_"); return None
    try:
        r = requests.get("https://api.github.com/user",
                         headers={"Authorization": f"token {tok}"},
                         timeout=30)
    except Exception as e:
        err(f"Network: {e}"); return None
    if r.status_code != 200:
        err(f"Invalid token ({r.status_code})"); return None
    user = r.json().get("login", "unknown")
    cfg = load_config(); cfg["token"] = tok; cfg["username"] = user
    save_config(cfg)
    ok(f"Logged in as {col(user, C.B)}")
    info(f"Stored at {CONFIG_FILE} (chmod 600)")
    return tok

def do_logout():
    cfg = load_config()
    if "token" in cfg:
        cfg.pop("token", None); save_config(cfg)
        ok("Token removed from this device.")
    else:
        warn("No token stored.")

def get_token():
    tok = os.environ.get("GH_TOKEN", "").strip()
    if tok: return tok
    tok = load_config().get("token", "").strip()
    if tok: return tok
    return do_login()

def do_set_path():
    head("Choose storage folder")
    cur = base_path()
    info(f"Current   : {cur}")
    if Path("/sdcard").exists():
        info("Suggested : /sdcard/GitHubBackup")
    info(f"Suggested : {HOME / 'GitHubBackup'}")
    print()
    for e in ["/sdcard/GitHubBackup",
              "/sdcard/Download/gh-backup",
              str(HOME / "GitHubBackup")]:
        print(col("  · ", C.D) + e)
    try:
        raw = input(col("\n  Enter folder path (or Enter for default): ",
                        C.B)).strip()
    except (KeyboardInterrupt, EOFError):
        print(); return
    if not raw: raw = str(default_base())
    p = Path(raw).expanduser()
    try:
        p.mkdir(parents=True, exist_ok=True)
        test = p / ".write_test"
        test.write_text("x"); test.unlink()
    except Exception as e:
        err(f"Cannot write to {p}: {e}"); return
    cfg = load_config(); cfg["base_path"] = str(p)
    save_config(cfg)
    ok(f"Storage folder set to {col(str(p), C.B)}")

def ensure_storage_prompt():
    cfg = load_config()
    if cfg.get("base_path"): return
    head("First-time setup: choose where backups are stored")
    info(f"Default: {col(str(default_base()), C.B)}")
    info("Change anytime with badhon-x --set-path")
    try:
        choice = input(col("\n  Use default? [Y/n]: ", C.B)).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print(); return
    if choice in ("", "y", "yes"):
        cfg["base_path"] = str(default_base()); save_config(cfg)
        ok(f"Using {cfg['base_path']}")
    else:
        do_set_path()

def api(url, token):
    r = requests.get(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }, timeout=60)
    if r.status_code == 401:
        err("Token rejected. Run: badhon-x --login"); return None
    if r.status_code != 200:
        raise RuntimeError(f"API {r.status_code}: {r.text[:200]}")
    return r

def get_all_repos(token):
    out, page = [], 1
    while True:
        url = ("https://api.github.com/user/repos"
               f"?per_page=100&page={page}&affiliation=owner&sort=full_name")
        r = api(url, token)
        if not r: return []
        batch = r.json()
        if not batch: break
        out.extend(batch); page += 1
    return out

def filter_repos(repos):
    return [r for r in repos
            if (INCLUDE_FORKS or not r.get("fork"))
            and (INCLUDE_ARCHIVED or not r.get("archived"))]

def auth_url(u, user, tok):
    return u.replace("https://", f"https://{user}:{tok}@")

def zip_folder(src: Path, out_zip: Path) -> int:
    tmp = out_zip.with_suffix(".zip.tmp")
    n = 0
    all_files = []
    for root, _, files in os.walk(src):
        for f in files:
            all_files.append(Path(root) / f)
    total = len(all_files)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED,
                             compresslevel=6) as zf:
            for i, full in enumerate(all_files, 1):
                try:
                    if full.is_symlink() and not full.exists():
                        continue
                    zf.write(full, full.relative_to(src.parent))
                    n += 1
                except (OSError, ValueError):
                    pass
                if total > 0 and (i % 25 == 0 or i == total):
                    mini_progress(i, total, f"packing {out_zip.name}")
        tmp.replace(out_zip); return n
    except Exception:
        if tmp.exists(): tmp.unlink()
        raise

def validate_zip(zp: Path) -> bool:
    try:
        with zipfile.ZipFile(zp) as z:
            return len(z.namelist()) > 0
    except Exception:
        return False

def download_zipball(full_name, dest, token):
    url = f"https://api.github.com/repos/{full_name}/zipball"
    try:
        with requests.get(url, headers={"Authorization": f"token {token}"},
                          allow_redirects=True, stream=True, timeout=3600) as r:
            if r.status_code != 200:
                warn(f"zipball {r.status_code}"); return False
            total = int(r.headers.get("Content-Length", 0))
            done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk); done += len(chunk)
                    if total > 0:
                        mini_progress(done, total, "downloading zip")
        return validate_zip(dest)
    except Exception as e:
        warn(f"zipball: {e}"); return False

def git_clone(url, dest, user, token):
    try:
        subprocess.run(
            ["git","-c","submodule.recurse=true","clone","--quiet",
             "--recurse-submodules", auth_url(url,user,token), str(dest)],
            check=True, capture_output=True, timeout=3600)
        subprocess.run(["git","-C",str(dest),"lfs","pull"],
                       check=False, capture_output=True, timeout=900)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        warn(f"clone failed: {getattr(e,'stderr',b'')[:120]}")
        return False

def load_state():
    st = dirs()["state"]
    if st.exists():
        try: return json.loads(st.read_text())
        except Exception: return {}
    return {}

def save_state(repos):
    st = dirs()["state"]; st.parent.mkdir(parents=True, exist_ok=True)
    st.write_text(json.dumps({
        "last_run": datetime.now().isoformat(),
        "repos": {r["full_name"]: r["pushed_at"] for r in repos},
    }, indent=2))

def human_size(n):
    for unit in ("B","KB","MB","GB"):
        if n < 1024: return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def sync_repo(repo, user, token, force_zip=False):
    d = dirs()
    name = repo["name"]; full = repo["full_name"]
    url  = auth_url(repo["clone_url"], user, token)
    local = d["working"] / name
    zp    = d["repos"] / f"{name}.zip"

    if not (local / ".git").exists():
        info("cloning first time")
        if local.exists(): shutil.rmtree(local, ignore_errors=True)
        if not git_clone(repo["clone_url"], local, user, token):
            info("zipball fallback")
            return "CLONED" if download_zipball(full, zp, token) else "FAIL"
        n = zip_folder(local, zp)
        ok(f"zipped {n} files"); return "CLONED"

    try:
        subprocess.run(["git","-C",str(local),"remote","set-url","origin",url],
                       check=False, capture_output=True)
        subprocess.run(["git","-C",str(local),"config","submodule.recurse","true"],
                       check=False, capture_output=True)
        before = subprocess.run(["git","-C",str(local),"rev-parse","HEAD"],
                                capture_output=True,text=True,check=True
                                ).stdout.strip()
        subprocess.run(["git","-C",str(local),"fetch","--all","--prune",
                        "--tags","--force","--quiet"],
                       check=True,capture_output=True,timeout=1800)
        branch = subprocess.run(
            ["git","-C",str(local),"rev-parse","--abbrev-ref","HEAD"],
            capture_output=True,text=True,check=True
        ).stdout.strip() or "main"
        subprocess.run(["git","-C",str(local),"reset","--hard",
                        f"origin/{branch}"], check=True, capture_output=True)
        subprocess.run(["git","-C",str(local),"clean","-fdxq"],
                       check=False, capture_output=True)
        subprocess.run(["git","-C",str(local),"submodule","update","--init",
                        "--recursive","--force","--quiet"],
                       check=False, capture_output=True, timeout=1800)
        subprocess.run(["git","-C",str(local),"lfs","pull"],
                       check=False, capture_output=True, timeout=900)
        after = subprocess.run(["git","-C",str(local),"rev-parse","HEAD"],
                               capture_output=True,text=True,check=True
                               ).stdout.strip()
        changed = before != after
        zip_bad = not zp.exists() or not validate_zip(zp)
        if changed:
            ok(f"updated {before[:7]} to {after[:7]}")
            n = zip_folder(local, zp); ok(f"re-zipped {n} files")
            return "UPDATED"
        if force_zip or zip_bad:
            zip_folder(local, zp); return "REZIPPED"
        print(col("    ✓ up to date", C.D), flush=True)
        return "UNCHANGED"
    except subprocess.CalledProcessError as e:
        warn(f"git error: {(e.stderr or b'')[:120]}")
        info("repairing with fresh clone")
        shutil.rmtree(local, ignore_errors=True)
        if git_clone(repo["clone_url"], local, user, token):
            zip_folder(local, zp); return "REPAIRED"
        return "FAIL"

def ensure_dirs():
    for k in ("repos","working","logs"):
        dirs()[k].mkdir(parents=True, exist_ok=True)

def run_full(user, token):
    ensure_dirs()
    head(f"FULL BACKUP  →  {dirs()['repos']}")
    info(f"Fetching repos for {user}...")
    all_repos = get_all_repos(token)
    if not all_repos: return
    repos = filter_repos(all_repos)
    ok(f"{len(repos)} repos total"); rule()
    summary = []
    for i, r in enumerate(repos, 1):
        progress_bar(i-1, len(repos), label="overall")
        print(col(f"  [{i}/{len(repos)}] ", C.B) + r["full_name"], flush=True)
        zp = dirs()["repos"] / f"{r['name']}.zip"
        if zp.exists() and validate_zip(zp):
            print(col("    ⏭  already backed up", C.D), flush=True)
            summary.append((r["full_name"], "SKIP")); continue
        summary.append((r["full_name"], sync_repo(r, user, token)))
        progress_bar(i, len(repos), label="overall")
    save_state(all_repos); write_report("BACKUP", summary)

def run_update(user, token, force_zip=False, only_new=False):
    ensure_dirs()
    mode = "NEW-ONLY" if only_new else ("UPGRADE" if force_zip else "UPDATE")
    head(f"{mode} MODE (force re-zip: {force_zip})")
    info(f"Fetching repos for {user}...")
    all_repos = get_all_repos(token)
    if not all_repos: return
    repos = filter_repos(all_repos)
    known = load_state().get("repos", {})
    if only_new:
        d = dirs()
        targets = [r for r in repos
                   if r["full_name"] not in known
                   or not (d["repos"] / f"{r['name']}.zip").exists()
                   or not (d["working"] / r["name"] / ".git").exists()]
        ok(f"{len(targets)} new or missing repos (of {len(repos)})")
    else:
        targets = repos; ok(f"{len(targets)} repos to sync")
    rule()
    summary = []
    for i, r in enumerate(targets, 1):
        progress_bar(i-1, len(targets), label="overall")
        print(col(f"  [{i}/{len(targets)}] ", C.B) + r["full_name"], flush=True)
        summary.append((r["full_name"], sync_repo(r, user, token, force_zip)))
        progress_bar(i, len(targets), label="overall")
    save_state(all_repos); write_report(mode, summary)

def run_verify():
    head("VERIFY: every zip")
    d = dirs()
    if not d["repos"].exists():
        warn("No backups yet."); return
    good, bad = [], []
    for zp in sorted(d["repos"].glob("*.zip")):
        if validate_zip(zp):
            try:
                with zipfile.ZipFile(zp) as z:
                    names = z.namelist()
                    has_dot = any(n.startswith(".") or "/." in n
                                  for n in names[:10000])
                good.append((zp.name, len(names), has_dot, zp.stat().st_size))
            except Exception:
                bad.append(zp.name)
        else:
            bad.append(zp.name)
    rule()
    ok(f"{len(good)} valid zips")
    for name, n, dot, sz in good:
        tag = col("dotfiles ok", C.GRN) if dot else col("no dot", C.YEL)
        print(f"    {name:42} {n:>6} files  {human_size(sz):>9}  {tag}",
              flush=True)
    if bad:
        err(f"{len(bad)} broken zips")
        for b in bad: print(f"    {b}", flush=True)

def run_status():
    head("STATUS")
    cfg = load_config(); d = dirs()
    info(f"User       : {cfg.get('username','?')}")
    info(f"Token      : {'set' if cfg.get('token') else 'not set'}")
    info(f"Storage    : {d['root']}")
    if d["repos"].exists():
        zips = list(d["repos"].glob("*.zip"))
        total = sum(z.stat().st_size for z in zips)
        ok(f"{len(zips)} zips, {human_size(total)}")
    if d["state"].exists():
        try:
            st = json.loads(d["state"].read_text())
            info(f"Last run   : {st.get('last_run','?')}")
            info(f"Known repos: {len(st.get('repos',{}))}")
        except Exception: pass

def run_where():
    b = base_path()
    print(col(f"\n  Storage folder:  {b}\n", C.B))
    for sub in ("repos","working","logs"):
        p = b / sub
        mark = col("✔", C.GRN) if p.exists() else col("·", C.D)
        print(f"    {mark}  {p}")
    print()

def write_report(kind, summary):
    d = dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = d["logs"] / f"report_{kind}_{ts}.txt"
    counts = {}
    for _, s in summary: counts[s] = counts.get(s, 0) + 1
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"BADHON-X {kind} {datetime.now()}\n{'='*45}\n")
        f.write(f"Total: {len(summary)}\n\n")
        for k, v in counts.items(): f.write(f"{k:10}: {v}\n")
        f.write("\n")
        for n, s in summary: f.write(f"{s:10}  {n}\n")
    rule()
    for k, v in counts.items():
        print(f"  {col(k, C.B):22} {v}", flush=True)
    info(f"Zips   → {d['repos']}")
    info(f"Local  → {d['working']}")
    info(f"Report → {path}")

def main():
    p = argparse.ArgumentParser(
        prog="badhon-x",
        description="BADHON-X premium GitHub backup tool for Termux",
        add_help=False,
    )
    p.add_argument("--update",  action="store_true")
    p.add_argument("--upgrade", action="store_true")
    p.add_argument("--new",     action="store_true")
    p.add_argument("--verify",  action="store_true")
    p.add_argument("--status",  action="store_true")
    p.add_argument("--where",   action="store_true")
    p.add_argument("--set-path",action="store_true")
    p.add_argument("--login",   action="store_true")
    p.add_argument("--logout",  action="store_true")
    p.add_argument("-h","--help",action="store_true")
    p.add_argument("--version", action="store_true")
    args = p.parse_args()

    if args.help:
        banner(); print(HELP_BANNER); return
    if args.version:
        print(f"BADHON-X v{VERSION}"); return

    banner()

    if args.logout:   do_logout(); return
    if args.login:    do_login();  return
    if args.set_path: do_set_path(); return
    if args.where:    run_where(); return
    if args.status:   run_status(); return

    ensure_storage_prompt()

    token = get_token()
    if not token: return
    cfg = load_config(); user = cfg.get("username","")
    if not user:
        try:
            r = requests.get("https://api.github.com/user",
                             headers={"Authorization": f"token {token}"},
                             timeout=30)
            if r.status_code == 200:
                user = r.json().get("login","user")
                cfg["username"] = user; save_config(cfg)
        except Exception:
            user = "user"

    if args.verify: run_verify(); return

    if args.new and (args.update or args.upgrade):
        run_update(user, token, force_zip=args.upgrade, only_new=False)
    elif args.new:
        run_update(user, token, force_zip=False, only_new=True)
    elif args.upgrade:
        run_update(user, token, force_zip=True, only_new=False)
    elif args.update:
        run_update(user, token, force_zip=False, only_new=False)
    else:
        run_full(user, token)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Interrupted. Rerun anytime.")
    except Exception as e:
        err(f"{type(e).__name__}: {e}")

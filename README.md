
██████╗░░█████╗░██████╗░██╗░░██╗░█████╗░███╗░░██╗██╗░░██╗
██╔══██╗██╔══██╗██╔══██╗██║░░██║██╔══██╗████╗░██║╚██╗██╔╝
██████╦╝███████║██║░░██║███████║██║░░██║██╔██╗██║░╚███╔╝░
██╔══██╗██╔══██║██║░░██║██╔══██║██║░░██║██║╚████║░██╔██╗░
██████╦╝██║░░██║██████╔╝██║░░██║╚█████╔╝██║░╚███║██╔╝╚██╗
╚═════╝░╚═╝░░╚═╝╚═════╝░╚═╝░░╚═╝░╚════╝░╚═╝░░╚══╝╚═╝░░╚═╝

### Premium GitHub Backup Tool for Termux

**Every repo, every dot-file, every byte, backed up forever.**

</div>

## Highlights

| | Feature |
|---|---|
| 🔐 | No credentials in the repository |
| 📁 | Custom storage path, pick any folder |
| 📦 | One ZIP per repo, dot-files guaranteed |
| ⚡ | Update pulls latest without re-cloning |
| 🆕 | New flag auto-detects new or forked repos |
| 🛡 | Force-push safe, submodule aware, LFS aware, auto-repair |
| 📊 | Live progress bars for every repo and every zip |
| 🧪 | Verify audits every zip |

## Install

```bash
git clone https://github.com/Badhon-00/badhon-x.git
cd badhon-x
bash install.sh
badhon-x --login
```
## Usage
badhon-x                    Full backup
badhon-x --update           Pull latest, no re-clone
badhon-x --upgrade          Pull latest and re-zip all
badhon-x --new              Only new, forked or missing
badhon-x --update --new     Daily driver
badhon-x --verify           Validate every zip
badhon-x --status           Show stats
badhon-x --set-path         Choose custom storage folder
badhon-x --where            Print current storage folder
badhon-x --login            Save or replace token
badhon-x --logout           Delete token from device

## NOTICE!!
Hi, I am Badhon. I built this tool because I know how scary it feels when your GitHub account is suspended/flagged  your whole work life is gone and you have no copy of it.

I want you to know three things before you use it.

First, I do not take your data. BADHON-X runs completely on your phone. Your token, your repositories, your files, your username, nothing ever leaves your device except the requests that go directly to GitHub's own servers. There is no analytics, no tracking, no server of mine anywhere in the code. You can read every line and confirm this yourself.

Second, I do not log anything. There is no logging service. The reports you see in the logs folder are plain text files that only exist on your phone and only you can read them.

Third, I built this for safety, not for access. In case something ever happens to your GitHub account, whether it is a suspension, a lockout, a lost password, or a hack, this tool is your way back. As long as you have your backup folder, you have all your code. You can recreate every repository from the zips. Nothing is lost.

If you want to be extra safe, here is what I recommend:

Fork the repository on GitHub first, then clone your own fork to your phone and install from there. This way if anything ever happens to my original repo, you still have your fork, and you know exactly what code you are running because it is your own copy.

I also recommend that you open the source files and read them once. It takes five minutes and it is the best way to trust any tool that handles your tokens.

Thank you for using BADHON-X. I hope you never need it, but if you do, I am glad it is there for you.

Badhon-00


## Privacy
Read the full policy in PRIVACY.md.

In short: no tracking, no telemetry, no server, no data collection. Token is stored on your device only, with file permissions 600. Delete it anytime with badhon-x --logout.

## License and Copyright
MIT License. See LICENSE and COPYRIGHT.md.

Copyright (c) 2025 Badhon-00

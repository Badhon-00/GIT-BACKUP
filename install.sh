#!/data/data/com.termux/files/usr/bin/bash
set -e

CYAN='\033[36m'
GREEN='\033[32m'
RED='\033[31m'
NC='\033[0m'

printf "${CYAN}"
cat << 'EOF'
   ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗   ██╗  ██╗
   ██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔═══██╗████╗  ██║   ╚██╗██╔╝
   ██████╔╝███████║██║  ██║███████║██║   ██║██╔██╗ ██║    ╚███╔╝
   ██╔══██╗██╔══██║██║  ██║██╔══██║██║   ██║██║╚██╗██║    ██╔██╗
   ██████╔╝██║  ██║██████╔╝██║  ██║╚██████╔╝██║ ╚████║   ██╔╝ ██╗
   ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝  ╚═╝
EOF
printf "${NC}\n"

pkg update -y >/dev/null 2>&1 || true
pkg install -y python git curl zip unzip termux-api >/dev/null 2>&1 || true

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
fi

if [ -f "badhon_x.py" ]; then
    chmod +x badhon_x.py
fi

if [ -f "badhon-x" ]; then
    install -Dm755 badhon-x "$PREFIX/bin/badhon-x"
else
    cat << 'WRAPPER' > "$PREFIX/bin/badhon-x"
#!/data/data/com.termux/files/usr/bin/bash
python "$HOME/badhon_x.py" "$@"
WRAPPER
    chmod +x "$PREFIX/bin/badhon-x"
fi

echo -e "${GREEN}✔  Installed successfully! Run: badhon-x${NC}"

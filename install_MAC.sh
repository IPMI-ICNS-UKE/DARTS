#!/usr/bin/env bash
# install_darts.sh  — one-shot installer for the DARTS pipeline on macOS ≥ 10.15 (Intel)

set -euo pipefail

############################################
# Configurable bits — tweak if you like
ENV_NAME="DARTS"
PY_VERSION="3.10.0"
PY_PACKAGES=(
  matplotlib stardist trackpy tomli tensorflow alive-progress
  openpyxl pystackreg tkcalendar tomlkit simpleitk-simpleelastix
  python-bioformats
)
PROFILE_FILE="${HOME}/.zshrc"   # change to ~/.bash_profile if you use Bash
############################################

echo "🔍 Verifying conda …"
if ! command -v conda &>/dev/null ; then
  echo "❌  Conda not found. Install Anaconda/Miniconda first:"
  echo "    https://docs.anaconda.com/free/anaconda/install/"
  exit 1
fi

# Conda must be initialised for non-interactive shells
source "$(conda info --base)/etc/profile.d/conda.sh"

if conda env list | grep -qE "^${ENV_NAME}\s" ; then
  echo "✅  Conda env '${ENV_NAME}' already exists."
else
  echo "⏳ Creating conda env '${ENV_NAME}' (Python ${PY_VERSION}) …"
  conda create -y -n "${ENV_NAME}" "python=${PY_VERSION}"
fi

echo "⚙️  Activating env '${ENV_NAME}' …"
conda activate "${ENV_NAME}"

echo "📦 Installing Python requirements …"
python -m pip install -U pip
python -m pip install "${PY_PACKAGES[@]}"

echo "👉 Checking for Java Runtime …"
if ! command -v java &>/dev/null ; then
  echo "⏬ Java not found — installing latest OpenJDK via Homebrew."
  # Install Homebrew if it’s missing
  if ! command -v brew &>/dev/null ; then
    echo "➕ Homebrew missing; installing it first (non-interactive)."
    NONINTERACTIVE=1 /bin/bash -c \
      "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # shellenv adds brew to PATH for the *current* shell
    eval "$(/usr/libexec/java_home >/dev/null 2>&1 || true)"
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
  fi
  brew install openjdk
fi

echo "🔧 Setting JAVA_HOME …"
JAVA_HOME_PATH="$(/usr/libexec/java_home)"
echo "    Found Java at ${JAVA_HOME_PATH}"
# Persist for future shells if not already present
if ! grep -q "JAVA_HOME" "${PROFILE_FILE}" ; then
  {
    echo ""
    echo "# >>> Added by install_darts.sh >>>"
    echo "export JAVA_HOME=\"${JAVA_HOME_PATH}\""
    echo "export PATH=\"\$JAVA_HOME/bin:\$PATH\""
    echo "# <<< End install_darts.sh <<<"
  } >> "${PROFILE_FILE}"
  echo "    ℹ️  JAVA_HOME appended to ${PROFILE_FILE}"
fi
export JAVA_HOME="${JAVA_HOME_PATH}"
export PATH="${JAVA_HOME}/bin:${PATH}"

echo ""
echo "🎉  DARTS installation finished!"
echo "➡️   Next steps:"
echo "   • Open a **new** terminal or run 'source ${PROFILE_FILE}'"
echo "   • Activate the environment:    conda activate ${ENV_NAME}"
echo "   • Start using the DARTS tools. Happy analysing! 🍀"
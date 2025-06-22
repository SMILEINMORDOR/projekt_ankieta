#!/bin/bash

# 1. Usuń CAŁE stare środowisko Python
rm -rf /tmp/8ddb1d54ab37833/antenv
rm -rf /home/site/wwwroot/antenv

# 2. Instalacja WYMAGANYCH zależności systemowych
apt-get update && apt-get install -y \
    unixodbc-dev \
    g++ \
    build-essential \
    libodbc1 \
    odbcinst1debian2

# 3. Instalacja Pythonowych zależności Z POMINIĘCIEM CACHE
python -m pip install --upgrade pip
python -m pip cache purge
python -m pip install --no-cache-dir --force-reinstall -r requirements.txt

# 4. WERYFIKACJA INSTALACJI
echo "### SPRAWDZAM PYODBC ###"
python -c "import pyodbc; print(f'\nSUKCES: pyodbc {pyodbc.version} działa poprawnie\n')" || {
    echo "### BŁĄD: pyodbc NIEZAINSTALOWANY ###";
    pip debug --verbose;
    exit 1;
}

# 5. Uruchomienie aplikacji
exec gunicorn --bind 0.0.0.0:8000 --timeout 600 --log-level debug app:app

#!/bin/bash

# 1. Instalacja wymaganych pakietów systemowych
apt-get update && apt-get install -y \
    unixodbc-dev \
    g++ \
    odbcinst1debian2 \
    libodbc1 \
    odbcinst

# 2. Czyszczenie środowiska i instalacja Python
rm -rf /tmp/8ddb1d54ab37833/antenv  # Usuń stare środowisko
python -m pip install --upgrade pip
python -m pip cache purge

# 3. Instalacja zależności z wymuszeniem
python -m pip install --no-cache-dir -r requirements.txt --force-reinstall

# 4. Weryfikacja pyodbc
python -c "import pyodbc; print(f'pyodbc {pyodbc.version} installed')" || exit 1

# 5. Uruchomienie aplikacji
exec gunicorn --bind 0.0.0.0:8000 --timeout 600 app:app

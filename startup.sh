#!/bin/bash

# 1. Instalacja zależności systemowych
apt-get update && apt-get install -y \
    unixodbc-dev \
    g++ \
    odbcinst1debian2 \
    libodbc1 \
    odbcinst

# 2. Czyszczenie cache pip i instalacja pakietów
python -m pip install --upgrade pip
python -m pip cache purge
python -m pip install --no-cache-dir -r requirements.txt

# 3. Weryfikacja instalacji pyodbc
python -c "import pyodbc; print(f'pyodbc {pyodbc.version} installed successfully')" || exit 1

# 4. Uruchomienie aplikacji z dodatkowymi parametrami
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --timeout 600 \
    --workers 1 \
    --log-level debug \
    app:app

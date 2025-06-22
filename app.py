from flask import Flask, request, render_template, redirect, url_for, make_response
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import openpyxl
from openpyxl.styles import Font
from io import BytesIO

# Ładowanie zmiennych środowiskowych
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'tajny-klucz-dla-developmentu')

# Konfiguracja bazy danych
DB_CONFIG = {
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_NAME'),
    'username': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Sprawdzenie wymaganych zmiennych środowiskowych
required_env_vars = ['DB_SERVER', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
for var in required_env_vars:
    if not os.getenv(var):
        raise RuntimeError(f'Wymagana zmienna środowiskowa {var} nie jest ustawiona')

# Tworzenie połączenia z bazą danych
connection_string = f"mssql+pymssql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['server']}/{DB_CONFIG['database']}"
engine = create_engine(connection_string)

@app.route('/', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        try:
            # Pobieranie danych z formularza
            pijesz_kawe = request.form.get('pijesz_kawe', '')

            # Przetwarzanie marek kawy
            marki = request.form.getlist('marki')
            if 'Inne' in marki:
                marki.remove('Inne')
            marki_inne = request.form.get('marki_inne_text', '')
            if marki_inne.strip():
                marki.append(marki_inne.strip())
            marki_str = ', '.join(marki) if marki else None

            # Przetwarzanie rodzajów kawy
            rodzaje = request.form.getlist('rodzaje')
            if 'Inne' in rodzaje:
                rodzaje.remove('Inne')
            rodzaje_inne = request.form.get('rodzaje_inne_text', '')
            if rodzaje_inne.strip():
                rodzaje.append(rodzaje_inne.strip())
            rodzaje_str = ', '.join(rodzaje) if rodzaje else None

            # Zapisywanie do bazy danych
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO odpowiedzi_kawa (pijesz_kawe, marki, rodzaje, data_wypelnienia)
                    VALUES (:pijesz_kawe, :marki, :rodzaje, GETDATE())
                """), {
                    "pijesz_kawe": pijesz_kawe,
                    "marki": marki_str,
                    "rodzaje": rodzaje_str
                })
                conn.commit()

            return redirect(url_for('thank_you'))

        except Exception as e:
            app.logger.error(f'Błąd podczas zapisu do bazy: {str(e)}')
            return render_template('error.html', error_message="Wystąpił błąd podczas zapisywania odpowiedzi"), 500

    return render_template('index.html')

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/wyniki')
def wyniki():
    try:
        with engine.connect() as conn:
            # Pobierz podstawowe dane
            result = conn.execute(text("SELECT pijesz_kawe, marki, rodzaje FROM odpowiedzi_kawa"))
            rows = result.fetchall()

            # Pobierz daty wypełnienia dla wykresu trendu
            trend_result = conn.execute(text("SELECT CONVERT(date, data_wypelnienia) as data FROM odpowiedzi_kawa ORDER BY data_wypelnienia"))
            trend_rows = trend_result.fetchall()

        # Przetwarzanie wyników
        pijesz_kawe_list = [row[0] for row in rows if row[0]]
        marki_list = []
        rodzaje_list = []
        trend_dates = []

        for row in rows:
            if row[1]:
                marki_list.extend([m.strip() for m in row[1].split(',') if m.strip()])
            if row[2]:
                rodzaje_list.extend([r.strip() for r in row[2].split(',') if r.strip()])

        for row in trend_rows:
            if row[0]:
                trend_dates.append(str(row[0]))

        # Przygotowanie danych dla wykresu trendu
        trend_data = {}
        for date in trend_dates:
            trend_data[date] = trend_data.get(date, 0) + 1

        def count_items(items):
            counts = {}
            for item in items:
                counts[item] = counts.get(item, 0) + 1
            return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

        data = {
            'pijesz_kawe': count_items(pijesz_kawe_list),
            'marki': count_items(marki_list),
            'rodzaje': count_items(rodzaje_list),
            'odpowiedzi': trend_data
        }

        return render_template('wyniki.html', data=data)

    except Exception as e:
        app.logger.error(f'Błąd podczas pobierania wyników: {str(e)}')
        return render_template('error.html', error_message="Wystąpił błąd podczas ładowania wyników"), 500

@app.route('/export_excel')
def export_excel():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    pijesz_kawe, 
                    marki, 
                    rodzaje, 
                    CONVERT(varchar, data_wypelnienia, 120) as data_wypelnienia
                FROM odpowiedzi_kawa
                ORDER BY data_wypelnienia
            """))
            rows = result.fetchall()

        # Tworzenie pliku Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Wyniki ankiety"

        # Nagłówki
        headers = ["Czy pije kawę", "Marki", "Rodzaje", "Data wypełnienia"]
        ws.append(headers)

        # Formatowanie nagłówków
        for cell in ws[1]:
            cell.font = Font(bold=True)

        # Dane
        for row in rows:
            ws.append(row)

        # Zapisz do bufora
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        # Zwróć plik
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=wyniki_ankiety.xlsx'
        return response

    except Exception as e:
        app.logger.error(f'Błąd podczas eksportu do Excela: {str(e)}')
        return render_template('error.html', error_message="Wystąpił błąd podczas eksportu danych"), 500

if __name__ == '__main__':
    app.run(debug=True)
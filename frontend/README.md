# Streamlit frontend

## Uruchomienie (Windows / PowerShell)

1. Wejdź do katalogu projektu (tam gdzie jest `frontend/`).
2. Zainstaluj zależności:

```bash
python -m pip install -r frontend/requirements.txt
```

3. Ustaw klucz API (opcje):

- **A)** plik `.env` w katalogu głównym projektu:

```env
OPENAI_API_KEY=twoj_klucz
```

- **B)** zmienna środowiskowa w PowerShell:

```powershell
$env:OPENAI_API_KEY="twoj_klucz"
```

4. Uruchom aplikację:

```bash
streamlit run frontend/app.py
```

## Co potrafi aplikacja

- Generuje quiz (temat / trudność / liczba pytań)
- Pozwala odpowiedzieć przez UI
- Pokazuje wynik liczony lokalnie
- Opcjonalnie: analiza odpowiedzi przez AI (checkbox w konfiguracji)


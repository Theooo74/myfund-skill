# myfund-portfolio skill

Skill do pobierania i analizy danych portfeli inwestycyjnych z platformy [myFund.pl](https://myfund.pl) przez jej API.

**Autor:** Marcin Golonka — [kontakt@mgolonka.pl](mailto:kontakt@mgolonka.pl)

## Co robi

- Pobiera dane dla jednego lub wielu portfeli w jednym wywołaniu
- Pobiera historię portfela (wartość, zysk, stopa zwrotu w czasie)
- Oblicza dzienne zmiany i trendy 7-dniowe
- Generuje czytelne podsumowania portfeli

## Struktura

```
myfund-portfolio/
├── SKILL.md                  # Definicja skilla i dokumentacja użycia
├── scripts/
│   ├── get_portfolio.py      # Pobieranie surowych danych z API
│   └── daily_summary.py      # Generowanie dziennego podsumowania z trendem 7d
└── references/               # Dodatkowe materiały referencyjne
```

## Wymagania

- Python 3.8+
- Biblioteka `requests` (`pip install requests`)
- Aktywne konto na myFund.pl z kluczem API

## Instalacja skilla

### 1. Sklonuj repozytorium

### 2. Zainstaluj zależności

```bash
pip install requests
```

### 3. Skonfiguruj klucz API

Ustaw zmienną środowiskową z kluczem API myFund.pl:

```bash
export MYFUND_API_KEY="twoj_klucz_api"
```

Aby zmienna była dostępna stale, dodaj ją do `~/.zshrc` lub `~/.bashrc`:

```bash
echo 'export MYFUND_API_KEY="twoj_klucz_api"' >> ~/.zshrc
source ~/.zshrc
```

### 4. Dostosuj nazwy portfeli

Otwórz `scripts/daily_summary.py` i podmień listę `PORTFOLIOS` na nazwy swoich portfeli z myFund.pl:

```python
PORTFOLIOS = ["NazwaPortfela1", "NazwaPortfela2", "NazwaPortfela3"]
```

### 5. (Opcjonalnie) Zarejestruj skill w GitHub Copilot

Skopiuj katalog `myfund-portfolio/` do katalogu skillów swojego agenta, np.:

```bash
cp -r myfund-portfolio/ ~/.moltis/skills/
```

## Użycie

### Pobieranie danych jednego portfela

```bash
python3 scripts/get_portfolio.py --portfel "NazwaPortfela" --format json
```

### Pobieranie danych wielu portfeli

```bash
python3 scripts/get_portfolio.py --portfel "Portfel1,Portfel2" --format json
```

### Dzienne podsumowanie z trendem 7-dniowym

```bash
python3 scripts/daily_summary.py
```

Przykładowe wyjście:

```
Daily portfolio summary for 2026-03-25

Alfa:
  Wartość: 12500.00 PLN
  Zmiana dzienna: +0.01%
  Trend tygodniowy (7d): +0.50%

Beta:
  Wartość: 8000.00 PLN
  Zmiana dzienna: +0.02%
  Trend tygodniowy (7d): +0.35%
```

## Bezpieczeństwo

- Klucz API **nigdy** nie jest wpisany na stałe w kodzie — odczytywany wyłącznie ze zmiennej środowiskowej `MYFUND_API_KEY`
- Klucz nie jest przekazywany jako parametr URL ani logowany

## Autor

Marcin Golonka — [kontakt@mgolonka.pl](mailto:kontakt@mgolonka.pl)

## Licencja

MIT

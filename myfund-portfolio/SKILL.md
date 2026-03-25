---
name: myfund-portfolio
description: Pobieranie i analiza danych portfeli inwestycyjnych z myFund.pl — obsługa wielu portfeli, historia wartości, dzienne zmiany i trendy 7-dniowe
author: Marcin Golonka <kontakt@mgolonka.pl>
---

## Opis Skilla

### Co robi

Skill `myfund-portfolio` umożliwia pobieranie i analizę danych portfeli inwestycyjnych z platformy myFund.pl. Pozwala na:
- Pobranie danych dla wielu portfeli jednocześnie
- Pobieranie historycznych danych portfela
- Obliczanie dziennych zmian i trendów 7-dniowych
- Generowanie podsumowań portfeli z analizą wydajności

### Jakie wartości pobiera

#### Dane główne portfela
- **wartosc** - aktualna wartość portfela w PLN
- **liczbaJednostek** - liczba jednostek uczestnictwa
- **zmianaDzienna** - zmiana wartości z poprzedniego dnia (%)
- **zmiana** - zmiana wartości od początku inwestycji (%)
- **zysk** - zysk w PLN od początku inwestycji
- **zyskDzienny** - zysk z ostatniego dnia w PLN
- **data** - data ostatniej aktualizacji

#### Dane historyczne
- **zyskWCzasie** - historia zysku w PLN po datach
- **wartoscWCzasie** - historia wartości portfela po datach
- **wkladWCzasie** - historia wkładów inwestorów
- **stopaZwrotuWCzasie** - historia stopy zwrotu (%)
- **zmianaDzienna** - zmiana codziennie

#### Struktura portfela
- **tickers** - lista instrumentów w portfelu z:
  - Nazwą i tickerem
  - Ceną zamknięcia
  - Liczbą jednostek
  - Typem (np. Treasury bonds - Obligacje oszczędnościowe)
  - Ryzykiem (Very low risk, itd.)
  - Udziałem w portfelu (%)
  - Datą rozpoczęcia inwestycji
  - Zyskiem
  
- **struktura** - agregacja wartości po typach instrumentów
- **strukturaWalory** - udziały procentowe poszczególnych instrumentów

#### Metryki
- **benchName** - nazwa benchmarku (np. Inflation Poland)
- **benchWCzasie** - wartości benchmarku w czasie
- **udzial** - całkowity udział portfela (%)

### Jak używać

#### Składnia

```bash
# Pobranie danych dla jednego portfela
python3 get_portfolio.py --portfel "Alfa" --format json

# Pobranie danych dla wielu portfeli
python3 get_portfolio.py --portfel "Alfa,Beta,Gamma" --format json

# Jeśli nie podasz portfela, domyślnie pobiera "Alfa"
python3 get_portfolio.py --format json
```

#### Wyjście

Zwraca JSON z kluczami portfeli, po jednym obiekcie danych API (lub błędy).

### Uwaga dotycząca filtrowania po dacie

- API zwraca dane historyczne; nie wszystkie portfele udostępniają bieżące wartości w jednym wywołaniu
- Jeśli potrzebujesz dziennych/tygodniowych zmian, należy filtrować lokalnie po datach dostępnych w odpowiedziach
- Dla agregacji danych użyj skryptu `daily_summary.py`, który oblicza zmiany dzienne i trendy 7-dniowe

### Bezpieczeństwo

- Klucz API nie jest logowany ani przekazywany jawnie w poleceniach
- Odczytywany jest ze zmiennej środowiskowej `MYFUND_API_KEY`
- Nie jest przesyłany w parametrach URL

### Ograniczenia i uwagi

- API zwraca dane historyczne aż do daty bieżącej
- Dane mogą się opóźniać w stosunku do rzeczywistej wartości portfela
- Historia obejmuje wszystkie zmiany wartości portfela i dokonane inwestycje
- Dla kompletnej analizy trendu rekomenduje się korzystanie z `daily_summary.py`

### Przykładowe wyjście

Dla portfela "Alfa" z dnia 2026-03-18:

```json
{
  "Alfa": {
    "status": {
      "code": "0",
      "text": "OK!"
    },
    "portfel": {
      "nazwa": "Portfolio in total",
      "waluta": "PLN",
      "wartosc": "12500.00",
      "liczbaJednostek": 125.00,
      "zmianaDzienna": 0.01,
      "zmiana": 5.2,
      "zysk": 617.50,
      "zyskDzienny": 1.25,
      "data": "2026-03-18",
      "benchName": "Inflation Poland"
    },
    "tickers": [
      {
        "nazwa": "EDO0430 (2024-04-01) (6.00%)",
        "typ": "Treasury bonds",
        "wartosc": "5250.00",
        "udzial": "42.00%",
        "zmiana": "6.00",
        "zysk": "300.00",
        "ryzyko": "Very low risk",
        "liczbaJednostek": "50"
      },
      {
        "nazwa": "COI0430 (2024-04-01) (5.50%)",
        "typ": "Treasury bonds",
        "wartosc": "7250.00",
        "udzial": "58.00%",
        "zmiana": "4.50",
        "zysk": "317.50",
        "ryzyko": "Very low risk",
        "liczbaJednostek": "70"
      }
    ],
    "struktura": {
      "Treasury bonds": "12500.00"
    },
    "zyskWCzasie": {
      "2026-03-16": "612.50",
      "2026-03-17": "615.00",
      "2026-03-18": "617.50"
    },
    "wartoscWCzasie": {
      "2026-03-16": "12495.00",
      "2026-03-17": "12497.50",
      "2026-03-18": "12500.00"
    }
  }
}
```

### Dostępne skrypty

#### `get_portfolio.py`
Bezpośrednie pobieranie danych portfela z API myFund.pl

#### `daily_summary.py`
Generuje dzienne podsumowanie portfeli z:
- Aktualną wartością
- Zmianą dzienną (%)
- Trendem 7-dniowym (%)
- Historią zmian

Przykład użycia:
```bash
python3 daily_summary.py
```

Przykładowe wyjście:
```
Daily portfolio summary for 2026-03-18

Alfa:
  Wartość: 12500.00 PLN
  Zmiana dzienna: +0.01%
  Trend tygodniowy (7d): +0.50%

Beta:
  Wartość: 8000.00 PLN
  Zmiana dzienna: +0.02%
  Trend tygodniowy (7d): +0.35%

Gamma:
  Wartość: 5000.00 PLN
  Zmiana dzienna: -0.01%
  Trend tygodniowy (7d): +0.60%
```

### Wymagane zmienne środowiskowe

```bash
export MYFUND_API_KEY="your_api_key_here"
```

Następnie uruchom skrypty w tym samym terminalu lub dodaj zmienną do pliku `.bashrc` aby była dostępna stale.

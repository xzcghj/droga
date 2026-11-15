# ADR-003: Metryka sprawiedliwości — minimax z rozstrzyganiem sumą

- **Status:** zaakceptowana
- **Data:** 2026-11-15

## Kontekst
Trzeba uszeregować kandydatów na miejsce spotkania tak, aby nikt nie był wyraźnie pokrzywdzony.

## Rozważane opcje
1. Suma (średnia) czasów — premiuje miejsca blisko większości, krzywdzi osoby z daleka.
2. Wariancja czasów — może premiować miejsca daleko od wszystkich (wszyscy jadą równie długo).
3. Minimax — minimalizujemy najdłuższy dojazd.

## Decyzja
Minimax; remis rozstrzyga suma czasów, potem nazwa (deterministycznie). Dodatkowo raportujemy różnicę max–min jako „odznakę sprawiedliwości”.

## Konsekwencje
Prosta, intuicyjna i łatwa do wyjaśnienia użytkownikowi („najdłuższy dojazd: 18 min”).

# Farverig Fakturasystem

Dansk webapp til fakturakladder, udstedelse, PDF og fakturaoversigt.

## Aktuel status
Kildekoden er lagt i GitHub. **Ikke produktionsklar og ikke offentligt hostet.** Dette er en første fungerende implementering, som skal gennemgås og testes før brug med rigtige kunder.

**Implementeret:** Login, kladder, fakturalinjer, 0/25 % moms, SQLite, atomisk fakturanummerering, kopiering, firmaindstillinger og PDF-download.

**Mangler før endelig ibrugtagning:** Google Drive-integration, logo-upload, robust PDF-layout med fuld Unicode, kreditnotaer, backup/restore, adgangssikring og test af hele brugerflowet. Momsfritagelse og fakturakrav skal kontrolleres konkret. Systemet er ikke et bogføringssystem.

## Lokal start
Installer Python 3.12. Kør:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export APP_PASSWORD='vælg-en-lang-unik-adgangskode'
export APP_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
uvicorn app:app --host 127.0.0.1 --port 8000
```
På Windows skal miljøvariabler sættes med PowerShell og venv aktiveres med `.venv\\Scripts\\Activate.ps1`.

Åbn http://127.0.0.1:8000. Kør tests med `python -m unittest discover -s tests -v`.

## VIGTIGT: fakturanummer
Databasen starter på faktura 1. Hvis seneste udstedte faktura er nr. 131, **skal næste nummer sættes til 132 før første udstedelse**. Stop appen og kør:
```bash
python -c "import sqlite3; c=sqlite3.connect('data/invoices.sqlite3'); c.execute('UPDATE sequence SET next_number=132 WHERE id=1'); c.commit(); c.close()"
```
Kontrollér først, at 132 faktisk er næste ledige nummer.

## Hosting
Dockerfile er inkluderet til deployment på en server med HTTPS, stærke hemmeligheder og **persistent, sikker lagring monteret på /data**. Deploy ikke på en platform med flygtig disk: fakturaer og nummersekvens kan ellers forsvinde. GitHub er kildekodelager, ikke hosting. Hosting kræver separat udbyderkonto og opsætning.

## Sikkerhed
Repositoryet er offentligt. Commit aldrig fakturaer, kundeoplysninger, databaser, tokens eller adgangskoder. Lav krypterede, verificerede backups. Én adgangskode er ikke tilstrækkelig til alle produktionsscenarier; sæt ikke appen offentligt online uden yderligere sikkerhedsgennemgang.

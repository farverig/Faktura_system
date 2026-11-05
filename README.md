# Farverig Fakturasystem

## Åbn hjemmesiden
**GitHub Pages:** https://farverig.github.io/Faktura_system/

Hvis linket ikke virker endnu, skal Pages aktiveres i **Settings → Pages → Build and deployment → Source: GitHub Actions**. Workflowet `.github/workflows/pages.yml` udgiver automatisk de statiske filer ved ændringer på `main`.

## Logo
Upload dit logo til `assets/logo.png`. Se [assets/README.md](assets/README.md). Det vises automatisk på hjemmesiden og på fakturaudskriften.

## GitHub Pages-version
Den statiske version ligger i `index.html`, `styles.css` og `app.js`. Den har:
- Flot responsiv fakturaoversigt
- Opret og redigér kladder
- Fakturalinjer med 0 % eller 25 % moms
- Fakturanumre og låsning af udstedte fakturaer **på den enkelte enhed**
- Udskriv / Gem som PDF via browserens udskriftsdialog
- Indstillinger og eksport/import af JSON-backup

**Vigtigt:** GitHub Pages kan ikke køre Python eller SQLite. Fakturaer og indstillinger gemmes i browserens `localStorage` på den aktuelle enhed. De synkroniseres **ikke** mellem enheder, og de kan forsvinde ved rydning af browserdata. Data er **ikke krypteret** og denne løsning har **ikke login, serverbaseret adgangskontrol eller automatisk Google Drive-upload**. Det er en prototype, ikke et produktionsklart faktura-/bogføringssystem. Brug ikke til rigtige kundeoplysninger uden passende databeskyttelse og sikker serverlagring.

**Fakturanumre:** Sæt korrekt næste fakturanummer under Indstillinger, før du udsteder en faktura. Sekvensen er kun lokal; to browsere kan udstede samme nummer. Dette er ikke egnet til egentlig fakturering på flere enheder.

## Tidligere Python-prototype
`app.py`, `requirements.txt`, `Dockerfile` og `tests/` indeholder en separat backend-prototype. Den kører **ikke** på GitHub Pages og er ikke integreret med den statiske version.

## Før produktionsbrug
Kræver sikker backend, central database med transaktionssikker nummersekvens, login, krypterede backups, korrekt revisionsspor, gennemgang af danske fakturakrav og Google Drive OAuth-integration.

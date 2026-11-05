# Farverig Fakturasystem

Et dansk fakturasystem til Farverig I/S.

## Status
Projektets GitHub-repository er nu tilsluttet. Dette er første opsætning af repositoryet, **ikke en produktionsklar udgivelse**. Applikationskoden, automatiske tests og deployment skal lægges ind og verificeres, inden der udstedes fakturaer.

## Planlagt funktionalitet
- Kladder, kunder og fakturalinjer
- Korrekt dansk momsberegning og PDF-fakturaer
- Fortløbende, unikke fakturanumre med transaktioner
- Fakturaoversigt, kopiering og arkivering
- Automatisk Google Drive-upload via OAuth
- Sikker opbevaring af adgangskoder og data uden for GitHub

## Sikkerhed
Repositoryet er offentligt. Læg **aldrig** kundedata, rigtige faktura-PDF'er, databasefiler, OAuth-tokens eller adgangskoder her. Se `.gitignore`.

## Før produktion
Der kræves end-to-end-tests, backup/restore, afprøvning af Drive-upload, adgangskontrol og validering af fakturaoplysninger og nummersekvens. Udstedte fakturaer skal bevares uændret, og eventuelle korrektioner håndteres som kreditnotaer.

## Hosting
GitHub opbevarer kildekoden, men hoster ikke en Python-backend eller en persistent fakturadatabase. En separat driftsløsning skal vælges.

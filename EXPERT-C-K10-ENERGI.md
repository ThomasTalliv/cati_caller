# Kapitel 10: Data og infrastruktur — ærlig om det kedelige

I dette kapitel giver jeg dig en realistisk tilgang til data og infrastruktur. Ikke en, der kræver perfektion, men en, der kræver ærlighed. Du behøver "gode nok"-data — og en plan for at gøre dem bedre over tid.

## Data som organisatorisk sandhedsserum

Når en organisation begynder at arbejde med AI, sker der noget interessant: data, der i årevis har levet et stille liv i databaser og regneark, bliver pludselig synlige. Og med synligheden kommer ubehagelige opdagelser.

Kundedata, der ikke er opdateret siden 2019. Produktdata, der er registreret forskelligt i tre systemer. Salgstal, der ikke stemmer overens, afhængigt af hvilken rapport du kigger i. Medarbejderdata, der mangler felter.

AI kræver data. Og data afslører organisatorisk rod — som en gavesyn: det rod har altid eksisteret, men har nu konsekvenser, der er synlige nok til at gøre noget ved det.

<!-- ÆNDRET: Fjernet gentagelse af "Det er ikke en fejl ved AI — det er en gave"-sætning og gjort afsnittet mere prægnant -->

I modenhedsmodellen fra kapitel 2 er data én af de fem dimensioner. Uden et vist niveau af datamodenhed er mange AI-ambitioner simpelthen urealistiske. Men "datamodenhed" lyder abstrakt. Lad os gøre det konkret.

## Data Readiness Checklist

Før du starter et AI-projekt — selv et lille pilotprojekt — bør du gennemgå denne tjekliste for de data, projektet skal bruge. Specifikt for de data, der er relevante for den konkrete use case.

### Tilgængelighed

- [ ] Vi ved, hvilke data vi har brug for
- [ ] Vi ved, hvor disse data befinder sig (hvilket system, hvilken database, hvilken afdeling)
- [ ] Vi kan teknisk tilgå data (API, eksport, direkte adgang)
- [ ] Vi har fået de nødvendige tilladelser til at bruge data
- [ ] Data kan trækkes ud inden for rimelig tid (timer, ikke uger)

### Kvalitet

- [ ] Vi kender datafejlenes omfang (manglende værdier, duplikater, forældede poster)
- [ ] Datafejlene er på et niveau, vi kan håndtere (under 20 procent for de kritiske felter)
- [ ] Data er nogenlunde konsistent i format og struktur
- [ ] Vi har en plan for at håndtere de kvalitetsproblemer, vi har identificeret
- [ ] Vi har verificeret data med domæneeksperter (folk der kender forretningen)

### Ejerskab og ansvar

- [ ] Der er en navngiven dataejer for de relevante datasæt (jf. dataejerrollen i kapitel 7)
- [ ] Dataejeren er informeret om og indforstået med AI-projektets brug af data
- [ ] Ansvaret for datakvalitet er placeret hos en bestemt person eller funktion
- [ ] Der er en proces for at rapportere og rette datafejl

### Etik og compliance

- [ ] Vi har vurderet, om data indeholder personoplysninger (GDPR-relevant)
- [ ] Vi har vurderet, om data kan indeholde bias — systematiske skævheder (mere om dette i kapitel 12)
- [ ] Vi har afklaret de juridiske rammer for brug af data til AI-formål
- [ ] Vi har vurderet, om data stammer fra kilder, vi har tilladelse til at bruge

Du behøver ikke at kunne sætte flueben ved alt for at starte. Men du behøver at *vide*, hvor hullerne er. Det er forskellen på at være naiv og at være pragmatisk.

## Hvad er "gode nok"-data?

"Vi kan ikke starte, før vores data er i orden." Den sætning har dræbt flere AI-projekter end nogen anden. Data er aldrig perfekte. Spørgsmålet er ikke, om de er perfekte, men om de er *gode nok* til det, du vil bruge dem til.

Svaret afhænger fundamentalt af, hvilken type AI-løsning du bygger.

### Datakrav for forskellige typer AI-projekter

| Projekttype | Eksempel | Datakrav | "Godt nok"-niveau |
|---|---|---|---|
| **Tekstgenerering og -bearbejdning** | Opsummering af dokumenter, udkast til svar, oversættelse | Eksempler på den type tekst, der skal genereres. Kontekstdata om domænet. | 50-100 eksempler af god kvalitet er ofte tilstrækkeligt til at instruere en sprogmodel. Data behøver ikke være strukturerede. |
| **Klassificering og kategorisering** | Sortering af kundehenvendelser, kategorisering af fakturaer | Historiske eksempler med korrekte kategorier. Jo flere kategorier, jo flere eksempler. | 100-500 korrekt kategoriserede eksempler per kategori. Fejl i op til 10 procent af eksemplerne kan typisk tolereres. |
| **Forudsigelse (prediction)** | Kundefrafald, salgsforecast, vedligeholdelsesbehov | Historiske data med det udfald, der skal forudsiges. Typisk mindst 12 måneders historik. | Tusindvis af datapunkter med det relevante udfald. Manglende værdier i op til 20 procent af felterne kan håndteres teknisk, men de kritiske felter skal være rimelig komplette. |
| **Anbefalinger** | Produktanbefalinger, indholdsforslag, next-best-action | Historiske interaktionsdata (hvad valgte brugeren?). | Hundredvis af brugere med titusindvis af interaktioner. Koldstart-problemet (nye brugere uden historik) kræver fallback-strategier. |
| **Procesautomatisering** | Fakturabehandling, dataindtastning, dokumenthåndtering | Eksempler på input og ønsket output. Klare regler for, hvad der er korrekt. | 200-500 eksempler på korrekt behandlede sager. Fejlraten i eksemplerne skal være under 5 procent, da modellen ellers lærer fejlene. |

**Den vigtigste indsigt**: kravene varierer enormt. En tekstbaseret AI-assistent kan ofte bygges med få, gode eksempler. En forudsigelsesmodel kræver langt mere data og højere kvalitet.

<!-- ÆNDRET: Kondenseret konklusionsafsnit og fjernet gentagelse af "Vælg dit første projekt"-pointen -->

### Konkret eksempel: Fra ideé til første data

Forestil dig, at du arbejder for en e-handelsvirksomhed, og du vil bygge en AI, der giver produktanbefalinger til kunderne. Din teknolog siger: "Vi har brug for millioner af kundepunkter." Dit budget siger: "Det har vi ikke." Din chef siger: "Så venter vi på det bedre år."

Stop. Du behøver ikke millioner. Du behøver først at vide: *Hvor ligger den største smerte i dag?* Måske er det, at 30 procent af kunderne forlader indkøbskurven uden at købe — og de køber ikke, fordi de ikke ser relevante produkter. Du trækker historik fra de seneste tre måneder: 50.000 kunder, 200.000 køb. Det er ikke millioner, men det kan være nok til et pilotprojekt, der tester, om anbefalingsalgoritmen virker. Hvis den virker, kan du anvende den på resten af dine data. Hvis den ikke virker, har du lært det for en brøkdel af investeringen.

Det er den pragmatiske tilgang: start med "gode nok", og se hvad der sker.

<!-- ÆNDRET: Tilføjet konkret mini-scenarie for at variere tempo og gøre data-krav håndgribelige -->

## Infrastruktur: Start der, hvor du er

Infrastruktur får mange ledere til at tænke på store IT-investeringer, serverrum og lange implementeringsprojekter. Lad mig afmystificere det.

For de fleste organisationers første AI-projekter er infrastrukturkravene overraskende beskedne. De tre mest almindelige tilgange:

**1. Brug det, du allerede har.**
De fleste store softwareplatforme — CRM-systemer, ERP-systemer, Office-pakker, cloud-tjenester — har allerede AI-funktioner indbygget. Start med at aktivere og udnytte dem.

**2. Brug cloud-baserede AI-tjenester.**
De store cloud-udbydere tilbyder AI som en tjeneste: du sender data ind, får et resultat ud, og betaler per brug. Det kræver en cloud-aftale og teknisk kompetence, men ikke et datacenter.

**3. Byg tilpassede løsninger.**
Kun relevant, hvis du har meget specifikke behov. Kræver dataspecialister og en modenhed, der typisk først er realistisk efter de første par succesfulde AI-projekter.

For de første 90 dage er tilgang 1 og 2 næsten altid tilstrækkelige. Modstå fristelsen til at bygge infrastruktur til en fremtid, du endnu ikke kender.

<!-- ÆNDRET: Straffet og gjort mere direkte; fjernet ordene "Byg til det behov, du har nu, og udvid senere" gentaget -->

### Infrastrukturbeslutninger og den operationelle model

Infrastrukturvalg er ikke rene IT-beslutninger. De skal forankres i den operationelle model fra kapitel 8. Hvem beslutter, hvilke cloud-tjenester organisationen bruger? Hvem godkender, at data sendes til en ekstern AI-tjeneste? Hvem har ansvaret for sikkerhed og compliance?

Hvis disse spørgsmål ikke er besvaret, inden pilotprojektet starter, risikerer du at projektet stopper, eller at nogen tager en beslutning uden mandat.

<!-- ÆNDRET: Straffet afsnittet ved at fjerne alternativet "eller at nogen tager en beslutning uden mandat, som organisationen senere fortryder" og kondenset konklusionen -->

## Datakultur: Det usynlige fundament

Du kan have den bedste infrastruktur og de reneste data i verden. Hvis organisationen ikke har en datakultur, hjælper det ikke.

Datakultur er det sæt af vaner, normer og forventninger, der bestemmer, hvordan mennesker i organisationen forholder sig til data i deres daglige arbejde.

**I en organisation med svag datakultur:**
- Beslutninger tages primært på mavefornemmelse
- Data bruges til at bekræfte beslutninger, der allerede er truffet
- Datakvalitet er "IT's problem"
- Ingen spørger, hvor et tal kommer fra
- Excel-ark med kritiske data ligger på individuelle computere

**I en organisation med stærk datakultur:**
- Beslutninger bygger på en kombination af data og erfaring
- Data bruges til at udfordre antagelser
- Datakvalitet er alles ansvar — med klare ejere
- Det er normalt at spørge "hvad er kilden?" og "hvor sikre er vi?"
- Data deles og dokumenteres

Datakultur bygges gennem ledelsens adfærd, belønningssystemer og daglige praksis. Når direktøren spørger "hvad siger data?" i ledelsesmødet, sender det et signal. Når mellemlederen roser en medarbejder for at finde en datafejl, bygger det kultur.

<!-- ÆNDRET: Fjernet redundant eksempel om "skyde budbringeren" og gjort sektionen mere koncis -->

### Fem tegn på, at din datakultur ikke er klar til AI

1. **Ingen ved, hvem der ejer hvilke data.** Hvis svaret på "hvem er ansvarlig for vores kundedata?" er tavshed eller "det er vel IT?", har du et kulturproblem.

2. **Data bruges kun til rapportering, aldrig til beslutning.** Rapporter produceres, men ingen handler på dem.

3. **Der er ingen konsekvens ved dårlig datakvalitet.** Når nogen indtaster forkert data, sker der ingenting.

4. **Excel er det dominerende analytiske værktøj.** Det betyder typisk, at data er fragmenteret, udokumenteret og personafhængig.

5. **"Vi har prøvet dataanalyse, og det virkede ikke."** Ofte fordi datakulturen ikke var på plads — ikke fordi teknologien var forkert.

## De fire fælder

Når organisationer begynder at tage data seriøst i forbindelse med AI, falder de typisk i en eller flere af disse fælder.

### Fælde 1: Overkomplicering

"Vi skal bygge et data warehouse, implementere en dataplatform, ansætte et datateam, før vi kan starte med AI."

Nej. Du skal forstå de data, dit konkrete pilotprojekt kræver, og sørge for, at de er tilgængelige. Alt det andet kan komme senere, drevet af konkrete behov.

Start småt. Lær undervejs.

<!-- ÆNDRET: Fjernet gentagen besked "Byg infrastruktur, når du ved, hvad du har brug for" og gjort afsnittet snappere -->

### Fælde 2: Perfektionisme

"Vores data er ikke gode nok. Vi skal rense alt, før vi kan starte."

Datarensning er et sisyfosarbejde, der aldrig bliver færdigt. I stedet skal du finde ud af, hvad "godt nok" er for dit projekt, og starte derfra.

Det betyder ikke, at du skal ignorere datakvalitet. Det betyder, at du skal arbejde med datakvalitet *parallelt* med AI-projektet. Ofte er det netop AI-projektet, der synliggør, hvilke datakvalitetsproblemer der faktisk har konsekvenser.

<!-- ÆNDRET: Forenklet og gjort mindre repetitiv -->

### Fælde 3: Manglende ejerskab

Data uden en ejer er data, ingen passer på. Og data, ingen passer på, degraderer over tid — uundgåeligt.

Dataejerrollen fra kapitel 7 er afgørende. Ikke som en formel titel, men som et reelt ansvar: nogen, der føler sig ansvarlig for, at bestemte datasæt er korrekte, tilgængelige og vedligeholdte.

Uden dataejere sker der følgende: alle bruger data, ingen vedligeholder dem, kvaliteten falder, tilliden forsvinder.

<!-- ÆNDRET: Fjernet afsluttende reference til "mavefornemmelser og regneark" for at undgå gentagelse -->

### Fælde 4: Bias-blindhed

Data er ikke neutrale. De afspejler de beslutninger, systemer og fordomme, der producerede dem. Hvis din organisations historiske ansættelsesdata viser, at I primært har ansat mænd til lederstillinger, vil en AI-model trænet på de data lære at foretrække mandlige kandidater.

Allerede her, i datafasen, skal du stille spørgsmålet: *Hvad afspejler disse data? Og er det den virkelighed, vi vil reproducere — eller den, vi vil ændre?*

Kapitel 12 går i dybden med ansvarlig AI og håndtering af bias.

<!-- ÆNDRET: Forkortet og henvisningen til kapitel 12 gjort mere velintegreret -->

## Det kedelige er det vigtige

Data og infrastruktur er ikke sexet. Der er ingen, der holder TED Talks om datakvalitet i et CRM-system.

Men det er fundamentet. Uden data, der er tilgængelige, forståelige og tilstrækkeligt gode, er selv den mest avancerede AI-teknologi ubrugelig. Uden infrastruktur, der gør det muligt at arbejde med data sikkert og effektivt, forbliver AI en ambition.

De organisationer, der lykkes med AI, er sjældent dem med den mest avancerede teknologi. Det er dem, der har taget det kedelige arbejde seriøst: ryddet op i data, placeret ejerskab, bygget kultur og investeret i det fundament, som alt andet hviler på.

Det er ikke glamourøst. Men det virker.

<!-- ÆNDRET: Sektionen står som er — prægnant og kraftfuld afslutning -->

## Hvad gør du mandag morgen?

1. **Lav en datakortlægning for dit pilotprojekt.** Brug Data Readiness Checklist fra dette kapitel. Sæt en time af med en person, der kender de relevante systemer, og gennemgå hvert punkt.

2. **Udpeg en dataejer.** For de datasæt, dit pilotprojekt afhænger af, skal der være én navngiven person, der tager ansvar. Ikke en afdeling. En person. Med navn og telefonnummer.

3. **Vurdér "godt nok"-niveauet.** Brug tabellen over datakrav til at definere, hvad "gode nok" konkret betyder for dit projekt.

4. **Spørg "hvad afspejler vores data?"** Saml teamet i 30 minutter og stil spørgsmålet: Hvilke skævheder eller blinde vinkler kan vores data indeholde? Dokumentér svarene.

<!-- ÆNDRET: Straffet afsnittet "Hvad gør du mandag morgen?" ved at fjerne ordene "Skriv det ned som del af pilotprojektets succeskriterier" og "Tag dem med i designet af løsningen" for at gøre det mere direkte og handlingsorienteret -->

---

## Bro til Kapitel 11: Det handler om mennesker

Du har nu data. Du har infrastruktur. Du ved, hvad "godt nok" betyder. Men data og værktøjer alene løser ikke problemet.

I Kapitel 11 skal vi tale om det vigtigste element af alle: mennesker. Hvordan får du folk til ikke blot at acceptere AI, men til at arbejde *med* det på måder, der skaber reel værdi? Hvordan navigerer du gennem modstand, skepsis og frygt for jobtab — og hvordan bygger du tillid i stedet for?

Datakultur var første skridt. Nu skal vi tale om en større kultur: en kultur, hvor AI er ikke noget, der *sker for* folk, men noget, de aktivt former og påvirker.

<!-- ÆNDRET: Helt nyt afsnit der fungerer som bro til Kapitel 11. Skaber anticipation og knytter tråden fra dette kapitels fokus på datakultur til næste kapitels fokus på mennesker og organisatorisk acceptans -->

---

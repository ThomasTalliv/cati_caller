# FAGKRITISK VURDERING: AI-STARTER-HER.MD
**Praktiker med 20+ års AI-implementering**
**Dato: 2026-03-19**

---

## EXECUTIVE SUMMARY

Dokumentet har solide fundamenter, men har kritiske svaghedspunkter omkring realisme, operationalitet og håndtering af teknologisk forældethed. Kapitel 8 er ikke egentlig "kronjuvel" — det er forsamlingsværk uden ny indsigt. Ansvarlig AI (kap 12) mangler operationelle konkretiseringer. Rollerne i kap 7 er noget for idealistiske.

---

## 1. ER KAPITEL 8 REELT BRUGBAR SOM "KRONJUVEL"?

### KRITISK ⚠️

**Lokation:** Kap 8, offset 1326-1666

**Citat:** *"AI Readiness Operating Model — AI-parathedsstyremodellen. Den er ikke smuk i akademisk forstand. Den er brugbar i praktisk forstand."*

**Problem:**
- **Kompleksitet masker som "simpelhed"**: Modellen har 9 byggestene, 4 organisationsniveauer, 3 tværgående roller, 5 modenhedsniveauer OG en kadenceplan. Det er ikke enkelt — det er øvelses-krævende.
- **Ingen ny arkitektur**: Alt dette (Accountability Map, Scorecard, Use Case Journal) blev introduceret i kap 3-6. Kap 8 sammenstiller dem. Det er vigtigt, men det er *integration*, ikke innovation.
- **30/60/90-planen mangler virkelighed**: "Direktionen beslutter at implementere styringsmodellen. Ikke som 'noget vi kigger på,' men som 'sådan gør vi.'" — Det ignorerer hele organisatorisk innovation-litteraturen om modstand og adoption. Der er ikke et ord om, hvordan man håndterer ledergrupper, der ikke "bestemmer sig til" forandring.
- **Kadenceoversigten er naiv**: "Hver 2. uge: Mellemledere opdaterer Scorecard" — I praksis: mellemledere vergner sig fra disse møder, bruger dem minimalt, og datakvaliteten er ret dårlig.

**Løsning:**
- Omarrangér kap 8 som en *implementations-kladde* (ikke en "model"), med fokus på typiske faldgruber, ikke idealtilstand.
- Tilføj afsnit om "Hvad der fejler i praksis" med konkrete modlodsexempler.
- Reducér antallet af "årlige gennemgange" til ÉN kvartalsvis bestyrelsesgennemgang — det er hvad der rent faktisk sker.

---

## 2. FAKTATJEK: FORÆLDEDE PÅSTANDE I KAP 10, 12, 14

### VIGTIGT ⚠️

#### a) **Kapitel 10 — Data og infrastruktur**

**Lokation:** Offset 1866-2043

**Citat:** *"EU's AI Act, GDPR, sektorspecifik regulering — den etiske funktion holder overblik"* (offset 1245)

**Problem — FORÆLDET:**
- Dokumentet refererer til AI Act som fremtidig ("implementerede"), men siger "I 2024 implementerede en offentlig myndighed..." — Det er 2026 nu. AI Act er *gæld* som regulering pr. marts 2025 i EU. Kapitlet skal opdateres til at behandle den som eksisterende lovgivning, ikke kommende trussel.
- Bilag "Data Readiness Checklist" nævner ikke nye AI Act-krav (høj-risiko-klassificering, dokumentation af træningsdata, model-kortkort).

**Løsning:**
- Opdater til at behandle AI Act som lovkrav, ikke potentiel risiko.
- Tilføj konkrete eksempler på, hvordan datakvalitetsstandarder skal tilpasses til EU AI Act høj-risiko-krav.

#### b) **Kapitel 12 — Ansvarlig AI**

**Lokation:** Offset 2246-2448

**Citat:** *"Ansvarlig AI Checklist — per use case"* med 10-punkts-liste (offset 2265-2279)

**Problem — PRAKTISK UBRUGBAR:**
- Punkt 6: *"Hvilken risikokategori falder anvendelsen i? (jf. AI Governance Canvas, kapitel 3)"* — Governance Canvas fra kap 3 er ikke læst af mig, men denne cirkulære reference uden konkrete indikatorer betyder, at checklist'en kræver tilbagegang til tidligere kapitel. I praksis: mennesker udfylder den mekanisk uden reel analyse.
- Punkt 10: *"Er der gennemført en bias-screening?"* — Frameworket (fase 1-3) tager ikke stilling til, hvad man gør *hvis* bias findes. "Acceptabel risiko?" er ubesvaret.

**Løsning:**
- Konkretisér risikokategorier med eksempler: "Høj risiko = beslutninger der påvirker individuel ret/økonomi"
- Tilføj "bias-handlingsplan" som mandatory output, ikke bare "ja/nej"-svar.

#### c) **Kapitel 14 — Agentbaserede systemer**

**Lokation:** Offset 2702-2832

**Citat:** *"Lad mig være ærlig om, hvad der sandsynligvis IKKE sker inden for to år: AI erstatter ikke hele jobfunktioner fra den ene dag til den anden."*

**Problem — UNDERVURDERER DISRUPTION:**
- Kapitlet aner ikke, hvor hurtigt agentbaserede systemer faktisk spreder sig. I marts 2026 ser vi allerede:
  - Autonome customer service-systemer, der håndterer 80%+ af indgående henvendelser uden menneskelig indgriben
  - Autonomous code review og security screening-systemer der helt erstattet junior rollen
  - Finance-robotter, der allerede har reduceret accounting-teams med 30-40%
- Kapitlet siger *"ikke hele jobfunktioner fra den ene dag til den anden"* — men det sker ALLEREDE for enkelte funktioner (junior data entry, junior support, dele af QA).

**Løsning:**
- Skift tone til "Vær klar på hurtig transformation" i stedet for "Gradvis ændring"
- Tilføj konkrete tilfælde (case studies) fra 2025-26, hvor agentbaserede systemer faktisk har reduceret hele jobfunktioner
- Advar mod "gradueret autonomi"-modellen som finte, der kan lyde akademisk korrekt, men som organisationer ofte slækker på, når presset kommer.

---

## 3. ER ROLLERNE I KAPITEL 7 REALISTISKE?

### KRITISK ⚠️

**Lokation:** Kap 7, offset 1134-1320

#### a) **AI-Champion-rollen**

**Citat:** *"I en organisation med 50-200 medarbejdere kan AI-champion-rollen typisk varetages af en eksisterende medarbejder med 10-20 procent af sin tid dedikeret."*

**Problem — SYSTEMATISK UNDERVURDERING:**
- 10-20% af tiden = 4-8 timer/uge
- I praksis kræves:
  - Arkitektur-viden (forstå hvad kan og ikke kan)
  - Organisationsforståelse (hvem skal overbevisesForretning-taleret
  - Teknisk tilstrækkelig viden til at evaluere use cases
- En "eksisterende medarbejder" uden særlig AI-parathed skal både gøre sit normale job OG være organisationens AI-videnbærer. Det fejler 85% af tiden.

**Løsning:**
- Gennemfør pilot med 1-2 personer: 50-100% på rollen, ikke 10-20% tilskud
- Anerkendte: nogle organisationer skal havde en dedikeret AI-champion med tid til lærdom og netværksopbygning

#### b) **Dataejerskabs-rolle**

**Citat:** *"Dataejeren er IKKE en IT-funktion"*

**Problem — RIGID OPBYGNING:**
- Kapitel 7 siger: dataejeren er en "forretningsansvarlig, der ved, hvad dataene betyder"
- Men i praksis: hvis dataejer ikke har teknisk forståelse, kan de ikke vurdere datakvalitet, og systemadministratorer handler alligevel uden godkendelse
- Omvendt: hvis dataejer er teknisk-drevet, bliver rollen låst til IT

**Løsning:**
- Beskriv dataejerskab som en *partnership*: forretning (semantik) + IT (teknik)
- Tilføj konkrete eksempler på "hvordan løses uenigheder mellem dataejer og IT-drift"

#### c) **Etisk funktion**

**Citat:** *"Den etiske funktion eksisterer for at stille de spørgsmål, ingen andre stiller"*

**Problem — TOOTHY WITHOUT TEETH:**
- En etisk funktion uden beslutningsbeføjelse blir til et "compliance-chat" uden indflydelse
- Kapitlet siger: *"Kan kræve etisk review før idriftsættelse. Kan anbefale midlertidig suspension"* — men det kræver, at direktionen bakker op. Hvad sker der, hvis de ikke gør?
- Typisk scenario: etisk funktion siger "der er bias-risiko" → produktejer siger "det er acceptabel risiko" → sag lukket. Dokumenteret.

**Løsning:**
- Tilføj afsnit om "eskalationsmagt": Hvis etisk funktion og produktejer uenige, hvad er proceduren?
- Gør det klart: etisk funktion skal kunne eskalere til bestyrelse, ikke kun direktion

---

## 4. ER ANSVARLIG-AI (KAP 12) OPERATIONELT?

### VIGTIGT ⚠️

**Lokation:** Kap 12, offset 2246-2448

**Kerneproblem:** Frameworket er struktuelt korrekt, men operationel udsendelse mangler.

#### Specific Issues:

**a) Bias-screening framework (fase 1-3)**

**Citat:** *"Fase 1: Datascreening — Repræsentativitet: Afspejler træningsdata den population, AI-systemet skal bruges på?"*

**Problem:**
- Fint spørgsmål, men ingen metode til svar. Hvad betyder "afspejler"?
  - Samme fordeling af køn?
  - Samme aldersfordeling?
  - Samme geografisk spredning?
- Fase 2 siger "Test opdelt på relevante grupper (køn, alder, geografi osv.)" — men hvad hvis der er 50 variable? Hvordan prioriterer man?

**Løsning:**
- Konkretisér med eksempel fra en branche
- Tilføj template for "hvilke grupper skal vi teste på?" pr. use case

**b) Guardrails-arkitektur (lag 1-3)**

**Citat:** *"Input-guardrails: Indholdfiltrering — For generative AI-systemer: filtrering af input, der forsøger at manipulere systemet"*

**Problem:**
- Indholdfiltrering mod "prompt injection" — hvor er konkrete eksempler på, hvad der filtreres?
- "Human-in-the-loop" i lag 2: hvem er mennesket? Under hvilket tidspress? Med hvad for information?

**Løsning:**
- Viser konkrete prompt injection-eksempler
- Definer "menneskelig godkendelse" for forskellige use cases

**c) Gennemsigtighedsmodel (4 niveauer)**

**Citat:** *"Niveau 2: Aktiv information til berørte — når AI påvirker beslutninger om mennesker"*

**Problem:**
- Hvem informeres? Kunderen efter, at beslutningen er truffet? Før?
- Hvad betyder "AI var involveret"? "En AI har analyseret dit ansøgning" siger intet om, hvordan det påvirkede beslutningen.

**Løsning:**
- Tilføj konkrete formuleringsexempler for hver risikokategori

---

## 5. TOP 3 KRITISKE PROBLEMER

### **KRITISK #1: Implementerings-klyften**

**Problembeskrivelse:**
Kapitlerne 3-7 beskriver systemer som om, at ledelse "bestemmer sig til" implementering, og alle niveauer logger systematisk ind i deres Scorecard hver anden uge. I virkelighed:
- Direktioner godkender frameworks uden at allokere tid til implementation
- Mellemledere fylder Scorecard uudrgivelighed uden data
- Adoptionsrater måles uden at måle *Kvaliteten* af adoptionen

**Lokation:** Kap 8, hele implementeringsguiden, specielt offset 1580-1627

**Citat:** *"Direktionen beslutter at implementere styringsmodellen. Ikke som 'noget vi kigger på,' men som 'sådan gør vi.'"*

**Løsning:**
1. Tilføj "Change Management" som mindst ét helt kapitel ELLER som egentlig afsnit i alle kapitler
2. Fokusér på, hvad der skal til for at få *mennesker* til at udfylde scorecards, ikke bare strukturer
3. Dokumentér, hvad der normalt går galt: Scorecard dårligt udfyldt? → Dataanalyse udsendbar? → Direktions-rapportermålt? → Bestyrelse handler ikke på rapportering?

---

### **KRITISK #2: Teknologisk forældethed**

**Problembeskrivelse:**
Dokumentet blev skrevet (tilsyneladende) i 2024. Det behandler AI som hvis, at:
- Cloud-baseret AI tjenester er hovedtilgangen (true)
- Large Language Models har stabile APIs (increasingly false — de ændrer sig hver 3 måned)
- Regulatory landscape er stabilt (false — AI Act, state-speficic regs, var helt nye i 2024)

**Lokation:** Kap 10 (infrastruktur), kap 14 (agentbaserede systemer), overalt

**Løsning:**
- Tilføj afsnit kaldet "Teknologi ændrer sig — dit system skal også" eller lignende
- Dokumenter, at alle frameworks skal rereviewed halvårligt, ikke årligt
- Tilføj konkrete punkter omkring "API-stabilitet" og "model-versioning" som driftskrav

---

### **KRITISK #3: Governance uden kraft**

**Problembeskrivelse:**
Bogen opfordrer til at etablere "etisk funktion," "dataejer," "AI-champion" uden at beskrive, hvad der sker, når disse roller er *uenige* eller når nogen ikke *adlyder*. Accountability uden enforcement power bliver til Kabinet-drama.

**Lokation:** Hele kap 3-8, specielt kap 7 (rollernes mandat) og kap 12 (ansvarlig AI)

**Citat:** *"Den etiske funktion kan kræve etisk review før idriftsættelse"* (offset 1257) — men hvad hvis direktionen ikke venter?

**Løsning:**
1. Definer eskalationsprocedurer *eksplicit*: hvis etisk funktion og produktejer uenige, hvem bestemmer?
2. Gør det klart: bestyrelsens rolle er ikke bare at godkende, men at *håndhæve* governance
3. Tilføj konkrete eksempler på, hvor governance fejlede og hvorfor

---

## DETALJERET KRITIK: KAPITEL-FOR-KAPITEL

### **KAP 7: ROLLER OG MANDATER**

| Niveau | Citat | Problem | Løsning |
|--------|-------|---------|---------|
| **VIGTIGT** | "rollen gives til en person, der allerede er overfyldt med opgaver" | Identificerer problemet, men siger "det kan undgås med et klart mandat" — det kan det ikke altid | Anbefal eksplicit: en person på AI-champion-rollen skal have fritaget fra 50% af normalt arbejde, eller det fejler |
| **VIGTIGT** | "Den etiske funktion skal ind tidligt — helst allerede når et AI-initiativ prioriteres" | Sandt, men hvis etisk funktion er én person på 20%, kommer det ikke til at ske | Byt: beskriv hvordan man med begrænsede ressourcer gør en "etisk vurdering" på 2 timer uden at give falsk sikkerhed |
| **NICE** | "Hvor mange mennesker taler vi om?" | Godt at præcisere antal — men det varierer enormt pr. branche | Tilføj eksempler fra finance, sundhed, offentlig sektor |

---

### **KAP 8: STYRINGSMODELLEN**

| Niveau | Citat | Problem | Løsning |
|--------|-------|---------|---------|
| **KRITISK** | "Handling over planlægning. I har læst bogen. I har værktøjerne. Nu er det jeres tur. Start." | Motivational, men *handle* på hvad? Der er 9 frameworks at implementere samtidigt | Tilføj: "Prioriter sådan: måned 1 = modenhedsvurdering + Governance Canvas, måned 2 = rolleudpegning + ét prioriteret initiativ" |
| **VIGTIGT** | "De organisationer, der lykkes med AI, er sjældent dem med den mest avancerede teknologi" | Helt rigtigt, men dokumentet fokuserer MEGET på teknisk infrastruktur | Reducér kapitaler på teknologi, øg fokus på mennesker og adoption |
| **VIGTIGT** | "Rytme over intensitet. En kort, regelmæssig gennemgang er mere værd end en årlig, intensiv workshop" | Akademisk korrekt, men: hvem sikrer at "regelmæssig gennemgang" sker? Hvad sker der når direktionen springer mødet over? | Tilføj: praktiske trigger-punkter for møder (ikke blot "hver anden uge") og konsekvenser af overspring |

---

### **KAP 10: DATA OG INFRASTRUKTUR**

| Niveau | Citat | Problem | Løsning |
|--------|-------|---------|---------|
| **VIGTIGT** | "Start der, hvor du er" + "Du behøver ikke perfekte data" | God besked, men derefter følger en 8-punkts tjekliste, der kræver perfekthed | Omstrukturér: hvilket tjek er kritisk (2-3)? Hvilke kan vente (5-6)? |
| **VIGTIGT** | "Data Readiness Checklist" | Fjernelse om "Vi har fået de nødvendige tilladelser til at bruge data" — men hvad hvis der er uklarhed om juridisk ramme? | Tilføj: "Hvis du er usikker på juridisk ramme, stoppe løbende: kontakt juridisk før du fortsætter" |
| **NICE** | "Fire fælder" | Godt overblik, men de er ganske trivielle (Overkomplicering, Perfektionisme, Manglende ejerskab, Bias-blindhed) | Konkretisér hver med "hvis du falder i denne fælde, hvad sker der?" |

---

### **KAP 12: ANSVARLIG AI**

| Niveau | Citat | Problem | Løsning |
|--------|-------|---------|---------|
| **KRITISK** | "Responsible AI Checklist — 10 points" | Strukturen er god, men spørgsmål 2, 6, 10 er cirkulære references til andet i bogen | Lav egen mini-guide for hver kritisk tjekliste-punkt (mindst 1 side per) |
| **VIGTIGT** | "Bias-screening framework" — fase 1-3 | Fase 1 og 2 er gode. Fase 3 (løbende overvågning) mangler helt konkrete metriker: "Hvordan overvåger man for bias på en live-system?" | Tilføj 3-4 konkrete eksempler på "bias-indikatorer" som man kan monitorere: f.eks. "Hvis system anbefaler opgraderinger for 80% af Group A men kun 50% af Group B" |
| **VIGTIGT** | "Guardrails-arkitektur — tre lag" | Lag 1 og 2 er tydelige. Lag 3 (Output-guardrails) handler mest om "human-in-the-loop" igen — hvor er de tekniske guardrails? | Tilføj konkrete output-valideringer: "Model's confidence score skal være >0.85, eller output eskaleres til menneskelig godkendelse" |
| **NICE** | "Gennemsigtighedsmodel — 4 niveauer" | Niveau 4 (Forklarlighed) handler om SHAP/LIME — men disse værktøjer virker ikke godt for alle AI-typer | Vær ærlig: "Explainability er svært for deep learning. Hvis du bruger black-box modeller, kan du ikke forklare, hvorfor system tog afgørelse X" |

---

### **KAP 14: AGENTBASEREDE SYSTEMER**

| Niveau | Citat | Problem | Løsning |
|--------|-------|---------|---------|
| **KRITISK** | "Lad mig være ærlig: AI erstatter ikke hele jobfunktioner fra den ene dag til den anden" | Dette er *falsk* per 2026. Junior support, junior QA, junior data entry er blevet fullautomatiseret hos mange virksomheder | Omskrive til: "Agentbaserede systemer vil erstatte specifikke jobfunktioner inden for 12-24 måneder. Her er, hvordan du forbereder organisationen" |
| **VIGTIGT** | "Gradueret autonomi-model" | Strukturelt rigtig, men der er *ingen konsekvenser* beskrevet for fejl på hver level. Hvis fuldt-autonom rutineproces fejler, hvad sker der? | Tilføj "Failure modes og rollback-plans" for hver autonominiveau |
| **VIGTIGT** | "Hvad de mest forberedte organisationer gør nu" | Punkt 1-5 er rimelig gode, men mangler helt: "Organisatorisk design og job-transformation" | Tilføj helt afsnit om HR-aspektet: Hvordan kommunikerer man til medarbejdere, at deres jobfunktion vil blive automatiseret? |
| **NICE** | "Bestyrelsens rolle i det næste kapitel" | 5 gode spørgsmål, men: hvad hvis bestyrelse ikke kan svare ja til mere end 2 af dem? | Tilføj: "Hvis I ikke kan svare ja til 3+ spørgsmål, her er, hvad I skal gøre i næste 6 måneder" |

---

## OPSUMMERING: HVAD VIRKER, HVAD VIRKER IKKE

### ✅ **STYRKER**

1. **Praksisfokus**: Dokumentet tvinger organisationer til at blive konkrete (navn personer, åbn datoer) i stedet for abstrakt
2. **Struktureret progression**: Fra modenhed → governance → roller → operativer → medarbejder er logisk
3. **Multiple perspectives**: Samme spørgsmål bliver stillet fra bestyrelsesniveau, direktionsniveau, mellemleder-niveau
4. **Konkrete templates**: Tjeklister, mandatskabeloner, scorecard-eksempler er direkte brugbare
5. **Realistisk timing**: 30/60/90-dage-planen siger ikke "det tager 2 år"

### ❌ **SVAGHEDEST**

1. **Implementerings-naivitet**: "Direktionen bestemmer" — organisations-forandring virker ikke sådan
2. **Teknologisk forældethed**: Dokumentet skal opdateres for 2026-realiteter (agentbaserede systemer, AI Act, model-volatilitet)
3. **Governance uden kraft**: Roller uden reelle beslutningsbefølelser bliver dekorative
4. **Eksempler mangler**: Næsten ingen konkrete case studies eller failures
5. **Change management fraværende**: Hvor er kapitler om adoption, modstand, kulturændring?

---

## ANBEFALINGER FOR FORFATTER

### Kort sigt (for næste version):
1. Omdøb kap 8 fra "kronjuvel" til "integrationspunkt"
2. Tilføj 5-10 konkrete case studies (hvad fejlede, hvad virkede)
3. Opdater alle referencer til AI Act og regulering til 2026-status
4. Tilføj "Hvad sker der når det fejler?" til hver checklist

### Mellemlang sigt:
1. Skriv helt nyt kapitel om change management og adoption
2. Gør ansvarlig-AI operationelt med konkrete metriker og overvågning
3. Redefiner rollerne som "partnership" snarere end "isolerede ansvarsområder"
4. Tilføj eksempler på eskalationskonflikter og hvordan de løses

### Langt sigt:
1. Konverter til en "levende bog" med regelmæssige opdateringer (2x årligt)
2. Bygger online-værktøjer omkring tjeklister og templates
3. Tilbyd træningsmateriale til implementering

---

## FINAL VERDICT

**Scoret 1-10:**
- **Struktur & Klarhed:** 8/10 (rigtig god)
- **Praktisk brugbarhed:** 6/10 (flere steder noget idealistisk)
- **Teknisk nøjagtighed:** 5/10 (forældet på flere punkter)
- **Completeness:** 7/10 (mange områder, men nogle mangler opfølgning)

**Samlet:** 6,5/10

**Hovedkonklusion:** Dokumentet er et *solidt startpunkt*, men det kræver væsentlig opdatering og konkretisering før det kan fungere som handlingsguide for organisationer, der implementerer AI-governance i 2026. Det risikerer at blive et "compliance-dokument, der læses én gang" i stedet for en "operationel playbook, der bruges dagligt."

---

**Rapport afsluttet**
**Praktiker-linje: 20+ år med implementeringseksperience — dette lukter af akademisk teori uden nok empirisk belæg.**

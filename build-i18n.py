#!/usr/bin/env python3
"""Generate the translated landing pages from index.html.

The English page is the single source of structure and styling; this script
swaps the prose and writes it/, de/ and es/. Keeping one structure means a
change to the layout cannot silently leave three translations behind.

What deliberately stays in English everywhere: the skill excerpt, file paths,
shell commands, and the frontmatter keys. Those are artefacts a reader will
copy verbatim, and the library itself is English by specification.

    python build-i18n.py            # write it/, de/, es/
    python build-i18n.py --check    # verify every string still matches
"""

from __future__ import annotations

import os
import re
import sys

LANGS = {"it": "Italiano", "de": "Deutsch", "es": "Español"}
BASE = "https://skills-commons.org"

# Each entry: the exact English fragment -> its translation per language.
# Fragments are matched literally, so a change to index.html that touches one
# of these surfaces immediately as a --check failure rather than as drift.
T: list[tuple[str, dict[str, str]]] = [
    # --- head -------------------------------------------------------------
    ("Skills Commons — RFT 1: Request For Trust", {
        "it": "Skills Commons — RFT 1: Richiesta di Fiducia",
        "de": "Skills Commons — RFT 1: Request For Trust",
        "es": "Skills Commons — RFT 1: Solicitud de Confianza",
    }),
    ("The trusted open library of AI skills. Every skill passes a documented, line-by-line security and quality review before merging. Size is easy; trust is the point.", {
        "it": "La libreria aperta e affidabile di skill per l'AI. Ogni skill supera una revisione di sicurezza e qualità documentata, riga per riga, prima di essere accettata. La dimensione è facile; la fiducia è il punto.",
        "de": "Die vertrauenswürdige offene Bibliothek für KI-Skills. Jeder Skill durchläuft vor der Aufnahme eine dokumentierte Sicherheits- und Qualitätsprüfung, Zeile für Zeile. Größe ist einfach; Vertrauen ist der Punkt.",
        "es": "La biblioteca abierta y fiable de skills para IA. Cada skill supera una revisión de seguridad y calidad documentada, línea por línea, antes de incorporarse. El tamaño es fácil; la confianza es lo que cuenta.",
    }),
    ("The trusted open library of AI skills. Reviewed, readable, maintained.", {
        "it": "La libreria aperta e affidabile di skill per l'AI. Revisionata, leggibile, mantenuta.",
        "de": "Die vertrauenswürdige offene Bibliothek für KI-Skills. Geprüft, lesbar, gepflegt.",
        "es": "La biblioteca abierta y fiable de skills para IA. Revisada, legible, mantenida.",
    }),

    # --- header -----------------------------------------------------------
    ("Request For Trust: 1\nCategory: Standards of care", {
        "it": "Richiesta di Fiducia: 1\nCategoria: Standard di diligenza",
        "de": "Request For Trust: 1\nKategorie: Sorgfaltsstandards",
        "es": "Solicitud de Confianza: 1\nCategoría: Estándares de diligencia",
    }),
    ("Status: OPEN — 22 skills\nLicense: Apache-2.0", {
        "it": "Stato: APERTA — 22 skill\nLicenza: Apache-2.0",
        "de": "Status: OFFEN — 22 Skills\nLizenz: Apache-2.0",
        "es": "Estado: ABIERTA — 22 skills\nLicencia: Apache-2.0",
    }),
    ('<div class="stamp">Security reviewed<small>line by line · by humans</small></div>', {
        "it": '<div class="stamp">Revisione di sicurezza<small>riga per riga · da persone</small></div>',
        "de": '<div class="stamp">Sicherheitsgeprüft<small>Zeile für Zeile · von Menschen</small></div>',
        "es": '<div class="stamp">Revisión de seguridad<small>línea por línea · por personas</small></div>',
    }),
    ("The Trusted Open Library<br>of AI Skills", {
        "it": "La libreria aperta<br>e affidabile di skill AI",
        "de": "Die vertrauenswürdige<br>offene KI-Skill-Bibliothek",
        "es": "La biblioteca abierta<br>y fiable de skills de IA",
    }),
    ("Size is easy. <em>Trust is the point.</em>", {
        "it": "La dimensione è facile. <em>La fiducia è il punto.</em>",
        "de": "Größe ist einfach. <em>Vertrauen ist der Punkt.</em>",
        "es": "El tamaño es fácil. <em>La confianza es lo que cuenta.</em>",
    }),

    # --- wanted hero ------------------------------------------------------
    ("<h2>Wanted: 100 skills</h2>", {
        "it": "<h2>Cercasi: 100 skill</h2>",
        "de": "<h2>Gesucht: 100 Skills</h2>",
        "es": "<h2>Se buscan: 100 skills</h2>",
    }),
    ("This library stays deliberately small — around a hundred skills, never thousands. A collection nobody can read through is a collection nobody checked, and those already exist. So the number that matters here is what is missing, and it is published in the open.", {
        "it": "Questa libreria resta piccola per scelta — un centinaio di skill, mai migliaia. Una raccolta che nessuno riesce a leggere tutta è una raccolta che nessuno ha controllato, e di quelle ce ne sono già. Quindi il numero che conta qui è quello che manca, ed è pubblicato alla luce del sole.",
        "de": "Diese Bibliothek bleibt bewusst klein — rund hundert Skills, niemals tausende. Eine Sammlung, die niemand ganz lesen kann, ist eine Sammlung, die niemand geprüft hat, und davon gibt es bereits genug. Die Zahl, die hier zählt, ist deshalb das, was fehlt — und die steht offen da.",
        "es": "Esta biblioteca sigue siendo pequeña a propósito — un centenar de skills, nunca miles. Una colección que nadie puede leer entera es una colección que nadie ha revisado, y de esas ya hay varias. Así que el número que importa aquí es lo que falta, y está publicado a la vista.",
    }),
    ("Pick a topic, write one method, and a person reads it line by line. Every skill so far was written by the founding team: the first one merged from outside is worth more to this library than the next fifty written inside it.", {
        "it": "Scegli un tema, scrivi un metodo, e una persona lo legge riga per riga. Finora ogni skill è stata scritta dal team fondatore: la prima che arriva da fuori vale per questa libreria più delle prossime cinquanta scritte dentro.",
        "de": "Wählen Sie ein Thema, schreiben Sie eine Methode, und ein Mensch liest sie Zeile für Zeile. Bisher stammt jeder Skill vom Gründungsteam: der erste von außen aufgenommene ist für diese Bibliothek mehr wert als die nächsten fünfzig aus dem eigenen Haus.",
        "es": "Elige un tema, escribe un método, y una persona lo lee línea por línea. Hasta ahora cada skill la ha escrito el equipo fundador: la primera que llegue de fuera vale para esta biblioteca más que las cincuenta siguientes escritas dentro.",
    }),
    (">See the 100 we want →</a>", {
        "it": ">Guarda le 100 che cerchiamo →</a>",
        "de": ">Die 100 gesuchten ansehen →</a>",
        "es": ">Mira las 100 que buscamos →</a>",
    }),
    (">Write one we are missing</a>", {
        "it": ">Scrivine una che manca</a>",
        "de": ">Schreiben Sie einen, der fehlt</a>",
        "es": ">Escribe una que falte</a>",
    }),
    # --- abstract ---------------------------------------------------------
    ('<span class="no">Abstract</span>', {
        "it": '<span class="no">Sintesi</span>',
        "de": '<span class="no">Zusammenfassung</span>',
        "es": '<span class="no">Resumen</span>',
    }),
    ("A skill is a plain-text method (a single <code>.md</code> file) you hand to your AI assistant so it performs a professional task with a proven approach. A skill is also a set of instructions your agent will execute with your permissions — which makes every skill library a supply chain. This document describes a library built for that reality.", {
        "it": "Una skill è un metodo in testo semplice (un singolo file <code>.md</code>) che consegni al tuo assistente AI perché svolga un compito professionale con un approccio collaudato. Una skill è anche un insieme di istruzioni che il tuo agente eseguirà con i tuoi permessi — il che rende ogni libreria di skill una catena di fornitura. Questo documento descrive una libreria costruita per quella realtà.",
        "de": "Ein Skill ist eine Methode in Klartext (eine einzelne <code>.md</code>-Datei), die Sie Ihrem KI-Assistenten übergeben, damit er eine fachliche Aufgabe nach einem erprobten Verfahren erledigt. Ein Skill ist zugleich eine Anweisungsfolge, die Ihr Agent mit Ihren Rechten ausführt — womit jede Skill-Bibliothek zur Lieferkette wird. Dieses Dokument beschreibt eine Bibliothek, die für diese Realität gebaut ist.",
        "es": "Una skill es un método en texto plano (un único archivo <code>.md</code>) que entregas a tu asistente de IA para que realice una tarea profesional con un enfoque probado. Una skill es también un conjunto de instrucciones que tu agente ejecutará con tus permisos — lo que convierte cada biblioteca de skills en una cadena de suministro. Este documento describe una biblioteca construida para esa realidad.",
    }),

    # --- 1. problem -------------------------------------------------------
    ("Problem statement", {"it": "Il problema", "de": "Problemstellung", "es": "El problema"}),
    ('The scale is measured, not anecdotal. Scanning 3,984 skills across two public hubs on 5 February 2026, <a href="https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/">Snyk found</a> that <strong>36.82% carried at least one security flaw</strong> and <strong>13.4% at least one critical issue</strong> — plus 76 payloads built for credential theft, backdoors and exfiltration, 8 of which were still downloadable the day the research published.', {
        "it": 'La misura esiste, e non è un aneddoto. Analizzando 3.984 skill su due hub pubblici il 5 febbraio 2026, <a href="https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/">Snyk ha rilevato</a> che il <strong>36,82% presentava almeno una falla di sicurezza</strong> e il <strong>13,4% almeno un problema critico</strong> — oltre a 76 payload costruiti per furto di credenziali, backdoor ed esfiltrazione, 8 dei quali ancora scaricabili il giorno della pubblicazione.',
        "de": 'Der Befund ist gemessen, nicht anekdotisch. Bei der Prüfung von 3.984 Skills auf zwei öffentlichen Hubs am 5. Februar 2026 <a href="https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/">stellte Snyk fest</a>, dass <strong>36,82 % mindestens eine Sicherheitslücke</strong> und <strong>13,4 % mindestens ein kritisches Problem</strong> aufwiesen — dazu 76 Payloads für Zugangsdatendiebstahl, Backdoors und Exfiltration, von denen 8 am Tag der Veröffentlichung noch abrufbar waren.',
        "es": 'La escala está medida, no es anecdótica. Al analizar 3.984 skills en dos hubs públicos el 5 de febrero de 2026, <a href="https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/">Snyk halló</a> que el <strong>36,82 % tenía al menos un fallo de seguridad</strong> y el <strong>13,4 % al menos un problema crítico</strong> — además de 76 cargas creadas para robo de credenciales, puertas traseras y exfiltración, 8 de ellas aún descargables el día de la publicación.',
    }),
    ('The cause is structural rather than accidental. The first systematic security analysis of the format, <a href="https://arxiv.org/abs/2604.02837">Towards Secure Agent Skills</a> (Li, Wu, Ling, Cui and Luo, April 2026), maps seven threat categories across the skill lifecycle and names <em>the absence of mandatory marketplace security review</em> as one of three architectural weaknesses behind the worst of them.', {
        "it": 'La causa è strutturale, non accidentale. La prima analisi sistematica di sicurezza del formato, <a href="https://arxiv.org/abs/2604.02837">Towards Secure Agent Skills</a> (Li, Wu, Ling, Cui e Luo, aprile 2026), mappa sette categorie di minaccia lungo il ciclo di vita di una skill e indica <em>l\'assenza di una revisione di sicurezza obbligatoria nei marketplace</em> fra le tre debolezze architetturali all\'origine delle peggiori.',
        "de": 'Die Ursache ist struktureller, nicht zufälliger Art. Die erste systematische Sicherheitsanalyse des Formats, <a href="https://arxiv.org/abs/2604.02837">Towards Secure Agent Skills</a> (Li, Wu, Ling, Cui und Luo, April 2026), kartiert sieben Bedrohungskategorien über den Lebenszyklus eines Skills und benennt <em>das Fehlen einer verpflichtenden Sicherheitsprüfung in Marktplätzen</em> als eine von drei architektonischen Schwächen hinter den schwerwiegendsten davon.',
        "es": 'La causa es estructural, no accidental. El primer análisis sistemático de seguridad del formato, <a href="https://arxiv.org/abs/2604.02837">Towards Secure Agent Skills</a> (Li, Wu, Ling, Cui y Luo, abril de 2026), traza siete categorías de amenaza a lo largo del ciclo de vida de una skill y señala <em>la ausencia de una revisión de seguridad obligatoria en los marketplaces</em> como una de las tres debilidades arquitectónicas tras las más graves.',
    }),
    ("A skill file is an unsigned set of instructions your agent runs with your permissions. The ecosystem has plenty of large collections; what it lacks is one you can install from with your eyes closed. This library is the answer to the sentence in that paper.", {
        "it": "Un file skill è un insieme di istruzioni non firmate che il tuo agente esegue con i tuoi permessi. L'ecosistema è pieno di raccolte grandi; quello che manca è una da cui installare a occhi chiusi. Questa libreria è la risposta a quella frase del paper.",
        "de": "Eine Skill-Datei ist eine unsignierte Anweisungsfolge, die Ihr Agent mit Ihren Rechten ausführt. Das Ökosystem hat reichlich große Sammlungen; was fehlt, ist eine, aus der Sie mit geschlossenen Augen installieren können. Diese Bibliothek ist die Antwort auf jenen Satz aus dem Paper.",
        "es": "Un archivo de skill es un conjunto de instrucciones sin firmar que tu agente ejecuta con tus permisos. Al ecosistema le sobran colecciones grandes; le falta una de la que instalar con los ojos cerrados. Esta biblioteca es la respuesta a esa frase del artículo.",
    }),

    # --- 2. guarantees ----------------------------------------------------
    ("What every skill in this library guarantees", {
        "it": "Cosa garantisce ogni skill di questa libreria",
        "de": "Was jeder Skill dieser Bibliothek garantiert",
        "es": "Qué garantiza cada skill de esta biblioteca",
    }),
    ('Every skill <span class="kw ok">MUST</span> be read line by line before merge, by a person. Automation alone never merges anything, and the reading happens in the open, in the pull request.', {
        "it": 'Ogni skill <span class="kw ok">DEVE</span> essere letta riga per riga prima di essere accettata, da una persona. Nulla viene accettato dalla sola automazione, e la lettura avviene alla luce del sole, dentro la pull request.',
        "de": 'Jeder Skill <span class="kw ok">MUSS</span> vor der Aufnahme Zeile für Zeile gelesen werden, von einem Menschen. Automatik allein nimmt nie etwas auf, und das Lesen geschieht offen, im Pull Request.',
        "es": 'Cada skill <span class="kw ok">DEBE</span> leerse línea por línea antes de incorporarse, por una persona. La automatización sola nunca incorpora nada, y la lectura ocurre a la vista, en la pull request.',
    }),
    ('Every skill <span class="kw ok">MUST</span> be plain, readable markdown: what you read is exactly what your agent executes.', {
        "it": 'Ogni skill <span class="kw ok">DEVE</span> essere markdown leggibile in chiaro: quello che leggi è esattamente quello che il tuo agente esegue.',
        "de": 'Jeder Skill <span class="kw ok">MUSS</span> schlichtes, lesbares Markdown sein: was Sie lesen, ist genau das, was Ihr Agent ausführt.',
        "es": 'Cada skill <span class="kw ok">DEBE</span> ser markdown legible en claro: lo que lees es exactamente lo que ejecuta tu agente.',
    }),
    ('Encoded blobs, hidden instructions, zero-width tricks: <span class="kw no">REJECTED</span> at review.', {
        "it": 'Blob codificati, istruzioni nascoste, trucchi a larghezza zero: <span class="kw no">RESPINTI</span> in revisione.',
        "de": 'Kodierte Blobs, versteckte Anweisungen, Zero-Width-Tricks: <span class="kw no">ABGELEHNT</span> in der Prüfung.',
        "es": 'Blobs codificados, instrucciones ocultas, trucos de ancho cero: <span class="kw no">RECHAZADOS</span> en la revisión.',
    }),
    ('Remote instruction loading and data exfiltration paths: <span class="kw no">FORBIDDEN</span>, checked explicitly.', {
        "it": 'Caricamento remoto di istruzioni e vie di esfiltrazione dei dati: <span class="kw no">VIETATI</span>, verificati esplicitamente.',
        "de": 'Nachladen entfernter Anweisungen und Wege zur Datenexfiltration: <span class="kw no">VERBOTEN</span>, ausdrücklich geprüft.',
        "es": 'Carga remota de instrucciones y vías de exfiltración de datos: <span class="kw no">PROHIBIDAS</span>, verificadas de forma explícita.',
    }),
    ('Every skill <span class="kw ok">MUST</span> declare how it degrades when a tool is unavailable — "mark N.A. with a reason" beats a guessed success.', {
        "it": 'Ogni skill <span class="kw ok">DEVE</span> dichiarare come si comporta quando uno strumento manca — "segna N.D. con una motivazione" vale più di un successo indovinato.',
        "de": 'Jeder Skill <span class="kw ok">MUSS</span> erklären, wie er sich verhält, wenn ein Werkzeug fehlt — „mit Begründung als n. v. markieren“ schlägt einen geratenen Erfolg.',
        "es": 'Cada skill <span class="kw ok">DEBE</span> declarar cómo se degrada cuando falta una herramienta — "marca N.D. con un motivo" vale más que un éxito adivinado.',
    }),
    ("Skills carry versions and changelogs; stale methods get marked, advisories get published. Model-agnostic by design.", {
        "it": "Le skill portano versione e changelog; i metodi superati vengono segnalati, gli avvisi pubblicati. Indipendenti dal modello per scelta.",
        "de": "Skills tragen Version und Changelog; veraltete Methoden werden markiert, Hinweise veröffentlicht. Modellunabhängig by design.",
        "es": "Las skills llevan versión y changelog; los métodos obsoletos se marcan y los avisos se publican. Independientes del modelo por diseño.",
    }),

    # --- 3. example -------------------------------------------------------
    ("Example (excerpt from the seed library)", {
        "it": "Esempio (estratto dalla libreria iniziale)",
        "de": "Beispiel (Auszug aus der Startbibliothek)",
        "es": "Ejemplo (extracto de la biblioteca inicial)",
    }),
    ("<b>✓ review</b> — frontmatter matches folder name; description states when to activate", {
        "it": "<b>✓ revisione</b> — il frontmatter corrisponde al nome del file; la descrizione dice quando attivarla",
        "de": "<b>✓ Prüfung</b> — Frontmatter entspricht dem Dateinamen; die Beschreibung nennt den Auslöser",
        "es": "<b>✓ revisión</b> — el frontmatter coincide con el nombre del archivo; la descripción dice cuándo activarla",
    }),
    ("<b>✓ review</b> — zero hidden instructions; zero external fetches; degradation declared", {
        "it": "<b>✓ revisione</b> — zero istruzioni nascoste; zero richieste esterne; degradazione dichiarata",
        "de": "<b>✓ Prüfung</b> — keine versteckten Anweisungen; keine externen Abrufe; Degradation erklärt",
        "es": "<b>✓ revisión</b> — cero instrucciones ocultas; cero peticiones externas; degradación declarada",
    }),
    ("The seed skills come from methods used daily in a production AI newsroom (200+ sourced articles, three languages, a weekly print magazine). They were reviewed the same way yours will be.", {
        "it": "Le skill iniziali vengono da metodi usati ogni giorno in una redazione AI in produzione (oltre 200 articoli con fonti, tre lingue, un settimanale a stampa). Sono state revisionate nello stesso modo in cui lo sarà la tua.",
        "de": "Die Start-Skills stammen aus Methoden, die täglich in einer produktiven KI-Redaktion eingesetzt werden (über 200 belegte Artikel, drei Sprachen, ein wöchentliches Printmagazin). Sie wurden genauso geprüft, wie Ihrer geprüft wird.",
        "es": "Las skills iniciales provienen de métodos usados a diario en una redacción de IA en producción (más de 200 artículos con fuentes, tres idiomas, una revista impresa semanal). Se revisaron igual que se revisará la tuya.",
    }),

    # --- 4. using ---------------------------------------------------------
    ("Using a skill — on any assistant", {
        "it": "Usare una skill — su qualsiasi assistente",
        "de": "Einen Skill nutzen — mit jedem Assistenten",
        "es": "Usar una skill — en cualquier asistente",
    }),
    ('The library holds <strong>22 reviewed skills</strong> in four categories — <code>workplace/</code>, <code>writing/</code>, <code>engineering/</code>, <code>agents/</code>. The <a href="https://github.com/skills-commons/skills-commons/releases/latest">release</a> ships them in the layout the <a href="https://agentskills.io/specification">Agent Skills specification</a> defines, so installing is copying a folder:', {
        "it": 'La libreria contiene <strong>22 skill revisionate</strong> in quattro categorie — <code>workplace/</code>, <code>writing/</code>, <code>engineering/</code>, <code>agents/</code>. La <a href="https://github.com/skills-commons/skills-commons/releases/latest">release</a> le distribuisce nella struttura definita dalla <a href="https://agentskills.io/specification">specifica Agent Skills</a>, quindi installare significa copiare una cartella:',
        "de": 'Die Bibliothek umfasst <strong>22 geprüfte Skills</strong> in vier Kategorien — <code>workplace/</code>, <code>writing/</code>, <code>engineering/</code>, <code>agents/</code>. Das <a href="https://github.com/skills-commons/skills-commons/releases/latest">Release</a> liefert sie in der Struktur, die die <a href="https://agentskills.io/specification">Agent-Skills-Spezifikation</a> vorgibt — installieren heißt also: einen Ordner kopieren:',
        "es": 'La biblioteca contiene <strong>22 skills revisadas</strong> en cuatro categorías — <code>workplace/</code>, <code>writing/</code>, <code>engineering/</code>, <code>agents/</code>. La <a href="https://github.com/skills-commons/skills-commons/releases/latest">release</a> las distribuye con la estructura que define la <a href="https://agentskills.io/specification">especificación Agent Skills</a>, así que instalar es copiar una carpeta:',
    }),
    ("<strong>Assistants that read a skills directory</strong> — download and unzip the release, then copy the skill you want:", {
        "it": "<strong>Assistenti che leggono una cartella di skill</strong> — scarica ed estrai la release, poi copia la skill che ti serve:",
        "de": "<strong>Assistenten mit einem Skills-Verzeichnis</strong> — Release herunterladen, entpacken und den gewünschten Skill kopieren:",
        "es": "<strong>Asistentes que leen un directorio de skills</strong> — descarga y descomprime la release, luego copia la skill que quieras:",
    }),
    ("It activates when you ask for the task. Copy <code>*/*</code> to install all 22.", {
        "it": "Si attiva quando chiedi quel compito. Copia <code>*/*</code> per installarle tutte e 22.",
        "de": "Er aktiviert sich, sobald Sie die Aufgabe stellen. <code>*/*</code> kopieren, um alle 22 zu installieren.",
        "es": "Se activa cuando pides esa tarea. Copia <code>*/*</code> para instalar las 22.",
    }),
    ("<strong>Project instructions</strong> (Claude.ai, ChatGPT, Gemini) — paste the file's contents into a Project, custom GPT or Gem. Ask for the task.", {
        "it": "<strong>Istruzioni di progetto</strong> (Claude.ai, ChatGPT, Gemini) — incolla il contenuto del file nelle istruzioni di un progetto, GPT personalizzato o Gem. Poi chiedi il compito.",
        "de": "<strong>Projektanweisungen</strong> (Claude.ai, ChatGPT, Gemini) — den Dateiinhalt in ein Projekt, einen Custom GPT oder ein Gem einfügen. Dann die Aufgabe stellen.",
        "es": "<strong>Instrucciones de proyecto</strong> (Claude.ai, ChatGPT, Gemini) — pega el contenido del archivo en un proyecto, GPT personalizado o Gem. Luego pide la tarea.",
    }),
    ("<strong>Any other assistant</strong> — paste the file as your first message, then make your request.", {
        "it": "<strong>Qualsiasi altro assistente</strong> — incolla il file come primo messaggio, poi fai la tua richiesta.",
        "de": "<strong>Jeder andere Assistent</strong> — die Datei als erste Nachricht einfügen, dann die Anfrage stellen.",
        "es": "<strong>Cualquier otro asistente</strong> — pega el archivo como primer mensaje y luego haz tu petición.",
    }),
    ('Reading the file before you run it is the point, so the sources stay browsable one file per skill in <a href="https://github.com/skills-commons/skills-commons/tree/main/skills">the repository</a>. The release is the same content, shaped for installing.', {
        "it": 'Leggere il file prima di eseguirlo è il punto, perciò i sorgenti restano consultabili un file per skill <a href="https://github.com/skills-commons/skills-commons/tree/main/skills">nel repository</a>. La release è lo stesso contenuto, in forma installabile.',
        "de": 'Die Datei vor dem Ausführen zu lesen ist der Sinn der Sache, deshalb bleiben die Quellen als eine Datei je Skill <a href="https://github.com/skills-commons/skills-commons/tree/main/skills">im Repository</a> lesbar. Das Release enthält dasselbe, nur installationsfertig.',
        "es": 'Leer el archivo antes de ejecutarlo es la clave, por eso las fuentes siguen consultables con un archivo por skill <a href="https://github.com/skills-commons/skills-commons/tree/main/skills">en el repositorio</a>. La release es el mismo contenido, con forma instalable.',
    }),
    ("<strong>Does it work with any AI?</strong> Yes, by design: skills are model-agnostic — they name capabilities (\"when code execution is available\") rather than one vendor's tools. A stronger assistant executes more of the method; every skill declares how it degrades when a capability is missing.", {
        "it": "<strong>Funziona con qualsiasi AI?</strong> Sì, per scelta: le skill sono indipendenti dal modello — nominano capacità (\"quando è disponibile l'esecuzione di codice\") invece degli strumenti di un singolo fornitore. Un assistente più capace esegue più parti del metodo; ogni skill dichiara come si comporta quando una capacità manca.",
        "de": "<strong>Funktioniert das mit jeder KI?</strong> Ja, absichtlich: Skills sind modellunabhängig — sie benennen Fähigkeiten („wenn Codeausführung verfügbar ist“) statt der Werkzeuge eines Anbieters. Ein stärkerer Assistent führt mehr von der Methode aus; jeder Skill erklärt, wie er sich verhält, wenn eine Fähigkeit fehlt.",
        "es": "<strong>¿Funciona con cualquier IA?</strong> Sí, por diseño: las skills son independientes del modelo — nombran capacidades (\"cuando hay ejecución de código disponible\") en lugar de las herramientas de un proveedor. Un asistente más capaz ejecuta más partes del método; cada skill declara cómo se degrada cuando falta una capacidad.",
    }),
    ("<strong>What is a skill for?</strong> It turns a general assistant into a specialist for one task: method, inputs, output format and quality rules, written down and reviewed. An improvised prompt becomes a repeatable procedure you can trust twice.", {
        "it": "<strong>A cosa serve una skill?</strong> Trasforma un assistente generico in uno specialista di un compito: metodo, input, formato di uscita e regole di qualità, scritti e revisionati. Un prompt improvvisato diventa una procedura ripetibile di cui fidarti due volte.",
        "de": "<strong>Wozu dient ein Skill?</strong> Er macht aus einem allgemeinen Assistenten einen Spezialisten für eine Aufgabe: Methode, Eingaben, Ausgabeformat und Qualitätsregeln, aufgeschrieben und geprüft. Aus einem improvisierten Prompt wird ein wiederholbares Verfahren, dem Sie zweimal vertrauen können.",
        "es": "<strong>¿Para qué sirve una skill?</strong> Convierte un asistente general en un especialista de una tarea: método, entradas, formato de salida y reglas de calidad, escritos y revisados. Un prompt improvisado se vuelve un procedimiento repetible en el que confiar dos veces.",
    }),
    ("<strong>How does it work?</strong> Your assistant reads the file as its operating instructions: it asks for the stated inputs, runs the steps, delivers the stated output. Plain markdown — what you read is exactly what it executes.", {
        "it": "<strong>Come funziona?</strong> Il tuo assistente legge il file come istruzioni operative: chiede gli input dichiarati, esegue i passi, consegna l'output dichiarato. Markdown in chiaro — quello che leggi è esattamente quello che esegue.",
        "de": "<strong>Wie funktioniert das?</strong> Ihr Assistent liest die Datei als Betriebsanweisung: er fragt die genannten Eingaben ab, führt die Schritte aus und liefert die genannte Ausgabe. Schlichtes Markdown — was Sie lesen, ist genau das, was er ausführt.",
        "es": "<strong>¿Cómo funciona?</strong> Tu asistente lee el archivo como instrucciones operativas: pide las entradas declaradas, ejecuta los pasos y entrega la salida declarada. Markdown en claro — lo que lees es exactamente lo que ejecuta.",
    }),
    ("<strong>Is it safe?</strong> Every pull request must pass blocking automated checks — structure, self-consistency, encoded content, invisible characters, credential requests — and is then read line by line by a maintainer. Both are public: the checks report in the pull request and so does the review, so you can judge the depth yourself instead of taking our word for it. And the format is the last safety net: read the file before you install it.", {
        "it": "<strong>È sicuro?</strong> Ogni pull request deve superare controlli automatici bloccanti — struttura, coerenza interna, contenuto codificato, caratteri invisibili, richieste di credenziali — e poi viene letta riga per riga da un maintainer. Entrambi sono pubblici: i controlli e la revisione compaiono nella pull request, così puoi giudicare tu quanto è andata a fondo invece di crederci sulla parola. E il formato è l'ultima rete: leggi il file prima di installarlo.",
        "de": "<strong>Ist das sicher?</strong> Jeder Pull Request muss blockierende automatische Prüfungen bestehen — Struktur, innere Stimmigkeit, kodierte Inhalte, unsichtbare Zeichen, Abfragen von Zugangsdaten — und wird danach von einem Maintainer Zeile für Zeile gelesen. Beides ist öffentlich: Prüfungen und Review stehen im Pull Request, Sie können die Gründlichkeit also selbst beurteilen, statt uns zu glauben. Und das Format ist das letzte Netz: lesen Sie die Datei, bevor Sie sie installieren.",
        "es": "<strong>¿Es seguro?</strong> Cada pull request debe superar comprobaciones automáticas bloqueantes — estructura, coherencia interna, contenido codificado, caracteres invisibles, peticiones de credenciales — y después la lee línea por línea un maintainer. Ambas son públicas: las comprobaciones y la revisión constan en la pull request, así que puedes juzgar tú la profundidad en vez de creernos. Y el formato es la última red: lee el archivo antes de instalarlo.",
    }),
    ("<strong>Who reviews?</strong> Today, the AGORÀ Intelligence team. The library is young and the team is small, which is why every check that can be automated is automated and every review sits in a public pull request. As the library grows, review capacity is the thing that has to grow with it — a merge here will never mean less than a person having read the file.", {
        "it": "<strong>Chi revisiona?</strong> Oggi il team di AGORÀ Intelligence. La libreria è giovane e il team è piccolo: per questo tutto ciò che si può automatizzare è automatizzato, e ogni revisione sta in una pull request pubblica. Man mano che la libreria cresce, la capacità di revisione è la cosa che deve crescere con lei — un merge qui non significherà mai meno di una persona che ha letto il file.",
        "de": "<strong>Wer prüft?</strong> Heute das Team von AGORÀ Intelligence. Die Bibliothek ist jung und das Team klein — deshalb ist alles automatisiert, was sich automatisieren lässt, und jede Prüfung steht in einem öffentlichen Pull Request. Wächst die Bibliothek, muss die Prüfkapazität mitwachsen: ein Merge bedeutet hier nie weniger, als dass ein Mensch die Datei gelesen hat.",
        "es": "<strong>¿Quién revisa?</strong> Hoy, el equipo de AGORÀ Intelligence. La biblioteca es joven y el equipo pequeño: por eso todo lo automatizable está automatizado y cada revisión vive en una pull request pública. A medida que la biblioteca crece, la capacidad de revisión es lo que debe crecer con ella — un merge aquí nunca significará menos que una persona habiendo leído el archivo.",
    }),
    ("<strong>What does it cost?</strong> The library is free, Apache-2.0, commercial use included — keep the license notice.", {
        "it": "<strong>Quanto costa?</strong> La libreria è gratuita, Apache-2.0, uso commerciale incluso — mantieni la nota di licenza.",
        "de": "<strong>Was kostet das?</strong> Die Bibliothek ist kostenlos, Apache-2.0, kommerzielle Nutzung eingeschlossen — den Lizenzhinweis beibehalten.",
        "es": "<strong>¿Cuánto cuesta?</strong> La biblioteca es gratuita, Apache-2.0, uso comercial incluido — conserva el aviso de licencia.",
    }),

    # --- 5. participate ---------------------------------------------------
    ("How to participate", {"it": "Come partecipare", "de": "Wie Sie mitmachen", "es": "Cómo participar"}),
    ("Browse the library, install the skill file as described in section 4, ask for the task.", {
        "it": "Sfoglia la libreria, installa il file della skill come descritto nella sezione 4, chiedi il compito.",
        "de": "Die Bibliothek durchsehen, die Skill-Datei wie in Abschnitt 4 beschrieben installieren, die Aufgabe stellen.",
        "es": "Explora la biblioteca, instala el archivo de la skill como se describe en la sección 4 y pide la tarea.",
    }),
    ('New to the craft? <a href="/write/">RFT 2: Write Your First Skill</a> — anatomy, a reviewed example, and an editor that generates a conformant file.', {
        "it": 'Sei all\'inizio? <a href="/write/">RFT 2: Write Your First Skill</a> — anatomia, un esempio revisionato e un editor che genera un file conforme. La guida è in inglese, come le skill.',
        "de": 'Neu dabei? <a href="/write/">RFT 2: Write Your First Skill</a> — Aufbau, ein geprüftes Beispiel und ein Editor, der eine konforme Datei erzeugt. Der Leitfaden ist auf Englisch, wie die Skills selbst.',
        "es": '¿Empiezas ahora? <a href="/write/">RFT 2: Write Your First Skill</a> — anatomía, un ejemplo revisado y un editor que genera un archivo conforme. La guía está en inglés, igual que las skills.',
    }),
    ("Contribute one skill per pull request — the template mirrors the security checklist.", {
        "it": "Contribuisci una skill per pull request — il template rispecchia il checklist di sicurezza.",
        "de": "Einen Skill pro Pull Request beitragen — die Vorlage spiegelt die Sicherheits-Checkliste.",
        "es": "Contribuye una skill por pull request — la plantilla refleja la lista de comprobación de seguridad.",
    }),
    ("The automated checks run, a maintainer reads it line by line, and it merges. Credit lands in the skill itself.", {
        "it": "I controlli automatici girano, un maintainer la legge riga per riga, e viene accettata. Il credito finisce nella skill stessa.",
        "de": "Die automatischen Prüfungen laufen, ein Maintainer liest ihn Zeile für Zeile, dann wird er aufgenommen. Die Nennung steht im Skill selbst.",
        "es": "Se ejecutan las comprobaciones automáticas, un maintainer la lee línea por línea y se incorpora. El crédito queda en la propia skill.",
    }),
    ('Found something dangerous in a merged skill? <a href="https://github.com/skills-commons/skills-commons/security">Report it privately</a> or write to <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>: removal, advisory, credit.', {
        "it": 'Hai trovato qualcosa di pericoloso in una skill accettata? <a href="https://github.com/skills-commons/skills-commons/security">Segnalalo in privato</a> o scrivi a <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>: rimozione, avviso pubblico, credito.',
        "de": 'Etwas Gefährliches in einem aufgenommenen Skill entdeckt? <a href="https://github.com/skills-commons/skills-commons/security">Vertraulich melden</a> oder an <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a> schreiben: Entfernung, Hinweis, Nennung.',
        "es": '¿Has encontrado algo peligroso en una skill incorporada? <a href="https://github.com/skills-commons/skills-commons/security">Repórtalo en privado</a> o escribe a <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>: retirada, aviso público, crédito.',
    }),

    # --- cta and footer ---------------------------------------------------
    ("Browse the library →", {
        "it": "Sfoglia la libreria →", "de": "Bibliothek ansehen →", "es": "Explorar la biblioteca →",
    }),
    ("Certified catalog", {
        "it": "Catalogo certificato", "de": "Zertifizierter Katalog", "es": "Catálogo certificado",
    }),
    ('Seeded &amp; maintained by <a href="https://agora-intelligence.com">AGORÀ Intelligence</a> — every merge reviewed by the team', {
        "it": 'Avviata e mantenuta da <a href="https://agora-intelligence.com">AGORÀ Intelligence</a> — ogni accettazione è revisionata dal team',
        "de": 'Initiiert und gepflegt von <a href="https://agora-intelligence.com">AGORÀ Intelligence</a> — jede Aufnahme wird vom Team geprüft',
        "es": 'Iniciada y mantenida por <a href="https://agora-intelligence.com">AGORÀ Intelligence</a> — cada incorporación la revisa el equipo',
    }),
]

# The guide at /write/. Explanations translate; the editor form, the annotated
# example and everything the reader copies stay English, because what you type
# into that form becomes the skill — and skills in this library are English.
W: list[tuple[str, dict[str, str]]] = [
    ("Skills Commons — RFT 2: Write Your First Skill", {
        "it": "Skills Commons — RFT 2: Scrivi la tua prima skill",
        "de": "Skills Commons — RFT 2: Schreiben Sie Ihren ersten Skill",
        "es": "Skills Commons — RFT 2: Escribe tu primera skill",
    }),
    ("Write Your First Skill", {
        "it": "Scrivi la tua prima skill",
        "de": "Schreiben Sie Ihren ersten Skill",
        "es": "Escribe tu primera skill",
    }),
    ("Request For Trust: 2\nCategory: Craft", {
        "it": "Richiesta di Fiducia: 2\nCategoria: Mestiere",
        "de": "Request For Trust: 2\nKategorie: Handwerk",
        "es": "Solicitud de Confianza: 2\nCategoría: Oficio",
    }),
    ("Status: LIVING DOCUMENT", {
        "it": "Stato: DOCUMENTO VIVO",
        "de": "Status: LEBENDES DOKUMENT",
        "es": "Estado: DOCUMENTO VIVO",
    }),
    ('<a href="/">← RFT 1: the library</a>', {
        "it": '<a href="/it/">← RFT 1: la libreria</a>',
        "de": '<a href="/de/">← RFT 1: die Bibliothek</a>',
        "es": '<a href="/es/">← RFT 1: la biblioteca</a>',
    }),
    ("Learn the anatomy, study a reviewed example, <em>generate the file below</em>.", {
        "it": "Impara l'anatomia, studia un esempio revisionato, <em>genera il file qui sotto</em>.",
        "de": "Den Aufbau lernen, ein geprüftes Beispiel studieren, <em>die Datei unten erzeugen</em>.",
        "es": "Aprende la anatomía, estudia un ejemplo revisado, <em>genera el archivo abajo</em>.",
    }),
    ("A skill is a plain-text method your reader hands to an AI assistant. Writing one is closer to writing a procedure for a sharp new colleague than to prompt tinkering: you define the inputs, the steps, the output contract, and the rules that hold when things get ambiguous. This document teaches the anatomy, shows a reviewed example, lists what reviews reject, and ends with an editor that generates a spec-conformant file.", {
        "it": "Una skill è un metodo in testo semplice che il lettore consegna a un assistente AI. Scriverne una assomiglia più a redigere una procedura per un collega nuovo e sveglio che a smanettare con i prompt: definisci gli input, i passi, il contratto di uscita e le regole che reggono quando le cose diventano ambigue. Questo documento insegna l'anatomia, mostra un esempio revisionato, elenca cosa viene respinto in revisione e si chiude con un editor che genera un file conforme alla specifica.",
        "de": "Ein Skill ist eine Methode in Klartext, die Ihr Leser einem KI-Assistenten übergibt. Einen zu schreiben ähnelt eher dem Verfassen einer Arbeitsanweisung für eine kluge neue Kollegin als dem Herumprobieren an Prompts: Sie legen die Eingaben fest, die Schritte, den Ausgabevertrag und die Regeln, die tragen, wenn es mehrdeutig wird. Dieses Dokument vermittelt den Aufbau, zeigt ein geprüftes Beispiel, listet die häufigen Ablehnungsgründe auf und endet mit einem Editor, der eine spezifikationskonforme Datei erzeugt.",
        "es": "Una skill es un método en texto plano que tu lector entrega a un asistente de IA. Escribir una se parece más a redactar un procedimiento para un compañero nuevo y despierto que a trastear con prompts: defines las entradas, los pasos, el contrato de salida y las reglas que aguantan cuando las cosas se vuelven ambiguas. Este documento enseña la anatomía, muestra un ejemplo revisado, enumera lo que se rechaza en la revisión y termina con un editor que genera un archivo conforme a la especificación.",
    }),

    # --- 1. anatomy -------------------------------------------------------
    ("Anatomy of a skill", {
        "it": "Anatomia di una skill", "de": "Aufbau eines Skills", "es": "Anatomía de una skill",
    }),
    ('<strong>Frontmatter.</strong> <code>name</code> in kebab-case, matching the filename. <code>description</code> carries two jobs in one paragraph: what the skill does, and — crucially — <em>when to activate it</em> ("Use when asked to…"). Assistants pick skills by this field; a vague description means a skill that sleeps forever. Version, license, authors close the block.', {
        "it": '<strong>Frontmatter.</strong> <code>name</code> in kebab-case, uguale al nome del file. <code>description</code> svolge due compiti in un paragrafo: cosa fa la skill e — soprattutto — <em>quando attivarla</em> ("Use when asked to…"). Gli assistenti scelgono le skill da questo campo; una descrizione vaga produce una skill che dorme per sempre. Versione, licenza e autori chiudono il blocco.',
        "de": '<strong>Frontmatter.</strong> <code>name</code> in Kebab-Case, identisch mit dem Dateinamen. <code>description</code> erfüllt zwei Aufgaben in einem Absatz: was der Skill tut und — entscheidend — <em>wann er greifen soll</em> („Use when asked to…"). Assistenten wählen Skills über dieses Feld; eine vage Beschreibung ergibt einen Skill, der ewig schläft. Version, Lizenz und Autoren schließen den Block ab.',
        "es": '<strong>Frontmatter.</strong> <code>name</code> en kebab-case, igual al nombre del archivo. <code>description</code> cumple dos funciones en un párrafo: qué hace la skill y — sobre todo — <em>cuándo activarla</em> ("Use when asked to…"). Los asistentes eligen skills por este campo; una descripción vaga produce una skill que duerme para siempre. Versión, licencia y autores cierran el bloque.',
    }),
    ('<strong>Identity paragraph.</strong> Two or three sentences after the title, second person: who the assistant becomes and what it refuses to compromise on. This is voice and standard in one breath: "You write commit messages worthy of the permanent record."', {
        "it": '<strong>Paragrafo di identità.</strong> Due o tre frasi dopo il titolo, in seconda persona: chi diventa l\'assistente e su cosa rifiuta di transigere. È voce e standard in un respiro solo: "You write commit messages worthy of the permanent record."',
        "de": '<strong>Identitätsabsatz.</strong> Zwei bis drei Sätze nach dem Titel, in der zweiten Person: wer der Assistent wird und wobei er keine Abstriche macht. Das ist Tonfall und Maßstab in einem Atemzug: „You write commit messages worthy of the permanent record."',
        "es": '<strong>Párrafo de identidad.</strong> Dos o tres frases tras el título, en segunda persona: en quién se convierte el asistente y en qué se niega a transigir. Es voz y estándar en un mismo aliento: "You write commit messages worthy of the permanent record."',
    }),
    ("<strong>Inputs.</strong> The numbered list of what the skill needs, with the required ones marked and a rule for gaps (ask and stop, or proceed with labeled assumptions). Ask once — a skill that interrogates in rounds exhausts its user.", {
        "it": "<strong>Inputs.</strong> L'elenco numerato di ciò che la skill richiede, con i campi obbligatori segnati e una regola per i buchi (chiedi e fermati, oppure procedi con assunzioni dichiarate). Chiedi una volta sola — una skill che interroga a raffica sfinisce chi la usa.",
        "de": "<strong>Inputs.</strong> Die nummerierte Liste dessen, was der Skill braucht, mit markierten Pflichtangaben und einer Regel für Lücken (nachfragen und anhalten, oder mit ausgewiesenen Annahmen weitermachen). Einmal fragen — ein Skill, der in Runden verhört, zermürbt seine Nutzer.",
        "es": "<strong>Inputs.</strong> La lista numerada de lo que la skill necesita, con los obligatorios marcados y una regla para los huecos (pregunta y detente, o sigue con supuestos declarados). Pregunta una sola vez — una skill que interroga por tandas agota a quien la usa.",
    }),
    ('<strong>Method.</strong> Numbered steps, each one decidable: an instruction the assistant can follow or verify, with the judgment rules spelled out ("when X exceeds Y, do Z"). Steps that say "be thorough" delegate the hard part back to chance.', {
        "it": '<strong>Method.</strong> Passi numerati, ciascuno decidibile: un\'istruzione che l\'assistente può seguire o verificare, con le regole di giudizio esplicite ("quando X supera Y, fai Z"). I passi che dicono "sii accurato" restituiscono al caso la parte difficile.',
        "de": '<strong>Method.</strong> Nummerierte Schritte, jeder entscheidbar: eine Anweisung, der der Assistent folgen oder die er prüfen kann, mit ausformulierten Ermessensregeln („wenn X über Y liegt, tue Z"). Schritte wie „sei gründlich" geben den schwierigen Teil an den Zufall zurück.',
        "es": '<strong>Method.</strong> Pasos numerados, cada uno decidible: una instrucción que el asistente puede seguir o verificar, con las reglas de criterio explícitas ("cuando X supere Y, haz Z"). Los pasos que dicen "sé minucioso" devuelven al azar la parte difícil.',
    }),
    ("<strong>Output format.</strong> The contract: sections, order, lengths where they matter. Two runs of the same skill should produce the same shape — the format section is what makes a skill repeatable instead of improvised.", {
        "it": "<strong>Output format.</strong> Il contratto: sezioni, ordine, lunghezze dove contano. Due esecuzioni della stessa skill devono produrre la stessa forma — la sezione del formato è ciò che rende una skill ripetibile invece che improvvisata.",
        "de": "<strong>Output format.</strong> Der Vertrag: Abschnitte, Reihenfolge, Längen dort, wo sie zählen. Zwei Läufe desselben Skills sollten dieselbe Form ergeben — der Formatabschnitt macht einen Skill wiederholbar statt improvisiert.",
        "es": "<strong>Output format.</strong> El contrato: secciones, orden y longitudes donde importan. Dos ejecuciones de la misma skill deben producir la misma forma — la sección de formato es lo que hace una skill repetible en lugar de improvisada.",
    }),
    ('<strong>Rules.</strong> The invariants that survive every edge case: what gets refused, what gets labeled, what degrades and how. State how the skill behaves when a capability is missing — "mark N.A. with a reason" beats a guessed success.', {
        "it": '<strong>Rules.</strong> Gli invarianti che sopravvivono a ogni caso limite: cosa viene rifiutato, cosa viene etichettato, cosa degrada e come. Dichiara come si comporta la skill quando manca una capacità — "segna N.D. con una motivazione" vale più di un successo indovinato.',
        "de": '<strong>Rules.</strong> Die Invarianten, die jeden Grenzfall überstehen: was abgelehnt wird, was gekennzeichnet wird, was wie degradiert. Halten Sie fest, wie sich der Skill verhält, wenn eine Fähigkeit fehlt — „mit Begründung als n. v. markieren" schlägt einen geratenen Erfolg.',
        "es": '<strong>Rules.</strong> Los invariantes que sobreviven a cada caso límite: qué se rechaza, qué se etiqueta, qué se degrada y cómo. Declara cómo se comporta la skill cuando falta una capacidad — "marca N.D. con un motivo" vale más que un éxito adivinado.',
    }),

    # --- 2 & 3 ------------------------------------------------------------
    ("A reviewed example, annotated", {
        "it": "Un esempio revisionato, annotato",
        "de": "Ein geprüftes Beispiel, kommentiert",
        "es": "Un ejemplo revisado, anotado",
    }),
    ("What reviews reject", {
        "it": "Cosa viene respinto in revisione",
        "de": "Was in der Prüfung abgelehnt wird",
        "es": "Qué se rechaza en la revisión",
    }),
    ("Every submission is read line by line by a maintainer, after the automated checks pass. These are the recurring rejections — write with this list open:", {
        "it": "Ogni proposta viene letta riga per riga da un maintainer, dopo che i controlli automatici sono passati. Questi sono i motivi di rifiuto ricorrenti — scrivi tenendo aperta questa lista:",
        "de": "Jede Einreichung wird nach bestandenen automatischen Prüfungen von einem Maintainer Zeile für Zeile gelesen. Das sind die wiederkehrenden Ablehnungsgründe — schreiben Sie mit dieser Liste vor Augen:",
        "es": "Cada propuesta la lee línea por línea un maintainer, después de que pasen las comprobaciones automáticas. Estos son los rechazos recurrentes — escribe con esta lista abierta:",
    }),
    ('<strong>Undecidable steps.</strong> "Analyze carefully", "be helpful", "use best judgment" with zero criteria. A step earns its place when the assistant can tell whether it followed it.', {
        "it": '<strong>Passi non decidibili.</strong> "Analizza con attenzione", "sii utile", "usa il buon senso" senza alcun criterio. Un passo si merita il suo posto quando l\'assistente può dire se lo ha seguito.',
        "de": '<strong>Nicht entscheidbare Schritte.</strong> „Sorgfältig analysieren", „hilfreich sein", „nach bestem Ermessen" ohne jedes Kriterium. Ein Schritt verdient seinen Platz, wenn der Assistent feststellen kann, ob er ihn befolgt hat.',
        "es": '<strong>Pasos no decidibles.</strong> "Analiza con cuidado", "sé útil", "usa tu criterio" sin criterio alguno. Un paso se gana su lugar cuando el asistente puede saber si lo ha cumplido.',
    }),
    ("<strong>Missing degradation.</strong> The method assumes web access, code execution or file tools, and says zero about what happens on an assistant that lacks them. Declare the fallback.", {
        "it": "<strong>Degradazione assente.</strong> Il metodo dà per scontati accesso al web, esecuzione di codice o strumenti sui file, e tace su cosa succede su un assistente che ne è privo. Dichiara il ripiego.",
        "de": "<strong>Fehlende Degradation.</strong> Die Methode setzt Webzugriff, Codeausführung oder Dateiwerkzeuge voraus und sagt nichts darüber, was auf einem Assistenten ohne sie geschieht. Nennen Sie den Rückfall.",
        "es": "<strong>Degradación ausente.</strong> El método da por hechos el acceso web, la ejecución de código o las herramientas de archivos, y calla sobre qué ocurre en un asistente que carece de ellos. Declara la alternativa.",
    }),
    ("<strong>Hidden or encoded content.</strong> Base64 blobs, zero-width characters, instructions to fetch remote content at runtime. Plain readable markdown is the deal: what the reader sees is what the agent executes.", {
        "it": "<strong>Contenuto nascosto o codificato.</strong> Blob base64, caratteri a larghezza zero, istruzioni per scaricare contenuti remoti a runtime. Il patto è markdown leggibile in chiaro: quello che il lettore vede è quello che l'agente esegue.",
        "de": "<strong>Versteckte oder kodierte Inhalte.</strong> Base64-Blobs, Zero-Width-Zeichen, Anweisungen zum Nachladen entfernter Inhalte zur Laufzeit. Die Abmachung lautet: schlichtes, lesbares Markdown — was der Leser sieht, führt der Agent aus.",
        "es": "<strong>Contenido oculto o codificado.</strong> Blobs base64, caracteres de ancho cero, instrucciones para descargar contenido remoto en tiempo de ejecución. El trato es markdown legible en claro: lo que el lector ve es lo que el agente ejecuta.",
    }),
    ("<strong>Exfiltration paths.</strong> Steps that send user data anywhere. A skill transforms what it is given, in place.", {
        "it": "<strong>Vie di esfiltrazione.</strong> Passi che spediscono i dati dell'utente da qualche parte. Una skill trasforma ciò che riceve, sul posto.",
        "de": "<strong>Exfiltrationswege.</strong> Schritte, die Nutzerdaten irgendwohin senden. Ein Skill verarbeitet, was er bekommt, an Ort und Stelle.",
        "es": "<strong>Vías de exfiltración.</strong> Pasos que envían los datos del usuario a alguna parte. Una skill transforma lo que recibe, en el sitio.",
    }),
    ('<strong>Vendor lock phrasing.</strong> "Use the WebFetch tool", "call Code Interpreter". Name capabilities ("when live web access is available"), and the skill works on every assistant.', {
        "it": '<strong>Formule legate a un fornitore.</strong> "Usa lo strumento WebFetch", "chiama Code Interpreter". Nomina le capacità ("quando è disponibile l\'accesso live al web") e la skill funziona su ogni assistente.',
        "de": '<strong>Anbieterspezifische Formulierungen.</strong> „Nutze das WebFetch-Tool", „rufe Code Interpreter auf". Benennen Sie Fähigkeiten („wenn Live-Webzugriff verfügbar ist"), dann läuft der Skill auf jedem Assistenten.',
        "es": '<strong>Fórmulas atadas a un proveedor.</strong> "Usa la herramienta WebFetch", "llama a Code Interpreter". Nombra capacidades ("cuando hay acceso web en vivo") y la skill funciona en cualquier asistente.',
    }),
    ("<strong>Marketing in the method.</strong> Superlatives about the skill itself, links to products, self-promotion. The method speaks through its steps.", {
        "it": "<strong>Marketing dentro il metodo.</strong> Superlativi sulla skill stessa, link a prodotti, autopromozione. Il metodo parla attraverso i suoi passi.",
        "de": "<strong>Marketing in der Methode.</strong> Superlative über den Skill selbst, Produktlinks, Eigenwerbung. Die Methode spricht durch ihre Schritte.",
        "es": "<strong>Marketing dentro del método.</strong> Superlativos sobre la propia skill, enlaces a productos, autopromoción. El método habla a través de sus pasos.",
    }),
    ("<strong>A missing output contract.</strong> Ten sharp method steps, and zero words on what the deliverable looks like. The format section is half the value.", {
        "it": "<strong>Contratto di uscita mancante.</strong> Dieci passi di metodo affilati, e zero parole su che aspetto ha il risultato. La sezione del formato è metà del valore.",
        "de": "<strong>Fehlender Ausgabevertrag.</strong> Zehn präzise Methodenschritte und kein Wort dazu, wie das Ergebnis aussieht. Der Formatabschnitt ist die halbe Miete.",
        "es": "<strong>Contrato de salida ausente.</strong> Diez pasos de método afilados y ni una palabra sobre qué aspecto tiene el entregable. La sección de formato es la mitad del valor.",
    }),

    # --- 4 & 5 ------------------------------------------------------------
    ("The editor — generate your file", {
        "it": "L'editor — genera il tuo file",
        "de": "Der Editor — Ihre Datei erzeugen",
        "es": "El editor — genera tu archivo",
    }),
    ("Fill the sections; the editor assembles a spec-conformant <code>.md</code>. Everything runs in this page — your draft touches zero servers.", {
        "it": "Compila le sezioni; l'editor assembla un <code>.md</code> conforme alla specifica. Tutto gira dentro questa pagina — la tua bozza non tocca alcun server. <strong>Il modulo resta in inglese: quello che scrivi diventa la skill, e le skill di questa libreria sono in inglese.</strong>",
        "de": "Füllen Sie die Abschnitte aus; der Editor setzt eine spezifikationskonforme <code>.md</code> zusammen. Alles läuft in dieser Seite — Ihr Entwurf berührt keinen Server. <strong>Das Formular bleibt englisch: was Sie hineinschreiben, wird der Skill, und die Skills dieser Bibliothek sind englisch.</strong>",
        "es": "Rellena las secciones; el editor ensambla un <code>.md</code> conforme a la especificación. Todo se ejecuta en esta página — tu borrador no toca ningún servidor. <strong>El formulario sigue en inglés: lo que escribas se convierte en la skill, y las skills de esta biblioteca están en inglés.</strong>",
    }),
    ("Submit it", {"it": "Proponila", "de": "Einreichen", "es": "Propónla"}),
    ("Run your skill on a real case first — the sample output tells you where the method is thin.", {
        "it": "Prima esegui la tua skill su un caso vero — il risultato di prova ti dice dove il metodo è sottile.",
        "de": "Lassen Sie Ihren Skill zuerst an einem echten Fall laufen — die Probeausgabe zeigt, wo die Methode dünn ist.",
        "es": "Ejecuta primero tu skill en un caso real — la salida de prueba te dice dónde el método es delgado.",
    }),
    ('Fork <a href="https://github.com/skills-commons/skills-commons">the library</a>, add your file under <code>skills/&lt;category&gt;/&lt;name&gt;.md</code>, open one pull request per skill.', {
        "it": 'Forka <a href="https://github.com/skills-commons/skills-commons">la libreria</a>, aggiungi il file sotto <code>skills/&lt;category&gt;/&lt;name&gt;.md</code>, apri una pull request per skill.',
        "de": 'Forken Sie <a href="https://github.com/skills-commons/skills-commons">die Bibliothek</a>, legen Sie Ihre Datei unter <code>skills/&lt;category&gt;/&lt;name&gt;.md</code> ab und öffnen Sie einen Pull Request pro Skill.',
        "es": 'Haz un fork de <a href="https://github.com/skills-commons/skills-commons">la biblioteca</a>, añade tu archivo en <code>skills/&lt;category&gt;/&lt;name&gt;.md</code> y abre una pull request por skill.',
    }),
    ('Sign every commit with <code>git commit -s</code>. That one flag adds the <code>Signed-off-by</code> line certifying you may release the work under Apache-2.0 — the <a href="https://github.com/skills-commons/skills-commons/blob/main/DCO.txt">Developer Certificate of Origin</a>. A required check verifies it, so a PR merges once it is there. Already committed without it? <code>git commit --amend -s --no-edit</code> for the last one, <code>git rebase --signoff main</code> for several, then <code>git push --force-with-lease</code>.', {
        "it": 'Firma ogni commit con <code>git commit -s</code>. Quel flag aggiunge la riga <code>Signed-off-by</code> con cui certifichi di poter rilasciare il lavoro sotto Apache-2.0 — il <a href="https://github.com/skills-commons/skills-commons/blob/main/DCO.txt">Developer Certificate of Origin</a>. Un controllo obbligatorio lo verifica, quindi la PR si unisce quando c\'è. Hai già committato senza? <code>git commit --amend -s --no-edit</code> per l\'ultimo, <code>git rebase --signoff main</code> per diversi, poi <code>git push --force-with-lease</code>.',
        "de": 'Signieren Sie jeden Commit mit <code>git commit -s</code>. Dieses eine Flag fügt die Zeile <code>Signed-off-by</code> hinzu, mit der Sie bestätigen, die Arbeit unter Apache-2.0 freigeben zu dürfen — das <a href="https://github.com/skills-commons/skills-commons/blob/main/DCO.txt">Developer Certificate of Origin</a>. Eine Pflichtprüfung kontrolliert das, der Pull Request lässt sich also zusammenführen, sobald sie da ist. Schon ohne committet? <code>git commit --amend -s --no-edit</code> für den letzten, <code>git rebase --signoff main</code> für mehrere, dann <code>git push --force-with-lease</code>.',
        "es": 'Firma cada commit con <code>git commit -s</code>. Ese único flag añade la línea <code>Signed-off-by</code> con la que certificas que puedes publicar el trabajo bajo Apache-2.0 — el <a href="https://github.com/skills-commons/skills-commons/blob/main/DCO.txt">Developer Certificate of Origin</a>. Una comprobación obligatoria lo verifica, así que la PR se incorpora en cuanto está. ¿Ya has hecho commit sin ella? <code>git commit --amend -s --no-edit</code> para el último, <code>git rebase --signoff main</code> para varios, y luego <code>git push --force-with-lease</code>.',
    }),
    ("The automated checks run, then a maintainer reads it line by line. Credit lands in the file itself.", {
        "it": "Girano i controlli automatici, poi un maintainer lo legge riga per riga. Il credito finisce nel file stesso.",
        "de": "Die automatischen Prüfungen laufen, dann liest ein Maintainer sie Zeile für Zeile. Die Nennung steht in der Datei selbst.",
        "es": "Se ejecutan las comprobaciones automáticas, luego un maintainer lo lee línea por línea. El crédito queda en el propio archivo.",
    }),
    ('<span><a href="/">RFT 1: the library</a> · Apache-2.0', {
        "it": '<span><a href="/it/">RFT 1: la libreria</a> · Apache-2.0',
        "de": '<span><a href="/de/">RFT 1: die Bibliothek</a> · Apache-2.0',
        "es": '<span><a href="/es/">RFT 1: la biblioteca</a> · Apache-2.0',
    }),
]

# The privacy notice. Written from what the site actually does, so the
# translations describe the same processing, not a softer version of it.
P: list[tuple[str, dict[str, str]]] = [
    ("Skills Commons — Privacy notice", {
        "it": "Skills Commons — Informativa privacy",
        "de": "Skills Commons — Datenschutzhinweis",
        "es": "Skills Commons — Aviso de privacidad",
    }),
    ("What Skills Commons collects, why, and how to say no. Analytics run only with consent; the library needs no account at all.", {
        "it": "Cosa raccoglie Skills Commons, perché, e come dire di no. Le statistiche partono solo con il consenso; la libreria non richiede alcun account.",
        "de": "Was Skills Commons erhebt, warum, und wie Sie ablehnen. Die Messung läuft nur mit Einwilligung; die Bibliothek braucht überhaupt kein Konto.",
        "es": "Qué recoge Skills Commons, por qué y cómo decir que no. La analítica se activa solo con consentimiento; la biblioteca no requiere cuenta alguna.",
    }),
    ("What Skills Commons collects, why, and how to say no.", {
        "it": "Cosa raccoglie Skills Commons, perché, e come dire di no.",
        "de": "Was Skills Commons erhebt, warum, und wie Sie ablehnen.",
        "es": "Qué recoge Skills Commons, por qué y cómo decir que no.",
    }),
    ("Privacy notice\nCategory: Standards of care", {
        "it": "Informativa privacy\nCategoria: Standard di diligenza",
        "de": "Datenschutzhinweis\nKategorie: Sorgfaltsstandards",
        "es": "Aviso de privacidad\nCategoría: Estándares de diligencia",
    }),
    ("Controller: AGORÀ Intelligence S.r.l.\nLast updated: 10 August 2026", {
        "it": "Titolare: AGORÀ Intelligence S.r.l.\nUltimo aggiornamento: 10 agosto 2026",
        "de": "Verantwortlicher: AGORÀ Intelligence S.r.l.\nStand: 10. August 2026",
        "es": "Responsable: AGORÀ Intelligence S.r.l.\nÚltima actualización: 10 de agosto de 2026",
    }),
    ("<h1>Privacy notice</h1>", {
        "it": "<h1>Informativa privacy</h1>",
        "de": "<h1>Datenschutzhinweis</h1>",
        "es": "<h1>Aviso de privacidad</h1>",
    }),
    ("What this site collects, why, and how to say no.", {
        "it": "Cosa raccoglie questo sito, perché, e come dire di no.",
        "de": "Was diese Website erhebt, warum, und wie Sie ablehnen.",
        "es": "Qué recoge este sitio, por qué y cómo decir que no.",
    }),
    ("Reading the library, downloading a skill and using the editor require no account and collect nothing about you. Analytics run only after you agree, and declining changes nothing about what you can read or download. The one place that stores personal data is the builder, and only once you choose to sign in with GitHub.", {
        "it": "Leggere la libreria, scaricare una skill e usare l'editor non richiedono alcun account e non raccolgono nulla su di te. Le statistiche partono solo dopo il tuo consenso, e rifiutare lascia intatto tutto ciò che puoi leggere e scaricare. L'unico punto in cui vengono conservati dati personali è il builder, e soltanto se scegli di accedere con GitHub.",
        "de": "Die Bibliothek zu lesen, einen Skill herunterzuladen und den Editor zu nutzen verlangt kein Konto und erhebt nichts über Sie. Die Messung startet erst nach Ihrer Einwilligung, und eine Ablehnung ändert nichts daran, was Sie lesen oder herunterladen können. Der einzige Ort, an dem personenbezogene Daten gespeichert werden, ist der Builder — und nur, wenn Sie sich mit GitHub anmelden.",
        "es": "Leer la biblioteca, descargar una skill y usar el editor no requieren cuenta y no recogen nada sobre ti. La analítica se activa solo tras tu consentimiento, y rechazar no cambia nada de lo que puedes leer o descargar. El único lugar donde se guardan datos personales es el builder, y solo si eliges entrar con GitHub.",
    }),
    ("Who is responsible", {
        "it": "Chi è il titolare", "de": "Wer verantwortlich ist", "es": "Quién es el responsable",
    }),
    ('The controller is <strong>AGORÀ Intelligence S.r.l.</strong>, Italy, which maintains Skills Commons. For anything in this notice, including the requests in section 6, write to <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>.', {
        "it": 'Il titolare del trattamento è <strong>AGORÀ Intelligence S.r.l.</strong>, Italia, che mantiene Skills Commons. Per qualsiasi punto di questa informativa, comprese le richieste della sezione 6, scrivi a <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>.',
        "de": 'Verantwortlicher ist <strong>AGORÀ Intelligence S.r.l.</strong>, Italien, die Skills Commons betreibt. Zu allem in diesem Hinweis, einschließlich der Anliegen aus Abschnitt 6, schreiben Sie an <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>.',
        "es": 'El responsable del tratamiento es <strong>AGORÀ Intelligence S.r.l.</strong>, Italia, que mantiene Skills Commons. Para cualquier punto de este aviso, incluidas las solicitudes de la sección 6, escribe a <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>.',
    }),
    ("What runs on this site", {
        "it": "Cosa gira su questo sito", "de": "Was auf dieser Website läuft", "es": "Qué se ejecuta en este sitio",
    }),
    ("<tr><th>Purpose</th><th>What is processed</th><th>Legal basis</th><th>Kept for</th></tr>", {
        "it": "<tr><th>Finalità</th><th>Cosa viene trattato</th><th>Base giuridica</th><th>Conservazione</th></tr>",
        "de": "<tr><th>Zweck</th><th>Was verarbeitet wird</th><th>Rechtsgrundlage</th><th>Speicherdauer</th></tr>",
        "es": "<tr><th>Finalidad</th><th>Qué se trata</th><th>Base jurídica</th><th>Conservación</th></tr>",
    }),
    ("<tr><td>Serving the pages</td><td>Your IP address and browser, in the hosting provider's server logs</td><td>Legitimate interest in delivering and securing the site</td><td>By the provider, per its own policy</td></tr>", {
        "it": "<tr><td>Erogazione delle pagine</td><td>Indirizzo IP e browser, nei log del fornitore di hosting</td><td>Legittimo interesse a erogare e proteggere il sito</td><td>Dal fornitore, secondo la sua policy</td></tr>",
        "de": "<tr><td>Auslieferung der Seiten</td><td>IP-Adresse und Browser, in den Serverprotokollen des Hosters</td><td>Berechtigtes Interesse an Bereitstellung und Absicherung</td><td>Durch den Hoster, nach dessen Richtlinie</td></tr>",
        "es": "<tr><td>Entrega de las páginas</td><td>Tu IP y navegador, en los registros del proveedor de alojamiento</td><td>Interés legítimo en servir y proteger el sitio</td><td>Por el proveedor, según su política</td></tr>",
    }),
    ("<tr><td>Audience measurement</td><td>Anonymous usage statistics via Google Analytics 4, with IP anonymisation on</td><td><strong>Your consent</strong>, asked before anything loads</td><td>14 months</td></tr>", {
        "it": "<tr><td>Misurazione del pubblico</td><td>Statistiche d'uso anonime tramite Google Analytics 4, con anonimizzazione IP attiva</td><td><strong>Il tuo consenso</strong>, chiesto prima di qualsiasi caricamento</td><td>14 mesi</td></tr>",
        "de": "<tr><td>Reichweitenmessung</td><td>Anonyme Nutzungsstatistiken über Google Analytics 4, mit IP-Anonymisierung</td><td><strong>Ihre Einwilligung</strong>, vor jedem Laden erfragt</td><td>14 Monate</td></tr>",
        "es": "<tr><td>Medición de audiencia</td><td>Estadísticas de uso anónimas mediante Google Analytics 4, con anonimización de IP</td><td><strong>Tu consentimiento</strong>, solicitado antes de cargar nada</td><td>14 meses</td></tr>",
    }),
    ("<tr><td>Remembering your cookie choice</td><td>One entry in your browser's local storage (<code>sc-consent</code>)</td><td>Strictly necessary for a choice you made</td><td>Until you clear it</td></tr>", {
        "it": "<tr><td>Ricordare la tua scelta sui cookie</td><td>Una voce nella memoria locale del browser (<code>sc-consent</code>)</td><td>Strettamente necessaria per una scelta che hai fatto</td><td>Finché non la cancelli</td></tr>",
        "de": "<tr><td>Ihre Cookie-Entscheidung merken</td><td>Ein Eintrag im lokalen Speicher des Browsers (<code>sc-consent</code>)</td><td>Unbedingt erforderlich für eine von Ihnen getroffene Wahl</td><td>Bis Sie ihn löschen</td></tr>",
        "es": "<tr><td>Recordar tu elección sobre cookies</td><td>Una entrada en el almacenamiento local del navegador (<code>sc-consent</code>)</td><td>Estrictamente necesaria para una elección que hiciste</td><td>Hasta que la borres</td></tr>",
    }),
    ("Until you accept, Google Analytics loads in denied mode: it sets no analytics cookies and records no identifiers. Decline and it stays that way. There is no advertising, no profiling, no cross-site tracking and no sale of data, on any page.", {
        "it": "Finché non accetti, Google Analytics resta in modalità negata: non scrive cookie di misurazione e non registra identificatori. Se rifiuti, resta così. Su nessuna pagina esistono pubblicità, profilazione, tracciamento fra siti o vendita di dati.",
        "de": "Bis Sie zustimmen, läuft Google Analytics im abgelehnten Modus: keine Analyse-Cookies, keine Kennungen. Lehnen Sie ab, bleibt es dabei. Auf keiner Seite gibt es Werbung, Profilbildung, seitenübergreifendes Tracking oder Datenverkauf.",
        "es": "Hasta que aceptes, Google Analytics permanece en modo denegado: no escribe cookies de medición ni registra identificadores. Si rechazas, sigue así. En ninguna página hay publicidad, perfilado, seguimiento entre sitios ni venta de datos.",
    }),
    ("The builder, if you sign in", {
        "it": "Il builder, se accedi", "de": "Der Builder, wenn Sie sich anmelden", "es": "El builder, si inicias sesión",
    }),
    ('<a href="https://build.skills-commons.org">build.skills-commons.org</a> is optional. Visiting it collects nothing; signing in with GitHub creates an account, and only then does it store your GitHub numeric id, username and avatar URL, plus an access token held encrypted so it can open a pull request in your name. Sessions expire after 30 days. The legal basis is the contract you enter by signing in; the data lives on a server in Frankfurt, Germany. Ask at the address above and the account and its data are deleted.', {
        "it": '<a href="https://build.skills-commons.org">build.skills-commons.org</a> è facoltativo. Visitarlo non raccoglie nulla; accedere con GitHub crea un account, e solo allora vengono conservati il tuo id numerico GitHub, il nome utente, l\'URL dell\'avatar e un token di accesso, custodito cifrato per poter aprire una pull request a tuo nome. Le sessioni scadono dopo 30 giorni. La base giuridica è il contratto che concludi accedendo; i dati risiedono su un server a Francoforte, in Germania. Scrivi all\'indirizzo qui sopra e l\'account e i suoi dati vengono cancellati.',
        "de": '<a href="https://build.skills-commons.org">build.skills-commons.org</a> ist freiwillig. Der bloße Besuch erhebt nichts; die Anmeldung mit GitHub legt ein Konto an, und erst dann werden Ihre numerische GitHub-ID, der Benutzername, die Avatar-URL und ein verschlüsselt gespeichertes Zugriffstoken abgelegt, damit in Ihrem Namen ein Pull Request geöffnet werden kann. Sitzungen laufen nach 30 Tagen ab. Rechtsgrundlage ist der mit der Anmeldung geschlossene Vertrag; die Daten liegen auf einem Server in Frankfurt am Main. Auf Anfrage an die obige Adresse werden Konto und Daten gelöscht.',
        "es": '<a href="https://build.skills-commons.org">build.skills-commons.org</a> es opcional. Visitarlo no recoge nada; entrar con GitHub crea una cuenta, y solo entonces se guardan tu id numérico de GitHub, el nombre de usuario, la URL del avatar y un token de acceso, cifrado para poder abrir una pull request en tu nombre. Las sesiones caducan a los 30 días. La base jurídica es el contrato que celebras al entrar; los datos residen en un servidor de Fráncfort, Alemania. Escribe a la dirección anterior y la cuenta y sus datos se eliminan.',
    }),
    ("Who else sees anything", {
        "it": "Chi altro vede qualcosa", "de": "Wer sonst etwas sieht", "es": "Quién más ve algo",
    }),
    ("<strong>GitHub, Inc.</strong> — hosts these pages and the library. Its servers log requests.", {
        "it": "<strong>GitHub, Inc.</strong> — ospita queste pagine e la libreria. I suoi server registrano le richieste.",
        "de": "<strong>GitHub, Inc.</strong> — hostet diese Seiten und die Bibliothek. Die Server protokollieren Anfragen.",
        "es": "<strong>GitHub, Inc.</strong> — aloja estas páginas y la biblioteca. Sus servidores registran las peticiones.",
    }),
    ("<strong>Google Ireland Ltd.</strong> — audience measurement, only with your consent.", {
        "it": "<strong>Google Ireland Ltd.</strong> — misurazione del pubblico, solo con il tuo consenso.",
        "de": "<strong>Google Ireland Ltd.</strong> — Reichweitenmessung, nur mit Ihrer Einwilligung.",
        "es": "<strong>Google Ireland Ltd.</strong> — medición de audiencia, solo con tu consentimiento.",
    }),
    ("<strong>DigitalOcean, LLC</strong> — the server behind the builder, located in Germany.", {
        "it": "<strong>DigitalOcean, LLC</strong> — il server dietro il builder, situato in Germania.",
        "de": "<strong>DigitalOcean, LLC</strong> — der Server hinter dem Builder, Standort Deutschland.",
        "es": "<strong>DigitalOcean, LLC</strong> — el servidor tras el builder, ubicado en Alemania.",
    }),
    ("Transfers outside the European Economic Area rest on the European Commission's standard contractual clauses. Nobody else receives your data.", {
        "it": "I trasferimenti fuori dallo Spazio economico europeo si fondano sulle clausole contrattuali tipo della Commissione europea. Nessun altro riceve i tuoi dati.",
        "de": "Übermittlungen außerhalb des Europäischen Wirtschaftsraums stützen sich auf die Standardvertragsklauseln der Europäischen Kommission. Niemand sonst erhält Ihre Daten.",
        "es": "Las transferencias fuera del Espacio Económico Europeo se basan en las cláusulas contractuales tipo de la Comisión Europea. Nadie más recibe tus datos.",
    }),
    ("Changing your mind", {
        "it": "Cambiare idea", "de": "Ihre Meinung ändern", "es": "Cambiar de opinión",
    }),
    ('Reopen the choice at any time from the <a href="#cookies">Cookies</a> link in the footer of any page, and pick the other option. Clearing your browser storage has the same effect: the question is asked again on your next visit.', {
        "it": 'Riapri la scelta quando vuoi dal link <a href="#cookies">Cookie</a> in fondo a qualsiasi pagina, e seleziona l\'altra opzione. Svuotare la memoria del browser ha lo stesso effetto: la domanda ricompare alla visita successiva.',
        "de": 'Öffnen Sie die Auswahl jederzeit über den Link <a href="#cookies">Cookies</a> im Fuß jeder Seite und wählen Sie die andere Option. Den Browserspeicher zu leeren wirkt genauso: Die Frage erscheint beim nächsten Besuch erneut.',
        "es": 'Reabre la elección cuando quieras desde el enlace <a href="#cookies">Cookies</a> del pie de cualquier página y elige la otra opción. Vaciar el almacenamiento del navegador tiene el mismo efecto: la pregunta reaparece en tu siguiente visita.',
    }),
    ("Your rights", {"it": "I tuoi diritti", "de": "Ihre Rechte", "es": "Tus derechos"}),
    ('Under the GDPR you may ask for access to your data, its correction or erasure, a restriction of processing, a copy in portable form, and you may object to processing based on legitimate interest. Consent, once given, can be withdrawn at any moment without affecting what came before. Write to <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>; you also have the right to complain to the Italian supervisory authority, the <a href="https://www.garanteprivacy.it">Garante per la protezione dei dati personali</a>.', {
        "it": 'Ai sensi del GDPR puoi chiedere l\'accesso ai tuoi dati, la loro rettifica o cancellazione, la limitazione del trattamento, una copia in formato portabile, e puoi opporti ai trattamenti fondati sul legittimo interesse. Il consenso, una volta prestato, è revocabile in qualsiasi momento senza pregiudicare quanto avvenuto prima. Scrivi a <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>; hai inoltre diritto di reclamo all\'autorità di controllo italiana, il <a href="https://www.garanteprivacy.it">Garante per la protezione dei dati personali</a>.',
        "de": 'Nach der DSGVO können Sie Auskunft über Ihre Daten, deren Berichtigung oder Löschung, die Einschränkung der Verarbeitung und eine Kopie in übertragbarer Form verlangen sowie der Verarbeitung auf Grundlage berechtigter Interessen widersprechen. Eine erteilte Einwilligung ist jederzeit widerrufbar, ohne dass die bisherige Verarbeitung berührt wird. Schreiben Sie an <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>; zudem steht Ihnen die Beschwerde bei der italienischen Aufsichtsbehörde zu, dem <a href="https://www.garanteprivacy.it">Garante per la protezione dei dati personali</a>.',
        "es": 'Conforme al RGPD puedes solicitar el acceso a tus datos, su rectificación o supresión, la limitación del tratamiento, una copia en formato portátil, y puedes oponerte a los tratamientos basados en el interés legítimo. El consentimiento, una vez prestado, puede retirarse en cualquier momento sin afectar a lo anterior. Escribe a <a href="mailto:hello@agora-intelligence.com">hello@agora-intelligence.com</a>; también tienes derecho a reclamar ante la autoridad de control italiana, el <a href="https://www.garanteprivacy.it">Garante per la protezione dei dati personali</a>.',
    }),
    ("Changes", {"it": "Modifiche", "de": "Änderungen", "es": "Cambios"}),
    ('The date in the header shows when this notice last changed. Its history is public in the <a href="https://github.com/skills-commons/skills-commons.github.io">site repository</a>, so every revision can be compared with the one before it.', {
        "it": 'La data in testata indica quando questa informativa è cambiata l\'ultima volta. La sua storia è pubblica nel <a href="https://github.com/skills-commons/skills-commons.github.io">repository del sito</a>, quindi ogni revisione è confrontabile con la precedente.',
        "de": 'Das Datum im Kopf zeigt, wann dieser Hinweis zuletzt geändert wurde. Seine Historie ist im <a href="https://github.com/skills-commons/skills-commons.github.io">Repository der Website</a> öffentlich, jede Fassung lässt sich also mit der vorherigen vergleichen.',
        "es": 'La fecha del encabezado indica cuándo cambió por última vez este aviso. Su historial es público en el <a href="https://github.com/skills-commons/skills-commons.github.io">repositorio del sitio</a>, así que cada revisión puede compararse con la anterior.',
    }),
    ('<span>Maintained by <a href="https://agora-intelligence.com">AGORÀ Intelligence</a></span>', {
        "it": '<span>Mantenuto da <a href="https://agora-intelligence.com">AGORÀ Intelligence</a></span>',
        "de": '<span>Betreut von <a href="https://agora-intelligence.com">AGORÀ Intelligence</a></span>',
        "es": '<span>Mantenido por <a href="https://agora-intelligence.com">AGORÀ Intelligence</a></span>',
    }),
    ('<span><a href="/">RFT 1: the library</a> · <a href="#cookies">Cookies</a></span>', {
        "it": '<span><a href="/it/">RFT 1: la libreria</a> · <a href="#cookies">Cookie</a></span>',
        "de": '<span><a href="/de/">RFT 1: die Bibliothek</a> · <a href="#cookies">Cookies</a></span>',
        "es": '<span><a href="/es/">RFT 1: la biblioteca</a> · <a href="#cookies">Cookies</a></span>',
    }),
]

# Shown on every page, so translated once and appended to each table.
COMMON: list[tuple[str, dict[str, str]]] = [
    ('This site measures anonymous visits with Google Analytics, and only if you agree. Declining changes nothing about what you can read or download. <a href="/privacy/">Privacy notice</a>.', {
        "it": 'Questo sito misura le visite in forma anonima con Google Analytics, e solo se sei d\'accordo. Rifiutare lascia intatto tutto ciò che puoi leggere e scaricare. <a href="/it/privacy/">Informativa privacy</a>.',
        "de": 'Diese Website misst Besuche anonym mit Google Analytics, und nur wenn Sie zustimmen. Eine Ablehnung ändert nichts daran, was Sie lesen oder herunterladen können. <a href="/de/privacy/">Datenschutzhinweis</a>.',
        "es": 'Este sitio mide las visitas de forma anónima con Google Analytics, y solo si estás de acuerdo. Rechazar no cambia nada de lo que puedes leer o descargar. <a href="/es/privacy/">Aviso de privacidad</a>.',
    }),
    ('<button type="button" class="yes" id="cbar-yes">Accept</button>', {
        "it": '<button type="button" class="yes" id="cbar-yes">Accetto</button>',
        "de": '<button type="button" class="yes" id="cbar-yes">Zustimmen</button>',
        "es": '<button type="button" class="yes" id="cbar-yes">Acepto</button>',
    }),
    ('<button type="button" id="cbar-no">Decline</button>', {
        "it": '<button type="button" id="cbar-no">Rifiuto</button>',
        "de": '<button type="button" id="cbar-no">Ablehnen</button>',
        "es": '<button type="button" id="cbar-no">Rechazo</button>',
    }),
    ('<a href="/privacy/">Privacy</a> · <a href="#cookies">Cookies</a>', {
        "it": '<a href="/it/privacy/">Privacy</a> · <a href="#cookies">Cookie</a>',
        "de": '<a href="/de/privacy/">Datenschutz</a> · <a href="#cookies">Cookies</a>',
        "es": '<a href="/es/privacy/">Privacidad</a> · <a href="#cookies">Cookies</a>',
    }),
]

# path relative to the site root -> its translation table
PAGES: dict[str, list] = {"": T, "write/": W, "privacy/": P}

SELECTOR_CSS = """
  .langs { display:flex; gap:2px; justify-content:flex-end; margin:0 0 14px; font-size:12.5px; }
  .langs a { display:inline-block; padding:3px 9px; border:1px solid var(--rule); border-radius:5px;
    color:var(--dim); text-decoration:none; background:#fbfaf6; }
  .langs a:hover { border-color:var(--ink); color:var(--ink); }
  .langs a[aria-current="page"] { background:var(--ink); border-color:var(--ink); color:var(--paper); font-weight:700; }
"""


def selector(current: str, page: str) -> str:
    """Links to the same page in the other languages, never to the front door."""
    items = []
    for code, label in [("en", "EN"), ("it", "IT"), ("de", "DE"), ("es", "ES")]:
        href = f"/{page}" if code == "en" else f"/{code}/{page}"
        cur = ' aria-current="page"' if code == current else ""
        items.append(f'<a href="{href}" hreflang="{code}" lang="{code}"{cur}>{label}</a>')
    return '  <nav class="langs" aria-label="Language">' + "".join(items) + "</nav>\n\n"


def alternates(page: str) -> str:
    out = [f'<link rel="alternate" hreflang="en" href="{BASE}/{page}">']
    for code in LANGS:
        out.append(f'<link rel="alternate" hreflang="{code}" href="{BASE}/{code}/{page}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}/{page}">')
    return "\n".join(out)


def build(lang: str | None, source: str, page: str, table: list, check: bool):
    """lang=None renders the English page (selector + alternates only)."""
    html = source
    missing = []

    for english, translations in table:
        if english not in html:
            missing.append(english[:70])
            continue
        if lang:
            # Every occurrence, not just the first. A headline lives in <title>,
            # in og:title and in <h1>; replacing one of them left the rest in
            # English and, worse, sent the next replacement to the wrong place.
            html = html.replace(english, translations[lang])

    if check:
        return html, missing

    code = lang or "en"
    html = html.replace('<html lang="en">', f'<html lang="{code}">', 1)
    html = html.replace('<link rel="icon"', alternates(page) + '\n<link rel="icon"', 1)
    # Anchor on </style>, which every page has. Anchoring on a media query that
    # only the landing page carries left the selector unstyled everywhere else.
    html = html.replace("</style>", SELECTOR_CSS + "</style>", 1)
    html = html.replace('<div class="sheet">\n\n', '<div class="sheet">\n\n' + selector(code, page), 1)
    return html, missing


def strip_generated(html: str) -> str:
    """Remove anything a previous run injected, so the build is idempotent."""
    html = re.sub(r'  <nav class="langs".*?</nav>\n\n', "", html, flags=re.S)
    html = re.sub(r'<link rel="alternate"[^>]*>\n', "", html)
    return html.replace(SELECTOR_CSS.rstrip() + "\n", "")


def to_markdown(html: str) -> str:
    """The readable part of a page, as markdown, for llms-full.txt."""
    body = html.split('<div class="sheet">', 1)[1].rsplit("</div>", 1)[0]
    body = re.sub(r'<nav class="langs".*?</nav>', "", body, flags=re.S)
    body = re.sub(r"<style.*?</style>|<script.*?</script>", "", body, flags=re.S)
    body = re.sub(r"<br\s*/?>", " ", body)

    body = re.sub(r'<h1[^>]*>(.*?)</h1>', r"\n# \1\n", body, flags=re.S)
    body = re.sub(r'<h2[^>]*>(.*?)</h2>', r"\n## \1\n", body, flags=re.S)
    body = re.sub(r'<h3[^>]*>(.*?)</h3>', r"\n### \1\n", body, flags=re.S)
    body = re.sub(r'<span class="no">(.*?)</span>', r"\1 ", body)
    body = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", body, flags=re.S)
    body = re.sub(r"<t[hd][^>]*>(.*?)</t[hd]>", r"| \1 ", body, flags=re.S)
    body = re.sub(r"</tr>", "|\n", body)
    body = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", body, flags=re.S)
    body = re.sub(r"<code>(.*?)</code>", r"`\1`", body, flags=re.S)
    body = re.sub(r"<(strong|b)>(.*?)</\1>", r"**\2**", body, flags=re.S)
    body = re.sub(r"<(em|i)>(.*?)</\1>", r"*\2*", body, flags=re.S)
    body = re.sub(r"<br\s*/?>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)

    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")]:
        body = body.replace(a, b)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" *\n *", "\n", body)
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def write_discovery(root: str) -> None:
    """robots.txt, sitemap.xml, llms.txt and llms-full.txt, from the pages."""
    langs = ["en"] + list(LANGS)

    def url(lang: str, page: str) -> str:
        return f"{BASE}/{page}" if lang == "en" else f"{BASE}/{lang}/{page}"

    # --- sitemap, with every language declared as an alternate of the others
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for page in PAGES:
        for lang in langs:
            rows.append("  <url>")
            rows.append(f"    <loc>{url(lang, page)}</loc>")
            for other in langs:
                rows.append(f'    <xhtml:link rel="alternate" hreflang="{other}" href="{url(other, page)}"/>')
            rows.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{url("en", page)}"/>')
            rows.append(f"    <priority>{'1.0' if page == '' else '0.8' if page == 'write/' else '0.3'}</priority>")
            rows.append("  </url>")
    rows.append("</urlset>")
    open(os.path.join(root, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")

    # --- robots
    open(os.path.join(root, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
        "# Everything here is meant to be read, by people and by machines alike.\n"
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n"
    )

    # --- llms.txt: the map an assistant reads first
    open(os.path.join(root, "llms.txt"), "w", encoding="utf-8", newline="\n").write(f"""# Skills Commons

> The trusted open library of AI skills. A skill is a plain-text method — a
> single markdown file — you hand to an AI assistant so it performs a
> professional task with a reviewed approach. Every skill here passed a
> documented, line-by-line security and quality review before merging.

The library holds 22 reviewed skills in four categories: workplace, writing,
engineering and agents. It is free under Apache-2.0, model-agnostic, and
readable in full before you run any of it.

## Documents

- [The library]({BASE}/): what the library guarantees, why it exists, how to install a skill on any assistant.
- [Write Your First Skill]({BASE}/write/): the anatomy of a skill, an annotated reviewed example, what reviews reject, and a browser editor that generates a conformant file.
- [Privacy notice]({BASE}/privacy/): what is collected and on what basis.

## The skills themselves

- [Repository](https://github.com/skills-commons/skills-commons): one markdown file per skill, browsable.
- [Latest release](https://github.com/skills-commons/skills-commons/releases/latest): the same skills as one directory each, in the layout the Agent Skills specification defines.
- [Format specification](https://github.com/skills-commons/skills-commons/blob/main/SPEC.md): frontmatter, required sections, the rules a skill must satisfy.
- [Security policy](https://github.com/skills-commons/skills-commons/blob/main/SECURITY.md): the checklist every submission is reviewed against.

## Optional

- [Full text of these documents]({BASE}/llms-full.txt): the three pages above, in one file.
- Translations: Italian, German and Spanish exist at /it/, /de/ and /es/. The skills themselves are English by specification.
- [Builder](https://build.skills-commons.org): optional account for writing and submitting a skill.
""")

    # --- llms-full.txt: the same documents, whole
    parts = [
        "# Skills Commons — full text",
        f"> The three documents at {BASE}, concatenated. Generated from the pages themselves.",
    ]
    titles = {"": "The library", "write/": "Write Your First Skill", "privacy/": "Privacy notice"}
    for page in PAGES:
        html = open(os.path.join(root, page, "index.html"), encoding="utf-8").read()
        parts.append(f"\n\n---\n\n# {titles.get(page, page)}\nSource: {BASE}/{page}\n")
        parts.append(to_markdown(html))
    open(os.path.join(root, "llms-full.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(parts) + "\n")

    print(f"  wrote robots.txt, sitemap.xml ({len(PAGES) * len(langs)} urls), llms.txt, llms-full.txt")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    check = "--check" in sys.argv
    root = os.path.dirname(os.path.abspath(__file__))
    failed = False

    for page, table in PAGES.items():
        src_path = os.path.join(root, page, "index.html")
        clean = strip_generated(open(src_path, encoding="utf-8").read())
        label = page or "index.html"

        _, missing = build(None, clean, page, table, check=True)
        table = table + COMMON
        if missing:
            failed = True
            print(f"{label}: {len(missing)} string(s) no longer in the source — the translation is stale:")
            for m in missing:
                print(f"  - {m}…")
            continue
        print(f"{label}: all {len(table)} translated strings matched")
        if check:
            continue

        en, _ = build(None, clean, page, table, check=False)
        open(src_path, "w", encoding="utf-8", newline="\n").write(en)
        print(f"  wrote {page}index.html (selector + hreflang)")

        for lang in LANGS:
            out, _ = build(lang, clean, page, table, check=False)
            d = os.path.join(root, lang, page)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="\n").write(out)
            print(f"  wrote {lang}/{page}index.html")

    if not check and not failed:
        write_discovery(root)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

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
    ('Every skill <span class="kw ok">MUST</span> pass a documented, line-by-line security and quality review before merge. Maintainer submissions included: a different maintainer reviews.', {
        "it": 'Ogni skill <span class="kw ok">DEVE</span> superare una revisione di sicurezza e qualità documentata, riga per riga, prima di essere accettata. Comprese quelle dei maintainer: le rivede un altro maintainer.',
        "de": 'Jeder Skill <span class="kw ok">MUSS</span> vor der Aufnahme eine dokumentierte Sicherheits- und Qualitätsprüfung Zeile für Zeile bestehen. Auch Einreichungen der Maintainer: ein anderer Maintainer prüft.',
        "es": 'Cada skill <span class="kw ok">DEBE</span> superar una revisión de seguridad y calidad documentada, línea por línea, antes de incorporarse. Incluidas las de los maintainers: las revisa otro maintainer.',
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
    ("<strong>Is it safe?</strong> Every merge passes two human reviews (quality + security); encoded blobs and remote instruction loading are rejected at review. And the format itself is the safety net: read the file before you install it.", {
        "it": "<strong>È sicuro?</strong> Ogni accettazione passa da due revisioni umane (qualità e sicurezza); blob codificati e caricamento remoto di istruzioni vengono respinti in revisione. E il formato stesso è la rete di protezione: leggi il file prima di installarlo.",
        "de": "<strong>Ist das sicher?</strong> Jede Aufnahme durchläuft zwei menschliche Prüfungen (Qualität und Sicherheit); kodierte Blobs und das Nachladen entfernter Anweisungen werden abgelehnt. Und das Format selbst ist das Sicherheitsnetz: lesen Sie die Datei, bevor Sie sie installieren.",
        "es": "<strong>¿Es seguro?</strong> Cada incorporación pasa dos revisiones humanas (calidad y seguridad); los blobs codificados y la carga remota de instrucciones se rechazan en la revisión. Y el formato mismo es la red de seguridad: lee el archivo antes de instalarlo.",
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
    ("Two human reviews (quality + security) merge it. Credit lands in the skill itself.", {
        "it": "Due revisioni umane (qualità e sicurezza) la accettano. Il credito finisce nella skill stessa.",
        "de": "Zwei menschliche Prüfungen (Qualität und Sicherheit) nehmen ihn auf. Die Nennung steht im Skill selbst.",
        "es": "Dos revisiones humanas (calidad y seguridad) la incorporan. El crédito queda en la propia skill.",
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

SELECTOR_CSS = """
  .langs { display:flex; gap:2px; justify-content:flex-end; margin:0 0 14px; font-size:12.5px; }
  .langs a { display:inline-block; padding:3px 9px; border:1px solid var(--rule); border-radius:5px;
    color:var(--dim); text-decoration:none; background:#fbfaf6; }
  .langs a:hover { border-color:var(--ink); color:var(--ink); }
  .langs a[aria-current="page"] { background:var(--ink); border-color:var(--ink); color:var(--paper); font-weight:700; }
"""


def selector(current: str) -> str:
    items = []
    for code, label in [("en", "EN"), ("it", "IT"), ("de", "DE"), ("es", "ES")]:
        href = "/" if code == "en" else f"/{code}/"
        cur = ' aria-current="page"' if code == current else ""
        items.append(f'<a href="{href}" hreflang="{code}" lang="{code}"{cur}>{label}</a>')
    return '  <nav class="langs" aria-label="Language">' + "".join(items) + "</nav>\n\n"


def alternates() -> str:
    out = [f'<link rel="alternate" hreflang="en" href="{BASE}/">']
    for code in LANGS:
        out.append(f'<link rel="alternate" hreflang="{code}" href="{BASE}/{code}/">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}/">')
    return "\n".join(out)


def build(lang: str | None, source: str, check: bool) -> tuple[str, list[str]]:
    """lang=None renders the English page (selector + alternates only)."""
    html = source
    missing = []

    for english, translations in T:
        if english not in html:
            missing.append(english[:70])
            continue
        if lang:
            html = html.replace(english, translations[lang], 1)

    if check:
        return html, missing

    code = lang or "en"
    html = html.replace('<html lang="en">', f'<html lang="{code}">', 1)
    html = html.replace(
        '<link rel="icon"',
        alternates() + '\n<link rel="icon"', 1)
    html = html.replace(
        "  @media (max-width:600px)",
        SELECTOR_CSS.rstrip() + "\n  @media (max-width:600px)", 1)
    html = html.replace('<div class="sheet">\n\n', '<div class="sheet">\n\n' + selector(code), 1)
    if lang:
        html = html.replace(f'href="{BASE}/{lang}/"', f'href="{BASE}/{lang}/"', 1)
    return html, missing


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    check = "--check" in sys.argv
    root = os.path.dirname(os.path.abspath(__file__))
    source = open(os.path.join(root, "index.html"), encoding="utf-8").read()

    # The English page must not already carry a selector, or we would stack them.
    clean = re.sub(r'  <nav class="langs".*?</nav>\n\n', "", source, flags=re.S)
    clean = re.sub(r'<link rel="alternate"[^>]*>\n', "", clean)
    clean = re.sub(re.escape(SELECTOR_CSS.rstrip()) + "\n", "", clean)

    _, missing = build(None, clean, check=True)
    if missing:
        print("Strings no longer found in index.html — the translation is stale:")
        for m in missing:
            print(f"  - {m}…")
        return 1
    print(f"all {len(T)} translated strings matched index.html")
    if check:
        return 0

    en, _ = build(None, clean, check=False)
    open(os.path.join(root, "index.html"), "w", encoding="utf-8", newline="\n").write(en)
    print("  wrote index.html (selector + hreflang)")

    for lang in LANGS:
        out, _ = build(lang, clean, check=False)
        d = os.path.join(root, lang)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="\n").write(out)
        print(f"  wrote {lang}/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())

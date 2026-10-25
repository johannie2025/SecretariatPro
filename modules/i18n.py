"""Traduction de l'interface : français (langue source), espagnol, anglais.

Le français sert de clé : t("Facturation") → « Facturación » / « Billing ».
Un texte absent du dictionnaire est affiché tel quel (jamais d'erreur).
"""
import re

LANGS = ("fr", "es", "en")
LANG_NAMES = {"fr": "Français", "es": "Español", "en": "English"}
_lang = "fr"


def set_lang(code: str):
    global _lang
    _lang = code if code in LANGS else "fr"


def get_lang() -> str:
    return _lang


_RAW = r"""
Erreur|Error|Error
Une erreur inattendue est survenue.\nLe détail a été enregistré dans le journal de l'application.|Ocurrió un error inesperado.\nEl detalle se guardó en el registro de la aplicación.|An unexpected error occurred.\nThe details were saved in the application log.
Licence|Licencia|License
Impossible de démarrer l'application.|No se pudo iniciar la aplicación.|The application could not start.
L'architecture et l'innovation qui donnent vie à vos idées !|La arquitectura y la innovación que dan vida a sus ideas.|Architecture and innovation that bring your ideas to life!
SecretariatPro est la solution bureautique de W Design : facturation, numérisation (OCR), outils PDF, rédaction automatique, courrier et tâches — 100 % sur votre ordinateur, sans abonnement ni envoi de données.|SecretariatPro es la solución ofimática de W Design: facturación, digitalización (OCR), herramientas PDF, redacción automática, correo y tareas — 100 % en su ordenador, sin suscripción ni envío de datos.|SecretariatPro is W Design's office solution: invoicing, scanning (OCR), PDF tools, automatic drafting, mail and tasks — 100% on your computer, no subscription, no data sent.
Nous contacter|Contáctenos|Contact us
Le bouton WhatsApp ouvre votre navigateur ; l'application elle-même n'envoie aucune donnée.|El botón de WhatsApp abre su navegador; la aplicación en sí no envía ningún dato.|The WhatsApp button opens your browser; the application itself sends no data.
Copier|Copiar|Copy
Agence d'Architecture • Design • Innovation|Agencia de Arquitectura • Diseño • Innovación|Architecture • Design • Innovation Agency
W Design — Agence d'Architecture • Design • Innovation|W Design — Agencia de Arquitectura • Diseño • Innovación|W Design — Architecture • Design • Innovation Agency
Information|Información|Information
Une erreur est survenue|Se ha producido un error|An error occurred
Confirmation|Confirmación|Confirmation
L'opération a échoué. Vérifiez le fichier et réessayez.|La operación falló. Compruebe el archivo e inténtelo de nuevo.|The operation failed. Check the file and try again.
Choisir à chaque enregistrement|Elegir en cada guardado|Choose each time I save
Date invalide : utilisez le format JJ/MM/AAAA.|Fecha no válida: use el formato DD/MM/AAAA.|Invalid date: use the DD/MM/YYYY format.
Enregistrer dans :|Guardar en:|Save to:
Impossible d'ouvrir ce fichier.|No se puede abrir este archivo.|This file cannot be opened.
Choisissez le dossier de destination|Elija la carpeta de destino|Choose the destination folder
Identifiant|Usuario|Username
Mot de passe|Contraseña|Password
10 caractères minimum|Mínimo 10 caracteres|At least 10 characters
Nouveau mot de passe|Nueva contraseña|New password
Confirmer le mot de passe|Confirmar la contraseña|Confirm password
Mot de passe mis à jour.|Contraseña actualizada.|Password updated.
Connexion|Iniciar sesión|Sign in
Accédez à votre espace de secrétariat.|Acceda a su espacio de secretaría.|Access your secretarial workspace.
Se connecter|Entrar|Log in
Activer ce poste|Activar este equipo|Activate this computer
Choisissez la durée de la licence pour cet ordinateur :|Elija la duración de la licencia para este ordenador:|Choose the license duration for this computer:
Activer sur ce poste|Activar en este equipo|Activate on this computer
—  ou activation à distance avec une clé  —|—  o activación remota con una clave  —|—  or remote activation with a key  —
Activer avec la clé|Activar con la clave|Activate with the key
Majuscules, minuscules, chiffre et symbole requis.|Se requieren mayúsculas, minúsculas, un número y un símbolo.|Uppercase, lowercase, a digit and a symbol are required.
Enregistrer|Guardar|Save
Les deux mots de passe sont différents.|Las dos contraseñas no coinciden.|The two passwords do not match.
Sécurisez votre compte|Proteja su cuenta|Secure your account
Première connexion : choisissez votre propre mot de passe.|Primer inicio de sesión: elija su propia contraseña.|First sign-in: choose your own password.
1 mois|1 mes|1 month
3 mois|3 meses|3 months
6 mois|6 meses|6 months
1 an|1 año|1 year
Entrepreneur *|Empresario *|Entrepreneur *
Type de document|Tipo de documento|Document type
Facture|Factura|Invoice
Proforma|Proforma|Proforma
Devis|Presupuesto|Quotation
Client final *|Cliente final *|End customer *
Nom du client|Nombre del cliente|Customer name
Adresse du client final|Dirección del cliente final|End customer address
Téléphone|Teléfono|Phone
Désignation|Descripción|Description
Qté|Cant.|Qty
Prix unitaire|Precio unitario|Unit price
Montant|Importe|Amount
Ex. : Plan architectural|Ej.: Plano arquitectónico|E.g.: Architectural plan
Terminé|Terminado|Done
Créez d'abord un entrepreneur dans l'onglet « Entrepreneurs ».|Primero cree un empresario en la pestaña «Empresarios».|First create an entrepreneur in the "Entrepreneurs" tab.
Aucun entrepreneur|Ningún empresario|No entrepreneur
{kind} {number} créé(e) et archivé(e).\nL'ouvrir maintenant ?|{kind} {number} creado/a y archivado/a.\n¿Abrirlo ahora?|{kind} {number} created and archived.\nOpen it now?
Facturation|Facturación|Billing
Lignes du document|Líneas del documento|Document lines
+  Ajouter une ligne|+  Añadir una línea|+  Add a line
Remise (%)|Descuento (%)|Discount (%)
Taxe / TVA (%)|Impuesto / IVA (%)|Tax / VAT (%)
Notes / conditions de paiement|Notas / condiciones de pago|Notes / payment terms
Générer le PDF|Generar el PDF|Generate PDF
Historique récent|Historial reciente|Recent history
Vérifiez le formulaire|Revise el formulario|Check the form
Sous-total|Subtotal|Subtotal
Remise|Descuento|Discount
Taxe|Impuesto|Tax
TOTAL|TOTAL|TOTAL
Saisie invalide : utilisez uniquement des chiffres.|Entrada no válida: use solo números.|Invalid input: use digits only.
Aucun document pour le moment.|Ningún documento por ahora.|No documents yet.
Ouvrir|Abrir|Open
Langue du document|Idioma del documento|Document language
Aucun logo|Sin logotipo|No logo
Entrepreneur enregistré.|Empresario guardado.|Entrepreneur saved.
Supprimer cet entrepreneur et son historique de documents ?\n(Les fichiers PDF déjà créés restent sur votre ordinateur.)|¿Eliminar este empresario y su historial de documentos?\n(Los PDF ya creados permanecen en su ordenador.)|Delete this entrepreneur and their document history?\n(PDF files already created stay on your computer.)
Nom de l'entreprise *|Nombre de la empresa *|Company name *
Adresse|Dirección|Address
E-mail|Correo electrónico|E-mail
Devise (FCFA, EUR...)|Moneda (FCFA, EUR...)|Currency (FCFA, EUR...)
Taxe / TVA par défaut (%)|Impuesto / IVA por defecto (%)|Default tax / VAT (%)
Entrepreneurs|Empresarios|Entrepreneurs
+  Nouvel entrepreneur|+  Nuevo empresario|+  New entrepreneur
Choisir un logo...|Elegir un logotipo...|Choose a logo...
Ouvrir le dossier|Abrir la carpeta|Open folder
Supprimer|Eliminar|Delete
🧾  Facturation|🧾  Facturación|🧾  Billing
Factures, devis, proformas|Facturas, presupuestos, proformas|Invoices, quotations, proformas
📄  Modèles Word|📄  Plantillas Word|📄  Word templates
Champs détectés automatiquement|Campos detectados automáticamente|Fields detected automatically
🔍  Numérisation|🔍  Digitalización|🔍  Scanning
Scan → Word / PDF avec mise en page|Escáner → Word / PDF con maquetación|Scan → Word / PDF with layout
📑  Outils PDF|📑  Herramientas PDF|📑  PDF tools
Éditer, fusionner, signer, protéger|Editar, unir, firmar, proteger|Edit, merge, sign, protect
✍️  Rédaction|✍️  Redacción|✍️  Writing
Lettres, attestations, mise en forme auto|Cartas, certificados, formato automático|Letters, certificates, auto-formatting
📬  Courrier & tâches|📬  Correo y tareas|📬  Mail & tasks
Registre, rappels, échéances|Registro, recordatorios, vencimientos|Register, reminders, deadlines
👥  Entrepreneurs|👥  Empresarios|👥  Entrepreneurs
Profils, logos, NIF, RCCM|Perfiles, logotipos, NIF, RCCM|Profiles, logos, tax IDs
ℹ️  À propos|ℹ️  Acerca de|ℹ️  About
Contacts W Design|Contactos de W Design|W Design contacts
🏠  Accueil|🏠  Inicio|🏠  Home
⚙️  Paramètres|⚙️  Ajustes|⚙️  Settings
Tâches ouvertes|Tareas abiertas|Open tasks
Bonjour 👋|Hola 👋|Hello 👋
Que souhaitez-vous faire aujourd'hui ?|¿Qué desea hacer hoy?|What would you like to do today?
Documents créés|Documentos creados|Documents created
Ce mois-ci|Este mes|This month
Se déconnecter|Cerrar sesión|Sign out
— Aucun —|— Ninguno —|— None —
À traiter|Por tramitar|To process
En cours|En curso|In progress
Traité|Tramitado|Processed
Archivé|Archivado|Archived
Registre du courrier|Registro de correspondencia|Mail register
Tâches & rappels|Tareas y recordatorios|Tasks & reminders
Entrant|Entrante|Incoming
Sortant|Saliente|Outgoing
JJ/MM/AAAA|DD/MM/AAAA|DD/MM/YYYY
Correspondant (expéditeur / destinataire)|Corresponsal (remitente / destinatario)|Correspondent (sender / recipient)
Objet du courrier|Asunto de la carta|Mail subject
Joindre un fichier...|Adjuntar un archivo...|Attach a file...
Rechercher (n°, correspondant, objet...)|Buscar (n.º, corresponsal, asunto...)|Search (no., correspondent, subject...)
Supprimer cette ligne du registre ?|¿Eliminar esta línea del registro?|Delete this line from the register?
Registre exporté (ouvrable dans Excel).|Registro exportado (se abre en Excel).|Register exported (opens in Excel).
Tâche à faire (ex. Appeler M. Obiang)|Tarea pendiente (ej. Llamar al Sr. Obiang)|Task to do (e.g. Call Mr. Obiang)
Échéance JJ/MM/AAAA|Vencimiento DD/MM/AAAA|Due date DD/MM/YYYY
Afficher les tâches terminées|Mostrar las tareas terminadas|Show completed tasks
Courrier & tâches|Correo y tareas|Mail & tasks
Exporter en CSV|Exportar a CSV|Export to CSV
N°|N.º|No.
Type|Tipo|Type
Date|Fecha|Date
Correspondant|Corresponsal|Correspondent
Objet|Asunto|Subject
Entrepreneur|Empresario|Entrepreneur
Statut|Estado|Status
Ajouter|Añadir|Add
Courrier|Correo|Mail
Aucun courrier enregistré.|Ninguna correspondencia registrada.|No mail recorded.
Rien à faire pour le moment 🎉|Nada que hacer por ahora 🎉|Nothing to do for now 🎉
Photo, scan ou PDF — texte, tableaux et images sont conservés|Foto, escaneo o PDF — se conservan texto, tablas e imágenes|Photo, scan or PDF — text, tables and images are preserved
Analyser le document|Analizar el documento|Analyze the document
Choisissez d'abord un fichier.|Primero elija un archivo.|Choose a file first.
Analyse en cours...|Analizando...|Analyzing...
La lecture a échoué. Le fichier est peut-être endommagé.|La lectura falló. Es posible que el archivo esté dañado.|Reading failed. The file may be damaged.
(Aucun texte détecté)|(No se detectó texto)|(No text detected)
Analysez d'abord un document.|Primero analice un documento.|Analyze a document first.
Fichier enregistré.\nL'ouvrir maintenant ?|Archivo guardado.\n¿Abrirlo ahora?|File saved.\nOpen it now?
Texte enregistré.|Texto guardado.|Text saved.
Numérisation (OCR)|Digitalización (OCR)|Scanning (OCR)
Choisir un fichier|Elegir un archivo|Choose a file
PDF recherchable|PDF con texto buscable|Searchable PDF
Texte (.txt)|Texto (.txt)|Text (.txt)
Envoyer vers Rédaction|Enviar a Redacción|Send to Writing
{n} page(s)|{n} página(s)|{n} page(s)
{n} tableau(x)|{n} tabla(s)|{n} table(s)
{n} image(s)/dessin(s)|{n} imagen(es)/dibujo(s)|{n} image(s)/drawing(s)
PDF numérique : mise en page d'origine reprise|PDF digital: se conserva la maquetación original|Digital PDF: original layout preserved
Choisir un PDF|Elegir un PDF|Choose a PDF
Éditeur|Editor|Editor
Organiser|Organizar|Organize
Convertir|Convertir|Convert
Sécuriser|Proteger|Secure
Aucun fichier|Ningún archivo|No file
Terminé ✔\nOuvrir le résultat ?|Terminado ✔\n¿Abrir el resultado?|Done ✔\nOpen the result?
Texte|Texto|Text
Texte à ajouter|Texto a añadir|Text to add
Noir|Negro|Black
Rouge|Rojo|Red
Bleu|Azul|Blue
Vert|Verde|Green
Choisir l'image...|Elegir la imagen...|Choose the image...
Fusionner plusieurs PDF|Unir varios PDF|Merge several PDFs
Aucun fichier (l'ordre d'ajout = l'ordre dans le PDF final)|Ningún archivo (el orden de adición = el orden en el PDF final)|No file (order added = order in the final PDF)
Pages d'un PDF|Páginas de un PDF|Pages of a PDF
ex. 1-3,5,8-|ej. 1-3,5,8-|e.g. 1-3,5,8-
PDF → Word (mise en page, tableaux et images conservés)|PDF → Word (se conservan maquetación, tablas e imágenes)|PDF → Word (layout, tables and images preserved)
Filigrane|Marca de agua|Watermark
ex. CONFIDENTIEL, COPIE, BROUILLON|ej. CONFIDENCIAL, COPIA, BORRADOR|e.g. CONFIDENTIAL, COPY, DRAFT
Autres|Otros|Other
Choisissez d'abord un fichier PDF.|Primero elija un archivo PDF.|Choose a PDF file first.
Supprimer cette page du document ?|¿Eliminar esta página del documento?|Delete this page from the document?
Ouvrez d'abord un PDF.|Primero abra un PDF.|Open a PDF first.
PDF enregistré.\nL'ouvrir maintenant ?|PDF guardado.\n¿Abrirlo ahora?|PDF saved.\nOpen it now?
Extraire / réorganiser|Extraer / reordenar|Extract / reorder
Supprimer ces pages|Eliminar estas páginas|Delete these pages
Pivoter ↻ 90°|Girar ↻ 90°|Rotate ↻ 90°
Pivoter ↺ 90°|Girar ↺ 90°|Rotate ↺ 90°
Séparer en pages|Dividir en páginas|Split into pages
Ajoutez au moins deux PDF à fusionner.|Añada al menos dos PDF para unir.|Add at least two PDFs to merge.
Outils PDF|Herramientas PDF|PDF tools
Ouvrir un PDF|Abrir un PDF|Open a PDF
Supprimer la page|Eliminar la página|Delete page
Pivoter|Girar|Rotate
Annuler l'action|Deshacer|Undo
Image / cachet|Imagen / sello|Image / stamp
Masquer|Ocultar|Redact
Remplacer|Reemplazar|Replace
Surligner|Resaltar|Highlight
Texte : cliquez sur la page.  Image, Masquer, Remplacer, Surligner : tracez un rectangle à la souris.|Texto: haga clic en la página.  Imagen, Ocultar, Reemplazar, Resaltar: trace un rectángulo con el ratón.|Text: click on the page.  Image, Redact, Replace, Highlight: draw a rectangle with the mouse.
Impossible d'ouvrir ce PDF.|No se puede abrir este PDF.|This PDF cannot be opened.
Ajouter des PDF...|Añadir PDF...|Add PDFs...
Vider|Vaciar|Clear
Fusionner|Unir|Merge
Pages :|Páginas:|Pages:
Réorganiser : saisissez toutes les pages dans le nouvel ordre (ex. 3,1,2).  Pivoter : laissez « Pages » vide pour tout le document.|Reordenar: escriba todas las páginas en el nuevo orden (ej. 3,1,2).  Girar: deje «Páginas» vacío para todo el documento.|Reorder: enter all pages in the new order (e.g. 3,1,2).  Rotate: leave "Pages" empty for the whole document.
Convertir en Word|Convertir a Word|Convert to Word
Convertir en images (PNG)|Convertir a imágenes (PNG)|Convert to images (PNG)
Les PDF scannés sont lus automatiquement par OCR.|Los PDF escaneados se leen automáticamente con OCR.|Scanned PDFs are read automatically with OCR.
Choisir des images et créer le PDF|Elegir imágenes y crear el PDF|Choose images and create the PDF
Protéger|Proteger|Protect
Retirer la protection|Quitar la protección|Remove protection
Ajouter le filigrane|Añadir la marca de agua|Add the watermark
Numéroter les pages|Numerar las páginas|Number the pages
Réduire la taille|Reducir el tamaño|Reduce size
Choisissez d'abord l'image (signature, cachet, logo).|Primero elija la imagen (firma, sello, logotipo).|Choose the image first (signature, stamp, logo).
Tracez un rectangle avec la souris pour cet outil.|Dibuje un rectángulo con el ratón para esta herramienta.|Draw a rectangle with the mouse for this tool.
Mot de passe du PDF :|Contraseña del PDF:|PDF password:
PDF protégé|PDF protegido|Protected PDF
Nouveau texte pour cette zone :|Nuevo texto para esta zona:|New text for this area:
Remplacer le texte|Reemplazar el texto|Replace text
Clair|Claro|Light
Sombre|Oscuro|Dark
Système|Sistema|System
Sauvegarde terminée. Conservez-la sur une clé USB ou un autre ordinateur.|Copia de seguridad terminada. Guárdela en una memoria USB o en otro ordenador.|Backup complete. Keep it on a USB drive or another computer.
Restaurer cette sauvegarde ?\nLes données actuelles seront remplacées.|¿Restaurar esta copia de seguridad?\nLos datos actuales serán reemplazados.|Restore this backup?\nCurrent data will be replaced.
Restauration terminée. Fermez puis rouvrez l'application.|Restauración terminada. Cierre y vuelva a abrir la aplicación.|Restore complete. Close and reopen the application.
Paramètres|Ajustes|Settings
Code machine :|Código del equipo:|Machine code:
Renouveler ce poste (la durée s'ajoute au temps restant) :|Renovar este equipo (la duración se suma al tiempo restante):|Renew this computer (the duration is added to the remaining time):
Renouveler sur ce poste|Renovar en este equipo|Renew on this computer
Ou collez une clé reçue de W Design :|O pegue una clave recibida de W Design:|Or paste a key received from W Design:
Activer / renouveler|Activar / renovar|Activate / renew
Mot de passe administrateur|Contraseña de administrador|Administrator password
Apparence|Apariencia|Appearance
Langue|Idioma|Language
Sauvegarde des données|Copia de seguridad de los datos|Data backup
Base de données + tous les documents des entrepreneurs, dans un seul fichier .zip.|Base de datos + todos los documentos de los empresarios, en un solo archivo .zip.|Database + all entrepreneurs' documents, in a single .zip file.
Sauvegarder|Hacer copia|Back up
Restaurer...|Restaurar...|Restore...
SecretariatPro v1.1 — fonctionne 100 % hors-ligne, aucune donnée envoyée.|SecretariatPro v1.1 — funciona 100 % sin conexión, no se envía ningún dato.|SecretariatPro v1.1 — works 100% offline, no data is sent.
Word (.docx) ou texte (.txt) contenant des [Champs] ou « Libellé : ______ »|Word (.docx) o texto (.txt) con [Campos] o «Etiqueta: ______»|Word (.docx) or text (.txt) containing [Fields] or "Label: ______"
Les champs détectés apparaîtront ici.|Los campos detectados aparecerán aquí.|Detected fields will appear here.
Choisissez d'abord un modèle contenant des champs.|Primero elija una plantilla que contenga campos.|Choose a template containing fields first.
Sélectionnez un entrepreneur (onglet « Entrepreneurs »).|Seleccione un empresario (pestaña «Empresarios»).|Select an entrepreneur ("Entrepreneurs" tab).
Modèles de documents|Plantillas de documentos|Document templates
Ce fichier n'a pas pu être lu. Vérifiez qu'il s'agit d'un .docx ou .txt valide.|No se pudo leer este archivo. Compruebe que es un .docx o .txt válido.|This file could not be read. Check that it is a valid .docx or .txt.
La génération a échoué. Fermez le fichier s'il est ouvert dans Word et réessayez.|La generación falló. Cierre el archivo si está abierto en Word e inténtelo de nuevo.|Generation failed. Close the file if it is open in Word and try again.
Modèles|Plantillas|Templates
Aucun champ détecté. Utilisez [NomClient] ou « Intitulé : ______ ».|No se detectó ningún campo. Use [NombreCliente] o «Título: ______».|No field detected. Use [ClientName] or "Title: ______".
1. Choisir un modèle|1. Elegir una plantilla|1. Choose a template
2. Générer le document|2. Generar el documento|2. Generate the document
Documents types|Documentos tipo|Standard documents
Mise en forme automatique|Formato automático|Automatic formatting
Montant en lettres|Importe en letras|Amount in words
Lettre administrative|Carta administrativa|Administrative letter
Lettre de démission|Carta de renuncia|Resignation letter
Relance de paiement|Recordatorio de pago|Payment reminder
Attestation de travail|Certificado de trabajo|Employment certificate
Attestation (libre)|Certificado (libre)|Certificate (free text)
Convocation|Convocatoria|Notice of meeting
Procès-verbal de réunion|Acta de reunión|Minutes of meeting
Note de service|Nota interna|Internal memo
Reçu de paiement|Recibo de pago|Payment receipt
Décharge|Acuse de recibo|Acknowledgement of receipt
Procuration|Poder|Power of attorney
Sans en-tête|Sin membrete|No letterhead
Classique (Times 12)|Clásico (Times 12)|Classic (Times 12)
Moderne (Calibri 11)|Moderno (Calibri 11)|Modern (Calibri 11)
Compact (Arial 10)|Compacto (Arial 10)|Compact (Arial 10)
Montant, ex. 1857250|Importe, ej. 1857250|Amount, e.g. 1857250
Document créé.\nL'ouvrir maintenant ?|Documento creado.\n¿Abrirlo ahora?|Document created.\nOpen it now?
Collez ou ouvrez d'abord un texte.|Primero pegue o abra un texto.|Paste or open a text first.
Rédaction|Redacción|Writing
Générer en Word|Generar en Word|Generate in Word
Générer en PDF|Generar en PDF|Generate in PDF
Ouvrir un fichier (txt, docx, pdf)|Abrir un archivo (txt, docx, pdf)|Open a file (txt, docx, pdf)
Mettre en forme automatiquement  ➜|Dar formato automáticamente  ➜|Format automatically  ➜
Collez ou ouvrez votre texte (même brut, issu d'un scan) : titres, listes, paragraphes, majuscules et ponctuation française sont corrigés.|Pegue o abra su texto (incluso en bruto, de un escaneo): se corrigen títulos, listas, párrafos, mayúsculas y puntuación.|Paste or open your text (even raw, from a scan): headings, lists, paragraphs, capitalization and punctuation are fixed.
Copier le résultat|Copiar el resultado|Copy the result
Ce fichier n'a pas pu être lu.|No se pudo leer este archivo.|This file could not be read.
Écrivez un montant en toutes lettres (chèques, reçus, factures, contrats).|Escriba un importe en letras (cheques, recibos, facturas, contratos).|Write an amount in words (cheques, receipts, invoices, contracts).
Écrire en lettres|Escribir en letras|Write in words
Montant invalide (chiffres uniquement, jusqu'à 999 milliards).|Importe no válido (solo cifras, hasta 999 mil millones).|Invalid amount (digits only, up to 999 billion).
Ce PDF est une image : utilisez d'abord « Numérisation (OCR) », puis « Envoyer vers Rédaction ».|Este PDF es una imagen: use primero «Digitalización (OCR)» y luego «Enviar a Redacción».|This PDF is an image: first use "Scanning (OCR)", then "Send to Writing".
Expéditeur (si pas d'en-tête)|Remitente (si no hay membrete)|Sender (if no letterhead)
Destinataire|Destinatario|Recipient
Fonction du destinataire|Cargo del destinatario|Recipient's position
Adresse du destinataire|Dirección del destinatario|Recipient's address
Corps de la lettre (un paragraphe par ligne)|Cuerpo de la carta (un párrafo por línea)|Body of the letter (one paragraph per line)
Formule de politesse (facultatif)|Fórmula de cortesía (opcional)|Closing phrase (optional)
Lieu|Lugar|Place
Date (laisser vide = aujourd'hui)|Fecha (vacío = hoy)|Date (leave empty = today)
Nom du signataire|Nombre del firmante|Signatory's name
Poste occupé|Puesto ocupado|Position held
Durée du préavis|Duración del preaviso|Notice period
Date de fin de contrat|Fecha de fin de contrato|Contract end date
Client débiteur|Cliente deudor|Debtor customer
N° de facture|N.º de factura|Invoice no.
Devise|Moneda|Currency
Date d'échéance|Fecha de vencimiento|Due date
Délai accordé|Plazo concedido|Time allowed
Nom de l'employé(e)|Nombre del empleado/a|Employee's name
Date de naissance|Fecha de nacimiento|Date of birth
Lieu de naissance|Lugar de nacimiento|Place of birth
Poste|Puesto|Position
Date d'embauche|Fecha de contratación|Hire date
Date de fin (vide si en poste)|Fecha de fin (vacío si sigue en el puesto)|End date (empty if still employed)
Fonction du signataire|Cargo del firmante|Signatory's position
Titre|Título|Title
Destinataire(s)|Destinatario(s)|Recipient(s)
Objet / réunion|Asunto / reunión|Subject / meeting
Jour|Día|Day
Heure|Hora|Time
Ordre du jour (un point par ligne)|Orden del día (un punto por línea)|Agenda (one item per line)
Participants (un par ligne)|Participantes (uno por línea)|Attendees (one per line)
Déroulement et décisions|Desarrollo y decisiones|Proceedings and decisions
De|De|From
À|Para|To
N° du reçu|N.º del recibo|Receipt no.
Reçu de|Recibido de|Received from
Motif|Concepto|Reason
Mode de paiement|Forma de pago|Payment method
Adresse du mandant|Dirección del poderdante|Principal's address
Mandataire|Apoderado|Attorney
Objet de la procuration|Objeto del poder|Purpose of the power of attorney
Objet remis|Objeto entregado|Item handed over
Mot de passe trop court (4 caractères minimum).|Contraseña demasiado corta (mínimo 4 caracteres).|Password too short (minimum 4 characters).
Saisissez le texte du filigrane.|Escriba el texto de la marca de agua.|Enter the watermark text.
Clé de licence invalide.|Clave de licencia no válida.|Invalid license key.
Cette clé n'a pas été émise pour cet ordinateur.|Esta clave no fue emitida para este ordenador.|This key was not issued for this computer.
Durée de licence non reconnue.|Duración de licencia no reconocida.|License duration not recognized.
Type de document inconnu.|Tipo de documento desconocido.|Unknown document type.
Choisissez un entrepreneur.|Elija un empresario.|Choose an entrepreneur.
Le nom de l'entreprise est obligatoire.|El nombre de la empresa es obligatorio.|The company name is required.
Indiquez le nom du client final.|Indique el nombre del cliente final.|Enter the end customer's name.
Ajoutez au moins une ligne.|Añada al menos una línea.|Add at least one line.
Quantités et prix doivent être positifs.|Las cantidades y los precios deben ser positivos.|Quantities and prices must be positive.
Cette clé a déjà été utilisée sur cet ordinateur.|Esta clave ya se utilizó en este ordenador.|This key has already been used on this computer.
Type de courrier invalide.|Tipo de correspondencia no válido.|Invalid mail type.
Indiquez le correspondant et l'objet.|Indique el corresponsal y el asunto.|Enter the correspondent and the subject.
Ce PDF est protégé : mot de passe requis ou incorrect.|Este PDF está protegido: contraseña requerida o incorrecta.|This PDF is protected: password required or incorrect.
Aucune licence activée sur cet ordinateur.|No hay ninguna licencia activada en este ordenador.|No license is activated on this computer.
Fichier de licence invalide pour cet ordinateur.|Archivo de licencia no válido para este ordenador.|License file invalid for this computer.
Indiquez la tâche à faire.|Indique la tarea pendiente.|Enter the task to do.
Date système incohérente : corrigez l'horloge de l'ordinateur.|Fecha del sistema incoherente: corrija el reloj del ordenador.|Inconsistent system date: correct the computer's clock.
Le taux de taxe doit être un nombre entre 0 et 100.|La tasa de impuesto debe ser un número entre 0 y 100.|The tax rate must be a number between 0 and 100.
Montant invalide.|Importe no válido.|Invalid amount.
Saisissez le texte à ajouter.|Escriba el texto que desea añadir.|Enter the text to add.
Impossible de supprimer la dernière page.|No se puede eliminar la última página.|The last page cannot be deleted.
Fichier introuvable.|Archivo no encontrado.|File not found.
Fichier trop volumineux (60 Mo maximum).|Archivo demasiado grande (máximo 60 MB).|File too large (60 MB maximum).
Format non pris en charge (PNG, JPG, TIFF, PDF...).|Formato no compatible (PNG, JPG, TIFF, PDF...).|Unsupported format (PNG, JPG, TIFF, PDF...).
Format non pris en charge (PNG, JPG, PDF...).|Formato no compatible (PNG, JPG, PDF...).|Unsupported format (PNG, JPG, PDF...).
Ce PDF est protégé par mot de passe : retirez-le d'abord (onglet PDF → Sécuriser).|Este PDF está protegido con contraseña: quítela primero (pestaña PDF → Proteger).|This PDF is password-protected: remove it first (PDF tab → Secure).
Ce fichier n'est pas une sauvegarde SecretariatPro.|Este archivo no es una copia de seguridad de SecretariatPro.|This file is not a SecretariatPro backup.
Format non pris en charge (utilisez .docx ou .txt).|Formato no compatible (use .docx o .txt).|Unsupported format (use .docx or .txt).
Nombre hors limites.|Número fuera de límites.|Number out of range.
Sauvegarde invalide.|Copia de seguridad no válida.|Invalid backup.
Indiquez au moins une page (ex. 1-3,5).|Indique al menos una página (ej. 1-3,5).|Enter at least one page (e.g. 1-3,5).
Sauvegarde invalide ou endommagée.|Copia de seguridad no válida o dañada.|Invalid or damaged backup.
Chemin non autorisé.|Ruta no permitida.|Path not allowed.
Un entrepreneur portant ce nom existe déjà.|Ya existe un empresario con este nombre.|An entrepreneur with this name already exists.
Le mot de passe doit contenir au moins 10 caractères.|La contraseña debe tener al menos 10 caracteres.|The password must contain at least 10 characters.
Utilisez des majuscules et des minuscules.|Use mayúsculas y minúsculas.|Use uppercase and lowercase letters.
Ajoutez au moins un chiffre.|Añada al menos un número.|Add at least one digit.
Ajoutez au moins un symbole (@, #, !, ...).|Añada al menos un símbolo (@, #, !, ...).|Add at least one symbol (@, #, !, ...).
Choisissez un mot de passe différent de celui par défaut.|Elija una contraseña distinta de la predeterminada.|Choose a password different from the default one.
Vous ne pouvez pas supprimer toutes les pages.|No puede eliminar todas las páginas.|You cannot delete all the pages.
Identifiant ou mot de passe incorrect.|Usuario o contraseña incorrectos.|Incorrect username or password.
Nom|Nombre|Name
Intelligence artificielle|Inteligencia artificial|Artificial intelligence
🤖  Intelligence artificielle|🤖  Inteligencia artificial|🤖  Artificial intelligence
Mode de fonctionnement|Modo de funcionamiento|Operating mode
Vous décidez de ce qui est actif. L'IA rédige dans la langue de l'application, sauf demande contraire de l'utilisateur. Si aucune IA n'est disponible (quota atteint, pas d'Internet), l'application utilise ses propres fonctions : mise en forme automatique et OCR intégré.|Usted decide qué está activo. La IA redacta en el idioma de la aplicación, salvo petición contraria del usuario. Si no hay ninguna IA disponible (cuota alcanzada, sin Internet), la aplicación usa sus propias funciones: formato automático y OCR integrado.|You decide what is active. The AI writes in the application's language unless the user asks otherwise. If no AI is available (quota reached, no Internet), the application uses its own functions: automatic formatting and built-in OCR.
IA locale (hors-ligne, modèle .gguf dans le dossier models)|IA local (sin conexión, modelo .gguf en la carpeta models)|Local AI (offline, .gguf model in the models folder)
IA en ligne (clés gratuites, rotation automatique)|IA en línea (claves gratuitas, rotación automática)|Online AI (free keys, automatic rotation)
Je comprends que les textes envoyés à l'IA en ligne (et les pages scannées si l'OCR IA est activé) quittent cet ordinateur et sont traités par le fournisseur choisi : à éviter pour les documents confidentiels.|Entiendo que los textos enviados a la IA en línea (y las páginas escaneadas si el OCR IA está activado) salen de este ordenador y los trata el proveedor elegido: evitar para documentos confidenciales.|I understand that texts sent to the online AI (and scanned pages if AI OCR is enabled) leave this computer and are processed by the chosen provider: avoid for confidential documents.
OCR IA : lire les documents scannés avec un modèle à vision (repli : OCR de l'application)|OCR IA: leer los documentos escaneados con un modelo de visión (alternativa: OCR de la aplicación)|AI OCR: read scanned documents with a vision model (fallback: the application's OCR)
Cochez d'abord la case de confirmation : l'IA en ligne envoie vos textes au fournisseur.|Marque primero la casilla de confirmación: la IA en línea envía sus textos al proveedor.|First tick the confirmation box: the online AI sends your texts to the provider.
Confirmation requise|Confirmación requerida|Confirmation required
Fournisseurs en ligne (paliers gratuits)|Proveedores en línea (niveles gratuitos)|Online providers (free tiers)
+  Ajouter un fournisseur personnalisé|+  Añadir un proveedor personalizado|+  Add a custom provider
Supprimer ce fournisseur et ses clés ?|¿Eliminar este proveedor y sus claves?|Delete this provider and its keys?
Ordre de priorité (le premier est essayé en premier)|Orden de prioridad (el primero se prueba primero)|Priority order (the first one is tried first)
Lever toutes les pauses|Quitar todas las pausas|Clear all pauses
Quand un quota est atteint, le fournisseur est mis en pause automatiquement puis repris.|Cuando se alcanza una cuota, el proveedor se pone en pausa automáticamente y luego se reanuda.|When a quota is reached, the provider is paused automatically and then resumed.
actif|activo|active
désactivé|desactivado|disabled
sans clé|sin clave|no key
Activé|Activado|Enabled
Configurer ▾|Configurar ▾|Configure ▾
Réduire ▴|Reducir ▴|Collapse ▴
Nom du fournisseur|Nombre del proveedor|Provider name
Clé(s) API — plusieurs clés séparées par « ; »|Clave(s) API — varias claves separadas por «;»|API key(s) — several keys separated by ";"
Obtenir une clé gratuite|Obtener una clave gratuita|Get a free key
Adresse de l'API (compatible OpenAI)|Dirección de la API (compatible con OpenAI)|API address (OpenAI-compatible)
Récupérer les modèles gratuits|Obtener los modelos gratuitos|Fetch the free models
Choix automatique|Selección automática|Automatic choice
Tester|Probar|Test
Cochez « Texte » pour la rédaction (l'ordre de la liste = ordre d'essai) et « OCR » pour la lecture de documents (modèles à vision).|Marque «Texto» para la redacción (el orden de la lista = orden de prueba) y «OCR» para la lectura de documentos (modelos con visión).|Tick "Text" for writing (list order = order tried) and "OCR" for reading documents (vision models).
Texte|Texto|Text
Aucun modèle : cliquez sur « Récupérer les modèles gratuits ».|Ningún modelo: haga clic en «Obtener los modelos gratuitos».|No model: click "Fetch the free models".
Indiquez l'adresse de l'API.|Indique la dirección de la API.|Enter the API address.
Récupération de la liste à jour...|Obteniendo la lista actualizada...|Fetching the up-to-date list...
Échec : {x}|Error: {x}|Failed: {x}
{n} modèle(s) trouvé(s). Cochez ceux à utiliser puis enregistrez.|{n} modelo(s) encontrado(s). Marque los que desea usar y guarde.|{n} model(s) found. Tick the ones to use, then save.
Récupérez d'abord la liste des modèles.|Obtenga primero la lista de modelos.|Fetch the model list first.
Sélection automatique faite : {n} modèle(s). Pensez à enregistrer.|Selección automática hecha: {n} modelo(s). Recuerde guardar.|Automatic selection done: {n} model(s). Remember to save.
Enregistré.|Guardado.|Saved.
Ajoutez une clé et cochez au moins un modèle.|Añada una clave y marque al menos un modelo.|Add a key and tick at least one model.
Test en cours...|Prueba en curso...|Test in progress...
⏳ en pause jusqu'à {t}|⏳ en pausa hasta las {t}|⏳ paused until {t}
{k} clé(s) • {m} modèle(s)|{k} clave(s) • {m} modelo(s)|{k} key(s) • {m} model(s)
L'IA n'est pas activée. L'administrateur peut l'activer dans le menu « Intelligence artificielle ».|La IA no está activada. El administrador puede activarla en el menú «Inteligencia artificial».|The AI is not enabled. The administrator can enable it in the "Artificial intelligence" menu.
✔ rédigé par : {x}|✔ redactado por: {x}|✔ written by: {x}
L'IA est indisponible pour le moment : {x}|La IA no está disponible por el momento: {x}|The AI is unavailable at the moment: {x}
Mise en forme automatique de l'application appliquée.|Se aplicó el formato automático de la aplicación.|The application's automatic formatting was applied.
L'IA est indisponible pour le moment ({x}). L'application a utilisé sa propre mise en forme automatique.|La IA no está disponible por el momento ({x}). La aplicación usó su propio formato automático.|The AI is unavailable at the moment ({x}). The application used its own automatic formatting.
OCR IA en cours...|OCR IA en curso...|AI OCR in progress...
OCR IA indisponible : OCR de l'application utilisé|OCR IA no disponible: se usó el OCR de la aplicación|AI OCR unavailable: the application's OCR was used
L'OCR IA est indisponible ({x}). L'OCR intégré de l'application a été utilisé.|El OCR IA no está disponible ({x}). Se usó el OCR integrado de la aplicación.|AI OCR is unavailable ({x}). The application's built-in OCR was used.
OCR IA : {x}|OCR IA: {x}|AI OCR: {x}
({n} page(s) lue(s) par l'OCR de l'application)|({n} página(s) leída(s) por el OCR de la aplicación)|({n} page(s) read by the application's OCR)
Word (texte IA)|Word (texto IA)|Word (AI text)
Aucune IA activée|Ninguna IA activada|No AI enabled
Assistant IA|Asistente IA|AI assistant
✨  Rédiger avec l'IA|✨  Redactar con la IA|✨  Write with AI
✨  Améliorer avec l'IA|✨  Mejorar con la IA|✨  Improve with AI
✨  Rédiger|✨  Redactar|✨  Write
Mettre en forme et exporter  ➜|Dar formato y exportar  ➜|Format and export  ➜
Rédaction en cours... (le premier lancement du modèle peut prendre 1 minute)|Redactando... (el primer arranque del modelo puede tardar 1 minuto)|Writing... (the first model start can take 1 minute)
Une rédaction est déjà en cours. Patientez un instant.|Ya hay una redacción en curso. Espere un momento.|A draft is already in progress. Please wait a moment.
IA locale|IA local|Local AI
Pas de rédaction IA pour ce type de document : utilisez l'onglet « Assistant IA ».|No hay redacción con IA para este tipo de documento: use la pestaña «Asistente IA».|No AI drafting for this document type: use the "AI assistant" tab.
La génération a échoué. Le modèle est peut-être trop lourd pour cet ordinateur.|La generación falló. Es posible que el modelo sea demasiado pesado para este ordenador.|Generation failed. The model may be too heavy for this computer.
Décrivez le texte voulu : l'IA locale le rédige sur cet ordinateur, sans Internet. Ex. : « Lettre au maire pour demander un rendez-vous au sujet du permis de construire de la villa Obiang ».|Describa el texto deseado: la IA local lo redacta en este ordenador, sin Internet. Ej.: «Carta al alcalde para pedir una cita sobre el permiso de construcción de la villa Obiang».|Describe the text you want: the local AI writes it on this computer, without Internet. E.g.: "Letter to the mayor requesting a meeting about the building permit for the Obiang villa".
Décrivez d'abord le texte à rédiger.|Primero describa el texto que desea redactar.|First describe the text to write.
Rédigez d'abord un texte avec l'IA.|Primero redacte un texto con la IA.|First write a text with the AI.
Intelligence artificielle locale|Inteligencia artificial local|Local artificial intelligence
L'IA rédige les textes (lettres, notes, procès-verbaux...) directement sur cet ordinateur, sans Internet. Placez un modèle .gguf dans le dossier models.|La IA redacta los textos (cartas, notas, actas...) directamente en este ordenador, sin Internet. Coloque un modelo .gguf en la carpeta models.|The AI writes texts (letters, memos, minutes...) directly on this computer, without Internet. Place a .gguf model in the models folder.
Ouvrir le dossier models|Abrir la carpeta models|Open the models folder
Tester l'IA|Probar la IA|Test the AI
Test en cours...|Prueba en curso...|Test in progress...
IA prête — modèle : {name}|IA lista — modelo: {name}|AI ready — model: {name}
Le test a échoué. Le modèle est peut-être incompatible ou trop lourd.|La prueba falló. Es posible que el modelo sea incompatible o demasiado pesado.|The test failed. The model may be incompatible or too heavy.
Le moteur d'IA n'est pas inclus dans cette version de l'application.|El motor de IA no está incluido en esta versión de la aplicación.|The AI engine is not included in this version of the application.
Aucun modèle trouvé : placez un fichier .gguf dans le dossier models.|No se encontró ningún modelo: coloque un archivo .gguf en la carpeta models.|No model found: place a .gguf file in the models folder.
Enregistrer les images|Guardar las imágenes|Save the images
Aucune image détectée dans ce document.|No se detectó ninguna imagen en este documento.|No image detected in this document.
{n} image(s) enregistrée(s).|{n} imagen(es) guardada(s).|{n} image(s) saved.
Tous|Todos|All
Rechercher (n°, client, entrepreneur, date...)|Buscar (n.º, cliente, empresario, fecha...)|Search (no., customer, entrepreneur, date...)
+  Créer une facture / un devis|+  Crear una factura / un presupuesto|+  Create an invoice / quotation
←  Retour à la liste|←  Volver a la lista|←  Back to the list
{n} document(s)|{n} documento(s)|{n} document(s)
Dossier|Carpeta|Folder
Retirer cette ligne de l'historique ?\n(Le fichier PDF reste sur votre ordinateur.)|¿Quitar esta línea del historial?\n(El archivo PDF permanece en su ordenador.)|Remove this line from the history?\n(The PDF file stays on your computer.)
Sélectionnez un entrepreneur dans la liste ou cliquez sur « + Nouvel entrepreneur ».|Seleccione un empresario de la lista o haga clic en «+ Nuevo empresario».|Select an entrepreneur from the list or click "+ New entrepreneur".
+  Nouveau courrier|+  Nuevo correo|+  New mail
+  Nouvelle tâche|+  Nueva tarea|+  New task
+  Nouveau compte|+  Nueva cuenta|+  New account
Annuler|Cancelar|Cancel
Module indisponible|Módulo no disponible|Module unavailable
Cette fonction n'a pas pu être chargée. Le reste de l'application fonctionne.|Esta función no se pudo cargar. El resto de la aplicación funciona.|This feature could not be loaded. The rest of the application works.
Détail technique : {x}|Detalle técnico: {x}|Technical detail: {x}
Comptes utilisateurs|Cuentas de usuario|User accounts
Créez un compte pour chaque employé du secrétariat : il pourra travailler mais pas gérer la licence, les sauvegardes ni les comptes.|Cree una cuenta para cada empleado de secretaría: podrá trabajar, pero no gestionar la licencia, las copias de seguridad ni las cuentas.|Create an account for each secretarial employee: they can work but cannot manage the license, backups or accounts.
Nom d'utilisateur|Nombre de usuario|Username
Mot de passe provisoire|Contraseña provisional|Temporary password
Secrétariat|Secretaría|Secretarial staff
Administrateur|Administrador|Administrator
Créer le compte|Crear la cuenta|Create account
Compte créé. L'utilisateur devra changer son mot de passe à la première connexion.|Cuenta creada. El usuario deberá cambiar su contraseña en el primer inicio de sesión.|Account created. The user must change their password at first sign-in.
Réinitialiser le mot de passe|Restablecer la contraseña|Reset password
Nouveau mot de passe provisoire pour {name} :|Nueva contraseña provisional para {name}:|New temporary password for {name}:
Mot de passe réinitialisé : {name} devra en choisir un nouveau à sa prochaine connexion.|Contraseña restablecida: {name} deberá elegir una nueva en su próximo inicio de sesión.|Password reset: {name} must choose a new one at next sign-in.
Supprimer le compte {name} ?|¿Eliminar la cuenta {name}?|Delete the account {name}?
Désactiver|Desactivar|Disable
Activer|Activar|Enable
Actif|Activo|Active
Désactivé|Desactivado|Disabled
Vous ne pouvez pas supprimer ou désactiver votre propre compte.|No puede eliminar ni desactivar su propia cuenta.|You cannot delete or disable your own account.
Il doit rester au moins un administrateur actif.|Debe quedar al menos un administrador activo.|At least one active administrator must remain.
Ce nom d'utilisateur existe déjà.|Este nombre de usuario ya existe.|This username already exists.
Nom d'utilisateur invalide (3 à 30 caractères : lettres, chiffres, . _ -).|Nombre de usuario no válido (3 a 30 caracteres: letras, números, . _ -).|Invalid username (3 to 30 characters: letters, digits, . _ -).
Rôle invalide.|Rol no válido.|Invalid role.
Ce compte est désactivé. Contactez l'administrateur.|Esta cuenta está desactivada. Contacte con el administrador.|This account is disabled. Contact the administrator.
Licence requise|Licencia requerida|License required
Demandez à l'administrateur d'activer ce poste, puis reconnectez-vous.|Pida al administrador que active este equipo y vuelva a iniciar sesión.|Ask the administrator to activate this computer, then sign in again.
Licence, sauvegardes et comptes : réservés à l'administrateur.|Licencia, copias de seguridad y cuentas: reservadas al administrador.|License, backups and accounts: reserved for the administrator.
Connecté : {name} ({role})|Conectado: {name} ({role})|Signed in: {name} ({role})
Sous-total|Subtotal|Subtotal
"""

TR = {}
for _line in _RAW.strip().split("\n"):
    _p = _line.split("|")
    if len(_p) == 3:
        _p = [x.replace("\\n", "\n") for x in _p]
        TR[_p[0]] = {"es": _p[1], "en": _p[2]}

# Messages dynamiques (expressions régulières sur le texte français).
PATTERNS = [
    (r"Licence activée jusqu'au (.+)\.", "Licencia activada hasta el \\1.", "License activated until \\1."),
    (r"Licence expirée le (.+)\.", "Licencia caducada el \\1.", "License expired on \\1."),
    (r"Trop de tentatives\. Réessayez dans (\d+) min\.", "Demasiados intentos. Vuelva a intentarlo en \\1 min.", "Too many attempts. Try again in \\1 min."),
    (r"Pages invalides : « (.+) »\.", "Páginas no válidas: «\\1».", "Invalid pages: \"\\1\"."),
    (r"La page (\d+) n'existe pas \(le document en compte (\d+)\)\.", "La página \\1 no existe (el documento tiene \\2).", "Page \\1 does not exist (the document has \\2)."),
    (r"Nombre invalide : (.+)", "Número no válido: \\1", "Invalid number: \\1"),
    (r"Active jusqu'au (.+) \((\d+) jours restants\)", "Activa hasta el \\1 (\\2 días restantes)", "Active until \\1 (\\2 days left)"),
    (r"dont (\d+) en retard", "de ellas \\1 con retraso", "\\1 overdue"),
    (r"(\d+) pour aujourd'hui", "\\1 para hoy", "\\1 due today"),
    (r"Licence : (\d+) j restants", "Licencia: \\1 d restantes", "License: \\1 d left"),
    (r"Courrier enregistré sous le n° (.+)\.", "Correspondencia registrada con el n.º \\1.", "Mail recorded under no. \\1."),
    (r"Document enregistré dans le dossier de (.+)\.\nL'ouvrir maintenant \?", "Documento guardado en la carpeta de \\1.\n¿Abrirlo ahora?", "Document saved in \\1's folder.\nOpen it now?"),
    (r"Texte archivé dans le dossier de (.+)\.", "Texto archivado en la carpeta de \\1.", "Text archived in \\1's folder."),
    (r"(\d+) fichiers créés\.", "\\1 archivos creados.", "\\1 files created."),
    (r"(\d+) image\(s\) créée\(s\)\.", "\\1 imagen(es) creada(s).", "\\1 image(s) created."),
]
_PAT = [(re.compile("^" + p + "$", re.S), es, en) for p, es, en in PATTERNS]


def t(text, **fmt):
    """Traduit `text` (français) dans la langue courante ; format() optionnel."""
    out = text
    if _lang != "fr" and isinstance(text, str):
        e = TR.get(text)
        if e:
            out = e[_lang]
        else:
            for rx, es, en in _PAT:
                m = rx.match(text)
                if m:
                    out = m.expand(es if _lang == "es" else en)
                    break
    return out.format(**fmt) if fmt else out

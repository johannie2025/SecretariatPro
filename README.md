# SecretariatPro — W Design

Application Windows 100 % hors-ligne pour secrétariats et cabinets d'assistance.

**Contacts W Design (WhatsApp) : +240 222 886 007 / +240 555 593 398 / +240 555 445 514**

## Langues / Idiomas / Languages
Interface **français, español, English** : choix sur l'écran de connexion et dans Paramètres → Langue
(mémorisé). Les factures/devis et les documents types (lettres, attestations, reçus...) se génèrent aussi
dans les trois langues, avec montants en toutes lettres, dates et séparateurs adaptés.
Note : l'OCR reconnaît bien le français, l'espagnol et l'anglais ; vérifiez les ñ, ¿ et ¡ sur les scans de
mauvaise qualité.

## Fonctionnalités
- **Facturation** : facture, proforma, devis pour les clients des entrepreneurs, avec montant en toutes lettres.
- **Numérisation (OCR)** : photo, scan ou PDF → Word reconstruit (titres, paragraphes, **tableaux, images et dessins**)
  ou PDF recherchable fidèle à l'original ; copie du texte ; enregistrement dans le dossier du client.
- **Outils PDF** : éditeur visuel (texte, signature/cachet, masquage, remplacement, surlignage), fusion,
  extraction, réorganisation, suppression, pivotement, séparation, PDF ↔ Word / images, mot de passe,
  filigrane, numérotation, compression.
- **Rédaction** : 11 documents types (lettres, attestations, convocation, PV, note de service, reçu,
  décharge, procuration, relance...), mise en forme automatique d'un texte brut (typographie française,
  titres, listes), montant en lettres.
- **Courrier & tâches** : registre entrant/sortant (export Excel/CSV), rappels et échéances.
- **Modèles Word** à champs détectés automatiquement, **sauvegarde/restauration**, thème clair/sombre,
  page **À propos** avec les contacts de W Design.

## Générer le .exe avec GitHub Actions
1. Créez un dépôt GitHub (privé de préférence) et envoyez-y le contenu de ce dossier :
   `git init && git add . && git commit -m "SecretariatPro v1.0" && git branch -M main`
   `git remote add origin https://github.com/VOTRE_COMPTE/SecretariatPro.git && git push -u origin main`
2. Onglet **Actions** → « Build SecretariatPro (Windows .exe) » (il démarre seul à chaque push ;
   ou **Run workflow** pour choisir « un seul .exe »).
3. En fin de build (≈ 6-10 min), téléchargez **SecretariatPro-Windows** dans *Artifacts*
   (ou dans *Releases* si vous poussez un tag `v1.0`). Décompressez puis lancez `SecretariatPro.exe`.

## Comptes
- **Administrateur** (`admin`) : tout, y compris licence, sauvegardes et création des comptes.
- **Secrétariat** : crée un compte pour chaque employé dans Paramètres → Comptes utilisateurs
  (mot de passe provisoire, changement obligatoire à la première connexion). Il travaille normalement mais
  ne peut ni activer la licence, ni sauvegarder/restaurer, ni gérer les comptes.
- Si la licence d'un poste expire, le secrétariat voit « Licence requise » : seul l'administrateur réactive.

## Premier démarrage
1. Connexion : identifiant `admin`, mot de passe initial communiqué par W Design
   (changement **obligatoire** à la première connexion).
2. Si le poste n'a pas de licence, l'écran « Activer ce poste » s'affiche : choisissez 1 mois,
   3 mois, 6 mois ou 1 an puis **Activer sur ce poste**. Chaque activation est journalisée.
3. Activation à distance (option) : le client vous envoie son code machine, vous générez une clé
   avec `keygen.py`, il la colle sur le même écran.
Le renouvellement se fait aussi dans **Paramètres → Licence**.

## Sécurité
- Mots de passe : PBKDF2-SHA256 (600 000 itérations, sel 32 octets), blocage 5 min après 5 échecs.
- Licence : clé signée Ed25519 (clé privée jamais dans l'application), liée au HWID, stockée chiffrée
  AES-256-GCM, détection de retour en arrière de l'horloge.
- Aucune télémétrie ; l'application n'envoie aucune donnée (le bouton WhatsApp de « À propos » ouvre seulement votre navigateur). Noms de fichiers nettoyés (anti Path Traversal).
- Requêtes SQL paramétrées, erreurs journalisées dans `%APPDATA%\SecretariatPro\app.log`.

## Données
- Base et licence : `%APPDATA%\SecretariatPro\`
- Documents : `Documents\Data_Secretariat\Clients\<Entrepreneur>\{Factures_Emises, Devis_Proforma, Documents_Generes, Documents_OCR, Documents_PDF, Courrier, Logo}`

## Modèles Word
Écrivez `[NomClient]`, `[Date]`… ou `Intitulé : ________` dans votre .docx : l'application détecte
les champs et génère le formulaire.

## Lancer en développement
`pip install -r requirements.txt && python main.py`

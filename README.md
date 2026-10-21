# SecretariatPro — W Design

Application Windows 100 % hors-ligne pour secrétariats et cabinets d'assistance :
facturation (facture / proforma / devis) pour des entrepreneurs tiers, modèles Word à champs
automatiques, OCR local (images et PDF), archivage par client.

**Contact W Design (WhatsApp) : +240 222 886 007 / +240 555 445 514**

## Générer le .exe avec GitHub Actions
1. Créez un dépôt GitHub (privé de préférence) et envoyez-y le contenu de ce dossier :
   `git init && git add . && git commit -m "SecretariatPro v1.0" && git branch -M main`
   `git remote add origin https://github.com/VOTRE_COMPTE/SecretariatPro.git && git push -u origin main`
2. Onglet **Actions** → « Build SecretariatPro (Windows .exe) » (il démarre seul à chaque push ;
   ou **Run workflow** pour choisir « un seul .exe »).
3. En fin de build (≈ 6-10 min), téléchargez **SecretariatPro-Windows** dans *Artifacts*
   (ou dans *Releases* si vous poussez un tag `v1.0`). Décompressez puis lancez `SecretariatPro.exe`.

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
- Aucun accès réseau, aucune télémétrie. Noms de fichiers nettoyés (anti Path Traversal).
- Requêtes SQL paramétrées, erreurs journalisées dans `%APPDATA%\SecretariatPro\app.log`.

## Données
- Base et licence : `%APPDATA%\SecretariatPro\`
- Documents : `Documents\Data_Secretariat\Clients\<Entrepreneur>\{Factures_Emises, Devis_Proforma, Documents_Generes, Documents_OCR, Logo}`

## Modèles Word
Écrivez `[NomClient]`, `[Date]`… ou `Intitulé : ________` dans votre .docx : l'application détecte
les champs et génère le formulaire.

## Lancer en développement
`pip install -r requirements.txt && python main.py`

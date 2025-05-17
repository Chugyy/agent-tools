## Outils à ajouter dans les `Settings` et l'`.env`dans la partie `ENABLED_TOOLS` ou nom similaire.

- `lister_evenements_calendrier`
- `creer_evenement_calendrier`
- `mettre_a_jour_evenement_calendrier`
- `supprimer_evenement_calendrier`

## Prérequis

- Un compte Google (Gmail) actif  
- Navigateur Web (Chrome, Firefox, etc.)  
- Accès à Internet  

## 1. Créer un compte et accéder à la Google Cloud Console

1. Rendez-vous sur [Google Cloud Console](https://console.cloud.google.com/).  
2. Connectez-vous avec votre compte Google ou créez-en un si nécessaire.  

## 2. Créer un nouveau projet

1. Dans la barre supérieure, cliquez sur le sélecteur de projet (nom du projet actuel ou **« Sélectionner un projet »**).  
2. Cliquez sur **NOUVEAU PROJET**.  
3. Donnez un nom à votre projet (par ex. `mon-calendrier-app`) et, si vous le souhaitez, modifiez l’organisation ou le dossier.  
4. Cliquez sur **CRÉER**.  

## 3. Activer l’API Google Calendar

1. Dans le menu latéral, allez dans **API et services › Bibliothèque**.  
2. Recherchez **Google Calendar API**.  
3. Cliquez sur **Google Calendar API**, puis sur **ACTIVER**.  

## 4. Configurer l’écran de consentement OAuth

1. Toujours dans **API et services**, sélectionnez **Écran de consentement OAuth**.  
2. Choisissez le mode **Externe** (si votre application n’est pas réservée aux utilisateurs de votre organisation) et cliquez sur **CRÉER**.  
3. Remplissez les champs obligatoires :  
   - **Nom de l’application**  
   - **Adresse e-mail de l’assistance utilisateur**  
   - **Logo**, si vous en avez un (facultatif)  
4. Cliquez sur **ENREGISTRER ET CONTINUER** jusqu’à l’étape **Utilisateurs de test**.  
5. Dans **Utilisateurs de test**, cliquez sur **AJOUTER DES UTILISATEURS** et entrez l’adresse e-mail de tout compte Google que vous souhaitez autoriser (votre compte principal, ou un compte de développement).  
6. Cliquez sur **ENREGISTRER ET CONTINUER**, puis **TERMINER**.  

## 5. Créer des identifiants OAuth 2.0

1. Dans **API et services › Identifiants**, cliquez sur **CRÉER DES IDENTIFIANTS › ID client OAuth**.  
2. Sélectionnez **Type d’application : Application Web**.  
3. Donnez un nom (par ex. `App Locale`).  
4. Sous **URIs de redirection autorisés**, cliquez sur **AJOUTER UN URI** et saisissez votre URL locale, par exemple :  
```

http://localhost/

````
5. Cliquez sur **CRÉER**.  

## 6. Récupérer le Client ID et le Client secret

Après la création, une fenêtre pop-up affiche :
- **Identifiant client (Client ID)**  
- **Secret client (Client secret)**  

Copiez ces deux valeurs dans votre fichier de configuration ou vos variables d’environnement, par exemple :
```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=ABCDefGHIJklmnOPQRstuVwX
````

## 7. Tester votre application en local

1. Dans votre application web, configurez la bibliothèque OAuth (Google APIs client) avec vos identifiants.
2. Lancez votre serveur local (ex. `npm start` ou `yarn dev`).
3. Ouvrez votre navigateur à l’URL locale (ex. `http://localhost:3000/`).
4. Initiez le flux d’authentification : vous êtes redirigé vers la page Google, puis renvoyé à votre callback local (`/oauth2callback`) avec un code d’autorisation.
5. Échangez ce code contre un token d’accès pour interagir avec l’API Calendar.

---

> 🎉 Vous avez maintenant :
>
> 1. Un projet Google Cloud configuré
> 2. L’API Google Calendar activée
> 3. Un écran de consentement OAuth avec utilisateur(s) test
> 4. Une application Web OAuth prête à l’emploi en local
> 5. Vos clés Client ID / Client Secret pour l’authentification

---

Tu peux ensuite supprimer `README.md`, `requirements.txt` et `.env.example` **SEULEMENT** si tu as déjà ré-installer les dépendances nécessaires avec un `pip3 install -r requirements.txt` et que les identifiants sont bien réangés dans la vraie partie `.env` et `settings.py` de ton agent IA.
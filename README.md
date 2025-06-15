# mcp-pilot

Note : cet exemple de code est dans des buts d'apprentissage, il n'y a pas (encore) aujourd'hui d'application concrète pour la coupe robotique.

Matériel requis :
- un PC équipé de bluetooth
- le robot démo Arduino et ses roues mecanum

Logiciel requis :
- un environnement python
- une licence github copilot (existe en version gratuite pour tout possesseur d'un compte github)
- GitHub copilot installé dans vs code

## Configurer le serveur MCP

Ajouter le serveur MCP au fichier de configuration, `%APPDATA%\Code\User\settings.json` avec les lignes suivantes :

   "mcp": {
        "servers": {
            "my-mcp-server-0d41d230": {
                "type": "stdio",
                "command": "python3",
                "args": [
                    "ble/pilot-mcp.py"
                ]
            }
        }
    }

Ajuster le chemin au fichier .py à votre environnement

## Ecrire un prompt dans la fenêtre chat de copilot en mode "agent"

Par exemple : "fais avancer le robot arduino pendant 10 secondes" ; "fais danser le robot en rock pendant 5 secondes"

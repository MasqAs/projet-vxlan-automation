## Table des matières

1. [Installation de ContainerLab](#installation-de-containerlab)
2. [Installation de vrnetlab](#installation-de-vrnetlab)
3. [Installation de Docker](#installation-de-docker)

## Installation de ContainerLab

Containerlab peut être installé à l'aide du script d'installation qui détecte le type de système d'exploitation et installe le paquetage approprié :  

```bash
# télécharger et installer la dernière version (peut nécessiter sudo)
bash -c "$(curl -sL https://get.containerlab.dev)"

# avec wget
bash -c "$(wget -qO - https://get.containerlab.dev)"
```

## Installation de vrnetlab

Vrnetlab place une VM normale dans un conteneur et la rend exécutable comme s'il s'agissait d'une image de conteneur.  
Pour ce faire, vrnetlab fournit un ensemble de scripts qui construisent l'image du conteneur à partir d'un disque VM fourni par l'utilisateur.  

```bash 
# mise à jour et installation des dépendances
sudo apt update
sudo apt -y install python3-bs4 sshpass make
sudo apt -y install git

# se déplacer dans /opt et cloner le projet
sudo cd /opt && sudo git clone https://github.com/hellt/vrnetlab

# optionnel : modification des droits du répertoire
sudo chown -R $USER:$USER vrnetlab
```

## Installation de docker

Il s'agit de moteur de conteneurisation utilisé par ContainerLab

```bash
# Mise à jour et installation des dépendances
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# Ajout de la clef GPG
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Ajout du dépôt
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Mise à jour et installation
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## Sources
- [InsContainerLab](https://containerlab.dev/install/)
- [vrnetlab](https://containerlab.dev/manual/vrnetlab/#vrnetlab)
- [BiranLinkLetter](https://www.brianlinkletter.com/2019/03/vrnetlab-emulate-networks-using-kvm-and-docker/)
- [Docker Engine for Debian](https://docs.docker.com/engine/install/debian/)
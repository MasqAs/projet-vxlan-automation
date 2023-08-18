# Projet d'Automatisation VXLAN EVPN

Ce projet vise à automatiser la création et la gestion d'un laboratoire de test VXLAN EVPN en utilisant ContainerLab, Arista cEOS, Cisco N9Kv, et Netbox. L'automatisation est réalisée principalement grâce à Ansible et des scripts Python.

## Table des matières

1. [Pré-requis](#pré-requis)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Structure du projet](#structure-du-projet)
5. [Contributions](#contributions)
6. [Licence](#licence)
7. [Sources](#sources)

## Pré-requis

- Docker & ContainerLab installés.
- Images pour Arista cEOS et Cisco N9Kv téléchargées.
- Python 3.x avec les bibliothèques nécessaires (voir `requirements.txt`).

## Installation

1. **Clonez le dépôt** :

   ```bash
   git clone https://github.com/MasqAs/projet-vxlan-automation.git
   cd projet-vxlan-automation
   ```

2. **Installez les dépendances Python** :

   ```bash
   pip install -r requirements.txt
   ```

3. **(Optionnel) Configurez les variables** :

   Adaptez les variables dans `ansible/vars/main.yml` selon vos besoins.

4. **Lancez l'automatisation** :

   Suivez les étapes dans [Usage](#usage) pour démarrer votre lab.

## Usage

1. **Mise en place du lab** :

   ```bash
   ansible-playbook ansible/playbooks/setup_containerlab.yml
   ```

2. **Configurer Netbox** :

   ```bash
   ansible-playbook ansible/playbooks/deploy_netbox.yml
   ```

3. **(Autres étapes)** :

   Suivez les instructions supplémentaires dans `documentation/USAGE.md`.

## Structure du projet

- `/ansible/` - Contient tous les playbooks, rôles, variables, et inventaires d'Ansible.
- `/python-scripts/` - Scripts Python pour diverses tâches.
- `/containerlab/` - Définitions et configurations pour ContainerLab.
- `/configs/` - Configurations initiales pour les équipements réseau.
- `/documentation/` - Documentation détaillée du projet.
- `/suzieq/` - Fichiers spécifiques à SuzieQ.

Pour plus de détails, veuillez consulter `documentation/STRUCTURE.md`.

## Contributions

Les contributions sont les bienvenues ! Veuillez soumettre des pull requests ou ouvrir des issues pour toute suggestion ou correction.

## Licence

Ce projet est sous licence APACHE. Voir le fichier [LICENSE](LICENSE) pour plus d'informations.

## Sources

- [ContainerLab](https://containerlab.dev/manual/kinds/ext-container/)
- [The ACSII Construct](https://www.theasciiconstruct.com/post/multivendor-evpn-vxlan-l2-overlay/)
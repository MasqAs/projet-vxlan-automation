# VXLAN EVPN Automation Project

This project aims to automate the creation and management of a VXLAN EVPN test lab using ContainerLab, Arista cEOS, Nokia SRLinux, and Netbox 4.1. The automation is primarily achieved through Ansible and Python scripts.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Usage](#usage)
4. [License](#license)
5. [Sources](#sources)

## Prerequisites

- Docker, ContainerLab, and Ansible installed.
- Images for Arista cEOS, Nokia SRLinux, and Linux Alpine downloaded.
- Python 3.13 with the necessary libraries installed (see `requirements.txt`).

## Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/MasqAs/projet-vxlan-automation.git
    cd vxlan-evpn-automation-project
    ```

2. **Install Python Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Install Depedencies**:

    The instructions are described here : [Installation Documentation](./documentation/INSTALLATION.md)

4. **Start the Automation**:

    Follow the steps in [Usage](#usage) to start your lab.

## Usage

1. **Set Up the Lab**:

    ```bash
    sudo containerlab deploy --topo containerlab/lab_definition.yml
    ```

2. **Configure Netbox**:

    For this project, we need to install specific plugin :
    - [Netbox BGP](https://github.com/netbox-community/netbox-bgp)

    ```bash
    git clone -b release https://github.com/netbox-community/netbox-docker.git netbox
    cd netbox
    touch plugin_requirements.txt Dockerfile-Plugins docker-compose.override.yml
    echo "netbox-bgp" > plugin_requirements.txt #Install BGP Plugin Pypi Package
    ```

    Create the Dockerfile used to build the custom Image

    ```bash
    cat << EOF > Dockerfile-Plugins
    FROM netboxcommunity/netbox:latest

    COPY ./plugin_requirements.txt /opt/netbox/
    RUN /opt/netbox/venv/bin/pip install  --no-warn-script-location -r /opt/netbox/plugin_requirements.txt

    COPY configuration/configuration.py /etc/netbox/config/configuration.py
    COPY configuration/plugins.py /etc/netbox/config/plugins.py
    RUN SECRET_KEY="dummydummydummydummydummydummydummydummydummydummy" /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py collectstatic --no-input
    EOF
    ```

    > [!TIP]
    > This `SECRET_KEY` is only used during the installation. There's no need to change it.

    Create the `docker-compose.override.yml`

    ```bash
    cat <<EOF > docker-compose.override.yml
    services:
      netbox:
        image: netbox:latest
        pull_policy: never
        ports:
          - 8000:8080
        build:
          context: .
          dockerfile: Dockerfile-Plugins
      netbox-worker:
        image: netbox:latest
        pull_policy: never
      netbox-housekeeping:
        image: netbox:latest
        pull_policy: never
    EOF
    ```

    Enable the plugin by adding configuration in `configuration/plugins.py`

    ```python
    PLUGINS = ["netbox_bgp"]

    # PLUGINS_CONFIG = {
    #   "netbox_bgp": {
    #     ADD YOUR SETTINGS HERE
    #   }
    # }
    ```

    Build and Deploy

    ```bash
    docker compose build --no-cache
    docker compose up -d
    ```

    Create the first admin user :

    ```bash
    docker compose exec netbox /opt/netbox/netbox/manage.py createsuperuser
    ```

## License

This project is licensed under the APACHE license. See the [LICENSE](LICENSE) file for more information.

## Sources

- [ContainerLab](https://containerlab.dev/)
- [NetBox Docker Plugin](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins)

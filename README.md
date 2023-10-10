# VXLAN EVPN Automation Project

This project aims to automate the creation and management of a VXLAN EVPN test lab using ContainerLab, Arista cEOS, Nokia SRLinux, and Netbox. The automation is primarily achieved through Ansible and Python scripts.

🖋️ **_NOTE_**: The environment used is Debian 12:

```bash
Distributor ID: Debian
Description:    Debian GNU/Linux 12 (bookworm)
Release:        12
Codename:       bookworm
```

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Project Structure](#project-structure)
5. [Contributions](#contributions)
6. [License](#license)
7. [Sources](#sources)

## Prerequisites

- Docker, ContainerLab, and Ansible installed.
- Images for Arista cEOS, Nokia SRLinux, and Linux Alpine downloaded.
- Python 3.11 with the necessary libraries installed (see `requirements.txt`).

## Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/MasqAs/vxlan-evpn-automation-project.git
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

    ```bash
    ansible-playbook ansible/playbooks/deploy_netbox.yml
    ```

3. **(Additional Steps)**:

    Follow the additional instructions in `documentation/USAGE.md`.

## Project Structure

- `/ansible/` - Contains all Ansible playbooks, roles, variables, and inventories.
- `/python-scripts/` - Python scripts for various tasks.
- `/containerlab/` - Definitions and configurations for ContainerLab.
- `/configs/` - Initial configurations for network equipment.
- `/documentation/` - Detailed project documentation.
- `/suzieq/` - Files specific to SuzieQ.

For more details, please refer to `documentation/STRUCTURE.md`.

## Contributions

Contributions are welcome! Please submit pull requests or open issues for any suggestions or corrections.

## License

This project is licensed under the APACHE license. See the [LICENSE](LICENSE) file for more information.

## Sources

- [ContainerLab](https://containerlab.dev/)
- [The ASCII Construct](https://www.theasciiconstruct.com/post/multivendor-evpn-vxlan-l2-overlay/)
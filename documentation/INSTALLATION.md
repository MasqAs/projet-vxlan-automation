## Table of Contents

1. [Installing ContainerLab](#installing-containerlab)
2. [Installing vrnetlab](#installing-vrnetlab)
3. [Installing Docker](#installing-docker)

## Installing ContainerLab

ContainerLab can be installed using the installation script that detects the operating system type and installs the appropriate package:

```bash
# download and install the latest version (may require sudo)
bash -c "$(curl -sL https://get.containerlab.dev)"

# with wget
bash -c "$(wget -qO - https://get.containerlab.dev)"
```

## Installing vrnetlab

Vrnetlab places a VM inside a container and makes it executable as if it were a container image.  
To do this, vrnetlab provides a set of scripts that build the container image from a VM disk provided by the user.

```bash 
# update and install dependencies
sudo apt update
sudo apt -y install python3-bs4 sshpass make
sudo apt -y install git

# move to /opt and clone the project
sudo cd /opt && sudo git clone https://github.com/hellt/vrnetlab

# optional: change the directory permissions
sudo chown -R $USER:$USER vrnetlab
```

## Installing Docker

This is the containerization engine used by ContainerLab.

```bash
# Update and install dependencies
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

## Sources
- [ContainerLab](https://containerlab.dev/install/)
- [vrnetlab](https://containerlab.dev/manual/vrnetlab/#vrnetlab)
- [BrianLinkLetter](https://www.brianlinkletter.com/2019/03/vrnetlab-emulate-networks-using-kvm-and-docker/)
- [Docker Engine for Debian](https://docs.docker.com/engine/install/debian/)
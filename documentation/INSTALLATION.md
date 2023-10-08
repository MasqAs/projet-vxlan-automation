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
cd /opt && sudo git clone https://github.com/hellt/vrnetlab

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
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# To be able to execute docker with the current user
sudo usermod -aG docker $USER
```

## Images installation

### Arista cEOS

To download and install the arista cEOS image, you need to be registered to [arista.com](https://www.arista.com/en/support/software-download).  
Once you created an account, please logged in and down the cEOS docker images.  

To add this new image to docker, please use the docker CLI command :
```bash
docker import cEOS-lab-4.30.3M.tar ceos:4.30.3M
```

### Cisco N9Kv

Cisco’s N9Kv is also available for free (again, locked behind an account registration).  
Please, download the qcow2 image and move it to the vrnetlab/n9kv folder :

```bash
➜  n9kv git:(master) pwd
/opt/vrnetlab/n9kv
➜  n9kv git:(master) ls -l
total 1931856
drwxr-xr-x 2 root root       4096  8 oct.  13:44 docker
-rw-r--r-- 1 root root        508  8 oct.  13:44 Makefile
-rwxr--r-- 1 root root 1978204160 14 mai    2022 nxosv.10.2.3.qcow2
-rw-r--r-- 1 root root        585  8 oct.  13:44 README.md
```

Be sure to use the "n9kv" folder and not the "nxos" folder - the "nxos" folder is for the older titanium images. Once the image is copied here, trigger "make" to build the docker image for this

```bash
➜  n9kv git:(master) sudo make                                
for IMAGE in nxosv.10.2.3.qcow2; do \
        echo "Making $IMAGE"; \
        make IMAGE=$IMAGE docker-build; \
done
Making nxosv.10.2.3.qcow2
make[1] : on entre dans le répertoire « /opt/vrnetlab/n9kv »
rm -f docker/*.qcow2* docker/*.tgz* docker/*.vmdk* docker/*.iso
Building docker image using nxosv.10.2.3.qcow2 as vrnetlab/vr-n9kv:10.2.3
cp ../common/* docker/
make IMAGE=$IMAGE docker-build-image-copy
make[2] : on entre dans le répertoire « /opt/vrnetlab/n9kv »
cp nxosv.10.2.3.qcow2* docker/
make[2] : on quitte le répertoire « /opt/vrnetlab/n9kv »
(cd docker; docker build --build-arg http_proxy= --build-arg https_proxy= --build-arg IMAGE=nxosv.10.2.3.qcow2 -t vrnetlab/vr-n9kv:10.2.3 .)
[+] Building 96.9s (10/10) 
FINISHED
docker:default

[...]

 => [internal] load build definition from Dockerfile
make[1] : on quitte le répertoire « /opt/vrnetlab/n9kv »
```

Now you should see images available to use :
```bash
➜  n9kv git:(master) sudo docker images 
REPOSITORY         TAG       IMAGE ID       CREATED         SIZE
vrnetlab/vr-n9kv   9.3.9     75c3c348b49f   48 seconds ago  2.43GB
ceos               4.30.3M   63870e68ff8d   2 hours ago     1.95GB
```

## Sources
- [ContainerLab](https://containerlab.dev/install/)
- [vrnetlab](https://containerlab.dev/manual/vrnetlab/#vrnetlab)
- [BrianLinkLetter](https://www.brianlinkletter.com/2019/03/vrnetlab-emulate-networks-using-kvm-and-docker/)
- [Docker Engine for Debian](https://docs.docker.com/engine/install/debian/)
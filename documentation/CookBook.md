# CookBook

## Prepare data

### Start Diode Server

Create a `.env` for Diode Server.  

```bash
cd diode_server
touch .env
```

Reuse the `sample.env` and adapt the API keys based on Diode plugin.  
To get the values, connect to netbox [How to install Netbox](documentation/INSTALLATION.md#install-netbox-and-plugins), and go `/plugins/diode/settings/`

```bash
export DIODE_API_KEY = diode-ingestion-key
```

### Popule data in Netbox

Generate a Netbox token via webui and execute the python script

```bash
python import.py http://localhost:8080 YOUR_NETBOX_TOKEN device_model.yml subnets.yml
```

This script will create Region, Site, and Device type on netbox.  
We have to modify it and create, manually the interface.

### Ansible

> [!NOTE]
> Secret used for ansible vault : `netlab`
>

To be able to access via SSH to network devices, we have to install `sshpass`
On Ubuntu/Debian :

```bash
sudo apt update
sudo apt install -y sshpass paramiko
```

To configure the SNMP :

```bash
ansible-playbook -i inventory/ansible-inventory.yml configure_snmp.yml
```

## Create Fabric

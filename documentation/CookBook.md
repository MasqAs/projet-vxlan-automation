# CookBook

>[!WARNING]
>
> Work in progress
>

## Prepare data

### Popule data in Netbox

Generate a Netbox token via webui and execute the python script

```bash
python import.py http://localhost:8080 YOUR_NETBOX_TOKEN device_model.yml subnets.yml
```

## Create Fabric

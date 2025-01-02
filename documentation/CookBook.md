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
python utilities/populate_data/populate_data.py "http://localhost:8080/" "<netbox_token>" "utilities/populate_data/subnets.yml"
```

import yaml
import pynetbox
import argparse

# Load YAML data
def load_yaml_data(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Initialize NetBox client
def init_netbox(api_url, token):
    return pynetbox.api(api_url, token=token)

# Main function to ingest data into NetBox
def main(yaml_file_path, api_url, token):
    # Load data from YAML
    data = load_yaml_data(yaml_file_path)
    nb = init_netbox(api_url, token)

    # Ensure the Paris region exists
    region_name = "Paris"
    region = nb.dcim.regions.get(name=region_name)
    if not region:
        region = nb.dcim.regions.create({"name": region_name, "slug": region_name.lower()})
        print(f"Region '{region_name}' created.")
    else:
        print(f"Region '{region_name}' already exists.")

    # Process each site and its prefixes
    for site_name, site_data in data[region_name].items():
        # Check if the site already exists; create if not
        site = nb.dcim.sites.get(name=site_name)
        if not site:
            site = nb.dcim.sites.create({
                "name": site_name,
                "slug": site_name.lower(),
                "region": region.id,
                "status": "active",
            })
            print(f"Site '{site_name}' created.")
        else:
            print(f"Site '{site_name}' already exists.")

        # Create prefix role if not already existing
        role_name = f"{site_name.lower()}_underlay"
        role = nb.ipam.roles.get(name=role_name)
        if not role:
            role = nb.ipam.roles.create({"name": role_name, "slug": role_name.lower()})
            print(f"Prefix role '{role_name}' created.")
        else:
            print(f"Prefix role '{role_name}' already exists.")

        # Add prefixes to NetBox under this role and site
        for prefix in site_data.get("Underlay", []):
            # Check if the prefix already exists; create if not
            existing_prefix = nb.ipam.prefixes.get(prefix=prefix)
            if not existing_prefix:
                nb.ipam.prefixes.create({
                    "prefix": prefix,
                    "site": site.id,
                    "status": "active",
                    "role": role.id,
                    "description": f"Underlay prefix for {site_name} in {region_name}",
                })
                print(f"Prefix '{prefix}' added to site '{site_name}'.")
            else:
                print(f"Prefix '{prefix}' already exists for site '{site_name}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest YAML data into NetBox using PyNetBox.")
    parser.add_argument("yaml_file", help="Path to the YAML file containing data to ingest.")
    parser.add_argument("--api_url", required=True, help="NetBox API URL.")
    parser.add_argument("--token", required=True, help="NetBox API token.")
    args = parser.parse_args()

    main(args.yaml_file, args.api_url, args.token)

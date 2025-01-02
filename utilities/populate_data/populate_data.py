import sys

import pynetbox
import yaml


# Function to load the YAML file
def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


# Main function to populate IPAM
def populate_ipam(netbox_url, netbox_token, yaml_file):
    nb = pynetbox.api(netbox_url, token=netbox_token)
    data = load_yaml(yaml_file)

    for region, sites in data.items():
        # Create or verify the region
        region_obj = nb.dcim.regions.get(name=region)
        if not region_obj:
            region_obj = nb.dcim.regions.create(
                {"name": region, "slug": region.lower()}
            )
            print(f"Region created: {region}")

        for site_name, roles in sites.items():
            # Create or verify the site
            site_obj = nb.dcim.sites.get(name=site_name)
            if not site_obj:
                site_obj = nb.dcim.sites.create(
                    {
                        "name": site_name,
                        "slug": site_name.lower(),
                        "region": region_obj.id,
                    }
                )
                print(f"Site created: {site_name}")

            for role_name, prefixes in roles.items():
                # Verify or create the prefix role (Underlay)
                role_obj = nb.ipam.roles.get(name=role_name)
                if not role_obj:
                    role_obj = nb.ipam.roles.create(
                        {"name": role_name, "slug": role_name.lower()}
                    )

                # First element = main prefix (e.g., 172.16.0.0/16)
                main_prefix = prefixes.pop(0)
                prefix_obj = nb.ipam.prefixes.get(prefix=main_prefix)
                if not prefix_obj:
                    prefix_obj = nb.ipam.prefixes.create(
                        {
                            "prefix": main_prefix,
                            "role": role_obj.id,
                            "site": site_obj.id,
                        }
                    )
                    print(f"Main prefix created: {main_prefix}")

                # Create locations (PA1, PA2, etc.) and sub-prefixes
                for location_data in prefixes:
                    for location, subnets in location_data.items():
                        location_obj = nb.dcim.locations.get(
                            name=location, site_id=site_obj.id
                        )
                        if not location_obj:
                            location_obj = nb.dcim.locations.create(
                                {
                                    "name": location,
                                    "slug": location.lower(),
                                    "site": site_obj.id,
                                }
                            )
                            print(f"Location created: {location}")

                        for subnet in subnets:
                            if not nb.ipam.prefixes.get(prefix=subnet):
                                nb.ipam.prefixes.create(
                                    {
                                        "prefix": subnet,
                                        "role": role_obj.id,
                                        "site": site_obj.id,
                                        "location": location_obj.id,
                                    }
                                )
                                print(f"Sub-prefix created: {subnet} in {location}")


# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <netbox_url> <netbox_token> <yaml_file>")
        sys.exit(1)

    netbox_url = sys.argv[1]
    netbox_token = sys.argv[2]
    yaml_file = sys.argv[3]

    populate_ipam(netbox_url, netbox_token, yaml_file)

import sys

import pynetbox
import yaml


# Load YAML file
def load_yaml(file_path):
    try:
        with open(file_path, "r") as stream:
            return yaml.safe_load(stream)
    except Exception as e:
        sys.exit(f"Error loading YAML file: {e}")


# Populate NetBox using the provided YAML data
def populate_netbox(nb_url, nb_token, yaml_data):
    nb = pynetbox.api(nb_url, token=nb_token)

    try:
        # Create Region
        if not nb.dcim.regions.filter(name="Europe"):
            region = nb.dcim.regions.create({"name": "Europe", "slug": "europe"})
        else:
            region = nb.dcim.regions.get(name="Europe")
        print(f"Region created or already exists: {region.name}")

        # Create Site
        if not nb.dcim.sites.filter(name="Paris"):
            site = nb.dcim.sites.create(
                {"name": "Paris", "slug": "paris", "region": region.id}
            )
        else:
            site = nb.dcim.sites.get(name="Paris")
        print(f"Site created or already exists: {site.name}")

        # Check and create the "Underlay" role if it doesn't exist
        underlay_role = nb.ipam.roles.get(name="Underlay")
        if not underlay_role:
            underlay_role = nb.ipam.roles.create(
                {
                    "name": "Underlay",
                    "slug": "underlay",
                    "description": "Underlay for VXLAN fabric",
                }
            )
            print("Role 'Underlay' created")
        underlay_role_id = underlay_role.id

        # Iterate over Buildings (Tenants and Locations)
        for building, data in (
            yaml_data.get("Europe", {}).get("Paris", {}).get("Underlay", {}).items()
        ):
            tenant_name = building[:-3]  # Remove "_00" suffix
            location_name = building

            # Create Tenant
            if not nb.tenancy.tenants.filter(name=tenant_name):
                tenant = nb.tenancy.tenants.create(
                    {"name": tenant_name, "slug": tenant_name.lower()}
                )
            else:
                tenant = nb.tenancy.tenants.get(name=tenant_name)
            print(f"Tenant created or already exists: {tenant.name}")

            # Create Location
            if not nb.dcim.locations.filter(name=location_name):
                location = nb.dcim.locations.create(
                    {
                        "name": location_name,
                        "slug": location_name.lower(),
                        "site": site.id,
                        "tenant": tenant.id,
                    }
                )
            else:
                location = nb.dcim.locations.get(name=location_name)
            print(f"Location created or already exists: {location.name}")

            # Create Prefixes for the Location
            for subnet_info in data:
                subnet = subnet_info.get("Subnet")
                if not nb.ipam.prefixes.filter(prefix=subnet):
                    prefix = nb.ipam.prefixes.create(
                        {
                            "prefix": subnet,
                            "site": site.id,
                            "tenant": tenant.id,
                            "role": underlay_role_id,  # Use the numeric ID of the role
                            "description": f"Underlay: {location_name}",
                        }
                    )
                    print(f"Prefix created: {prefix.prefix}")
                else:
                    print(f"Prefix already exists: {subnet}")

    except Exception as e:
        sys.exit(f"Error configuring NetBox: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python script.py <netbox_url> <netbox_token> <yaml_file>")

    netbox_url = sys.argv[1]
    netbox_token = sys.argv[2]
    yaml_file = sys.argv[3]

    # Load the YAML data
    yaml_data = load_yaml(yaml_file)

    # Populate NetBox with the YAML data
    populate_netbox(netbox_url, netbox_token, yaml_data)

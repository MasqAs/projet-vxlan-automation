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
    # Connect to NetBox
    nb = pynetbox.api(nb_url, token=nb_token)

    try:
        # Create or retrieve the "Europe" region
        regions = nb.dcim.regions.filter(name="Europe")
        region = next(iter(regions), None)
        if not region:
            region = nb.dcim.regions.create({"name": "Europe", "slug": "europe"})
            print(f"Region created: {region.name}")
        else:
            print(f"Region already exists: {region.name}")

        # Create or retrieve the "Paris" site
        sites = nb.dcim.sites.filter(name="Paris")
        site = next(iter(sites), None)
        if not site:
            site = nb.dcim.sites.create(
                {"name": "Paris", "slug": "paris", "region": region.id}
            )
            print(f"Site created: {site.name}")
        else:
            print(f"Site already exists: {site.name}")

        # Check and create the "Underlay" IP role if it doesn't exist
        roles = nb.ipam.roles.filter(name="Underlay")
        underlay_role = next(iter(roles), None)
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

        # Handle "Underlay" data in the YAML
        underlay_data = yaml_data.get("Europe", {}).get("Paris", {}).get("Underlay", {})
        for building, subnets in underlay_data.items():
            tenant_name = building[:-3]  # Remove "_00" suffix
            location_name = building

            # Create or retrieve the Tenant
            tenants = nb.tenancy.tenants.filter(name=tenant_name)
            tenant = next(iter(tenants), None)
            if not tenant:
                tenant = nb.tenancy.tenants.create(
                    {"name": tenant_name, "slug": tenant_name.lower()}
                )
                print(f"Tenant created: {tenant.name}")
            else:
                print(f"Tenant already exists: {tenant.name}")

            # Create or retrieve the Location
            locations = nb.dcim.locations.filter(name=location_name)
            location = next(iter(locations), None)
            if not location:
                location = nb.dcim.locations.create(
                    {
                        "name": location_name,
                        "slug": location_name.lower(),
                        "site": site.id,
                        "tenant": tenant.id,
                    }
                )
                print(f"Location created: {location.name}")
            else:
                print(f"Location already exists: {location.name}")

            # Create Prefixes for the current Location
            for subnet_info in subnets:
                subnet = subnet_info.get("Subnet")
                prefixes = nb.ipam.prefixes.filter(prefix=subnet)
                prefix = next(iter(prefixes), None)
                if not prefix:
                    prefix = nb.ipam.prefixes.create(
                        {
                            "prefix": subnet,
                            "site": site.id,
                            "tenant": tenant.id,
                            "role": underlay_role_id,
                            "description": f"Underlay: {location_name}",
                        }
                    )
                    print(f"Prefix created: {prefix.prefix}")
                else:
                    print(f"Prefix already exists: {subnet}")

        # Handle "DC" subnets in the YAML
        dc_subnets = yaml_data.get("Europe", {}).get("Paris", {}).get("DC", [])
        # Create or retrieve the "DC" tenant
        tenants = nb.tenancy.tenants.filter(name="DC")
        dc_tenant = next(iter(tenants), None)
        if not dc_tenant:
            dc_tenant = nb.tenancy.tenants.create({"name": "DC", "slug": "dc"})
            print(f"Tenant created: {dc_tenant.name}")
        else:
            print(f"Tenant already exists: {dc_tenant.name}")

        # Create or retrieve the "DC" location
        locations = nb.dcim.locations.filter(name="DC")
        dc_location = next(iter(locations), None)
        if not dc_location:
            dc_location = nb.dcim.locations.create(
                {
                    "name": "DC",
                    "slug": "dc",
                    "site": site.id,
                    "tenant": dc_tenant.id,
                }
            )
            print(f"Location created: {dc_location.name}")
        else:
            print(f"Location already exists: {dc_location.name}")

        # Associate the existing prefixes in "DC" with the "DC" tenant and location
        for dc_subnet_info in dc_subnets:
            subnet = dc_subnet_info.get("Subnet")
            if subnet:
                # Retrieve the existing prefix
                prefixes = nb.ipam.prefixes.filter(prefix=subnet)
                prefix = next(iter(prefixes), None)
                if prefix:
                    # Update the prefix to associate it with the "DC" tenant and location
                    prefix.update(
                        {
                            "tenant": dc_tenant.id,
                            "site": site.id,
                            "role": underlay_role_id,
                            "description": "DC-specific subnet",
                        }
                    )
                    print(f"Prefix updated for DC: {prefix.prefix}")
                else:
                    print(f"Warning: Prefix {subnet} not found in NetBox, skipping.")
            else:
                print("Warning: Invalid subnet entry in DC section, skipping.")

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

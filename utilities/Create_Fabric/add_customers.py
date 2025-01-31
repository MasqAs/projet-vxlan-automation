from helpers.netbox_backend import NetBoxBackend
import sys

# Ask user for NetBox connection details
url = input("Enter NetBox URL: ")
token = input("Enter NetBox API Token: ")
nb_backend = NetBoxBackend(url, token)

# Ask for customer details
customer_name = input("Enter Customer Name: ")
vlan_id = int(input("Enter VLAN ID: "))
vni_id = int(input("Enter VNI ID: "))

# Get available locations
locations = list(nb_backend.nb.dcim.locations.all())
for idx, loc in enumerate(locations):
    print(f"{idx}: {loc.name}")
selected_indices = input("Select one or multiple locations by index (comma-separated): ")
selected_locations = [loc for i, loc in enumerate(locations) if str(i) in selected_indices.split(",")]

# Create tenant
tenant = nb_backend.create_tenant(customer_name, customer_name.lower().replace(" ", "-"))

# Update locations to attach them to the tenant
for location in selected_locations:
    try:
        location.tenant = tenant.id
        location.save()
    except Exception as e:
        print(f"[ERROR] Failed to update location {location.name} with tenant: {e}")

# Allocate /24 prefix for customer
role_id = nb_backend.nb.ipam.roles.get(slug="customerscontainer").id
parent_prefixes = list(nb_backend.nb.ipam.prefixes.filter(role_id=role_id))
if not parent_prefixes:
    print("[ERROR] No available parent prefix found.")
    sys.exit(1)

customer_prefix = nb_backend.allocate_prefix(parent_prefixes[0], 24, None, None)
if not customer_prefix:
    print("[ERROR] Could not allocate /24 for customer.")
    sys.exit(1)

# Create L2VPN
l2vpn_slug = f"{customer_name.lower().replace(' ', '-')}-vpn"
l2vpn = nb_backend.create_l2vpn(vni_id, f"{customer_name}_vpn", l2vpn_slug, tenant.id)

# Create VLAN
vlan_slug = f"{customer_name.lower().replace(' ', '-')}-vlan"
vlan = nb_backend.create_vlan(vlan_id, f"{customer_name}_vlan", vlan_slug, tenant.id, location.id)

# Create VXLAN termination
vxlan_termination = nb_backend.create_vxlan_termination(l2vpn.id, "ipam.vlan", vlan.id)

# Assign IP to leaf devices Ethernet3
for location in selected_locations:
    leaf_devices = nb_backend.nb.dcim.devices.filter(role="leaf", location_id=location.id)
    if leaf_devices:
        ip_list = nb_backend.get_available_ips_in_prefix(customer_prefix)
        if len(ip_list) < len(leaf_devices):
            print("[ERROR] Not enough IP addresses available in the allocated /24.")
            sys.exit(1)
        
        for device, ip in zip(leaf_devices, ip_list):
            interface = nb_backend.get_or_create_interface(device.id, "Ethernet3")
            nb_backend.assign_ip_to_interface(interface, ip.address)
    else:
        print(f"[ERROR] No leaf devices found in location {location.name}.")

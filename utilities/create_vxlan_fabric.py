#!/usr/bin/env python3
"""
create_vxlan_fabric.py

Demonstration script that:
1. Connects to NetBox
2. Creates/Selects a Site
3. Creates DC devices: 2 Spines
4. Creates 1 Leaf + 1 Access Switch per Building (1–5)
5. Cables them
6. Allocates /31 IPs from an 'UnderlayContainer' prefix
7. Creates BGP ASNs and Sessions using netbox_bgp plugin

IMPORTANT:
- This example is specific to the 'synackray/netbox_bgp' plugin.
- Adjust fields and references as needed for your environment.
- Now using device_role by ID (not slug).
"""

import getpass
import sys

import pynetbox


def main():
    print("=== VXLAN Fabric Creation Script ===")

    # 1. Gather NetBox details
    netbox_url = input("NetBox URL (e.g., https://netbox.local): ").strip()
    if not netbox_url:
        print("ERROR: NetBox URL is required.")
        sys.exit(1)

    netbox_token = getpass.getpass("NetBox API Token: ")
    if not netbox_token:
        print("ERROR: NetBox API token is required.")
        sys.exit(1)

    # Initialize pynetbox connection
    try:
        nb = pynetbox.api(netbox_url, token=netbox_token)
        # If using self-signed certs or an SSL intercept:
        # nb.http_session.verify = False
    except Exception as e:
        print(f"ERROR: Failed to connect to NetBox: {e}")
        sys.exit(1)

    # 2. Choose or create Site
    existing_sites_list = list(nb.dcim.sites.all())
    if not existing_sites_list:
        print("No sites found in NetBox.")
        sys.exit(1)

    print("\nExisting Sites:")
    for idx, s in enumerate(existing_sites_list, start=1):
        print(f"  {idx}. {s.name} (slug: {s.slug})")

    choice = (
        input("Choose a site by number, or type 'new' to create a new one: ")
        .strip()
        .lower()
    )

    if choice == "new":
        site_name = input("New site name (e.g., 'Paris'): ").strip()
        site_code_input = input("New site code (e.g., 'PA'): ").strip()
        if not site_name or not site_code_input:
            print("ERROR: Site name and code required.")
            sys.exit(1)

        # Create new site
        try:
            site = nb.dcim.sites.create(name=site_name, slug=site_code_input.lower())
            print(f"Created new site: {site.name} ({site.slug})")
        except Exception as e:
            print(f"ERROR: Failed to create site: {e}")
            sys.exit(1)

        # Derive a 2-letter site_code from the new site's name
        site_name_clean = site.name.strip()
        if len(site_name_clean) >= 2:
            site_code = site_name_clean[:2].upper()
        else:
            site_code = site_name_clean.upper()

    else:
        try:
            site_index = int(choice)
            site = existing_sites_list[site_index - 1]
            # Derive site_code from first 2 letters of site.name
            site_name_clean = site.name.strip()
            if len(site_name_clean) >= 2:
                site_code = site_name_clean[:2].upper()
            else:
                site_code = site_name_clean.upper()
        except ValueError:
            print("ERROR: Please enter a valid number or 'new'.")
            sys.exit(1)
        except IndexError:
            print("ERROR: The site number you entered does not exist.")
            sys.exit(1)

    # 3. Number of buildings
    while True:
        try:
            num_buildings = int(input("How many buildings? (1–5): ").strip())
            if 1 <= num_buildings <= 5:
                break
            else:
                print("ERROR: Please enter a number between 1 and 5.")
        except ValueError:
            print("ERROR: Invalid input.")

    # 4. Device type selections
    print("\nEnter device type slugs/names for each category.")
    spine_device_type = input("Device Type for Spine: ").strip()
    leaf_device_type = input("Device Type for Leaf: ").strip()
    access_device_type = input("Device Type for Access Switch: ").strip()

    # 5. Fetch device roles by slug, store their IDs
    spine_role = nb.dcim.device_roles.get(slug="spine")
    if not spine_role:
        print("ERROR: No device role found with slug='spine'.")
        sys.exit(1)

    leaf_role = nb.dcim.device_roles.get(slug="leaf")
    if not leaf_role:
        print("ERROR: No device role found with slug='leaf'.")
        sys.exit(1)

    access_role = nb.dcim.device_roles.get(slug="access")
    if not access_role:
        print("ERROR: No device role found with slug='access'.")
        sys.exit(1)

    print(
        f"Using Device Role IDs: Spine={spine_role.id}, Leaf={leaf_role.id}, Access={access_role.id}"
    )

    # 6. Create Spines in the DC
    spine_names = [f"{site_code.lower()}dc_sp1_00", f"{site_code.lower()}dc_sp2_00"]
    spines = []
    for name in spine_names:
        existing_spine = nb.dcim.devices.get(name=name)
        if existing_spine:
            print(f"Spine '{name}' already exists; reusing.")
            spines.append(existing_spine)
            continue

        try:
            new_spine = nb.dcim.devices.create(
                name=name,
                device_type={"slug": spine_device_type},
                role=spine_role.id,
                site=site.id,
            )
            print(f"Created Spine: {new_spine.name}")
            spines.append(new_spine)
        except Exception as e:
            print(f"ERROR creating spine '{name}': {e}")
            sys.exit(1)

    # 7. Create Leaves and Access Switches per Building
    leaves = []
    access_switches = []

    for b_num in range(1, num_buildings + 1):
        building_code = f"{site_code}{b_num}"  # e.g. "PA1"

        # Create or retrieve the Location
        location = nb.dcim.locations.get(site_id=site.id, name=building_code)
        if location:
            print(f"Location '{location.name}' already exists; reusing.")
        else:
            try:
                location = nb.dcim.locations.create(
                    name=building_code, slug=building_code.lower(), site=site.id
                )
                print(f"Created Location '{location.name}'")
            except Exception as e:
                print(f"ERROR creating location '{building_code}': {e}")
                sys.exit(1)

        # Leaf device
        leaf_name = f"{site_code.lower()}{str(b_num).zfill(2)}_lf1_00"
        existing_leaf = nb.dcim.devices.get(name=leaf_name)
        if existing_leaf:
            print(f"Leaf '{leaf_name}' already exists; reusing.")
            leaf = existing_leaf
        else:
            try:
                leaf = nb.dcim.devices.create(
                    name=leaf_name,
                    device_type={"slug": leaf_device_type},
                    role=leaf_role.id,  # <--- Use Leaf role ID
                    site=site.id,
                    location=location.id,
                )
                print(f"Created Leaf: {leaf.name}")
            except Exception as e:
                print(f"ERROR creating leaf '{leaf_name}': {e}")
                sys.exit(1)

        leaves.append(leaf)

        # Access Switch device
        sw_name = f"{site_code.lower()}{str(b_num).zfill(2)}_sw1_00"
        existing_sw = nb.dcim.devices.get(name=sw_name)
        if existing_sw:
            print(f"Access Switch '{sw_name}' already exists; reusing.")
            access_sw = existing_sw
        else:
            try:
                access_sw = nb.dcim.devices.create(
                    name=sw_name,
                    device_type={"slug": access_device_type},
                    role=access_role.id,  # <--- Use Access Switch role ID
                    site=site.id,
                    location=location.id,
                )
                print(f"Created Access Switch: {access_sw.name}")
            except Exception as e:
                print(f"ERROR creating access switch '{sw_name}': {e}")
                sys.exit(1)

        access_switches.append(access_sw)

    # 8. Cabling
    def get_or_create_interface(device, name):
        intf = nb.dcim.interfaces.get(device_id=device.id, name=name)
        if not intf:
            # Adjust 'type' if needed (e.g., 10gbase-x-sfpp, 100gbase-xx, etc.)
            intf = nb.dcim.interfaces.create(
                device=device.id, name=name, type="40gbase-x-qsfpp"
            )
        return intf

    def create_cable_if_not_exists(intf_a, intf_b):
        # Check for existing cable
        cables = nb.dcim.cables.filter(
            termination_a_type="dcim.interface",
            termination_a_id=intf_a.id,
            termination_b_type="dcim.interface",
            termination_b_id=intf_b.id,
        )
        if cables:
            print(
                f"Cable exists: {intf_a.device.name}:{intf_a.name} -- {intf_b.device.name}:{intf_b.name}"
            )
            return

        try:
            nb.dcim.cables.create(
                termination_a_type="dcim.interface",
                termination_a_id=intf_a.id,
                termination_b_type="dcim.interface",
                termination_b_id=intf_b.id,
                status="connected",
            )
            print(
                f"Created cable: {intf_a.device.name}:{intf_a.name} <--> {intf_b.device.name}:{intf_b.name}"
            )
        except Exception as e:
            print(f"ERROR creating cable: {e}")

    # Spine1 <-> Leaf.Eth1, Spine2 <-> Leaf.Eth2, Leaf.Eth3 <-> Access Switch
    for i, leaf in enumerate(leaves, start=1):
        leaf_eth1 = get_or_create_interface(leaf, "Ethernet1")
        leaf_eth2 = get_or_create_interface(leaf, "Ethernet2")
        leaf_eth3 = get_or_create_interface(leaf, "Ethernet3")

        sp1_if = get_or_create_interface(spines[0], f"Ethernet{i}")
        sp2_if = get_or_create_interface(spines[1], f"Ethernet{i}")

        create_cable_if_not_exists(leaf_eth1, sp1_if)
        create_cable_if_not_exists(leaf_eth2, sp2_if)

        # Leaf.Eth3 -> Access Switch.Ethernet1
        access_sw = access_switches[i - 1]
        acc_if = get_or_create_interface(access_sw, "Ethernet1")
        create_cable_if_not_exists(leaf_eth3, acc_if)

    # 9. /31 IP Assignment & BGP
    # Fetch Underlay prefix by role
    underlay_role = nb.ipam.roles.get(slug="underlaycontainer")
    if not underlay_role:
        print("ERROR: No role 'underlaycontainer' found.")
        sys.exit(1)

    underlay_prefixes = nb.ipam.prefixes.filter(
        role_id=underlay_role.id, site_id=site.id
    )
    if not underlay_prefixes:
        print("ERROR: No underlay prefix found for this site.")
        sys.exit(1)

    # Pick the first underlay prefix
    underlay_prefix = underlay_prefixes[0]

    def get_next_available_31(parent_prefix):
        # We list available prefixes, then find the first /31
        available_children = parent_prefix.available_prefixes.list()
        for child in available_children:
            if child.prefix.endswith("/31"):
                return child.prefix
        return None

    # BGP AS Ranges
    next_spine_asn = 65001
    next_leaf_asn = 65101

    # Create/fetch BGP AutonomousSystem objects for each spine/leaf
    spine_as_map = {}
    for spine_dev in spines:
        as_obj = create_or_get_bgp_as(nb, next_spine_asn, spine_dev.name)
        spine_as_map[spine_dev.id] = as_obj
        next_spine_asn += 1

    leaf_as_map = {}
    for leaf_dev in leaves:
        as_obj = create_or_get_bgp_as(nb, next_leaf_asn, leaf_dev.name)
        leaf_as_map[leaf_dev.id] = as_obj
        next_leaf_asn += 1

    # For each leaf, create /31 for connections to each spine, then create BGP sessions
    for i, leaf_dev in enumerate(leaves, start=1):
        leaf_eth1 = nb.dcim.interfaces.get(device_id=leaf_dev.id, name="Ethernet1")
        sp1_if = nb.dcim.interfaces.get(device_id=spines[0].id, name=f"Ethernet{i}")

        # 1) Spine1 <-> Leaf
        prefix_str = get_next_available_31(underlay_prefix)
        if not prefix_str:
            print("ERROR: No available /31 for the Spine1 <-> Leaf link.")
            sys.exit(1)

        new_31_prefix = nb.ipam.prefixes.create(
            {
                "prefix": prefix_str,
                "site": site.id,
                "role": underlay_role.id,
            }
        )

        ip_list = list(new_31_prefix.available_ips.list())  # Should be 2 IPs in a /31
        if len(ip_list) < 2:
            print("ERROR: Not enough IPs in the /31 prefix.")
            sys.exit(1)

        spine_ip_1 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[0],
                "assigned_object_id": sp1_if.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )
        leaf_ip_1 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[1],
                "assigned_object_id": leaf_eth1.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )

        # Create BGP sessions (Spine1 <-> Leaf)
        create_bgp_session(
            nb,
            device=spines[0],
            local_as=spine_as_map[spines[0].id],
            remote_as=leaf_as_map[leaf_dev.id],
            local_address=ip_list[0].split("/")[0],
            remote_address=ip_list[1].split("/")[0],
        )
        create_bgp_session(
            nb,
            device=leaf_dev,
            local_as=leaf_as_map[leaf_dev.id],
            remote_as=spine_as_map[spines[0].id],
            local_address=ip_list[1].split("/")[0],
            remote_address=ip_list[0].split("/")[0],
        )

        # 2) Spine2 <-> Leaf (Ethernet2)
        leaf_eth2 = nb.dcim.interfaces.get(device_id=leaf_dev.id, name="Ethernet2")
        sp2_if = nb.dcim.interfaces.get(device_id=spines[1].id, name=f"Ethernet{i}")

        prefix_str = get_next_available_31(underlay_prefix)
        if not prefix_str:
            print("ERROR: No available /31 for the Spine2 <-> Leaf link.")
            sys.exit(1)

        new_31_prefix = nb.ipam.prefixes.create(
            {
                "prefix": prefix_str,
                "site": site.id,
                "role": underlay_role.id,
            }
        )

        ip_list = list(new_31_prefix.available_ips.list())
        spine_ip_2 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[0],
                "assigned_object_id": sp2_if.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )
        leaf_ip_2 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[1],
                "assigned_object_id": leaf_eth2.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )

        # Create BGP sessions (Spine2 <-> Leaf)
        create_bgp_session(
            nb,
            device=spines[1],
            local_as=spine_as_map[spines[1].id],
            remote_as=leaf_as_map[leaf_dev.id],
            local_address=ip_list[0].split("/")[0],
            remote_address=ip_list[1].split("/")[0],
        )
        create_bgp_session(
            nb,
            device=leaf_dev,
            local_as=leaf_as_map[leaf_dev.id],
            remote_as=spine_as_map[spines[1].id],
            local_address=ip_list[1].split("/")[0],
            remote_address=ip_list[0].split("/")[0],
        )

    print("\n=== Fabric Creation Completed ===")
    print(f"Site: {site.name} (slug: {site.slug})")
    print(f"Spines: {[s.name for s in spines]}")
    print(f"Leaves: {[l.name for l in leaves]}")
    print(f"Access Switches: {[sw.name for sw in access_switches]}")
    print("Please review the configuration in NetBox.")


def create_or_get_bgp_as(nb, asn, description=""):
    """
    Using the netbox_bgp plugin's AutonomousSystem model.
    We'll try to fetch an existing AS by 'asn' or create a new one.
    """
    as_obj = nb.plugins.netbox_bgp.autonomous_systems.filter(asn=asn)
    if as_obj:
        return as_obj[0]

    try:
        new_as = nb.plugins.netbox_bgp.autonomous_systems.create(
            asn=asn,
            description=description,
            status="active",  # You may use another status if desired
        )
        print(f"Created AutonomousSystem: {asn} ({description})")
        return new_as
    except Exception as e:
        print(f"ERROR creating/fetching ASN {asn}: {e}")
        sys.exit(1)


def create_bgp_session(nb, device, local_as, remote_as, local_address, remote_address):
    """
    Creates a BGPSession in the netbox_bgp plugin.
    Typically fields: device, local_as, remote_as, local_address, remote_address, ...
    """
    # Check if a session might already exist (very naive approach).
    existing = nb.plugins.netbox_bgp.bgp_sessions.filter(
        device_id=device.id,
        local_address=local_address,
        remote_address=remote_address,
        local_as_id=local_as.id,
        remote_as_id=remote_as.id,
    )
    if existing:
        print(
            f"[BGP] Session already exists on '{device.name}' local={local_address}, remote={remote_address}"
        )
        return

    try:
        sess = nb.plugins.netbox_bgp.bgp_sessions.create(
            device=device.id,
            local_as=local_as.id,
            remote_as=remote_as.id,
            local_address=local_address,
            remote_address=remote_address,
            status="active",  # or "enabled" field if you prefer
            enabled=True,
        )
        print(
            f"[BGP] Created session on '{device.name}': {local_as.asn} ({local_address}) <-> {remote_as.asn} ({remote_address})"
        )
    except Exception as e:
        print(f"ERROR creating BGP session for '{device.name}': {e}")


if __name__ == "__main__":
    main()

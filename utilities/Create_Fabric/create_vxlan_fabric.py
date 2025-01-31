#!/usr/bin/env python3
"""
create_vxlan_fabric.py (version avec NetBoxBackend)

Ce script illustre comment créer une fabric VXLAN sur NetBox,
notamment :
 - Création ou sélection d'un site.
 - Création de spines, leaves, et access.
 - Création du câblage.
 - Allocation automatique des /31 pour les liaisons.
 - Attribution d'un /32 loopback par device.
 - Attribution automatique d'ASN (Custom Field "ASN").

Il utilise une classe d'abstraction "NetBoxBackend" (dans NetBox_backend.py)
pour simplifier et clarifier les interactions avec l'API.
"""

import getpass
import sys

from helpers.netbox_backend import NetBoxBackend


def main():
    print("=== VXLAN Fabric Creation Script (via NetBoxBackend) ===")

    # 1) NetBox details
    netbox_url = input("NetBox URL (e.g. https://netbox.local): ").strip()
    if not netbox_url:
        print("ERROR: NetBox URL is required.")
        sys.exit(1)

    netbox_token = getpass.getpass("NetBox API Token: ")
    if not netbox_token:
        print("ERROR: NetBox API token is required.")
        sys.exit(1)

    # 2) Init the NetBox backend wrapper
    try:
        nb = NetBoxBackend(netbox_url, netbox_token, verify_ssl=True)
    except Exception as exc:
        print(f"ERROR: Failed to connect to NetBox: {exc}")
        sys.exit(1)

    # 3) Choose or create Site
    existing_sites = nb.get_sites()
    if not existing_sites:
        print("No sites found in NetBox.")
        sys.exit(1)

    print("\nExisting Sites:")
    for idx, s in enumerate(existing_sites, start=1):
        print(f"  {idx}. {s.name} (slug={s.slug})")

    choice = input("Choose a site by number, or type 'new' to create one: ").strip().lower()
    if choice == "new":
        site_name = input("New site name (e.g. 'Paris'): ").strip()
        site_code_input = input("New site code (e.g. 'PA'): ").strip()
        if not site_name or not site_code_input:
            print("ERROR: Site name and code required.")
            sys.exit(1)
        try:
            site = nb.create_site(site_name, site_code_input.lower())
            print(f"Created new site: {site.name} ({site.slug})")
        except Exception as exc:
            print(f"ERROR: Failed to create site: {exc}")
            sys.exit(1)

        site_clean = site.name.strip()
        site_code = site_clean[:2].upper() if len(site_clean) >= 2 else site_clean.upper()
    else:
        try:
            site_index = int(choice)
            site = existing_sites[site_index - 1]
            site_clean = site.name.strip()
            site_code = site_clean[:2].upper() if len(site_clean) >= 2 else site_clean.upper()
        except (ValueError, IndexError):
            print("ERROR: Invalid site selection.")
            sys.exit(1)

    # 4) Number of buildings
    while True:
        try:
            num_buildings = int(input("How many buildings? (1–5): ").strip())
            if 1 <= num_buildings <= 5:
                break
            else:
                print("ERROR: Please choose between 1 and 5.")
        except ValueError:
            print("ERROR: Invalid input. Try again.")

    # 5) Device type slugs
    print("\nEnter device type slugs (must exist in NetBox).")
    spine_devtype_slug = input("Spine Device Type Slug: ").strip()
    leaf_devtype_slug = input("Leaf Device Type Slug:  ").strip()
    access_devtype_slug = input("Access Switch Device Type Slug: ").strip()

    # 6) Roles
    spine_role = nb.get_device_role("spine")
    if not spine_role:
        print("ERROR: No device role with slug='spine'.")
        sys.exit(1)

    leaf_role = nb.get_device_role("leaf")
    if not leaf_role:
        print("ERROR: No device role with slug='leaf'.")
        sys.exit(1)

    access_role = nb.get_device_role("access")
    if not access_role:
        print("ERROR: No device role with slug='access'.")
        sys.exit(1)

    print(f"Using roles -> Spine={spine_role.id}, Leaf={leaf_role.id}, Access={access_role.id}")

    # 7) Create / Retrieve 2 Spines
    spine_names = [f"{site_code.lower()}dc_sp1_00", f"{site_code.lower()}dc_sp2_00"]
    spines = []

    for name in spine_names:
        try:
            new_spine = nb.create_device(
                name=name,
                device_type_slug=spine_devtype_slug,
                role_id=spine_role.id,
                site_id=site.id
            )
            print(f"Spine: {new_spine.name}")
            spines.append(new_spine)
        except Exception as exc:
            print(f"ERROR creating spine '{name}': {exc}")
            sys.exit(1)

    # 8) Create Leaves + Access per building
    leaves = []
    access_switches = []

    # Helper to create/find location
    def get_or_create_location(site_obj, location_name: str):
        existing_loc = nb.nb.dcim.locations.get(site_id=site_obj.id, name=location_name)
        if existing_loc:
            print(f"Location '{existing_loc.name}' already exists; reusing.")
            return existing_loc
        try:
            loc = nb.nb.dcim.locations.create(
                name=location_name,
                slug=location_name.lower(),
                site=site_obj.id
            )
            print(f"Created Location '{loc.name}'")
            return loc
        except Exception as loc_exc:
            print(f"ERROR creating location '{location_name}': {loc_exc}")
            sys.exit(1)

    for b_num in range(1, num_buildings + 1):
        building_code = f"{site_code}{b_num}"
        location = get_or_create_location(site, building_code)

        # Leaf device
        leaf_name = f"{site_code.lower()}{str(b_num).zfill(2)}_lf1_00"
        try:
            leaf_dev = nb.create_device(
                name=leaf_name,
                device_type_slug=leaf_devtype_slug,
                role_id=leaf_role.id,
                site_id=site.id,
                location_id=location.id
            )
            print(f"Leaf: {leaf_dev.name}")
        except Exception as exc:
            print(f"ERROR creating leaf '{leaf_name}': {exc}")
            sys.exit(1)
        leaves.append(leaf_dev)

        # Access Switch
        sw_name = f"{site_code.lower()}{str(b_num).zfill(2)}_sw1_00"
        try:
            acc_dev = nb.create_device(
                name=sw_name,
                device_type_slug=access_devtype_slug,
                role_id=access_role.id,
                site_id=site.id,
                location_id=location.id
            )
            print(f"Access Switch: {acc_dev.name}")
        except Exception as exc:
            print(f"ERROR creating access switch '{sw_name}': {exc}")
            sys.exit(1)
        access_switches.append(acc_dev)

    # 9) Cabling
    def create_leaf_spine_cables(leaf_dev, spine_dev, leaf_if_name, spine_if_name):
        leaf_if = nb.get_or_create_interface(leaf_dev.id, leaf_if_name)
        spine_if = nb.get_or_create_interface(spine_dev.id, spine_if_name)
        nb.create_cable_if_not_exists(leaf_if, spine_if)

    for i, leaf_dev in enumerate(leaves, start=1):
        # Leaf <-> Spine1 sur Ethernet1
        create_leaf_spine_cables(leaf_dev, spines[0], "Ethernet1", f"Ethernet{i}")
        # Leaf <-> Spine2 sur Ethernet2
        create_leaf_spine_cables(leaf_dev, spines[1], "Ethernet2", f"Ethernet{i}")

        # Leaf <-> Access Switch sur Ethernet3 (leaf) / Ethernet1 (access)
        leaf_eth3 = nb.get_or_create_interface(leaf_dev.id, "Ethernet3")
        acc_dev = access_switches[i - 1]
        acc_if = nb.get_or_create_interface(acc_dev.id, "Ethernet1")
        nb.create_cable_if_not_exists(leaf_eth3, acc_if)

    # 10) IP Assignments (/31) + ASN custom field
    # 10a) Récupérer le prefix underlay
    underlay_role = nb.nb.ipam.roles.get(slug="underlaycontainer")
    if not underlay_role:
        print("ERROR: No IPAM role 'underlaycontainer' found.")
        sys.exit(1)

    underlay_pfxs = nb.nb.ipam.prefixes.filter(role_id=underlay_role.id, scope_id=site.id)
    underlay_list = list(underlay_pfxs)
    if not underlay_list:
        print("ERROR: No underlay prefix found for this site.")
        sys.exit(1)

    parent_prefix = underlay_list[0]
    print(f"Using parent prefix '{parent_prefix.prefix}' for /31 allocations.")

    # 10b) Assign ASNs (spines 65001, leaves 65101)
    next_spine_asn = 65001
    next_leaf_asn = 65101

    # Spines
    for spine_dev in spines:
        dev_obj = nb.nb.dcim.devices.get(spine_dev.id)
        if not dev_obj:
            print(f"ERROR: Could not re-fetch spine '{spine_dev.name}'")
            sys.exit(1)
        if "ASN" not in dev_obj.custom_fields:
            print(f"[WARNING] Spine '{dev_obj.name}' has no custom field 'ASN'.")
        else:
            dev_obj.custom_fields["ASN"] = next_spine_asn
            try:
                dev_obj.save()
                print(f"Assigned ASN={next_spine_asn} to spine '{dev_obj.name}'.")
            except Exception as exc:
                print(f"ERROR saving 'ASN' on {dev_obj.name}: {exc}")
            next_spine_asn += 1

    # Leaves
    for leaf_dev in leaves:
        dev_obj = nb.nb.dcim.devices.get(leaf_dev.id)
        if not dev_obj:
            print(f"ERROR: Could not re-fetch leaf '{leaf_dev.name}'")
            sys.exit(1)
        if "ASN" not in dev_obj.custom_fields:
            print(f"[WARNING] Leaf '{dev_obj.name}' has no custom field 'ASN'.")
        else:
            dev_obj.custom_fields["ASN"] = next_leaf_asn
            try:
                dev_obj.save()
                print(f"Assigned ASN={next_leaf_asn} to leaf '{dev_obj.name}'.")
            except Exception as exc:
                print(f"ERROR saving 'ASN' on {dev_obj.name}: {exc}")
            next_leaf_asn += 1

    # 10c) Allouer /31 pour chaque liaison Spine<->Leaf
    for i, leaf_dev in enumerate(leaves, start=1):
        # Leaf.Eth1 <-> Spine1.Eth{i}
        leaf_eth1 = nb.nb.dcim.interfaces.get(device_id=leaf_dev.id, name="Ethernet1")
        sp1_if = nb.nb.dcim.interfaces.get(device_id=spines[0].id, name=f"Ethernet{i}")

        child_31 = nb.allocate_prefix(parent_prefix, 31, site.id, underlay_role.id)
        if not child_31:
            print("ERROR: Could not allocate /31 for Spine1<->Leaf.")
            sys.exit(1)
        ip_list = nb.get_available_ips_in_prefix(child_31)
        if len(ip_list) < 2:
            print("ERROR: Not enough IP addresses in newly allocated /31.")
            sys.exit(1)

        nb.assign_ip_to_interface(sp1_if, ip_list[0].address)
        nb.assign_ip_to_interface(leaf_eth1, ip_list[1].address)

        # Leaf.Eth2 <-> Spine2.Eth{i}
        leaf_eth2 = nb.nb.dcim.interfaces.get(device_id=leaf_dev.id, name="Ethernet2")
        sp2_if = nb.nb.dcim.interfaces.get(device_id=spines[1].id, name=f"Ethernet{i}")

        child_31b = nb.allocate_prefix(parent_prefix, 31, site.id, underlay_role.id)
        if not child_31b:
            print("ERROR: No /31 returned for Spine2<->Leaf.")
            sys.exit(1)
        ip_list_b = nb.get_available_ips_in_prefix(child_31b)
        if len(ip_list_b) < 2:
            print("ERROR: Not enough IP addresses in newly allocated /31.")
            sys.exit(1)

        nb.assign_ip_to_interface(sp2_if, ip_list_b[0].address)
        nb.assign_ip_to_interface(leaf_eth2, ip_list_b[1].address)

    # 11) Loopback /32 assignment
    loopback_role = nb.nb.ipam.roles.get(slug="loopbackcontainer")
    if not loopback_role:
        print("ERROR: No IPAM role 'loopbackcontainer' found.")
        sys.exit(1)

    loopback_pfxs = nb.nb.ipam.prefixes.filter(role_id=loopback_role.id, scope_id=site.id)
    loopback_list = list(loopback_pfxs)
    if not loopback_list:
        print("ERROR: No loopback prefix found for this site.")
        sys.exit(1)

    loopback_parent = loopback_list[0]
    print(f"Using parent prefix '{loopback_parent.prefix}' for /32 loopback allocations.")

    for dev in spines + leaves:
        # Get or create Loopback0
        loop0_if = nb.get_or_create_interface(dev.id, "Loopback0", "virtual")
        if not loop0_if:
            print(f"ERROR: Could not create/retrieve Loopback0 for {dev.name}")
            continue

        child_32 = nb.allocate_prefix(loopback_parent, 32, site.id, loopback_role.id)
        if not child_32:
            print(f"ERROR: Could not allocate /32 for {dev.name}.")
            continue

        ip_list_c = nb.get_available_ips_in_prefix(child_32)
        if not ip_list_c:
            print(f"ERROR: Not enough IP addresses in newly allocated /32 for {dev.name}.")
            continue

        new_lo_ip = nb.assign_ip_to_interface(loop0_if, ip_list_c[0].address)
        if new_lo_ip:
            print(f"Assigned {new_lo_ip.address} to {dev.name} Loopback0.")

    print("\n=== Fabric Creation Completed ===")
    print(f"Site: {site.name} (slug={site.slug})")
    print("Spines:", [dev.name for dev in spines])
    print("Leaves:", [dev.name for dev in leaves])
    print("Access Switches:", [dev.name for dev in access_switches])
    print("Each leaf/spine link got a new /31, Loopback0 got a new /32, and ASNs were assigned.")


if __name__ == "__main__":
    main()

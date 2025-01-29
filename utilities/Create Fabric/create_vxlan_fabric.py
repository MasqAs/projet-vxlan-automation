#!/usr/bin/env python3
"""
create_vxlan_fabric.py

(Original docstring truncated for brevity…)

Added behavior:
- Create "Loopback0" on each Spine and Leaf.
- Allocate a /32 from parent prefix with role="loopbackcontainer" and assign to the Loopback0 interface.
"""

import getpass
import sys

import pynetbox


def main():
    print(
        "=== VXLAN Fabric Creation Script (using available_prefixes.create for /31 and /32) ==="
    )

    # 1) NetBox details
    netbox_url = input("NetBox URL (e.g. https://netbox.local): ").strip()
    if not netbox_url:
        print("ERROR: NetBox URL is required.")
        sys.exit(1)

    netbox_token = getpass.getpass("NetBox API Token: ")
    if not netbox_token:
        print("ERROR: NetBox API token is required.")
        sys.exit(1)

    # Initialize pynetbox
    try:
        nb = pynetbox.api(netbox_url, token=netbox_token)
        # nb.http_session.verify = False  # e.g., if using self-signed cert
    except Exception as exc:
        print(f"ERROR: Failed to connect to NetBox: {exc}")
        sys.exit(1)

    # 2) Choose or create Site
    existing_sites = list(nb.dcim.sites.all())
    if not existing_sites:
        print("No sites found in NetBox.")
        sys.exit(1)

    print("\nExisting Sites:")
    for idx, s in enumerate(existing_sites, start=1):
        print(f"  {idx}. {s.name} (slug={s.slug})")

    choice = (
        input("Choose a site by number, or type 'new' to create one: ").strip().lower()
    )
    if choice == "new":
        site_name = input("New site name (e.g. 'Paris'): ").strip()
        site_code_input = input("New site code (e.g. 'PA'): ").strip()
        if not site_name or not site_code_input:
            print("ERROR: Site name and code required.")
            sys.exit(1)

        try:
            site = nb.dcim.sites.create(name=site_name, slug=site_code_input.lower())
            print(f"Created new site: {site.name} ({site.slug})")
        except Exception as exc:
            print(f"ERROR: Failed to create site: {exc}")
            sys.exit(1)

        # Derive a 2-letter code from site name
        site_clean = site.name.strip()
        site_code = (
            site_clean[:2].upper() if len(site_clean) >= 2 else site_clean.upper()
        )
    else:
        try:
            site_index = int(choice)
            site = existing_sites[site_index - 1]
            site_clean = site.name.strip()
            site_code = (
                site_clean[:2].upper() if len(site_clean) >= 2 else site_clean.upper()
            )
        except (ValueError, IndexError):
            print("ERROR: Invalid site selection.")
            sys.exit(1)

    # 3) Number of buildings
    while True:
        try:
            num_buildings = int(input("How many buildings? (1–5): ").strip())
            if 1 <= num_buildings <= 5:
                break
            else:
                print("ERROR: Please choose between 1 and 5.")
        except ValueError:
            print("ERROR: Invalid input. Try again.")

    # 4) Device type slugs
    print("\nEnter device type slugs (must exist in NetBox).")
    spine_devtype_slug = input("Spine Device Type Slug: ").strip()
    leaf_devtype_slug = input("Leaf Device Type Slug:  ").strip()
    access_devtype_slug = input("Access Switch Device Type Slug: ").strip()

    # 5) Roles: spine, leaf, access
    spine_role = nb.dcim.device_roles.get(slug="spine")
    if not spine_role:
        print("ERROR: No device role with slug='spine'.")
        sys.exit(1)

    leaf_role = nb.dcim.device_roles.get(slug="leaf")
    if not leaf_role:
        print("ERROR: No device role with slug='leaf'.")
        sys.exit(1)

    access_role = nb.dcim.device_roles.get(slug="access")
    if not access_role:
        print("ERROR: No device role with slug='access'.")
        sys.exit(1)

    print(
        f"Using roles -> Spine={spine_role.id}, Leaf={leaf_role.id}, Access={access_role.id}"
    )

    # 6) Create 2 Spines
    spine_names = [f"{site_code.lower()}dc_sp1_00", f"{site_code.lower()}dc_sp2_00"]
    spines = []

    for name in spine_names:
        existing_spine = nb.dcim.devices.get(name=name)
        if existing_spine:
            print(f"Spine '{name}' already exists; reusing it.")
            spines.append(existing_spine)
            continue

        try:
            new_spine = nb.dcim.devices.create(
                name=name,
                device_type={"slug": spine_devtype_slug},
                role=spine_role.id,
                site=site.id,
            )
            print(f"Created Spine: {new_spine.name}")
            spines.append(new_spine)
        except Exception as exc:
            print(f"ERROR creating spine '{name}': {exc}")
            sys.exit(1)

    # 7) Create Leaves + Access per building
    leaves = []
    access_switches = []

    for b_num in range(1, num_buildings + 1):
        building_code = f"{site_code}{b_num}"  # e.g. PA1

        # Make or find location
        location = nb.dcim.locations.get(site_id=site.id, name=building_code)
        if location:
            print(f"Location '{location.name}' already exists; reusing.")
        else:
            try:
                location = nb.dcim.locations.create(
                    name=building_code, slug=building_code.lower(), site=site.id
                )
                print(f"Created Location '{location.name}'")
            except Exception as exc:
                print(f"ERROR creating location '{building_code}': {exc}")
                sys.exit(1)

        # Leaf device
        leaf_name = f"{site_code.lower()}{str(b_num).zfill(2)}_lf1_00"
        existing_leaf = nb.dcim.devices.get(name=leaf_name)
        if existing_leaf:
            print(f"Leaf '{leaf_name}' already exists; reusing.")
            leaf_dev = existing_leaf
        else:
            try:
                leaf_dev = nb.dcim.devices.create(
                    name=leaf_name,
                    device_type={"slug": leaf_devtype_slug},
                    role=leaf_role.id,
                    site=site.id,
                    location=location.id,
                )
                print(f"Created Leaf: {leaf_dev.name}")
            except Exception as exc:
                print(f"ERROR creating leaf '{leaf_name}': {exc}")
                sys.exit(1)
        leaves.append(leaf_dev)

        # Access Switch
        sw_name = f"{site_code.lower()}{str(b_num).zfill(2)}_sw1_00"
        existing_sw = nb.dcim.devices.get(name=sw_name)
        if existing_sw:
            print(f"Access Switch '{sw_name}' already exists; reusing.")
            acc_dev = existing_sw
        else:
            try:
                acc_dev = nb.dcim.devices.create(
                    name=sw_name,
                    device_type={"slug": access_devtype_slug},
                    role=access_role.id,
                    site=site.id,
                    location=location.id,
                )
                print(f"Created Access Switch: {acc_dev.name}")
            except Exception as exc:
                print(f"ERROR creating access switch '{sw_name}': {exc}")
                sys.exit(1)
        access_switches.append(acc_dev)

    # 8) Cabling with multi-termination
    def get_or_create_interface(device, if_name, if_type="40gbase-x-qsfpp"):
        intf = nb.dcim.interfaces.get(device_id=device.id, name=if_name)
        if intf:
            return intf
        try:
            intf = nb.dcim.interfaces.create(
                device=device.id, name=if_name, type=if_type
            )
            return intf
        except Exception as exc:
            print(
                f"[ERROR] Could not create interface '{if_name}' on '{device.name}': {exc}"
            )
            return None

    def create_cable_if_not_exists(intf_a, intf_b):
        if not intf_a or not intf_b:
            print("[WARN] Missing interface(s); skipping cable creation.")
            return
        try:
            nb.dcim.cables.create(
                a_terminations=[
                    {"object_type": "dcim.interface", "object_id": intf_a.id}
                ],
                b_terminations=[
                    {"object_type": "dcim.interface", "object_id": intf_b.id}
                ],
                status="connected",
            )
            print(
                f"Created cable: {intf_a.device.name}:{intf_a.name} <--> {intf_b.device.name}:{intf_b.name}"
            )
        except Exception as exc:
            print(f"[INFO] Cable creation might have failed or already exists: {exc}")

    # Connect each leaf
    for i, leaf_dev in enumerate(leaves, start=1):
        leaf_eth1 = get_or_create_interface(leaf_dev, "Ethernet1")
        leaf_eth2 = get_or_create_interface(leaf_dev, "Ethernet2")
        leaf_eth3 = get_or_create_interface(leaf_dev, "Ethernet3")

        sp1_if = get_or_create_interface(spines[0], f"Ethernet{i}")
        sp2_if = get_or_create_interface(spines[1], f"Ethernet{i}")

        create_cable_if_not_exists(leaf_eth1, sp1_if)
        create_cable_if_not_exists(leaf_eth2, sp2_if)

        acc_dev = access_switches[i - 1]
        acc_if = get_or_create_interface(acc_dev, "Ethernet1")
        create_cable_if_not_exists(leaf_eth3, acc_if)

    # 9) /31 IP assignment + ASN custom field

    # 9a) Get underlay parent prefix
    underlay_role = nb.ipam.roles.get(slug="underlaycontainer")
    if not underlay_role:
        print("ERROR: No IPAM role 'underlaycontainer' found.")
        sys.exit(1)

    underlay_pfxs = nb.ipam.prefixes.filter(role_id=underlay_role.id, scope_id=site.id)
    underlay_list = list(underlay_pfxs)
    if not underlay_list:
        print("ERROR: No underlay prefix found for this site.")
        sys.exit(1)

    parent_prefix = underlay_list[0]
    print(f"Using parent prefix '{parent_prefix.prefix}' for /31 allocations.")

    # 9b) Assign ASNs in custom field 'ASN'
    next_spine_asn = 65001
    next_leaf_asn = 65101

    # Spines
    for spine_dev in spines:
        dev_obj = nb.dcim.devices.get(spine_dev.id)
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
        dev_obj = nb.dcim.devices.get(leaf_dev.id)
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

    # 9c) Allocate /31 from parent_prefix.available_prefixes for each Spine<->Leaf link
    for i, leaf_dev in enumerate(leaves, start=1):
        # Leaf.Eth1 <-> Spine1.Eth{i}
        leaf_eth1 = nb.dcim.interfaces.get(device_id=leaf_dev.id, name="Ethernet1")
        sp1_if = nb.dcim.interfaces.get(device_id=spines[0].id, name=f"Ethernet{i}")

        # 1) Spine1 <-> Leaf
        child_31 = None
        try:
            child_31 = parent_prefix.available_prefixes.create(
                {"prefix_length": 31, "site": site.id, "role": underlay_role.id}
            )
        except Exception as exc:
            print(f"ERROR allocating /31 for Spine1<->Leaf: {exc}")
            sys.exit(1)

        if not child_31:
            print("ERROR: No /31 returned for Spine1<->Leaf.")
            sys.exit(1)

        ip_list = list(child_31.available_ips.list())
        if len(ip_list) < 2:
            print("ERROR: Not enough IP addresses in newly allocated /31.")
            sys.exit(1)

        spine_ip_1 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[0].address,
                "assigned_object_id": sp1_if.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )
        leaf_ip_1 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[1].address,
                "assigned_object_id": leaf_eth1.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )

        # 2) Spine2 <-> Leaf
        leaf_eth2 = nb.dcim.interfaces.get(device_id=leaf_dev.id, name="Ethernet2")
        sp2_if = nb.dcim.interfaces.get(device_id=spines[1].id, name=f"Ethernet{i}")

        child_31b = None
        try:
            child_31b = parent_prefix.available_prefixes.create(
                {"prefix_length": 31, "site": site.id, "role": underlay_role.id}
            )
        except Exception as exc:
            print(f"ERROR allocating /31 for Spine2<->Leaf: {exc}")
            sys.exit(1)

        if not child_31b:
            print("ERROR: No /31 returned for Spine2<->Leaf.")
            sys.exit(1)

        ip_list = list(child_31b.available_ips.list())
        if len(ip_list) < 2:
            print("ERROR: Not enough IPs in newly allocated /31 (Spine2).")
            sys.exit(1)

        spine_ip_2 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[0].address,
                "assigned_object_id": sp2_if.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )
        leaf_ip_2 = nb.ipam.ip_addresses.create(
            {
                "address": ip_list[1].address,
                "assigned_object_id": leaf_eth2.id,
                "assigned_object_type": "dcim.interface",
                "status": "active",
            }
        )

    # === LOOPBACK CHANGES ===
    #
    # 9d) Allocate /32 from prefix role='loopbackcontainer' for spines & leaves
    loopback_role = nb.ipam.roles.get(slug="loopbackcontainer")
    if not loopback_role:
        print("ERROR: No IPAM role 'loopbackcontainer' found.")
        sys.exit(1)

    loopback_pfxs = nb.ipam.prefixes.filter(role_id=loopback_role.id, scope_id=site.id)
    loopback_list = list(loopback_pfxs)
    if not loopback_list:
        print("ERROR: No loopback prefix found for this site.")
        sys.exit(1)

    loopback_parent = loopback_list[0]
    print(
        f"Using parent prefix '{loopback_parent.prefix}' for /32 loopback allocations."
    )

    # We will create Loopback0 on each Spine & Leaf (you can also do Access if needed)
    for dev in spines + leaves:
        # 1) Get or create interface 'Loopback0'
        loop0_if = nb.dcim.interfaces.get(device_id=dev.id, name="Loopback0")
        if not loop0_if:
            try:
                loop0_if = nb.dcim.interfaces.create(
                    device=dev.id,
                    name="Loopback0",
                    type="virtual",  # or "loopback" if your NetBox has that type
                )
                print(f"Created Loopback0 on {dev.name}")
            except Exception as exc:
                print(f"ERROR creating Loopback0 on {dev.name}: {exc}")
                continue

        # 2) Allocate a new /32
        child_32 = None
        try:
            child_32 = loopback_parent.available_prefixes.create(
                {"prefix_length": 32, "site": site.id, "role": loopback_role.id}
            )
        except Exception as exc:
            print(f"ERROR allocating /32 for {dev.name} Loopback0: {exc}")
            continue

        if not child_32:
            print(f"ERROR: No /32 returned for {dev.name} Loopback0.")
            continue

        # 3) Assign first IP of that /32 to Loopback0
        ip_list = list(child_32.available_ips.list())
        if not ip_list:
            print(f"ERROR: Not enough IPs in newly allocated /32 for {dev.name}.")
            continue

        try:
            new_lo_ip = nb.ipam.ip_addresses.create(
                {
                    "address": ip_list[0].address,
                    "assigned_object_id": loop0_if.id,
                    "assigned_object_type": "dcim.interface",
                    "status": "active",
                }
            )
            print(f"Assigned {new_lo_ip.address} to {dev.name} Loopback0.")
        except Exception as exc:
            print(f"ERROR assigning IP to {dev.name} Loopback0: {exc}")
    # === /LOOPBACK CHANGES ===

    print("\n=== Fabric Creation Completed ===")
    print(f"Site: {site.name} (slug={site.slug})")
    print("Spines:", [dev.name for dev in spines])
    print("Leaves:", [dev.name for dev in leaves])
    print("Access Switches:", [dev.name for dev in access_switches])
    print(
        "Each leaf/spine link got a new /31 from 'available_prefixes', "
        "Loopback0 got a new /32, and ASNs were assigned via custom field 'ASN'."
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys

import requests
import yaml

#####################################
# NetBox API Helper Functions
#####################################


def create_or_get_custom_field_building_name(
    netbox_url, headers, field_name="building_name"
):
    """
    Creates or retrieves a Custom Field for ipam.prefix with object_types=["ipam.prefix"].
    For NetBox 3.x/4.x.
    """
    # 1) Check if the custom field already exists
    url = f"{netbox_url}/api/extras/custom-fields/?name={field_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if results:
        print(f"[INFO] Custom Field '{field_name}' already exists.")
        return results[0]

    # 2) Create the new custom field
    url = f"{netbox_url}/api/extras/custom-fields/"
    payload = {
        "name": field_name,
        "label": "Building Name",
        "type": "text",
        "description": "Stores building name for prefixes",
        "required": False,
        "object_types": ["ipam.prefix"],  # For NetBox 3.x/4.x
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    cf = resp.json()
    print(f"[INFO] Created Custom Field '{field_name}'.")
    return cf


def get_or_create_tenant(netbox_url, headers, tenant_name):
    """
    Check if a Tenant with 'tenant_name' exists via the API.
    If not found, create it. Return the tenant object.
    """
    search_url = f"{netbox_url}/api/tenancy/tenants/?name={tenant_name}"
    resp = requests.get(search_url, headers=headers)
    resp.raise_for_status()
    data = resp.json().get("results", [])
    if data:
        print(f"[INFO] Tenant '{tenant_name}' already exists.")
        return data[0]

    create_url = f"{netbox_url}/api/tenancy/tenants/"
    payload = {"name": tenant_name, "slug": tenant_name.lower().replace(" ", "-")}
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    tenant_obj = resp.json()
    print(f"[INFO] Tenant '{tenant_name}' created (ID={tenant_obj['id']}).")
    return tenant_obj


def get_or_create_region(netbox_url, headers, region_name):
    """
    Get or create a Region by name.
    """
    url = f"{netbox_url}/api/dcim/regions/?name={region_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if results:
        print(f"[INFO] Region '{region_name}' already exists.")
        return results[0]

    create_url = f"{netbox_url}/api/dcim/regions/"
    payload = {"name": region_name, "slug": region_name.lower().replace(" ", "-")}
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    region = resp.json()
    print(f"[INFO] Region '{region_name}' created (ID={region['id']}).")
    return region


def get_or_create_site(netbox_url, headers, site_name, region_id=None):
    """
    Get or create a Site by name. Optionally attach to a region.
    """
    url = f"{netbox_url}/api/dcim/sites/?name={site_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if results:
        print(f"[INFO] Site '{site_name}' already exists.")
        return results[0]

    create_url = f"{netbox_url}/api/dcim/sites/"
    payload = {"name": site_name, "slug": site_name.lower().replace(" ", "-")}
    if region_id:
        payload["region"] = region_id

    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    site_obj = resp.json()
    print(f"[INFO] Site '{site_name}' created (ID={site_obj['id']}).")
    return site_obj


def get_or_create_location(netbox_url, headers, location_name, site_id):
    """
    Creates or retrieves a Location (DCIM) under the specified site.
    """
    url = f"{netbox_url}/api/dcim/locations/?name={location_name}&site_id={site_id}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if results:
        print(f"[INFO] Location '{location_name}' already exists (Site={site_id}).")
        return results[0]

    create_url = f"{netbox_url}/api/dcim/locations/"
    payload = {"name": location_name, "slug": location_name.lower(), "site": site_id}
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    loc = resp.json()
    print(f"[INFO] Location '{location_name}' created (ID={loc['id']}).")
    return loc


def get_or_create_prefix_role(netbox_url, headers, role_name):
    """
    Get or create a Prefix Role (e.g. Container, Underlay, Loopback).
    """
    url = f"{netbox_url}/api/ipam/roles/?name={role_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if results:
        print(f"[INFO] Prefix Role '{role_name}' already exists.")
        return results[0]

    create_url = f"{netbox_url}/api/ipam/roles/"
    payload = {"name": role_name, "slug": role_name.lower().replace(" ", "-")}
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    role_obj = resp.json()
    print(f"[INFO] Prefix Role '{role_name}' created (ID={role_obj['id']}).")
    return role_obj


def create_or_get_prefix(
    netbox_url,
    headers,
    prefix_cidr,
    site_id=None,
    description=None,
    role_id=None,
    tenant_id=None,
    custom_fields=None,
):
    """
    Create or retrieve a Prefix in NetBox.
    If prefix already exists, skip creation.
    """
    # Check if prefix already exists
    search_url = f"{netbox_url}/api/ipam/prefixes/?prefix={prefix_cidr}"
    resp = requests.get(search_url, headers=headers)
    resp.raise_for_status()
    existing = resp.json().get("results", [])
    if existing:
        print(f"[WARN] Prefix '{prefix_cidr}' already exists; skipping.")
        return existing[0]

    # Create new prefix
    create_url = f"{netbox_url}/api/ipam/prefixes/"
    payload = {"prefix": prefix_cidr}
    if site_id is not None:
        payload["site"] = site_id
    if description:
        payload["description"] = description
    if role_id:
        payload["role"] = role_id
    if tenant_id:
        payload["tenant"] = tenant_id
    if custom_fields:
        payload["custom_fields"] = custom_fields

    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    new_prefix = resp.json()
    print(
        f"[INFO] Created prefix '{prefix_cidr}' (Desc='{description}', Role={role_id}, Tenant={tenant_id})."
    )
    return new_prefix


#####################################
# Main
#####################################


def main():
    if len(sys.argv) != 4:
        print("Usage: python populate_data.py <NETBOX_URL> <NETBOX_TOKEN> <YAML_FILE>")
        sys.exit(1)

    netbox_url = sys.argv[1].rstrip("/")
    netbox_token = sys.argv[2]
    yaml_file = sys.argv[3]

    headers = {
        "Authorization": f"Token {netbox_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 1) Load the YAML data
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    # 2) Create or get the Custom Field "building_name"
    create_or_get_custom_field_building_name(netbox_url, headers, "building_name")

    # 3) Create Tenants for each building
    buildings_info = data.get("Buildings", {})
    building_to_tenant = {}
    for building_name, b_data in buildings_info.items():
        tenant_name = b_data.get("Tenant")
        if tenant_name:
            tenant_obj = get_or_create_tenant(netbox_url, headers, tenant_name)
            building_to_tenant[building_name] = tenant_obj
        else:
            building_to_tenant[building_name] = None

    # 4) Region & Site
    region_name = data.get("Location", {}).get("Region", "Europe")
    region_obj = get_or_create_region(netbox_url, headers, region_name)
    region_id = region_obj["id"]

    site_name = data.get("Location", {}).get("City", "Paris")
    site_obj = get_or_create_site(netbox_url, headers, site_name, region_id=region_id)
    site_id = site_obj["id"]

    # 5) Create a DCIM Location for each building
    for building_name in buildings_info.keys():
        get_or_create_location(netbox_url, headers, building_name, site_id)

    # 6) Create Roles: Container, Underlay, Loopback
    container_role_obj = get_or_create_prefix_role(netbox_url, headers, "Container")
    underlay_role_obj = get_or_create_prefix_role(netbox_url, headers, "Underlay")
    loopback_role_obj = get_or_create_prefix_role(netbox_url, headers, "Loopback")

    container_role_id = container_role_obj["id"]
    underlay_role_id = underlay_role_obj["id"]
    loopback_role_id = loopback_role_obj["id"]

    # 7) Create Container prefixes
    containers = data.get("Containers", {})
    for c_name, c_data in containers.items():
        cidr = c_data.get("cidr")
        desc = c_data.get("description", f"Container prefix {c_name}")
        create_or_get_prefix(
            netbox_url,
            headers,
            prefix_cidr=cidr,
            site_id=None,  # container prefixes usually not attached to a site
            description=desc,
            role_id=container_role_id,
            tenant_id=None,
            custom_fields=None,
        )

    # 8) Create Underlay prefixes
    underlay = data.get("Underlay", {})
    for building_name, subnets in underlay.items():
        tenant_obj = building_to_tenant.get(building_name)
        tenant_id = tenant_obj["id"] if tenant_obj else None

        for entry in subnets:
            prefix_cidr = entry.get("Subnet")
            spine_ip = entry.get("spine_ip")
            leaf_ip = entry.get("leaf_ip")

            desc = f"Underlay {building_name}"
            if spine_ip and leaf_ip:
                desc += f" (Spine={spine_ip}, Leaf={leaf_ip})"

            cf = {"building_name": building_name}

            create_or_get_prefix(
                netbox_url,
                headers,
                prefix_cidr=prefix_cidr,
                site_id=site_id,
                description=desc,
                role_id=underlay_role_id,
                tenant_id=tenant_id,
                custom_fields=cf,
            )

    # 9) Create Loopback prefixes
    loopbacks = data.get("Loopback", {})
    for device_name, loopback_cidr in loopbacks.items():
        desc = f"Loopback for {device_name}"
        # If you know the building for this device, set it here. Otherwise "N/A"
        cf = {"building_name": "N/A"}

        create_or_get_prefix(
            netbox_url,
            headers,
            prefix_cidr=loopback_cidr,
            site_id=site_id,
            description=desc,
            role_id=loopback_role_id,
            tenant_id=None,
            custom_fields=cf,
        )

    print("[INFO] NetBox population completed successfully!")


if __name__ == "__main__":
    main()

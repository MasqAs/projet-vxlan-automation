#!/usr/bin/env python3
import sys
import requests
import yaml

########################################
# Functions for importing device_model.yml
########################################

def get_or_create_manufacturer(netbox_url, headers, manufacturer_name, slug):
    # Check if the manufacturer already exists
    url = f"{netbox_url}/api/dcim/manufacturers/?slug={slug}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results:
        print(f"[INFO] Manufacturer '{manufacturer_name}' (slug={slug}) already exists.")
        return results[0]

    # Otherwise create it
    url = f"{netbox_url}/api/dcim/manufacturers/"
    payload = {
        "name": manufacturer_name,
        "slug": slug
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    created = resp.json()
    print(f"[INFO] Manufacturer '{manufacturer_name}' created (ID={created['id']}).")
    return created

def get_or_create_device_role(netbox_url, headers, role):
    name = role["name"]
    slug = role["slug"]
    url = f"{netbox_url}/api/dcim/device-roles/?slug={slug}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results:
        print(f"[INFO] Device Role '{name}' (slug={slug}) already exists.")
        return results[0]

    url = f"{netbox_url}/api/dcim/device-roles/"
    payload = {
        "name": name,
        "slug": slug
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    created = resp.json()
    print(f"[INFO] Device Role '{name}' created (ID={created['id']}).")
    return created

def get_or_create_device_type(netbox_url, headers, device_type, manufacturers_cache):
    manufacturer_slug = device_type["manufacturer"]
    # Retrieve the manufacturer object from the cache
    if manufacturer_slug not in manufacturers_cache:
        # If it's not found, skip
        print(f"[WARN] Manufacturer slug '{manufacturer_slug}' not found in cache. Skipping device type.")
        return None

    manufacturer_obj = manufacturers_cache[manufacturer_slug]

    # Check if this device type already exists (based on slug+manufacturer)
    slug = device_type["slug"]
    url = f"{netbox_url}/api/dcim/device-types/?slug={slug}&manufacturer_id={manufacturer_obj['id']}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results:
        print(f"[INFO] Device Type '{device_type['model']}' (slug={slug}) already exists.")
        dt = results[0]
        # No interface creation logic here
        return dt

    # Otherwise create it
    create_url = f"{netbox_url}/api/dcim/device-types/"
    payload = {
        "manufacturer": manufacturer_obj["id"],
        "model": device_type["model"],
        "slug": slug,
        "part_number": device_type.get("part_number", ""),
        "u_height": device_type.get("u_height", 1),
        "is_full_depth": device_type.get("is_full_depth", False),
        "comments": device_type.get("comments", "")
    }
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    created_dt = resp.json()
    print(f"[INFO] Device Type '{created_dt['model']}' created (ID={created_dt['id']}).")

    # Interface templates (NetBox does not support bulk interface creation via
    # the standard REST API in v3/v4). For demo, we only print the interfaces.
    if "interfaces" in device_type:
        for iface in device_type["interfaces"]:
            print(f"    [INFO] Interface template '{iface['name']}' would be created for device-type {created_dt['model']}")

    return created_dt


########################################
# Functions for importing subnets.yml
########################################

def get_or_create_region(netbox_url, headers, region_name):
    url = f"{netbox_url}/api/dcim/regions/?name={region_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results:
        print(f"[INFO] Region '{region_name}' already exists.")
        return results[0]

    create_url = f"{netbox_url}/api/dcim/regions/"
    payload = {
        "name": region_name,
        "slug": region_name.lower().replace(" ", "-")
    }
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    created = resp.json()
    print(f"[INFO] Region '{region_name}' created (ID={created['id']}).")
    return created

def get_or_create_site(netbox_url, headers, site_name, region_id=None):
    url = f"{netbox_url}/api/dcim/sites/?name={site_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results:
        print(f"[INFO] Site '{site_name}' already exists.")
        return results[0]

    create_url = f"{netbox_url}/api/dcim/sites/"
    payload = {
        "name": site_name,
        "slug": site_name.lower().replace(" ", "-")
    }
    if region_id:
        payload["region"] = region_id

    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    created = resp.json()
    print(f"[INFO] Site '{site_name}' created (ID={created['id']}).")
    return created

def get_or_create_location(netbox_url, headers, location_name, site_id):
    # Check if the location exists
    url = f"{netbox_url}/api/dcim/locations/?name={location_name}&site_id={site_id}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results:
        print(f"[INFO] Location '{location_name}' already exists for site ID={site_id}.")
        return results[0]

    # Otherwise create it
    create_url = f"{netbox_url}/api/dcim/locations/"
    payload = {
        "name": location_name,
        "slug": location_name.lower(),
        "site": site_id
    }
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    created = resp.json()
    print(f"[INFO] Location '{location_name}' created (ID={created['id']}).")
    return created

def get_or_create_prefix_role(netbox_url, headers, role_name):
    url = f"{netbox_url}/api/ipam/roles/?name={role_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results:
        print(f"[INFO] Prefix Role '{role_name}' already exists.")
        return results[0]

    create_url = f"{netbox_url}/api/ipam/roles/"
    payload = {
        "name": role_name,
        "slug": role_name.lower().replace(" ", "-")
    }
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    created = resp.json()
    print(f"[INFO] Prefix Role '{role_name}' created (ID={created['id']}).")
    return created

def create_container_prefix(netbox_url, headers, cidr, description, role_id):
    # Check if the prefix already exists
    check_url = f"{netbox_url}/api/ipam/prefixes/?prefix={cidr}"
    resp = requests.get(check_url, headers=headers)
    resp.raise_for_status()
    existing = resp.json()["results"]
    if existing:
        print(f"[WARN] Container prefix '{cidr}' already exists. Not recreating.")
        return existing[0]

    create_url = f"{netbox_url}/api/ipam/prefixes/"
    payload = {
        "prefix": cidr,
        "description": description,
        "role": role_id
    }
    resp = requests.post(create_url, headers=headers, json=payload)
    resp.raise_for_status()
    new_prefix = resp.json()
    print(f"[INFO] Container prefix '{cidr}' created (ID={new_prefix['id']}).")
    return new_prefix


########################################
# MAIN
########################################

def main():
    if len(sys.argv) != 5:
        print("Usage: python import_netbox.py <NETBOX_URL> <NETBOX_TOKEN> <DEVICE_MODEL_YML> <SUBNETS_YML>")
        sys.exit(1)

    netbox_url = sys.argv[1].rstrip("/")
    netbox_token = sys.argv[2]
    device_model_file = sys.argv[3]
    subnets_file = sys.argv[4]

    headers = {
        "Authorization": f"Token {netbox_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Load device_model.yml
    with open(device_model_file, "r") as f:
        device_model_data = yaml.safe_load(f)

    # Load subnets.yml
    with open(subnets_file, "r") as f:
        subnets_data = yaml.safe_load(f)

    ######################################################
    # 1) device_model.yml : manufacturers, roles, types
    ######################################################

    # a) Manufacturers
    manufacturers_cache = {}
    if "manufacturers" in device_model_data:
        for mf in device_model_data["manufacturers"]:
            name = mf["name"]
            slug = mf["slug"]
            mf_obj = get_or_create_manufacturer(netbox_url, headers, name, slug)
            manufacturers_cache[slug] = mf_obj

    # b) Device Roles
    if "device_roles" in device_model_data:
        for role in device_model_data["device_roles"]:
            get_or_create_device_role(netbox_url, headers, role)

    # c) Device Types
    if "device_types" in device_model_data:
        for dt in device_model_data["device_types"]:
            get_or_create_device_type(netbox_url, headers, dt, manufacturers_cache)

    ######################################################
    # 2) subnets.yml : Region, Site, Containers, Locations
    ######################################################

    # a) Region & Site
    region_name = subnets_data.get("Location", {}).get("Region", "Europe")
    region_obj = get_or_create_region(netbox_url, headers, region_name)
    region_id = region_obj["id"]

    city_name = subnets_data.get("Location", {}).get("City", "Paris")
    site_obj = get_or_create_site(netbox_url, headers, city_name, region_id=region_id)
    site_id = site_obj["id"]

    # b) Container role
    container_role_obj = get_or_create_prefix_role(netbox_url, headers, "Container")
    container_role_id = container_role_obj["id"]

    # c) Containers
    containers = subnets_data.get("Containers", {})
    for c_key, c_data in containers.items():
        cidr = c_data.get("cidr")
        desc = c_data.get("description", f"Container {c_key}")
        create_container_prefix(netbox_url, headers, cidr, desc, container_role_id)

    # d) (Optional) Buildings as locations
    buildings = subnets_data.get("Buildings", {})
    for building_name in buildings.keys():
        get_or_create_location(netbox_url, headers, building_name, site_id)

    print("[INFO] Script completed successfully!")


if __name__ == "__main__":
    main()

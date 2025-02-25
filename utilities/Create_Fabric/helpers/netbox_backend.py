"""
NetBox_backend.py
=================
A Python class to interact with NetBox using pynetbox.
"""

import pynetbox
from typing import Optional, List, Dict


class NetBoxBackend:
    def __init__(self, url: str, token: str, verify_ssl: bool = True):
        """
        Initializes the NetBox API connection.
        """
        self.url = url
        self.token = token
        self.nb = pynetbox.api(self.url, token=self.token)
        self.nb.http_session.verify = verify_ssl

    ## ----------------------------------
    ## TENANTS MANAGEMENT
    ## ----------------------------------

    def get_tenants(self) -> List:
        """ Returns all tenants in NetBox. """
        try:
            return list(self.nb.tenancy.tenants.all())
        except Exception as e:
            print(f"[ERROR] Failed to fetch tenants: {e}")
            return []

    def create_tenant(self, name: str, slug: str):
        """ Creates a new tenant in NetBox. """
        try:
            return self.nb.tenancy.tenants.create({"name": name, "slug": slug})
        except Exception as e:
            print(f"[ERROR] Failed to create tenant '{name}': {e}")
            return None

    ## ----------------------------------
    ## SITES MANAGEMENT
    ## ----------------------------------

    def get_sites(self) -> List:
        """ Returns all sites in NetBox. """
        try:
            return list(self.nb.dcim.sites.all())
        except Exception as e:
            print(f"[ERROR] Failed to fetch sites: {e}")
            return []

    def create_site(self, name: str, slug: str):
        """ Creates a new site in NetBox. """
        try:
            return self.nb.dcim.sites.create({"name": name, "slug": slug})
        except Exception as e:
            print(f"[ERROR] Failed to create site '{name}': {e}")
            return None

    ## ----------------------------------
    ## DEVICE MANAGEMENT
    ## ----------------------------------

    def get_device_type_by_slug(self, slug: str) -> Optional[Dict]:
        """ Returns a device type by slug. """
        try:
            return self.nb.dcim.device_types.get(slug=slug)
        except Exception as e:
            print(f"[ERROR] Failed to fetch device type '{slug}': {e}")
            return None

    def get_device_role(self, slug: str) -> Optional[Dict]:
        """ Returns a device role by slug. """
        try:
            return self.nb.dcim.device_roles.get(slug=slug)
        except Exception as e:
            print(f"[ERROR] Failed to fetch device role '{slug}': {e}")
            return None

    def create_device(self, name: str, device_type_slug: str, role_id: int, site_id: int, location_id: Optional[int] = None):
        """ Creates a device in NetBox if it doesn't already exist. """
        try:
            existing_device = self.nb.dcim.devices.get(name=name)
            if existing_device:
                return existing_device

            device_type = self.get_device_type_by_slug(device_type_slug)
            if not device_type:
                print(f"[ERROR] Device type '{device_type_slug}' not found.")
                return None

            return self.nb.dcim.devices.create({
                "name": name,
                "device_type": {"id": device_type.id},
                "role": role_id,
                "site": site_id,
                "location": location_id
            })
        except Exception as e:
            print(f"[ERROR] Failed to create device '{name}': {e}")
            return None

    ## ----------------------------------
    ## INTERFACES & CABLING
    ## ----------------------------------

    def get_or_create_interface(self, device_id: int, if_name: str, if_type: str = "40gbase-x-qsfpp"):
        """ Retrieves or creates an interface on a given device. """
        try:
            intf = self.nb.dcim.interfaces.get(device_id=device_id, name=if_name)
            if intf:
                return intf
            return self.nb.dcim.interfaces.create({
                "device": device_id,
                "name": if_name,
                "type": if_type,
            })
        except Exception as e:
            print(f"[ERROR] Failed to create/get interface '{if_name}': {e}")
            return None

    def create_cable_if_not_exists(self, intf_a, intf_b):
        """ Creates a cable between two interfaces if it doesn't exist. """
        if not intf_a or not intf_b:
            print("[WARN] Missing interfaces to create cable.")
            return None
        try:
            return self.nb.dcim.cables.create({
                "a_terminations": [{"object_type": "dcim.interface", "object_id": intf_a.id}],
                "b_terminations": [{"object_type": "dcim.interface", "object_id": intf_b.id}],
                "status": "connected",
            })
        except Exception as e:
            print(f"[ERROR] Failed to create cable: {e}")
            return None

    ## ----------------------------------
    ## NETWORK MANAGEMENT
    ## ----------------------------------

    def create_vlan(self, vlan_id: int, vlan_name: str, slug:str, tenant_id: str):
        """ Creates a VLAN in NetBox. """
        try:
            return self.nb.ipam.vlans.create({
                "vid": vlan_id,
                "name": vlan_name,
                "slug": slug,
                "tenant": tenant_id,
            })
        except Exception as e:
            print(f"[ERROR] Failed to create VLAN '{vlan_name}': {e}")
            return None

    def create_l2vpn(self, vni_id: int, vpn_name: str, slug: str, tenant_id: str):
        """ Creates an L2VPN in NetBox. """
        try:
            return self.nb.vpn.l2vpns.create({
                "name": vpn_name,
                "slug": slug,
                "type": "vxlan-evpn",
                "tenant": tenant_id,
                "identifier": vni_id
            })
        except Exception as e:
            print(f"[ERROR] Failed to create L2VPN '{vpn_name}': {e}")
            return None

    def create_vxlan_termination(self, l2vpn_id: int, assigned_object_type: str, assigned_object_id: int):
        """ Creates a VXLAN termination for L2VPN. """
        try:
            return self.nb.vpn.l2vpn_terminations.create({
                "l2vpn": l2vpn_id,
                "assigned_object_type": assigned_object_type,
                "assigned_object_id": assigned_object_id
            })
        except Exception as e:
            print(f"[ERROR] Failed to create VXLAN termination: {e}")
            return None
        
    def allocate_prefix(self, parent_prefix, prefix_length: int, site_id: int, role_id: int):
        """
        Alloue un sous-réseau enfant (ex: /31 ou /32) à partir d'un préfixe parent
        via available_prefixes.create().
        """
        try:
            child_prefix = parent_prefix.available_prefixes.create({
                "prefix_length": prefix_length,
                "site": site_id,
                "role": role_id,
            })
            return child_prefix
        except Exception as exc:
            print(f"[ERROR] Echec de l'allocation d'un /{prefix_length} pour {parent_prefix.prefix}: {exc}")
            return None

    def assign_ip_to_interface(self, interface, ip_address: str, status: str = "active"):
        """ Assigns an IP address to an interface. """
        try:
            return self.nb.ipam.ip_addresses.create({
                "address": ip_address,
                "assigned_object_id": interface.id,
                "assigned_object_type": "dcim.interface",
                "status": status,
            })
        except Exception as e:
            print(f"[ERROR] Failed to assign IP {ip_address}: {e}")
            return None

    def get_available_ips_in_prefix(self, prefix) -> List:
        """ Fetches available IPs within a prefix. """
        if not hasattr(prefix, "available_ips"):
            print(f"[ERROR] Invalid prefix object: {prefix}")
            return []
        return list(prefix.available_ips.list())

    def save_custom_fields(self, device, fields: Dict[str, any]):
        """ Saves custom fields for a device. """
        try:
            for key, value in fields.items():
                device.custom_fields[key] = value
            device.save()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save custom fields: {e}")
            return False

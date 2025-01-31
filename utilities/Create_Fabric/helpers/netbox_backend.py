#!/usr/bin/env python3

"""
NetBox_backend.py
=================

Ce module propose une classe NetBoxBackend qui encapsule et simplifie
les interactions de base avec l'API NetBox via pynetbox. L'objectif est
de rendre le code plus lisible et réutilisable dans des scripts,
comme par exemple create_vxlan_fabric.py.
"""

import pynetbox
from typing import Optional, List, Dict


class NetBoxBackend:
    def __init__(self, url: str, token: str, verify_ssl: bool = True):
        """
        Initialise l'instance pynetbox et stocke la référence
        pour les opérations ultérieures.
        """
        self.url = url
        self.token = token
        self.nb = pynetbox.api(self.url, token=self.token)
        self.nb.http_session.verify = verify_ssl

    def get_sites(self):
        """
        Retourne la liste de tous les sites.
        """
        return list(self.nb.dcim.sites.all())

    def create_site(self, name: str, slug: str):
        """
        Crée un nouveau site avec le nom et le slug donnés.
        """
        return self.nb.dcim.sites.create(name=name, slug=slug)

    def get_site_by_index(self, index: int) -> Optional[Dict]:
        """
        Retourne le site se trouvant à l'index donné (basé sur la liste ordonnée)
        ou None si l'index est invalide.
        """
        all_sites = self.get_sites()
        if 0 <= index < len(all_sites):
            return all_sites[index]
        return None

    def get_device_type_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Retourne un device_type depuis son slug, ou None si introuvable.
        """
        return self.nb.dcim.device_types.get(slug=slug)

    def get_device_role(self, slug: str) -> Optional[Dict]:
        """
        Retourne le device_role depuis son slug, ou None si introuvable.
        """
        return self.nb.dcim.device_roles.get(slug=slug)

    def create_device(self, name: str, device_type_slug: str, role_id: int, site_id: int,
                      location_id: Optional[int] = None):
        """
        Crée un device NetBox, s'il n'existe pas déjà.
        """
        existing_device = self.nb.dcim.devices.get(name=name)
        if existing_device:
            return existing_device
        # device_type est référencé par slug
        return self.nb.dcim.devices.create(
            name=name,
            device_type={"slug": device_type_slug},
            role=role_id,
            site=site_id,
            location=location_id
        )

    def get_or_create_interface(self, device_id: int, if_name: str, if_type: str = "40gbase-x-qsfpp"):
        """
        Récupère ou crée une interface sur un device donné.
        """
        intf = self.nb.dcim.interfaces.get(device_id=device_id, name=if_name)
        if intf:
            return intf
        return self.nb.dcim.interfaces.create(
            device=device_id,
            name=if_name,
            type=if_type,
        )

    def create_cable_if_not_exists(self, intf_a, intf_b):
        """
        Crée un câble entre deux interfaces si ce câble n'existe pas.
        Utilise la forme multi-termination fournie par NetBox 3.x.
        """
        if not intf_a or not intf_b:
            print("[WARN] create_cable_if_not_exists: interfaces manquantes.")
            return
        try:
            self.nb.dcim.cables.create(
                a_terminations=[
                    {"object_type": "dcim.interface", "object_id": intf_a.id}
                ],
                b_terminations=[
                    {"object_type": "dcim.interface", "object_id": intf_b.id}
                ],
                status="connected",
            )
        except Exception as exc:
            print(f"[INFO] Echec ou duplication possible pour la création de câble: {exc}")

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
        """
        Associe une adresse IP existante ou nouvelle à l'interface indiquée.
        """
        try:
            new_ip = self.nb.ipam.ip_addresses.create({
                "address": ip_address,
                "assigned_object_id": interface.id,
                "assigned_object_type": "dcim.interface",
                "status": status,
            })
            return new_ip
        except Exception as exc:
            print(f"[ERROR] Impossible d'assigner l'IP {ip_address} à l'interface {interface.name}: {exc}")
            return None

    def get_available_ips_in_prefix(self, prefix) -> List:
        """
        Récupère la liste des adresses IP disponibles dans un préfixe donné.
        """
        return list(prefix.available_ips.list())

    def save_custom_fields(self, device, fields: Dict[str, any]):
        """
        Met à jour plusieurs custom fields pour un device donné.
        """
        for key, value in fields.items():
            device.custom_fields[key] = value
        try:
            device.save()
            return True
        except Exception as exc:
            print(f"[ERROR] Echec de sauvegarde des champs custom sur {device.name}: {exc}")
            return False

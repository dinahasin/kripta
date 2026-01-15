import json
import subprocess
from dataclasses import dataclass
from typing import List, Optional
import logging

@dataclass
class DriveInfo:
    device: str          # /dev/sdb1
    name: str            # Label or model
    size: str            # Human readable size
    mountpoint: str      # /media/user/usb or empty
    type: str            # ext4, ntfs, etc.
    is_mounted: bool
    is_removable: bool
    is_system: bool      # True if it's the root drive or swap

class DriveService:
    """
    Gestionnaire de disques pour Linux utilisant udisksctl et lsblk.
    Permet de lister, monter, démonter et éjecter des disques.
    """
    
    @staticmethod
    def get_drives() -> List[DriveInfo]:
        """Récupère la liste des disques et partitions pertinents."""
        drives = []
        try:
            # Utiliser lsblk pour avoir une structure JSON claire
            # -J: JSON output
            # -o: Output columns
            # -p: Full paths
            cmd = [
                "lsblk", "-J", "-p", "-o", 
                "NAME,LABEL,MODEL,SIZE,MOUNTPOINT,FSTYPE,RM,TYPE,HOTPLUG,UUID"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            for device in data.get("blockdevices", []):
                DriveService._process_device_recursive(device, drives)
                
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des disques: {e}")
            
        return drives

    @staticmethod
    def _process_device_recursive(device: dict, drives: List[DriveInfo]):
        """Traite un device et ses enfants récursivement."""
        # On s'intéresse principalement aux partitions (part) ou disques sans partition (disk avec fs)
        dev_type = device.get("type")
        mountpoint = device.get("mountpoint")
        fstype = device.get("fstype")
        
        # Déterminer si c'est un disque système basique
        is_system = mountpoint == "/" or mountpoint == "[SWAP]"
        
        # Nom convivial
        label = device.get("label")
        model = device.get("model")
        name = label if label else (model if model else device.get("name"))
        
        # Créer l'objet DriveInfo si c'est pertinent
        # pertinent = (est une partition OU est un disque simple) ET a un système de fichiers ou est monté
        if (dev_type == "part" or (dev_type == "disk" and fstype)) and device.get("name"):
            drive = DriveInfo(
                device=device.get("name"),
                name=name or "Disque Inconnu",
                size=device.get("size"),
                mountpoint=mountpoint or "",
                type=fstype or "Inconnu",
                is_mounted=bool(mountpoint),
                is_removable=device.get("rm") == True or device.get("hotplug") == True,
                is_system=is_system
            )
            drives.append(drive)
            
        # Traiter les enfants (partitions)
        for child in device.get("children", []):
            # Propager l'info du model parent si l'enfant n'a pas de label
            if not child.get("model") and model:
                child["model"] = model
            DriveService._process_device_recursive(child, drives)

    @staticmethod
    def mount_drive(device: str) -> bool:
        """Monte un périphérique."""
        try:
            subprocess.run(
                ["udisksctl", "mount", "-b", device],
                check=True, capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Erreur mount: {e.stderr}")
            return False

    @staticmethod
    def unmount_drive(device: str) -> bool:
        """Démonte un périphérique."""
        try:
            subprocess.run(
                ["udisksctl", "unmount", "-b", device],
                check=True, capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Erreur unmount: {e.stderr}")
            return False

    @staticmethod
    def power_off_drive(device: str) -> bool:
        """Éteint (power-off) un périphérique pour retrait sécurisé."""
        try:
            subprocess.run(
                ["udisksctl", "power-off", "-b", device],
                check=True, capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Erreur power-off: {e.stderr}")
            return False

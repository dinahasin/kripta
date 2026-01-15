import json
import subprocess
from dataclasses import dataclass
from typing import List, Optional
import logging
import shutil
import platform
import os

@dataclass
class DriveInfo:
    device: str          # /dev/sdb1 (Linux) or C: (Windows)
    name: str            # Label or model
    size: str            # Human readable size (capacity from lsblk)
    mountpoint: str      # /media/user/usb or C:\ or empty
    type: str            # ext4, ntfs, etc.
    is_mounted: bool
    is_removable: bool
    is_system: bool      # True if it's the root drive or swap
    # New fields for usage stats
    total_size: int = 0
    used_size: int = 0
    free_size: int = 0
    percent: float = 0.0

class DriveService:
    """
    Gestionnaire de disques multiplateforme (Windows et Linux).
    Permet de lister, monter, démonter et éjecter des disques.
    """
    
    @staticmethod
    def get_drives() -> List[DriveInfo]:
        """Récupère la liste des disques et partitions pertinents."""
        system = platform.system()
        
        if system == "Windows":
            return DriveService._get_drives_windows()
        elif system == "Linux":
            return DriveService._get_drives_linux()
        else:
            logging.warning(f"Système d'exploitation non supporté: {system}")
            return []
    
    @staticmethod
    def _get_drives_windows() -> List[DriveInfo]:
        """Récupère la liste des disques sous Windows."""
        drives = []
        try:
            # Utiliser PowerShell pour obtenir les informations sur les disques
            # Get-Volume donne des informations sur les volumes montés
            ps_command = """
            Get-Volume | Where-Object {$_.DriveLetter} | ForEach-Object {
                [PSCustomObject]@{
                    DriveLetter = $_.DriveLetter
                    FileSystemLabel = $_.FileSystemLabel
                    FileSystem = $_.FileSystemType
                    SizeGB = [math]::Round($_.Size / 1GB, 2)
                    SizeBytes = $_.Size
                    SizeRemaining = $_.SizeRemaining
                    DriveType = $_.DriveType
                }
            } | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            
            # Parser le JSON retourné
            data = json.loads(result.stdout) if result.stdout.strip() else []
            
            # Si un seul disque, PowerShell retourne un objet, pas une liste
            if isinstance(data, dict):
                data = [data]
            
            for volume in data:
                drive_letter = volume.get("DriveLetter", "")
                if not drive_letter:
                    continue
                    
                device = f"{drive_letter}:"
                mountpoint = f"{drive_letter}:\\"
                
                # Obtenir les stats d'utilisation
                total = volume.get("SizeBytes", 0)
                free = volume.get("SizeRemaining", 0)
                used = total - free if total > 0 else 0
                percent = (used / total) * 100 if total > 0 else 0
                
                # Déterminer le type de disque
                drive_type = volume.get("DriveType", "")
                is_removable = drive_type == "Removable"
                is_system = drive_letter.upper() == "C"  # C: est généralement le disque système
                
                # Nom convivial
                label = volume.get("FileSystemLabel", "")
                name = label if label else f"Disque {drive_letter}"
                
                # Taille formatée
                size_gb = volume.get("SizeGB", 0)
                size_str = f"{size_gb} GB" if size_gb > 0 else "0 GB"
                
                drive = DriveInfo(
                    device=device,
                    name=name,
                    size=size_str,
                    mountpoint=mountpoint,
                    type=volume.get("FileSystem", "Inconnu"),
                    is_mounted=True,  # Sous Windows, si on le voit, il est monté
                    is_removable=is_removable,
                    is_system=is_system,
                    total_size=total,
                    used_size=used,
                    free_size=free,
                    percent=percent
                )
                drives.append(drive)
                
        except subprocess.CalledProcessError as e:
            logging.error(f"Erreur PowerShell lors de la récupération des disques: {e}")
            logging.error(f"Stderr: {e.stderr}")
        except json.JSONDecodeError as e:
            logging.error(f"Erreur de parsing JSON: {e}")
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des disques: {e}")
            
        return drives
    
    @staticmethod
    def _get_drives_linux() -> List[DriveInfo]:
        """Récupère la liste des disques sous Linux."""
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
        """Traite un device et ses enfants récursivement (Linux uniquement)."""
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
        
        # Stats d'usage
        total = 0
        used = 0
        free = 0
        percent = 0.0
        
        if mountpoint:
            try:
                usage = shutil.disk_usage(mountpoint)
                total = usage.total
                used = usage.used
                free = usage.free
                percent = (used / total) * 100 if total > 0 else 0
            except Exception:
                pass
        
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
                is_system=is_system,
                total_size=total,
                used_size=used,
                free_size=free,
                percent=percent
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
        system = platform.system()
        
        if system == "Windows":
            # Sous Windows, les disques sont généralement déjà montés
            # On pourrait implémenter le montage de disques réseau ici si nécessaire
            logging.info("Montage automatique sous Windows")
            return True
        elif system == "Linux":
            try:
                subprocess.run(
                    ["udisksctl", "mount", "-b", device],
                    check=True, capture_output=True
                )
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Erreur mount: {e.stderr}")
                return False
        return False

    @staticmethod
    def unmount_drive(device: str) -> bool:
        """Démonte un périphérique."""
        system = platform.system()
        
        if system == "Windows":
            # Sous Windows, on peut utiliser PowerShell pour éjecter
            try:
                # Extraire la lettre du lecteur (ex: "C:" -> "C")
                drive_letter = device.rstrip(":\\")
                ps_command = f"(New-Object -comObject Shell.Application).Namespace(17).ParseName('{drive_letter}:').InvokeVerb('Eject')"
                subprocess.run(
                    ["powershell", "-Command", ps_command],
                    check=True, capture_output=True
                )
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Erreur unmount Windows: {e.stderr}")
                return False
        elif system == "Linux":
            try:
                subprocess.run(
                    ["udisksctl", "unmount", "-b", device],
                    check=True, capture_output=True
                )
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Erreur unmount: {e.stderr}")
                return False
        return False

    @staticmethod
    def power_off_drive(device: str) -> bool:
        """Éteint (power-off) un périphérique pour retrait sécurisé."""
        system = platform.system()
        
        if system == "Windows":
            # Sous Windows, utiliser l'éjection sécurisée
            return DriveService.unmount_drive(device)
        elif system == "Linux":
            try:
                subprocess.run(
                    ["udisksctl", "power-off", "-b", device],
                    check=True, capture_output=True
                )
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"Erreur power-off: {e.stderr}")
                return False
        return False

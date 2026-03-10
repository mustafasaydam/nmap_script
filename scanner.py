#!/usr/bin/env python3
import subprocess
import json
import datetime
import re
import xml.etree.ElementTree as ET
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

class PortScanner:
    def __init__(self):
        self.nmap_path = "/usr/bin/nmap"  # Kali'de nmap yolu
        
    def scan_targets(self, targets, ports="1-1000", arguments="-sV -T4"):
        """
        Hedef IP'leri nmap komutu ile tarar
        """
        results = {
            'scan_date': datetime.datetime.now().isoformat(),
            'targets': targets,
            'ports_scanned': ports,
            'hosts': {}
        }
        
        console.print(f"[bold cyan]🔍 Tarama başlatılıyor: {targets}[/bold cyan]")
        console.print(f"[dim]Port aralığı: {ports}[/dim]")
        console.print(f"[dim]Nmap argümanları: {arguments}[/dim]")
        
        try:
            # Nmap komutunu hazırla
            cmd = [
                self.nmap_path,
                '-oX', '-',  # XML çıktı
                '-p', ports,
                '--open',  # Sadece açık portlar
            ]
            
            # Argümanları ekle
            cmd.extend(arguments.split())
            cmd.append(targets)
            
            console.print(f"[dim]Çalıştırılan komut: {' '.join(cmd)}[/dim]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("[cyan]Nmap taranıyor...", total=None)
                
                # Nmap'i çalıştır
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    console.print(f"[red]Nmap hatası: {result.stderr}[/red]")
                    return None
                
                progress.update(task, completed=100)
            
            # XML çıktısını parse et
            root = ET.fromstring(result.stdout)
            
            # Hostları işle
            for host in root.findall('host'):
                ip_addr = host.find('address').get('addr')
                
                # Host durumu
                status = host.find('status').get('state')
                if status != 'up':
                    continue
                
                # Hostname
                hostname = 'unknown'
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    hostname_elem = hostnames.find('hostname')
                    if hostname_elem is not None:
                        hostname = hostname_elem.get('name', 'unknown')
                
                host_info = {
                    'hostname': hostname,
                    'state': status,
                    'protocols': {'tcp': {}}  # Şimdilik sadece TCP
                }
                
                # Portları işle
                ports_elem = host.find('ports')
                if ports_elem is not None:
                    for port in ports_elem.findall('port'):
                        port_id = port.get('portid')
                        protocol = port.get('protocol')
                        
                        state_elem = port.find('state')
                        if state_elem is None or state_elem.get('state') != 'open':
                            continue
                        
                        service_elem = port.find('service')
                        
                        port_info = {
                            'state': 'open',
                            'name': service_elem.get('name', 'unknown') if service_elem is not None else 'unknown',
                            'product': service_elem.get('product', '') if service_elem is not None else '',
                            'version': service_elem.get('version', '') if service_elem is not None else '',
                            'extrainfo': service_elem.get('extrainfo', '') if service_elem is not None else ''
                        }
                        
                        if protocol not in host_info['protocols']:
                            host_info['protocols'][protocol] = {}
                        
                        host_info['protocols'][protocol][port_id] = port_info
                
                results['hosts'][ip_addr] = host_info
            
            console.print(f"[bold green]✅ Tarama tamamlandı! {len(results['hosts'])} host bulundu.[/bold green]")
            return results
            
        except subprocess.TimeoutExpired:
            console.print("[bold red]❌ Zaman aşımı! Tarama çok uzun sürdü.[/bold red]")
            return None
        except Exception as e:
            console.print(f"[bold red]❌ Hata: {str(e)}[/bold red]")
            return None
    
    def save_results(self, results, filename=None):
        """Sonuçları JSON olarak kaydet"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        console.print(f"[green]📁 Sonuçlar kaydedildi: {filename}[/green]")
        return filename
    
    def load_results(self, filename):
        """Önceki tarama sonuçlarını yükle"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]❌ Dosya yüklenemedi: {str(e)}[/red]")
            return None
    
    def quick_scan(self, targets):
        """Hızlı tarama (en popüler portlar)"""
        return self.scan_targets(targets, ports="top100", arguments="-sV -T4 --top-ports 100")

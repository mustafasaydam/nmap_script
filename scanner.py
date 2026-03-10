#!/usr/bin/env python3
import subprocess
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import ipaddress
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import print as rprint

console = Console()

class PortScanner:
    def __init__(self):
        self.nmap_path = self._find_nmap()
        
    def _find_nmap(self):
        """Nmap yolunu bul"""
        try:
            # Windows için
            if os.name == 'nt':
                common_paths = [
                    r"C:\Program Files (x86)\Nmap\nmap.exe",
                    r"C:\Program Files\Nmap\nmap.exe"
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        return path
            
            # Linux/Mac için (PATH'te ara)
            result = subprocess.run(['which', 'nmap'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
                
        except Exception as e:
            console.print(f"[yellow]Nmap bulunamadı: {e}[/yellow]")
        
        return 'nmap'  # Varsayılan olarak nmap dene
    
    def scan_targets(self, targets, ports="1-1000"):
        """Hedefleri tara"""
        
        # Nmap komutunu oluştur
        cmd = [
            self.nmap_path,
            '-sS',  # SYN stealth scan
            '-sV',  # Version detection
            '-O',   # OS detection
            '--script', 'default',  # Default script scan
            '-p', ports,
            '-oX', '-',  # XML output to stdout
            '--open',  # Sadece açık portları göster
            targets
        ]
        
        console.print(f"[cyan]🚀 Nmap komutu: {' '.join(cmd)}[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Tarama yapılıyor...", total=None)
            
            try:
                # Nmap çalıştır
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 saat timeout
                
                if result.returncode != 0:
                    console.print(f"[red]Nmap hatası: {result.stderr}[/red]")
                    return None
                
                # XML çıktısını parse et
                return self._parse_nmap_xml(result.stdout)
                
            except subprocess.TimeoutExpired:
                console.print("[red]❌ Tarama zaman aşımına uğradı![/red]")
                return None
            except Exception as e:
                console.print(f"[red]❌ Tarama hatası: {str(e)}[/red]")
                return None
    
    def _parse_nmap_xml(self, xml_output):
        """Nmap XML çıktısını parse et"""
        try:
            root = ET.fromstring(xml_output)
            
            results = {
                'scan_date': datetime.now().isoformat(),
                'command': root.get('args', ''),
                'hosts': {}
            }
            
            # Her host için
            for host in root.findall('host'):
                ip = None
                hostname = ''
                
                # IP adresini bul
                address = host.find('address')
                if address is not None and address.get('addrtype') == 'ipv4':
                    ip = address.get('addr')
                
                if not ip:
                    continue
                
                # Hostname'i bul
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    hostname_elem = hostnames.find('hostname')
                    if hostname_elem is not None:
                        hostname = hostname_elem.get('name', '')
                
                # Portları bul
                ports_info = {'protocols': {}}
                
                ports_elem = host.find('ports')
                if ports_elem is not None:
                    for port in ports_elem.findall('port'):
                        protocol = port.get('protocol', 'tcp')
                        port_id = port.get('portid')
                        
                        # Port durumu
                        state = port.find('state')
                        if state is None or state.get('state') != 'open':
                            continue
                        
                        # Servis bilgisi
                        service = port.find('service')
                        if service is not None:
                            service_info = {
                                'name': service.get('name', 'unknown'),
                                'product': service.get('product', ''),
                                'version': service.get('version', ''),
                                'extrainfo': service.get('extrainfo', ''),
                                'method': service.get('method', ''),
                                'conf': service.get('conf', '')
                            }
                        else:
                            service_info = {
                                'name': 'unknown',
                                'product': '',
                                'version': '',
                                'extrainfo': '',
                                'method': '',
                                'conf': ''
                            }
                        
                        # Protocol bazlı portları ekle
                        if protocol not in ports_info['protocols']:
                            ports_info['protocols'][protocol] = {}
                        
                        ports_info['protocols'][protocol][port_id] = service_info
                
                # OS detection
                os_elem = host.find('os')
                if os_elem is not None:
                    os_match = os_elem.find('osmatch')
                    if os_match is not None:
                        ports_info['os'] = {
                            'name': os_match.get('name', ''),
                            'accuracy': os_match.get('accuracy', ''),
                            'line': os_match.get('line', '')
                        }
                
                results['hosts'][ip] = {
                    'hostname': hostname,
                    'protocols': ports_info.get('protocols', {}),
                    'os': ports_info.get('os', {}),
                    'port_count': sum(len(p) for p in ports_info.get('protocols', {}).values())
                }
            
            return results
            
        except ET.ParseError as e:
            console.print(f"[red]XML parse hatası: {e}[/red]")
            return None
    
    def save_results(self, results):
        """Sonuçları JSON dosyasına kaydet"""
        if not results:
            return None
        
        # Dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]✅ Sonuçlar kaydedildi: {filename}[/green]")
            return filename
            
        except Exception as e:
            console.print(f"[red]❌ Dosya kaydetme hatası: {e}[/red]")
            return None
    
    def load_results(self, filename):
        """JSON dosyasından sonuçları yükle"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]❌ Dosya yükleme hatası: {e}[/red]")
            return None
    
    def display_summary(self, results):
        """Tarama sonuçlarını özetle"""
        if not results:
            return
        
        table = Table(title="📊 Tarama Özeti")
        table.add_column("IP Adresi", style="cyan")
        table.add_column("Hostname", style="green")
        table.add_column("Açık Port", style="yellow")
        table.add_column("Servis", style="magenta")
        table.add_column("Versiyon", style="blue")
        
        total_ports = 0
        for ip, host in results['hosts'].items():
            for protocol, ports in host['protocols'].items():
                for port, service in ports.items():
                    total_ports += 1
                    table.add_row(
                        ip,
                        host['hostname'][:20] if host['hostname'] else '-',
                        f"{port}/{protocol}",
                        service['name'],
                        f"{service['product']} {service['version']}".strip() or '-'
                    )
        
        console.print(f"\n[bold]Toplam Host: {len(results['hosts'])} | Toplam Açık Port: {total_ports}[/bold]")
        console.print(table)

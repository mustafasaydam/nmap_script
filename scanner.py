#!/usr/bin/env python3
import subprocess
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import sys

class PortScanner:
    def __init__(self):
        self.nmap_path = self._find_nmap()
        
    def _find_nmap(self):
        """Nmap yolunu bul"""
        # Kali'de nmap genellikle /usr/bin/nmap
        common_paths = [
            '/usr/bin/nmap',
            '/usr/local/bin/nmap',
            '/bin/nmap'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # PATH'te ara
        try:
            result = subprocess.run(['which', 'nmap'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return 'nmap'  # Varsayılan
    
    def scan_targets(self, targets, ports="1-1000"):
        """Hedefleri tara"""
        
        print(f"\n[+] Nmap taraması başlıyor: {targets}")
        print(f"[+] Port aralığı: {ports}")
        print("-" * 60)
        
        # Nmap komutunu oluştur - Kali için optimize edilmiş
        cmd = [
            self.nmap_path,
            '-sS',      # SYN stealth scan
            '-sV',      # Version detection
            '-O',       # OS detection
            '-T4',      # Daha hızlı tarama
            '--open',   # Sadece açık portlar
            '-p', ports,
            '-oX', '-', # XML output
            targets
        ]
        
        print(f"[+] Komut: {' '.join(cmd)}")
        
        try:
            # Nmap çalıştır
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                print(f"[-] Nmap hatası: {result.stderr}")
                return None
            
            # XML çıktısını parse et
            return self._parse_nmap_xml(result.stdout)
            
        except subprocess.TimeoutExpired:
            print("[-] Tarama zaman aşımına uğradı!")
            return None
        except Exception as e:
            print(f"[-] Tarama hatası: {str(e)}")
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
                            'accuracy': os_match.get('accuracy', '')
                        }
                
                results['hosts'][ip] = {
                    'hostname': hostname,
                    'protocols': ports_info.get('protocols', {}),
                    'os': ports_info.get('os', {}),
                    'port_count': sum(len(p) for p in ports_info.get('protocols', {}).values())
                }
            
            return results
            
        except ET.ParseError as e:
            print(f"[-] XML parse hatası: {e}")
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
            
            print(f"[+] Sonuçlar kaydedildi: {filename}")
            return filename
            
        except Exception as e:
            print(f"[-] Dosya kaydetme hatası: {e}")
            return None
    
    def load_results(self, filename):
        """JSON dosyasından sonuçları yükle"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[-] Dosya yükleme hatası: {e}")
            return None
    
    def display_summary(self, results):
        """Tarama sonuçlarını özetle"""
        if not results:
            return
        
        print("\n" + "="*80)
        print("TARAMA SONUÇLARI".center(80))
        print("="*80)
        
        total_ports = 0
        for ip, host in results['hosts'].items():
            print(f"\n[+] Host: {ip}")
            if host['hostname']:
                print(f"    Hostname: {host['hostname']}")
            if host.get('os', {}).get('name'):
                print(f"    İşletim Sistemi: {host['os']['name']} (Doğruluk: {host['os']['accuracy']}%)")
            
            print("    Açık Portlar:")
            for protocol, ports in host['protocols'].items():
                for port, service in ports.items():
                    total_ports += 1
                    version = f"{service['product']} {service['version']}".strip()
                    if version:
                        print(f"      {port}/{protocol:<8} {service['name']:<15} {version}")
                    else:
                        print(f"      {port}/{protocol:<8} {service['name']}")
        
        print("\n" + "-"*80)
        print(f"Toplam Host: {len(results['hosts'])} | Toplam Açık Port: {total_ports}")
        print("="*80)

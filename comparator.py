#!/usr/bin/env python3
from datetime import datetime
import os

class PortComparator:
    def __init__(self, old_scan, new_scan):
        self.old = old_scan
        self.new = new_scan
        self.differences = {
            'new_hosts': [],
            'removed_hosts': [],
            'new_ports': {},
            'closed_ports': {},
            'service_changes': {}
        }
        
    def compare(self):
        """İki tarama arasındaki farkları bul"""
        
        old_hosts = set(self.old.get('hosts', {}).keys())
        new_hosts = set(self.new.get('hosts', {}).keys())
        
        # Yeni hostlar
        self.differences['new_hosts'] = list(new_hosts - old_hosts)
        
        # Kapanan hostlar
        self.differences['removed_hosts'] = list(old_hosts - new_hosts)
        
        # Ortak hostlardaki port değişiklikleri
        common_hosts = old_hosts & new_hosts
        
        for host in common_hosts:
            old_ports = self._get_ports(self.old['hosts'][host])
            new_ports = self._get_ports(self.new['hosts'][host])
            
            # Yeni portlar
            new_ports_set = new_ports - old_ports
            if new_ports_set:
                self.differences['new_ports'][host] = list(new_ports_set)
            
            # Kapanan portlar
            closed_ports_set = old_ports - new_ports
            if closed_ports_set:
                self.differences['closed_ports'][host] = list(closed_ports_set)
            
            # Servis değişiklikleri
            self._check_service_changes(host)
        
        return self.differences
    
    def _get_ports(self, host_data):
        """Host'taki tüm portları set olarak döndür"""
        ports = set()
        for protocol, port_dict in host_data.get('protocols', {}).items():
            for port in port_dict.keys():
                ports.add((protocol, port))
        return ports
    
    def _check_service_changes(self, host):
        """Servis değişikliklerini kontrol et"""
        old_host = self.old['hosts'][host]
        new_host = self.new['hosts'][host]
        
        changes = []
        
        for protocol in old_host.get('protocols', {}):
            if protocol in new_host.get('protocols', {}):
                old_ports = old_host['protocols'][protocol]
                new_ports = new_host['protocols'][protocol]
                
                # Ortak portlar
                common_ports = set(old_ports.keys()) & set(new_ports.keys())
                
                for port in common_ports:
                    old_service = old_ports[port]
                    new_service = new_ports[port]
                    
                    # Servis bilgisi değişmiş mi?
                    if (old_service['name'] != new_service['name'] or
                        old_service['product'] != new_service['product'] or
                        old_service['version'] != new_service['version']):
                        
                        changes.append({
                            'port': port,
                            'protocol': protocol,
                            'old': old_service,
                            'new': new_service
                        })
        
        if changes:
            self.differences['service_changes'][host] = changes
    
    def generate_report(self):
        """Karşılaştırma raporu oluştur - Terminal çıktısı"""
        
        old_date = datetime.fromisoformat(self.old['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        new_date = datetime.fromisoformat(self.new['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*80)
        print("KARŞILAŞTIRMA RAPORU".center(80))
        print("="*80)
        print(f"İlk Tarama: {old_date}")
        print(f"Son Tarama: {new_date}")
        print("-"*80)
        print(f"Yeni Hostlar    : {len(self.differences['new_hosts'])}")
        print(f"Kapanan Hostlar : {len(self.differences['removed_hosts'])}")
        print(f"Yeni Portlar    : {sum(len(v) for v in self.differences['new_ports'].values())}")
        print(f"Kapanan Portlar : {sum(len(v) for v in self.differences['closed_ports'].values())}")
        print(f"Servis Değişikliği: {sum(len(v) for v in self.differences['service_changes'].values())}")
        print("="*80)
        
        # Yeni Hostlar
        if self.differences['new_hosts']:
            print("\n[+] YENİ HOSTLAR:")
            for host in self.differences['new_hosts']:
                host_data = self.new['hosts'][host]
                ports = self._get_ports(host_data)
                port_list = ', '.join([f"{p[1]}/{p[0]}" for p in ports])
                print(f"  {host} - {host_data['hostname']} - Portlar: {port_list}")
        
        # Kapanan Hostlar
        if self.differences['removed_hosts']:
            print("\n[-] KAPANAN HOSTLAR:")
            for host in self.differences['removed_hosts']:
                host_data = self.old['hosts'][host]
                ports = self._get_ports(host_data)
                port_list = ', '.join([f"{p[1]}/{p[0]}" for p in ports])
                print(f"  {host} - {host_data['hostname']} - Eski Portlar: {port_list}")
        
        # Yeni Portlar
        if self.differences['new_ports']:
            print("\n[+] YENİ AÇILAN PORTLAR:")
            for host, ports in self.differences['new_ports'].items():
                for protocol, port in ports:
                    service = self.new['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    print(f"  {host:15} {port}/{protocol:8} {service['name']:15} {version}")
        
        # Kapanan Portlar
        if self.differences['closed_ports']:
            print("\n[-] KAPANAN PORTLAR:")
            for host, ports in self.differences['closed_ports'].items():
                for protocol, port in ports:
                    service = self.old['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    print(f"  {host:15} {port}/{protocol:8} {service['name']:15} {version}")
        
        # Servis Değişiklikleri
        if self.differences['service_changes']:
            print("\n[*] SERVİS DEĞİŞİKLİKLERİ:")
            for host, changes in self.differences['service_changes'].items():
                for change in changes:
                    old_ver = f"{change['old']['product']} {change['old']['version']}".strip()
                    new_ver = f"{change['new']['product']} {change['new']['version']}".strip()
                    print(f"  {host:15} {change['port']}/{change['protocol']:8}")
                    print(f"      Eski: {change['old']['name']} {old_ver}")
                    print(f"      Yeni: {change['new']['name']} {new_ver}")
        
        # HTML raporu oluştur
        self._generate_html_report()
        
        return self.differences
    
    def _generate_html_report(self):
        """Basit HTML rapor oluştur"""
        
        old_date = datetime.fromisoformat(self.old['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        new_date = datetime.fromisoformat(self.new['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        
        filename = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Port Tarama Karşılaştırma</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 20px 0; }}
        .stat {{ background: #f9f9f9; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat.new {{ border-left: 5px solid #4CAF50; }}
        .stat.removed {{ border-left: 5px solid #f44336; }}
        .new-host {{ color: #4CAF50; }}
        .removed-host {{ color: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #4CAF50; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .date {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Port Tarama Karşılaştırma Raporu</h1>
        <div class="date">
            <p>İlk Tarama: {old_date}</p>
            <p>Son Tarama: {new_date}</p>
        </div>
        
        <div class="stats">
            <div class="stat new">
                <h3>Yeni Host</h3>
                <h2>{len(self.differences['new_hosts'])}</h2>
            </div>
            <div class="stat removed">
                <h3>Kapanan Host</h3>
                <h2>{len(self.differences['removed_hosts'])}</h2>
            </div>
            <div class="stat new">
                <h3>Yeni Port</h3>
                <h2>{sum(len(v) for v in self.differences['new_ports'].values())}</h2>
            </div>
            <div class="stat removed">
                <h3>Kapanan Port</h3>
                <h2>{sum(len(v) for v in self.differences['closed_ports'].values())}</h2>
            </div>
            <div class="stat">
                <h3>Servis Değişikliği</h3>
                <h2>{sum(len(v) for v in self.differences['service_changes'].values())}</h2>
            </div>
        </div>
"""
        
        # Yeni Hostlar
        if self.differences['new_hosts']:
            html += "<h2 class='new-host'>🆕 Yeni Hostlar</h2><table><tr><th>IP</th><th>Hostname</th><th>Portlar</th></tr>"
            for host in self.differences['new_hosts']:
                host_data = self.new['hosts'][host]
                ports = self._get_ports(host_data)
                port_list = ', '.join([f"{p[1]}/{p[0]}" for p in ports])
                html += f"<tr><td>{host}</td><td>{host_data['hostname']}</td><td>{port_list}</td></tr>"
            html += "</table>"
        
        # Yeni Portlar
        if self.differences['new_ports']:
            html += "<h2 class='new-host'>🔓 Yeni Açılan Portlar</h2><table><tr><th>IP</th><th>Port/Proto</th><th>Servis</th><th>Versiyon</th></tr>"
            for host, ports in self.differences['new_ports'].items():
                for protocol, port in ports:
                    service = self.new['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    html += f"<tr><td>{host}</td><td>{port}/{protocol}</td><td>{service['name']}</td><td>{version}</td></tr>"
            html += "</table>"
        
        # Kapanan Portlar
        if self.differences['closed_ports']:
            html += "<h2 class='removed-host'>🔒 Kapanan Portlar</h2><table><tr><th>IP</th><th>Port/Proto</th><th>Eski Servis</th><th>Eski Versiyon</th></tr>"
            for host, ports in self.differences['closed_ports'].items():
                for protocol, port in ports:
                    service = self.old['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    html += f"<tr><td>{host}</td><td>{port}/{protocol}</td><td>{service['name']}</td><td>{version}</td></tr>"
            html += "</table>"
        
        html += """
    </div>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n[+] HTML rapor oluşturuldu: {filename}")
        
        # Firefox ile aç (Kali'de varsayılan)
        try:
            os.system(f"firefox {filename} &")
        except:
            try:
                os.system(f"xdg-open {filename} &")
            except:
                pass

#!/usr/bin/env python3
from datetime import datetime
import os
from html_reporter import HTMLReporter

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
    
    def generate_report(self, show_html=True):
        """Karşılaştırma raporu oluştur"""
        
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
                os_info = host_data.get('os', {}).get('name', 'Bilinmiyor')
                print(f"  {host} - {host_data['hostname']}")
                print(f"      OS: {os_info}")
                print(f"      Portlar: {port_list}")
        
        # Kapanan Hostlar
        if self.differences['removed_hosts']:
            print("\n[-] KAPANAN HOSTLAR:")
            for host in self.differences['removed_hosts']:
                host_data = self.old['hosts'][host]
                ports = self._get_ports(host_data)
                port_list = ', '.join([f"{p[1]}/{p[0]}" for p in ports])
                os_info = host_data.get('os', {}).get('name', 'Bilinmiyor')
                print(f"  {host} - {host_data['hostname']}")
                print(f"      OS: {os_info}")
                print(f"      Eski Portlar: {port_list}")
        
        # Yeni Portlar
        if self.differences['new_ports']:
            print("\n[+] YENİ AÇILAN PORTLAR:")
            for host, ports in self.differences['new_ports'].items():
                print(f"\n  {host}:")
                for protocol, port in sorted(ports, key=lambda x: int(x[1])):
                    service = self.new['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    extrainfo = f" ({service['extrainfo']})" if service['extrainfo'] else ""
                    print(f"      {port}/{protocol:<8} {service['name']:<15} {version}{extrainfo}")
        
        # Kapanan Portlar
        if self.differences['closed_ports']:
            print("\n[-] KAPANAN PORTLAR:")
            for host, ports in self.differences['closed_ports'].items():
                print(f"\n  {host}:")
                for protocol, port in sorted(ports, key=lambda x: int(x[1])):
                    service = self.old['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    extrainfo = f" ({service['extrainfo']})" if service['extrainfo'] else ""
                    print(f"      {port}/{protocol:<8} {service['name']:<15} {version}{extrainfo}")
        
        # Servis Değişiklikleri
        if self.differences['service_changes']:
            print("\n[*] SERVİS DEĞİŞİKLİKLERİ:")
            for host, changes in self.differences['service_changes'].items():
                print(f"\n  {host}:")
                for change in changes:
                    old_ver = f"{change['old']['product']} {change['old']['version']}".strip()
                    new_ver = f"{change['new']['product']} {change['new']['version']}".strip()
                    old_extra = f" ({change['old']['extrainfo']})" if change['old']['extrainfo'] else ""
                    new_extra = f" ({change['new']['extrainfo']})" if change['new']['extrainfo'] else ""
                    print(f"      {change['port']}/{change['protocol']}:")
                    print(f"          Eski: {change['old']['name']} {old_ver}{old_extra}")
                    print(f"          Yeni: {change['new']['name']} {new_ver}{new_extra}")
        
        # HTML Raporu
        if show_html:
            reporter = HTMLReporter(self.old, self.new, self.differences)
            reporter.generate_html()
        
        return self.differences

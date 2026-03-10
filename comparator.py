#!/usr/bin/env python3
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from datetime import datetime
from html_reporter import HTMLReporter

console = Console()

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
        
        # Özet Panel
        summary = f"""
[bold cyan]📅 İlk Tarama:[/bold cyan] {old_date}
[bold cyan]📅 Son Tarama:[/bold cyan] {new_date}

[bold green]🆕 Yeni Hostlar:[/bold green] {len(self.differences['new_hosts'])}
[bold red]❌ Kapanan Hostlar:[/bold red] {len(self.differences['removed_hosts'])}
[bold yellow]🔓 Yeni Portlar:[/bold yellow] {sum(len(v) for v in self.differences['new_ports'].values())}
[bold blue]🔒 Kapanan Portlar:[/bold blue] {sum(len(v) for v in self.differences['closed_ports'].values())}
        """
        
        console.print(Panel(summary, title="📊 Karşılaştırma Özeti", border_style="cyan"))
        
        # Yeni Hostlar
        if self.differences['new_hosts']:
            table = Table(title="🆕 Yeni Hostlar")
            table.add_column("IP Adresi", style="green")
            table.add_column("Hostname", style="cyan")
            table.add_column("Açık Portlar", style="yellow")
            
            for host in self.differences['new_hosts']:
                host_data = self.new['hosts'][host]
                ports = self._get_ports(host_data)
                port_list = ', '.join([f"{p[1]}/{p[0]}" for p in ports])
                table.add_row(host, host_data['hostname'], port_list[:50])
            
            console.print(table)
        
        # Kapanan Hostlar
        if self.differences['removed_hosts']:
            table = Table(title="❌ Kapanan Hostlar")
            table.add_column("IP Adresi", style="red")
            table.add_column("Hostname", style="cyan")
            table.add_column("Eski Portlar", style="yellow")
            
            for host in self.differences['removed_hosts']:
                host_data = self.old['hosts'][host]
                ports = self._get_ports(host_data)
                port_list = ', '.join([f"{p[1]}/{p[0]}" for p in ports])
                table.add_row(host, host_data['hostname'], port_list[:50])
            
            console.print(table)
        
        # Yeni Portlar
        if self.differences['new_ports']:
            table = Table(title="🔓 Yeni Açılan Portlar")
            table.add_column("IP Adresi", style="green")
            table.add_column("Port/Proto", style="yellow")
            table.add_column("Servis", style="cyan")
            table.add_column("Versiyon", style="magenta")
            
            for host, ports in self.differences['new_ports'].items():
                for protocol, port in ports:
                    service = self.new['hosts'][host]['protocols'][protocol][port]
                    table.add_row(
                        host,
                        f"{port}/{protocol}",
                        service['name'],
                        f"{service['product']} {service['version']}".strip()
                    )
            
            console.print(table)
        
        # Kapanan Portlar
        if self.differences['closed_ports']:
            table = Table(title="🔒 Kapanan Portlar")
            table.add_column("IP Adresi", style="red")
            table.add_column("Port/Proto", style="yellow")
            table.add_column("Eski Servis", style="cyan")
            table.add_column("Eski Versiyon", style="magenta")
            
            for host, ports in self.differences['closed_ports'].items():
                for protocol, port in ports:
                    service = self.old['hosts'][host]['protocols'][protocol][port]
                    table.add_row(
                        host,
                        f"{port}/{protocol}",
                        service['name'],
                        f"{service['product']} {service['version']}".strip()
                    )
            
            console.print(table)
        
        # Servis Değişiklikleri
        if self.differences['service_changes']:
            table = Table(title="🔄 Servis Değişiklikleri")
            table.add_column("IP Adresi", style="cyan")
            table.add_column("Port/Proto", style="yellow")
            table.add_column("Eski Servis", style="red")
            table.add_column("Yeni Servis", style="green")
            
            for host, changes in self.differences['service_changes'].items():
                for change in changes:
                    old = f"{change['old']['name']} {change['old']['product']} {change['old']['version']}".strip()
                    new = f"{change['new']['name']} {change['new']['product']} {change['new']['version']}".strip()
                    table.add_row(
                        host,
                        f"{change['port']}/{change['protocol']}",
                        old,
                        new
                    )
            
            console.print(table)
        
        # HTML Raporu
        if show_html:
            reporter = HTMLReporter(self.old, self.new, self.differences)
            html_file = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            reporter.generate_html(html_file)
        
        return self.differences

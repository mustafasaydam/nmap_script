#!/usr/bin/env python3
from datetime import datetime
import os
import json

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
        
        # Detaylı HTML rapor oluştur
        self._generate_detailed_html_report(old_date, new_date)
        
        return self.differences
    
    def _generate_detailed_html_report(self, old_date, new_date):
        """Çok detaylı HTML rapor oluştur"""
        
        filename = f"comparison_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # İstatistikler
        total_new_hosts = len(self.differences['new_hosts'])
        total_removed_hosts = len(self.differences['removed_hosts'])
        total_new_ports = sum(len(v) for v in self.differences['new_ports'].values())
        total_closed_ports = sum(len(v) for v in self.differences['closed_ports'].values())
        total_service_changes = sum(len(v) for v in self.differences['service_changes'].values())
        
        # Tüm hostların listesi
        all_hosts = sorted(set(list(self.old['hosts'].keys()) + list(self.new['hosts'].keys())))
        
        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detaylı Port Tarama Karşılaştırma Raporu</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .date-info {{
            display: flex;
            gap: 30px;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 5px solid;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .stat-card.new {{ border-color: #27ae60; }}
        .stat-card.removed {{ border-color: #e74c3c; }}
        .stat-card.changed {{ border-color: #f39c12; }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 10px;
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: white;
        }}
        
        /* Search Box */
        .search-box {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 15px;
            background: #1a1a1a;
            border: 1px solid #444;
            color: white;
            border-radius: 5px;
            font-size: 1.1em;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #3498db;
        }}
        
        /* Host Cards */
        .host-card {{
            background: #2d2d2d;
            border-radius: 10px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .host-header {{
            background: #1a1a1a;
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #444;
        }}
        
        .host-header:hover {{
            background: #333;
        }}
        
        .host-ip {{
            font-size: 1.2em;
            font-weight: bold;
            color: #3498db;
        }}
        
        .hostname {{
            color: #888;
            font-size: 0.9em;
            margin-left: 10px;
        }}
        
        .host-stats {{
            display: flex;
            gap: 20px;
        }}
        
        .host-stat {{
            text-align: center;
            min-width: 60px;
        }}
        
        .host-stat .label {{
            font-size: 0.7em;
            color: #888;
            text-transform: uppercase;
        }}
        
        .host-stat .value {{
            font-size: 1.1em;
            font-weight: bold;
        }}
        
        .host-stat.new .value {{ color: #27ae60; }}
        .host-stat.removed .value {{ color: #e74c3c; }}
        .host-stat.total .value {{ color: #3498db; }}
        
        /* Host Details */
        .host-details {{
            padding: 20px;
            display: none;
            background: #262626;
        }}
        
        .host-details.active {{
            display: block;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: #1a1a1a;
            border-radius: 5px;
            overflow: hidden;
        }}
        
        th {{
            background: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #444;
        }}
        
        tr:hover {{
            background: #333;
        }}
        
        /* Port Status */
        .port-new {{
            background: rgba(39, 174, 96, 0.1);
        }}
        
        .port-closed {{
            background: rgba(231, 76, 60, 0.1);
            text-decoration: line-through;
            opacity: 0.7;
        }}
        
        .port-changed {{
            background: rgba(243, 156, 18, 0.1);
        }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .badge-new {{
            background: #27ae60;
            color: white;
        }}
        
        .badge-closed {{
            background: #e74c3c;
            color: white;
        }}
        
        .badge-changed {{
            background: #f39c12;
            color: black;
        }}
        
        /* Service Info */
        .service-name {{
            font-weight: bold;
            color: #3498db;
        }}
        
        .service-version {{
            color: #888;
            font-size: 0.9em;
        }}
        
        .service-extra {{
            color: #f39c12;
            font-size: 0.85em;
        }}
        
        /* OS Info */
        .os-info {{
            background: #1a1a1a;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 3px solid #3498db;
        }}
        
        /* Expand/Collapse All */
        .controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }}
        
        .btn {{
            padding: 10px 20px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
        }}
        
        .btn:hover {{
            background: #2980b9;
        }}
        
        .btn.secondary {{
            background: #2d2d2d;
            color: #e0e0e0;
        }}
        
        .btn.secondary:hover {{
            background: #3d3d3d;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 20px;
            color: #888;
            margin-top: 30px;
            border-top: 1px solid #444;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .host-header {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .date-info {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
        
        /* Tab Navigation */
        .tab-nav {{
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            background: #2d2d2d;
            padding: 10px;
            border-radius: 10px;
        }}
        
        .tab-btn {{
            padding: 10px 20px;
            background: transparent;
            color: #e0e0e0;
            border: none;
            cursor: pointer;
            font-size: 1em;
            border-radius: 5px;
        }}
        
        .tab-btn.active {{
            background: #3498db;
            color: white;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔍 Detaylı Port Tarama Karşılaştırma Raporu</h1>
            <div class="date-info">
                <div>📅 İlk Tarama: <strong>{old_date}</strong></div>
                <div>📅 Son Tarama: <strong>{new_date}</strong></div>
            </div>
        </div>
        
        <!-- Statistics -->
        <div class="stats-grid">
            <div class="stat-card new">
                <h3>Yeni Hostlar</h3>
                <div class="number">{total_new_hosts}</div>
            </div>
            <div class="stat-card removed">
                <h3>Kapanan Hostlar</h3>
                <div class="number">{total_removed_hosts}</div>
            </div>
            <div class="stat-card new">
                <h3>Yeni Portlar</h3>
                <div class="number">{total_new_ports}</div>
            </div>
            <div class="stat-card removed">
                <h3>Kapanan Portlar</h3>
                <div class="number">{total_closed_ports}</div>
            </div>
            <div class="stat-card changed">
                <h3>Servis Değişikliği</h3>
                <div class="number">{total_service_changes}</div>
            </div>
            <div class="stat-card">
                <h3>Toplam Host</h3>
                <div class="number">{len(all_hosts)}</div>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="controls">
            <button class="btn" onclick="expandAll()">Tümünü Genişlet</button>
            <button class="btn secondary" onclick="collapseAll()">Tümünü Daralt</button>
        </div>
        
        <!-- Search -->
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 IP veya hostname ile ara..." onkeyup="filterHosts()">
        </div>
        
        <!-- Tab Navigation -->
        <div class="tab-nav">
            <button class="tab-btn active" onclick="showTab('all')">Tüm Hostlar</button>
            <button class="tab-btn" onclick="showTab('new')">Yeni Hostlar ({total_new_hosts})</button>
            <button class="tab-btn" onclick="showTab('changed')">Değişen Hostlar</button>
            <button class="tab-btn" onclick="showTab('removed')">Kapanan Hostlar ({total_removed_hosts})</button>
        </div>
        
        <!-- All Hosts Tab -->
        <div id="tab-all" class="tab-content active">
"""
        
        # Tüm hostlar için kartlar
        for host in sorted(all_hosts):
            old_host_data = self.old['hosts'].get(host, {})
            new_host_data = self.new['hosts'].get(host, {})
            
            # Host durumu
            if host in self.differences['new_hosts']:
                status = 'new'
                status_text = 'Yeni Host'
                status_class = 'new'
            elif host in self.differences['removed_hosts']:
                status = 'removed'
                status_text = 'Kapanan Host'
                status_class = 'removed'
            else:
                status = 'existing'
                status_text = 'Mevcut Host'
                status_class = 'existing'
            
            # Host istatistikleri
            old_port_count = len(self._get_ports(old_host_data)) if old_host_data else 0
            new_port_count = len(self._get_ports(new_host_data)) if new_host_data else 0
            
            html += f"""
            <div class="host-card" data-host="{host}" data-hostname="{old_host_data.get('hostname', '')} {new_host_data.get('hostname', '')}" data-status="{status}">
                <div class="host-header" onclick="toggleHost(this)">
                    <div>
                        <span class="host-ip">{host}</span>
                        <span class="hostname">{new_host_data.get('hostname', old_host_data.get('hostname', ''))}</span>
                    </div>
                    <div class="host-stats">
                        <div class="host-stat {status_class}">
                            <div class="label">Durum</div>
                            <div class="value">{status_text}</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">Eski Port</div>
                            <div class="value">{old_port_count}</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">Yeni Port</div>
                            <div class="value">{new_port_count}</div>
                        </div>
                    </div>
                </div>
                
                <div class="host-details">
"""
            
            # OS Bilgisi
            if new_host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>İşletim Sistemi:</strong> {new_host_data['os']['name']} 
                        (Doğruluk: {new_host_data['os']['accuracy']}%)
                    </div>
"""
            elif old_host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>Eski İşletim Sistemi:</strong> {old_host_data['os']['name']} 
                        (Doğruluk: {old_host_data['os']['accuracy']}%)
                    </div>
"""
            
            # Yeni portlar tablosu
            if host in self.differences['new_ports'] and self.differences['new_ports'][host]:
                html += """
                    <h4>🆕 Yeni Açılan Portlar</h4>
                    <table>
                        <tr>
                            <th>Port/Proto</th>
                            <th>Servis</th>
                            <th>Ürün</th>
                            <th>Versiyon</th>
                            <th>Ek Bilgi</th>
                        </tr>
"""
                for protocol, port in sorted(self.differences['new_ports'][host], key=lambda x: int(x[1])):
                    service = new_host_data['protocols'][protocol][port]
                    html += f"""
                        <tr class="port-new">
                            <td><span class="badge badge-new">{port}/{protocol}</span></td>
                            <td class="service-name">{service['name']}</td>
                            <td>{service['product']}</td>
                            <td class="service-version">{service['version']}</td>
                            <td class="service-extra">{service['extrainfo']}</td>
                        </tr>
"""
                html += "</table>"
            
            # Kapanan portlar tablosu
            if host in self.differences['closed_ports'] and self.differences['closed_ports'][host]:
                html += """
                    <h4>🔒 Kapanan Portlar</h4>
                    <table>
                        <tr>
                            <th>Port/Proto</th>
                            <th>Servis</th>
                            <th>Ürün</th>
                            <th>Versiyon</th>
                            <th>Ek Bilgi</th>
                        </tr>
"""
                for protocol, port in sorted(self.differences['closed_ports'][host], key=lambda x: int(x[1])):
                    service = old_host_data['protocols'][protocol][port]
                    html += f"""
                        <tr class="port-closed">
                            <td><span class="badge badge-closed">{port}/{protocol}</span></td>
                            <td>{service['name']}</td>
                            <td>{service['product']}</td>
                            <td>{service['version']}</td>
                            <td>{service['extrainfo']}</td>
                        </tr>
"""
                html += "</table>"
            
            # Servis değişiklikleri
            if host in self.differences['service_changes'] and self.differences['service_changes'][host]:
                html += """
                    <h4>🔄 Servis Değişiklikleri</h4>
                    <table>
                        <tr>
                            <th>Port/Proto</th>
                            <th colspan="2">Değişim</th>
                        </tr>
"""
                for change in self.differences['service_changes'][host]:
                    html += f"""
                        <tr class="port-changed">
                            <td><span class="badge badge-changed">{change['port']}/{change['protocol']}</span></td>
                            <td style="width: 50%;">
                                <div style="color: #e74c3c;">❌ Eski:</div>
                                <div class="service-name">{change['old']['name']}</div>
                                <div class="service-version">{change['old']['product']} {change['old']['version']}</div>
                                <div class="service-extra">{change['old']['extrainfo']}</div>
                            </td>
                            <td style="width: 50%;">
                                <div style="color: #27ae60;">✅ Yeni:</div>
                                <div class="service-name">{change['new']['name']}</div>
                                <div class="service-version">{change['new']['product']} {change['new']['version']}</div>
                                <div class="service-extra">{change['new']['extrainfo']}</div>
                            </td>
                        </tr>
"""
                html += "</table>"
            
            # Tüm portlar (değişmeyenler)
            if host in new_host_data:
                unchanged_ports = []
                for protocol, ports in new_host_data.get('protocols', {}).items():
                    for port, service in ports.items():
                        if (host not in self.differences['new_ports'] or (protocol, port) not in self.differences['new_ports'][host]):
                            unchanged_ports.append((protocol, port, service))
                
                if unchanged_ports:
                    html += """
                        <h4>📌 Değişmeyen Portlar</h4>
                        <table>
                            <tr>
                                <th>Port/Proto</th>
                                <th>Servis</th>
                                <th>Ürün</th>
                                <th>Versiyon</th>
                                <th>Ek Bilgi</th>
                            </tr>
"""
                    for protocol, port, service in sorted(unchanged_ports, key=lambda x: int(x[1])):
                        html += f"""
                            <tr>
                                <td>{port}/{protocol}</td>
                                <td>{service['name']}</td>
                                <td>{service['product']}</td>
                                <td>{service['version']}</td>
                                <td>{service['extrainfo']}</td>
                            </tr>
"""
                    html += "</table>"
            
            html += """
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <!-- New Hosts Tab -->
        <div id="tab-new" class="tab-content">
"""
        for host in sorted(self.differences['new_hosts']):
            host_data = self.new['hosts'][host]
            html += f"""
            <div class="host-card">
                <div class="host-header" onclick="toggleHost(this)">
                    <div>
                        <span class="host-ip">{host}</span>
                        <span class="hostname">{host_data.get('hostname', '')}</span>
                    </div>
                    <div class="host-stats">
                        <div class="host-stat new">
                            <div class="label">Durum</div>
                            <div class="value">Yeni Host</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">Açık Port</div>
                            <div class="value">{len(self._get_ports(host_data))}</div>
                        </div>
                    </div>
                </div>
                
                <div class="host-details">
"""
            if host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>İşletim Sistemi:</strong> {host_data['os']['name']} 
                        (Doğruluk: {host_data['os']['accuracy']}%)
                    </div>
"""
            
            html += """
                    <h4>🔓 Açık Portlar</h4>
                    <table>
                        <tr>
                            <th>Port/Proto</th>
                            <th>Servis</th>
                            <th>Ürün</th>
                            <th>Versiyon</th>
                            <th>Ek Bilgi</th>
                        </tr>
"""
            for protocol, ports in host_data.get('protocols', {}).items():
                for port, service in sorted(ports.items(), key=lambda x: int(x[0])):
                    html += f"""
                        <tr>
                            <td>{port}/{protocol}</td>
                            <td>{service['name']}</td>
                            <td>{service['product']}</td>
                            <td>{service['version']}</td>
                            <td>{service['extrainfo']}</td>
                        </tr>
"""
            html += """
                    </table>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <!-- Removed Hosts Tab -->
        <div id="tab-removed" class="tab-content">
"""
        for host in sorted(self.differences['removed_hosts']):
            host_data = self.old['hosts'][host]
            html += f"""
            <div class="host-card">
                <div class="host-header" onclick="toggleHost(this)">
                    <div>
                        <span class="host-ip">{host}</span>
                        <span class="hostname">{host_data.get('hostname', '')}</span>
                    </div>
                    <div class="host-stats">
                        <div class="host-stat removed">
                            <div class="label">Durum</div>
                            <div class="value">Kapanan Host</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">Eski Port</div>
                            <div class="value">{len(self._get_ports(host_data))}</div>
                        </div>
                    </div>
                </div>
                
                <div class="host-details">
"""
            if host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>Eski İşletim Sistemi:</strong> {host_data['os']['name']} 
                        (Doğruluk: {host_data['os']['accuracy']}%)
                    </div>
"""
            
            html += """
                    <h4>🔒 Kapanan Portlar</h4>
                    <table>
                        <tr>
                            <th>Port/Proto</th>
                            <th>Servis</th>
                            <th>Ürün</th>
                            <th>Versiyon</th>
                            <th>Ek Bilgi</th>
                        </tr>
"""
            for protocol, ports in host_data.get('protocols', {}).items():
                for port, service in sorted(ports.items(), key=lambda x: int(x[0])):
                    html += f"""
                        <tr>
                            <td>{port}/{protocol}</td>
                            <td>{service['name']}</td>
                            <td>{service['product']}</td>
                            <td>{service['version']}</td>
                            <td>{service['extrainfo']}</td>
                        </tr>
"""
            html += """
                    </table>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <!-- Changed Hosts Tab -->
        <div id="tab-changed" class="tab-content">
"""
        for host, changes in self.differences['service_changes'].items():
            html += f"""
            <div class="host-card">
                <div class="host-header" onclick="toggleHost(this)">
                    <div>
                        <span class="host-ip">{host}</span>
                        <span class="hostname">{self.new['hosts'][host].get('hostname', '')}</span>
                    </div>
                    <div class="host-stats">
                        <div class="host-stat changed">
                            <div class="label">Değişen</div>
                            <div class="value">{len(changes)}</div>
                        </div>
                    </div>
                </div>
                
                <div class="host-details">
                    <h4>🔄 Servis Değişiklikleri</h4>
                    <table>
                        <tr>
                            <th>Port/Proto</th>
                            <th colspan="2">Değişim</th>
                        </tr>
"""
            for change in changes:
                html += f"""
                        <tr>
                            <td><span class="badge badge-changed">{change['port']}/{change['protocol']}</span></td>
                            <td style="width: 50%;">
                                <div style="color: #e74c3c;">❌ Eski:</div>
                                <div class="service-name">{change['old']['name']}</div>
                                <div class="service-version">{change['old']['product']} {change['old']['version']}</div>
                                <div class="service-extra">{change['old']['extrainfo']}</div>
                            </td>
                            <td style="width: 50%;">
                                <div style="color: #27ae60;">✅ Yeni:</div>
                                <div class="service-name">{change['new']['name']}</div>
                                <div class="service-version">{change['new']['product']} {change['new']['version']}</div>
                                <div class="service-extra">{change['new']['extrainfo']}</div>
                            </td>
                        </tr>
"""
            html += """
                    </table>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Rapor Oluşturulma: {}</p>
            <p>🔧 Internal Network Security Scanner - Detaylı Karşılaştırma Raporu</p>
        </div>
    </div>
    
    <script>
        // Toggle host details
        function toggleHost(element) {{
            const details = element.nextElementSibling;
            details.classList.toggle('active');
        }}
        
        // Expand all hosts
        function expandAll() {{
            const details = document.querySelectorAll('.host-details');
            details.forEach(d => d.classList.add('active'));
        }}
        
        // Collapse all hosts
        function collapseAll() {{
            const details = document.querySelectorAll('.host-details');
            details.forEach(d => d.classList.remove('active'));
        }}
        
        // Filter hosts
        function filterHosts() {{
            const searchText = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.host-card');
            
            cards.forEach(card => {{
                const host = card.getAttribute('data-host').toLowerCase();
                const hostname = card.getAttribute('data-hostname').toLowerCase();
                
                if (host.includes(searchText) || hostname.includes(searchText)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
        
        // Tab switching
        function showTab(tabName) {{
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById('tab-' + tabName).classList.add('active');
            
            // Update tab buttons
            const buttons = document.querySelectorAll('.tab-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n[+] Detaylı HTML rapor oluşturuldu: {filename}")
        print(f"[+] Rapor {os.path.abspath(filename)} adresinde kaydedildi")
        
        # Firefox ile aç (Kali'de varsayılan)
        try:
            os.system(f"firefox {filename} &")
            print("[+] Rapor Firefox ile açılıyor...")
        except:
            try:
                os.system(f"xdg-open {filename} &")
                print("[+] Rapor varsayılan tarayıcı ile açılıyor...")
            except:
                pass

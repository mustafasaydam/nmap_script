#!/usr/bin/env python3
import os
from datetime import datetime

class HTMLReporter:
    def __init__(self, old_scan, new_scan, differences):
        self.old = old_scan
        self.new = new_scan
        self.diffs = differences
        
    def _get_ports(self, host_data):
        """Host'taki tüm portları set olarak döndür"""
        ports = set()
        for protocol, port_dict in host_data.get('protocols', {}).items():
            for port in port_dict.keys():
                ports.add((protocol, port))
        return ports
    
    def generate_html(self, filename=None):
        """HTML rapor oluştur"""
        
        if not filename:
            filename = f"comparison_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        old_date = datetime.fromisoformat(self.old['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        new_date = datetime.fromisoformat(self.new['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        
        # İstatistikler
        total_new_hosts = len(self.diffs.get('new_hosts', []))
        total_removed_hosts = len(self.diffs.get('removed_hosts', []))
        total_new_ports = sum(len(v) for v in self.diffs.get('new_ports', {}).values())
        total_closed_ports = sum(len(v) for v in self.diffs.get('closed_ports', {}).values())
        total_service_changes = sum(len(v) for v in self.diffs.get('service_changes', {}).values())
        
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
            background: linear-gradient(135deg, #2c3e50, #34495e);
            padding: 20px 25px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #444;
            transition: all 0.3s;
        }}
        
        .host-header:hover {{
            background: linear-gradient(135deg, #34495e, #3d566e);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        
        .host-ip {{
            font-size: 1.3em;
            font-weight: bold;
            color: #3498db;
        }}
        
        .hostname {{
            color: #888;
            font-size: 1em;
            margin-left: 15px;
            font-style: italic;
        }}
        
        .host-stats {{
            display: flex;
            gap: 25px;
        }}
        
        .host-stat {{
            text-align: center;
            min-width: 70px;
            padding: 5px 10px;
            border-radius: 5px;
            background: rgba(0,0,0,0.3);
        }}
        
        .host-stat .label {{
            font-size: 0.8em;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .host-stat .value {{
            font-size: 1.3em;
            font-weight: bold;
        }}
        
        .host-stat.new .value {{ color: #27ae60; }}
        .host-stat.removed .value {{ color: #e74c3c; }}
        .host-stat.changed .value {{ color: #f39c12; }}
        .host-stat.total .value {{ color: #3498db; }}
        
        /* Host Details */
        .host-details {{
            padding: 30px;
            background: #262626;
            border-top: 1px solid #444;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background: #1e1e1e;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        th {{
            background: #3498db;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 1.1em;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #444;
            color: #e0e0e0;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        tr:hover {{
            background: #333;
        }}
        
        /* Section Headers */
        h4 {{
            color: #3498db;
            font-size: 1.3em;
            margin: 25px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #3498db;
        }}
        
        h4:first-child {{
            margin-top: 0;
        }}
        
        /* Port Status */
        .port-new {{
            background: rgba(39, 174, 96, 0.15);
            border-left: 4px solid #27ae60;
        }}
        
        .port-closed {{
            background: rgba(231, 76, 60, 0.15);
            border-left: 4px solid #e74c3c;
            opacity: 0.8;
        }}
        
        .port-changed {{
            background: rgba(243, 156, 18, 0.15);
            border-left: 4px solid #f39c12;
        }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            text-align: center;
            min-width: 90px;
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
            font-size: 1.1em;
        }}
        
        .service-product {{
            color: #27ae60;
        }}
        
        .service-version {{
            color: #e67e22;
        }}
        
        .service-extra {{
            color: #f39c12;
            font-size: 0.9em;
            font-style: italic;
        }}
        
        /* OS Info */
        .os-info {{
            background: #1e1e1e;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            border-left: 5px solid #f39c12;
            font-size: 1.1em;
        }}
        
        /* Expand/Collapse All */
        .controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }}
        
        .btn {{
            padding: 12px 25px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s;
        }}
        
        .btn:hover {{
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
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
            padding: 25px;
            color: #888;
            margin-top: 40px;
            border-top: 1px solid #444;
            font-size: 0.95em;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .host-header {{
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }}
            
            .host-stats {{
                flex-wrap: wrap;
                justify-content: center;
            }}
            
            .date-info {{
                flex-direction: column;
                gap: 10px;
            }}
            
            table {{
                font-size: 0.9em;
            }}
            
            td, th {{
                padding: 8px;
            }}
        }}
        
        /* Tab Navigation */
        .tab-nav {{
            display: flex;
            gap: 5px;
            margin-bottom: 25px;
            background: #2d2d2d;
            padding: 10px;
            border-radius: 10px;
            flex-wrap: wrap;
        }}
        
        .tab-btn {{
            padding: 12px 25px;
            background: transparent;
            color: #e0e0e0;
            border: none;
            cursor: pointer;
            font-size: 1em;
            border-radius: 5px;
            transition: all 0.3s;
            flex: 1;
            min-width: 120px;
        }}
        
        .tab-btn:hover {{
            background: #3d3d3d;
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
        
        /* Summary Cards */
        .summary-card {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 5px solid #3498db;
        }}
        
        .summary-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 10px;
        }}
        
        .summary-stats {{
            display: flex;
            gap: 20px;
            color: #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔍 Detaylı Port Tarama Karşılaştırma Raporu</h1>
            <div class="date-info">
                <div>📅 <strong>İlk Tarama:</strong> {old_date}</div>
                <div>📅 <strong>Son Tarama:</strong> {new_date}</div>
            </div>
        </div>
        
        <!-- Statistics -->
        <div class="stats-grid">
            <div class="stat-card new">
                <h3>🆕 YENİ HOSTLAR</h3>
                <div class="number">{total_new_hosts}</div>
            </div>
            <div class="stat-card removed">
                <h3>❌ KAPANAN HOSTLAR</h3>
                <div class="number">{total_removed_hosts}</div>
            </div>
            <div class="stat-card new">
                <h3>🔓 YENİ PORTLAR</h3>
                <div class="number">{total_new_ports}</div>
            </div>
            <div class="stat-card removed">
                <h3>🔒 KAPANAN PORTLAR</h3>
                <div class="number">{total_closed_ports}</div>
            </div>
            <div class="stat-card changed">
                <h3>🔄 SERVİS DEĞİŞİKLİĞİ</h3>
                <div class="number">{total_service_changes}</div>
            </div>
            <div class="stat-card">
                <h3>📊 TOPLAM HOST</h3>
                <div class="number">{len(all_hosts)}</div>
            </div>
        </div>
        
        <!-- Quick Summary -->
        <div class="summary-card">
            <div class="summary-title">📋 Hızlı Özet</div>
            <div class="summary-stats">
                <div>🆕 Yeni Hostlar: {total_new_hosts}</div>
                <div>❌ Kapanan Hostlar: {total_removed_hosts}</div>
                <div>🔓 Yeni Portlar: {total_new_ports}</div>
                <div>🔒 Kapanan Portlar: {total_closed_ports}</div>
                <div>🔄 Değişen Servisler: {total_service_changes}</div>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="controls">
            <button class="btn" onclick="expandAll()">🔽 Tümünü Genişlet</button>
            <button class="btn secondary" onclick="collapseAll()">🔼 Tümünü Daralt</button>
        </div>
        
        <!-- Search -->
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 IP, hostname veya port ara..." onkeyup="filterHosts()">
        </div>
        
        <!-- Tab Navigation -->
        <div class="tab-nav">
            <button class="tab-btn active" onclick="showTab('all')">📋 Tüm Hostlar ({len(all_hosts)})</button>
            <button class="tab-btn" onclick="showTab('new')">🆕 Yeni Hostlar ({total_new_hosts})</button>
            <button class="tab-btn" onclick="showTab('changed')">🔄 Değişen Servisler ({total_service_changes})</button>
            <button class="tab-btn" onclick="showTab('removed')">❌ Kapanan Hostlar ({total_removed_hosts})</button>
        </div>
        
        <!-- ALL HOSTS TAB -->
        <div id="tab-all" class="tab-content active">
"""
        
        # TÜM HOSTLAR (detaylı)
        for host in sorted(all_hosts):
            old_host_data = self.old['hosts'].get(host, {})
            new_host_data = self.new['hosts'].get(host, {})
            
            # Host durumu
            if host in self.diffs['new_hosts']:
                status_class = 'new'
                status_text = '🆕 YENİ HOST'
            elif host in self.diffs['removed_hosts']:
                status_class = 'removed'
                status_text = '❌ KAPANAN HOST'
            else:
                status_class = 'existing'
                status_text = '📌 MEVCUT HOST'
            
            # Port sayıları
            old_port_count = len(self._get_ports(old_host_data)) if old_host_data else 0
            new_port_count = len(self._get_ports(new_host_data)) if new_host_data else 0
            
            # Host başlığı
            html += f"""
            <div class="host-card" data-host="{host}" data-hostname="{old_host_data.get('hostname', '')} {new_host_data.get('hostname', '')}">
                <div class="host-header" onclick="toggleHost(this)">
                    <div>
                        <span class="host-ip">{host}</span>
                        <span class="hostname">{new_host_data.get('hostname', old_host_data.get('hostname', ''))}</span>
                    </div>
                    <div class="host-stats">
                        <div class="host-stat {status_class}">
                            <div class="label">DURUM</div>
                            <div class="value">{status_text}</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">ESKİ PORT</div>
                            <div class="value">{old_port_count}</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">YENİ PORT</div>
                            <div class="value">{new_port_count}</div>
                        </div>
                    </div>
                </div>
                
                <!-- Host Detayları -->
                <div class="host-details" style="display: block;">
            """
            
            # OS Bilgisi
            if new_host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>💻 İşletim Sistemi:</strong> {new_host_data['os']['name']} 
                        (Doğruluk: {new_host_data['os']['accuracy']}%)
                    </div>
                """
            elif old_host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>💻 Eski İşletim Sistemi:</strong> {old_host_data['os']['name']} 
                        (Doğruluk: {old_host_data['os']['accuracy']}%)
                    </div>
                """
            
            # YENİ PORTLAR
            if host in self.diffs['new_ports'] and self.diffs['new_ports'][host]:
                html += """
                    <h4>🆕 YENİ AÇILAN PORTLAR</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Port/Proto</th>
                                <th>Servis</th>
                                <th>Ürün</th>
                                <th>Versiyon</th>
                                <th>Ek Bilgi</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for protocol, port in sorted(self.diffs['new_ports'][host], key=lambda x: int(x[1])):
                    service = new_host_data['protocols'][protocol][port]
                    html += f"""
                            <tr class="port-new">
                                <td><span class="badge badge-new">{port}/{protocol}</span></td>
                                <td class="service-name">{service['name']}</td>
                                <td class="service-product">{service['product']}</td>
                                <td class="service-version">{service['version']}</td>
                                <td class="service-extra">{service['extrainfo']}</td>
                            </tr>
                    """
                html += "</tbody></table>"
            
            # KAPANAN PORTLAR
            if host in self.diffs['closed_ports'] and self.diffs['closed_ports'][host]:
                html += """
                    <h4>🔒 KAPANAN PORTLAR</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Port/Proto</th>
                                <th>Servis</th>
                                <th>Ürün</th>
                                <th>Versiyon</th>
                                <th>Ek Bilgi</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for protocol, port in sorted(self.diffs['closed_ports'][host], key=lambda x: int(x[1])):
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
                html += "</tbody></table>"
            
            # SERVİS DEĞİŞİKLİKLERİ
            if host in self.diffs['service_changes'] and self.diffs['service_changes'][host]:
                html += """
                    <h4>🔄 SERVİS DEĞİŞİKLİKLERİ</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Port/Proto</th>
                                <th>Eski Servis</th>
                                <th>Yeni Servis</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for change in self.diffs['service_changes'][host]:
                    html += f"""
                            <tr class="port-changed">
                                <td><span class="badge badge-changed">{change['port']}/{change['protocol']}</span></td>
                                <td>
                                    <span class="service-name">{change['old']['name']}</span><br>
                                    <span class="service-product">{change['old']['product']}</span>
                                    <span class="service-version">{change['old']['version']}</span><br>
                                    <span class="service-extra">{change['old']['extrainfo']}</span>
                                </td>
                                <td>
                                    <span class="service-name">{change['new']['name']}</span><br>
                                    <span class="service-product">{change['new']['product']}</span>
                                    <span class="service-version">{change['new']['version']}</span><br>
                                    <span class="service-extra">{change['new']['extrainfo']}</span>
                                </td>
                            </tr>
                    """
                html += "</tbody></table>"
            
            # TÜM AÇIK PORTLAR (mevcut durum)
            if new_host_data:
                all_ports = []
                for protocol, ports in new_host_data.get('protocols', {}).items():
                    for port, service in ports.items():
                        all_ports.append((protocol, port, service))
                
                if all_ports:
                    html += """
                        <h4>📋 TÜM AÇIK PORTLAR (GÜNCEL DURUM)</h4>
                        <table>
                            <thead>
                                <tr>
                                    <th>Port/Proto</th>
                                    <th>Servis</th>
                                    <th>Ürün</th>
                                    <th>Versiyon</th>
                                    <th>Ek Bilgi</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                    for protocol, port, service in sorted(all_ports, key=lambda x: int(x[1])):
                        html += f"""
                            <tr>
                                <td><strong>{port}/{protocol}</strong></td>
                                <td class="service-name">{service['name']}</td>
                                <td class="service-product">{service['product']}</td>
                                <td class="service-version">{service['version']}</td>
                                <td class="service-extra">{service['extrainfo']}</td>
                            </tr>
                        """
                    html += "</tbody></table>"
            
            html += """
                </div>
            </div>
            """
        
        html += """
        </div> <!-- tab-all sonu -->
        
        <!-- YENİ HOSTLAR TAB -->
        <div id="tab-new" class="tab-content">
        """
        
        # Sadece yeni hostlar
        for host in sorted(self.diffs['new_hosts']):
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
                            <div class="label">DURUM</div>
                            <div class="value">🆕 YENİ HOST</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">AÇIK PORT</div>
                            <div class="value">{len(self._get_ports(host_data))}</div>
                        </div>
                    </div>
                </div>
                <div class="host-details" style="display: block;">
            """
            
            if host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>💻 İşletim Sistemi:</strong> {host_data['os']['name']} 
                        (Doğruluk: {host_data['os']['accuracy']}%)
                    </div>
                """
            
            html += """
                    <h4>🔓 AÇIK PORTLAR</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Port/Proto</th>
                                <th>Servis</th>
                                <th>Ürün</th>
                                <th>Versiyon</th>
                                <th>Ek Bilgi</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for protocol, ports in host_data.get('protocols', {}).items():
                for port, service in sorted(ports.items(), key=lambda x: int(x[0])):
                    html += f"""
                            <tr>
                                <td><strong>{port}/{protocol}</strong></td>
                                <td class="service-name">{service['name']}</td>
                                <td class="service-product">{service['product']}</td>
                                <td class="service-version">{service['version']}</td>
                                <td class="service-extra">{service['extrainfo']}</td>
                            </tr>
                    """
            html += """
                        </tbody>
                    </table>
                </div>
            </div>
            """
        
        html += """
        </div> <!-- tab-new sonu -->
        
        <!-- KAPANAN HOSTLAR TAB -->
        <div id="tab-removed" class="tab-content">
        """
        
        # Sadece kapanan hostlar
        for host in sorted(self.diffs['removed_hosts']):
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
                            <div class="label">DURUM</div>
                            <div class="value">❌ KAPANAN HOST</div>
                        </div>
                        <div class="host-stat total">
                            <div class="label">ESKİ PORT</div>
                            <div class="value">{len(self._get_ports(host_data))}</div>
                        </div>
                    </div>
                </div>
                <div class="host-details" style="display: block;">
            """
            
            if host_data.get('os', {}).get('name'):
                html += f"""
                    <div class="os-info">
                        <strong>💻 Eski İşletim Sistemi:</strong> {host_data['os']['name']} 
                        (Doğruluk: {host_data['os']['accuracy']}%)
                    </div>
                """
            
            html += """
                    <h4>🔒 ESKİ AÇIK PORTLAR</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Port/Proto</th>
                                <th>Servis</th>
                                <th>Ürün</th>
                                <th>Versiyon</th>
                                <th>Ek Bilgi</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for protocol, ports in host_data.get('protocols', {}).items():
                for port, service in sorted(ports.items(), key=lambda x: int(x[0])):
                    html += f"""
                            <tr>
                                <td><strong>{port}/{protocol}</strong></td>
                                <td>{service['name']}</td>
                                <td>{service['product']}</td>
                                <td>{service['version']}</td>
                                <td>{service['extrainfo']}</td>
                            </tr>
                    """
            html += """
                        </tbody>
                    </table>
                </div>
            </div>
            """
        
        html += """
        </div> <!-- tab-removed sonu -->
        
        <!-- DEĞİŞEN SERVİSLER TAB -->
        <div id="tab-changed" class="tab-content">
        """
        
        # Sadece servis değişikliği olan hostlar
        changed_hosts = sorted(self.diffs['service_changes'].keys())
        for host in changed_hosts:
            changes = self.diffs['service_changes'][host]
            html += f"""
            <div class="host-card">
                <div class="host-header" onclick="toggleHost(this)">
                    <div>
                        <span class="host-ip">{host}</span>
                        <span class="hostname">{self.new['hosts'][host].get('hostname', '')}</span>
                    </div>
                    <div class="host-stats">
                        <div class="host-stat changed">
                            <div class="label">DEĞİŞEN</div>
                            <div class="value">{len(changes)}</div>
                        </div>
                    </div>
                </div>
                <div class="host-details" style="display: block;">
                    <h4>🔄 SERVİS DEĞİŞİKLİKLERİ</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Port/Proto</th>
                                <th>Eski Servis</th>
                                <th>Yeni Servis</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            for change in changes:
                html += f"""
                        <tr class="port-changed">
                            <td><span class="badge badge-changed">{change['port']}/{change['protocol']}</span></td>
                            <td>
                                <span class="service-name">{change['old']['name']}</span><br>
                                <span class="service-product">{change['old']['product']}</span>
                                <span class="service-version">{change['old']['version']}</span>
                            </td>
                            <td>
                                <span class="service-name">{change['new']['name']}</span><br>
                                <span class="service-product">{change['new']['product']}</span>
                                <span class="service-version">{change['new']['version']}</span>
                            </td>
                        </tr>
                """
            html += """
                        </tbody>
                    </table>
                </div>
            </div>
            """
        
        html += """
        </div> <!-- tab-changed sonu -->
        
        <!-- Footer -->
        <div class="footer">
            <p>📊 Rapor Oluşturulma: {}</p>
            <p>🔧 Internal Network Security Scanner - Detaylı Port Karşılaştırma Raporu</p>
            <p>🆕 Yeni Portlar | 🔒 Kapanan Portlar | 🔄 Değişen Servisler | 📋 Tüm Açık Portlar</p>
        </div>
    </div>
    
    <script>
        // Tüm host detaylarını göster
        document.addEventListener('DOMContentLoaded', function() {{
            // Tüm detayları aç
            expandAll();
        }});
        
        // Toggle host details
        function toggleHost(element) {{
            var details = element.nextElementSibling;
            if (details.style.display === 'none' || details.style.display === '') {{
                details.style.display = 'block';
            }} else {{
                details.style.display = 'none';
            }}
        }}
        
        // Expand all hosts
        function expandAll() {{
            var details = document.querySelectorAll('.host-details');
            for(var i = 0; i < details.length; i++) {{
                details[i].style.display = 'block';
            }}
        }}
        
        // Collapse all hosts
        function collapseAll() {{
            var details = document.querySelectorAll('.host-details');
            for(var i = 0; i < details.length; i++) {{
                details[i].style.display = 'none';
            }}
        }}
        
        // Filter hosts
        function filterHosts() {{
            var searchText = document.getElementById('searchInput').value.toLowerCase();
            var cards = document.querySelectorAll('.host-card');
            
            for(var i = 0; i < cards.length; i++) {{
                var card = cards[i];
                var host = card.getAttribute('data-host').toLowerCase();
                var hostname = card.getAttribute('data-hostname').toLowerCase();
                var cardText = card.innerText.toLowerCase();
                
                if (host.includes(searchText) || hostname.includes(searchText) || cardText.includes(searchText)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }}
        }}
        
        // Tab switching
        function showTab(tabName) {{
            // Hide all tabs
            var tabs = document.querySelectorAll('.tab-content');
            for(var i = 0; i < tabs.length; i++) {{
                tabs[i].classList.remove('active');
            }}
            
            // Show selected tab
            document.getElementById('tab-' + tabName).classList.add('active');
            
            // Update tab buttons
            var buttons = document.querySelectorAll('.tab-btn');
            for(var i = 0; i < buttons.length; i++) {{
                buttons[i].classList.remove('active');
            }}
            event.target.classList.add('active');
            
            // Sayfa başına scroll
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}
    </script>
</body>
</html>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n[+] DETAYLI HTML rapor oluşturuldu: {filename}")
        print(f"[+] Rapor konumu: {os.path.abspath(filename)}")
        
        # Firefox ile aç
        try:
            os.system(f"firefox {filename} &")
            print("[+] Rapor Firefox ile açılıyor...")
        except:
            try:
                os.system(f"xdg-open {filename} &")
                print("[+] Rapor varsayılan tarayıcı ile açılıyor...")
            except:
                pass
        
        return filename

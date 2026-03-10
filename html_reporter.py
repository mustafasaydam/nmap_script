#!/usr/bin/env python3
import json
import webbrowser
import os
from datetime import datetime
from rich.console import Console

console = Console()

class HTMLReporter:
    def __init__(self, old_scan, new_scan, differences):
        self.old = old_scan
        self.new = new_scan
        self.diffs = differences
        
    def generate_html(self, filename="comparison_report.html"):
        """HTML rapor oluştur"""
        
        old_date = datetime.fromisoformat(self.old['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        new_date = datetime.fromisoformat(self.new['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
        
        # Renk kodları için CSS
        html_content = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Port Tarama Karşılaştırma Raporu</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                }}
                .header {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header h1 {{
                    margin: 0;
                    color: #333;
                    font-size: 2.5em;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    transition: transform 0.3s;
                }}
                .stat-card:hover {{
                    transform: translateY(-5px);
                }}
                .stat-card.new-host {{ border-left: 5px solid #4CAF50; }}
                .stat-card.removed-host {{ border-left: 5px solid #f44336; }}
                .stat-card.new-port {{ border-left: 5px solid #ff9800; }}
                .stat-card.closed-port {{ border-left: 5px solid #2196F3; }}
                .stat-number {{
                    font-size: 2.5em;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .stat-label {{
                    color: #666;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .timestamp {{
                    color: #999;
                    font-size: 0.9em;
                    margin-top: 10px;
                }}
                table {{
                    width: 100%;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                    border-collapse: collapse;
                }}
                th {{
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    font-weight: 600;
                    padding: 15px;
                    text-align: left;
                }}
                td {{
                    padding: 12px 15px;
                    border-bottom: 1px solid #f0f0f0;
                }}
                tr:hover {{
                    background: #f8f9fa;
                }}
                .badge {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 0.85em;
                    font-weight: 600;
                }}
                .badge-new {{ background: #ff9800; color: white; }}
                .badge-closed {{ background: #2196F3; color: white; }}
                .badge-changed {{ background: #9C27B0; color: white; }}
                .service-info {{
                    font-size: 0.9em;
                    color: #666;
                }}
                .ip-address {{
                    font-family: monospace;
                    font-size: 1.1em;
                    color: #333;
                }}
                .section-title {{
                    color: white;
                    font-size: 1.8em;
                    margin: 30px 0 20px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .footer {{
                    text-align: center;
                    color: white;
                    margin-top: 50px;
                    padding: 20px;
                }}
                @media (max-width: 768px) {{
                    .stats-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Port Tarama Karşılaştırma Raporu</h1>
                    <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                        <div>
                            <strong>📅 İlk Tarama:</strong> {old_date}
                        </div>
                        <div>
                            <strong>📅 Son Tarama:</strong> {new_date}
                        </div>
                    </div>
                </div>
        """
        
        # İstatistik kartları
        total_new_hosts = len(self.diffs.get('new_hosts', []))
        total_removed_hosts = len(self.diffs.get('removed_hosts', []))
        total_new_ports = sum(len(v) for v in self.diffs.get('new_ports', {}).values())
        total_closed_ports = sum(len(v) for v in self.diffs.get('closed_ports', {}).values())
        
        html_content += f"""
                <div class="stats-grid">
                    <div class="stat-card new-host">
                        <div class="stat-label">🆕 YENİ HOSTLAR</div>
                        <div class="stat-number">+{total_new_hosts}</div>
                        <div class="timestamp">Sisteme eklenen hostlar</div>
                    </div>
                    <div class="stat-card removed-host">
                        <div class="stat-label">❌ KAPANAN HOSTLAR</div>
                        <div class="stat-number">-{total_removed_hosts}</div>
                        <div class="timestamp">Sistemden çıkan hostlar</div>
                    </div>
                    <div class="stat-card new-port">
                        <div class="stat-label">🔓 YENİ PORTLAR</div>
                        <div class="stat-number">+{total_new_ports}</div>
                        <div class="timestamp">Yeni açılan portlar</div>
                    </div>
                    <div class="stat-card closed-port">
                        <div class="stat-label">🔒 KAPANAN PORTLAR</div>
                        <div class="stat-number">-{total_closed_ports}</div>
                        <div class="timestamp">Kapanan portlar</div>
                    </div>
                </div>
        """
        
        # Yeni Hostlar Tablosu
        if self.diffs.get('new_hosts'):
            html_content += """
                <h2 class="section-title">🆕 YENİ HOSTLAR</h2>
                <table>
                    <thead>
                        <tr>
                            <th>IP Adresi</th>
                            <th>Hostname</th>
                            <th>Açık Port Sayısı</th>
                            <th>Servisler</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for host in self.diffs['new_hosts']:
                host_data = self.new['hosts'][host]
                port_count = sum(len(host_data['protocols'].get('tcp', {})) for p in host_data['protocols'])
                
                # Servisleri listele
                services = []
                for proto, ports in host_data['protocols'].items():
                    for port, info in ports.items():
                        services.append(f"{port}/{proto} ({info['name']})")
                
                services_str = "<br>".join(services[:5])  # İlk 5 servis
                if len(services) > 5:
                    services_str += f"<br>...ve {len(services)-5} daha"
                
                html_content += f"""
                        <tr>
                            <td class="ip-address">{host}</td>
                            <td>{host_data['hostname']}</td>
                            <td style="text-align: center;">{port_count}</td>
                            <td class="service-info">{services_str}</td>
                        </tr>
                """
            
            html_content += """
                    </tbody>
                </table>
            """
        
        # Yeni Portlar Tablosu
        if self.diffs.get('new_ports'):
            html_content += """
                <h2 class="section-title">🔓 YENİ AÇILAN PORTLAR</h2>
                <table>
                    <thead>
                        <tr>
                            <th>IP Adresi</th>
                            <th>Port/Proto</th>
                            <th>Servis</th>
                            <th>Versiyon</th>
                            <th>Detay</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for host, ports in self.diffs['new_ports'].items():
                for proto, port in ports:
                    service = self.new['hosts'][host]['protocols'][proto][str(port)]
                    html_content += f"""
                        <tr>
                            <td class="ip-address">{host}</td>
                            <td><span class="badge badge-new">{port}/{proto}</span></td>
                            <td>{service['name']}</td>
                            <td>{service['product']} {service['version']}</td>
                            <td class="service-info">{service['extrainfo']}</td>
                        </tr>
                    """
            
            html_content += """
                    </tbody>
                </table>
            """
        
        # Kapanan Portlar Tablosu
        if self.diffs.get('closed_ports'):
            html_content += """
                <h2 class="section-title">🔒 KAPANAN PORTLAR</h2>
                <table>
                    <thead>
                        <tr>
                            <th>IP Adresi</th>
                            <th>Port/Proto</th>
                            <th>Eski Servis</th>
                            <th>Eski Versiyon</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for host, ports in self.diffs['closed_ports'].items():
                for proto, port in ports:
                    service = self.old['hosts'][host]['protocols'][proto][str(port)]
                    html_content += f"""
                        <tr>
                            <td class="ip-address">{host}</td>
                            <td><span class="badge badge-closed">{port}/{proto}</span></td>
                            <td>{service['name']}</td>
                            <td>{service['product']} {service['version']}</td>
                        </tr>
                    """
            
            html_content += """
                    </tbody>
                </table>
            """
        
        # Servis Değişiklikleri
        if self.diffs.get('service_changes'):
            html_content += """
                <h2 class="section-title">🔄 SERVİS DEĞİŞİKLİKLERİ</h2>
                <table>
                    <thead>
                        <tr>
                            <th>IP Adresi</th>
                            <th>Port</th>
                            <th>Değişim</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for host, changes in self.diffs['service_changes'].items():
                for change in changes:
                    old = f"{change['old']['name']} {change['old']['product']} {change['old']['version']}".strip()
                    new = f"{change['new']['name']} {change['new']['product']} {change['new']['version']}".strip()
                    
                    html_content += f"""
                        <tr>
                            <td class="ip-address">{host}</td>
                            <td><span class="badge badge-changed">{change['port']}/{change['protocol']}</span></td>
                            <td>
                                <div style="color: #f44336;">❌ {old}</div>
                                <div style="color: #4CAF50; margin-top: 5px;">✅ {new}</div>
                            </td>
                        </tr>
                    """
            
            html_content += """
                    </tbody>
                </table>
            """
        
        # Footer
        html_content += f"""
                <div class="footer">
                    <p>Rapor Oluşturma Zamanı: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p style="font-size: 0.9em;">🔧 Internal Network Security Scanner</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # HTML'i kaydet
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        console.print(f"[green]✅ HTML rapor oluşturuldu: {filename}[/green]")
        
        # Tarayıcıda aç
        webbrowser.open('file://' + os.path.realpath(filename))
        
        return filename

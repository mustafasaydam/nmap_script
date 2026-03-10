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
        
        # İstatistikler
        total_new_hosts = len(self.diffs.get('new_hosts', []))
        total_removed_hosts = len(self.diffs.get('removed_hosts', []))
        total_new_ports = sum(len(v) for v in self.diffs.get('new_ports', {}).values())
        total_closed_ports = sum(len(v) for v in self.diffs.get('closed_ports', {}).values())
        total_service_changes = sum(len(v) for v in self.diffs.get('service_changes', {}).values())
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Port Tarama Karşılaştırma Raporu</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 2rem;
                }}
                
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                }}
                
                /* Header */
                .header {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 24px;
                    padding: 2rem;
                    margin-bottom: 2rem;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }}
                
                .header h1 {{
                    font-size: 2.5rem;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }}
                
                .date-info {{
                    display: flex;
                    gap: 2rem;
                    color: #4a5568;
                    font-size: 1.1rem;
                }}
                
                .date-info span {{
                    font-weight: 600;
                    color: #667eea;
                }}
                
                /* Stats Grid */
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 1.5rem;
                    margin-bottom: 2rem;
                }}
                
                .stat-card {{
                    background: white;
                    border-radius: 20px;
                    padding: 1.5rem;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                    border-left: 6px solid;
                    position: relative;
                    overflow: hidden;
                }}
                
                .stat-card::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    right: 0;
                    width: 100px;
                    height: 100px;
                    background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1));
                    transform: rotate(45deg) translate(30px, -30px);
                }}
                
                .stat-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
                }}
                
                .stat-card.new-host {{ border-color: #4CAF50; }}
                .stat-card.removed-host {{ border-color: #f44336; }}
                .stat-card.new-port {{ border-color: #ff9800; }}
                .stat-card.closed-port {{ border-color: #2196F3; }}
                .stat-card.changed {{ border-color: #9C27B0; }}
                
                .stat-label {{
                    color: #718096;
                    font-size: 0.9rem;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 0.5rem;
                }}
                
                .stat-number {{
                    font-size: 3rem;
                    font-weight: 800;
                    line-height: 1;
                    margin-bottom: 0.5rem;
                }}
                
                .stat-desc {{
                    color: #a0aec0;
                    font-size: 0.9rem;
                }}
                
                /* Section Titles */
                .section-title {{
                    color: white;
                    font-size: 2rem;
                    margin: 2rem 0 1.5rem;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }}
                
                .section-title i {{
                    font-size: 2rem;
                }}
                
                /* Tables */
                .table-container {{
                    background: white;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    margin-bottom: 2rem;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                
                th {{
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    font-weight: 600;
                    padding: 1rem;
                    text-align: left;
                    font-size: 0.95rem;
                }}
                
                td {{
                    padding: 1rem;
                    border-bottom: 1px solid #edf2f7;
                    color: #2d3748;
                }}
                
                tr:last-child td {{
                    border-bottom: none;
                }}
                
                tr:hover td {{
                    background: #f7fafc;
                }}
                
                /* Badges */
                .badge {{
                    display: inline-block;
                    padding: 0.35rem 0.75rem;
                    border-radius: 9999px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    background: #edf2f7;
                    color: #4a5568;
                }}
                
                .badge-new {{
                    background: #ff9800;
                    color: white;
                }}
                
                .badge-closed {{
                    background: #2196F3;
                    color: white;
                }}
                
                .badge-changed {{
                    background: #9C27B0;
                    color: white;
                }}
                
                /* IP Address */
                .ip-address {{
                    font-family: 'Courier New', monospace;
                    font-weight: 600;
                    color: #2d3748;
                }}
                
                /* Service Info */
                .service-info {{
                    font-size: 0.9rem;
                    color: #718096;
                }}
                
                .service-change {{
                    display: flex;
                    flex-direction: column;
                    gap: 0.25rem;
                }}
                
                .old-service {{
                    color: #f44336;
                    text-decoration: line-through;
                }}
                
                .new-service {{
                    color: #4CAF50;
                    font-weight: 600;
                }}
                
                /* Footer */
                .footer {{
                    text-align: center;
                    color: white;
                    margin-top: 3rem;
                    padding: 2rem;
                    background: rgba(0, 0, 0, 0.2);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }}
                
                /* Responsive */
                @media (max-width: 768px) {{
                    body {{ padding: 1rem; }}
                    .stats-grid {{ grid-template-columns: 1fr; }}
                    .date-info {{ flex-direction: column; gap: 0.5rem; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <h1>
                        <span>🔍</span>
                        Port Tarama Karşılaştırma Raporu
                    </h1>
                    <div class="date-info">
                        <div>📅 <span>İlk Tarama:</span> {old_date}</div>
                        <div>📅 <span>Son Tarama:</span> {new_date}</div>
                    </div>
                </div>
                
                <!-- Statistics -->
                <div class="stats-grid">
                    <div class="stat-card new-host">
                        <div class="stat-label">🆕 YENİ HOSTLAR</div>
                        <div class="stat-number">+{total_new_hosts}</div>
                        <div class="stat-desc">Sisteme yeni eklenen hostlar</div>
                    </div>
                    <div class="stat-card removed-host">
                        <div class="stat-label">❌ KAPANAN HOSTLAR</div>
                        <div class="stat-number">-{total_removed_hosts}</div>
                        <div class="stat-desc">Sistemden çıkan hostlar</div>
                    </div>
                    <div class="stat-card new-port">
                        <div class="stat-label">🔓 YENİ PORTLAR</div>
                        <div class="stat-number">+{total_new_ports}</div>
                        <div class="stat-desc">Yeni açılan portlar</div>
                    </div>
                    <div class="stat-card closed-port">
                        <div class="stat-label">🔒 KAPANAN PORTLAR</div>
                        <div class="stat-number">-{total_closed_ports}</div>
                        <div class="stat-desc">Kapanan portlar</div>
                    </div>
                    <div class="stat-card changed">
                        <div class="stat-label">🔄 SERVİS DEĞİŞİKLİĞİ</div>
                        <div class="stat-number">{total_service_changes}</div>
                        <div class="stat-desc">Servis bilgisi değişen portlar</div>
                    </div>
                </div>
        """
        
        # Yeni Hostlar
        if self.diffs.get('new_hosts'):
            html_content += """
                <h2 class="section-title">
                    <span>🆕</span>
                    Yeni Hostlar
                </h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>IP Adresi</th>
                                <th>Hostname</th>
                                <th>Açık Portlar</th>
                                <th>Servisler</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for host in self.diffs['new_hosts']:
                host_data = self.new['hosts'][host]
                ports = []
                services = []
                
                for protocol, port_dict in host_data.get('protocols', {}).items():
                    for port, service in port_dict.items():
                        ports.append(f"{port}/{protocol}")
                        services.append(f"{port}/{protocol}: {service['name']}")
                
                html_content += f"""
                            <tr>
                                <td class="ip-address">{host}</td>
                                <td>{host_data.get('hostname', '-')}</td>
                                <td><span class="badge">{len(ports)} port</span> {', '.join(ports[:3])}</td>
                                <td class="service-info">{', '.join(services[:2])}</td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Yeni Portlar
        if self.diffs.get('new_ports'):
            html_content += """
                <h2 class="section-title">
                    <span>🔓</span>
                    Yeni Açılan Portlar
                </h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>IP Adresi</th>
                                <th>Port/Proto</th>
                                <th>Servis</th>
                                <th>Versiyon</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for host, ports in self.diffs['new_ports'].items():
                for protocol, port in ports:
                    service = self.new['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    html_content += f"""
                            <tr>
                                <td class="ip-address">{host}</td>
                                <td><span class="badge badge-new">{port}/{protocol}</span></td>
                                <td>{service['name']}</td>
                                <td class="service-info">{version or '-'}</td>
                            </tr>
                    """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Kapanan Portlar
        if self.diffs.get('closed_ports'):
            html_content += """
                <h2 class="section-title">
                    <span>🔒</span>
                    Kapanan Portlar
                </h2>
                <div class="table-container">
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
                for protocol, port in ports:
                    service = self.old['hosts'][host]['protocols'][protocol][port]
                    version = f"{service['product']} {service['version']}".strip()
                    html_content += f"""
                            <tr>
                                <td class="ip-address">{host}</td>
                                <td><span class="badge badge-closed">{port}/{protocol}</span></td>
                                <td>{service['name']}</td>
                                <td class="service-info">{version or '-'}</td>
                            </tr>
                    """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Servis Değişiklikleri
        if self.diffs.get('service_changes'):
            html_content += """
                <h2 class="section-title">
                    <span>🔄</span>
                    Servis Değişiklikleri
                </h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>IP Adresi</th>
                                <th>Port/Proto</th>
                                <th>Değişim</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for host, changes in self.diffs['service_changes'].items():
                for change in changes:
                    old_ver = f"{change['old']['product']} {change['old']['version']}".strip()
                    new_ver = f"{change['new']['product']} {change['new']['version']}".strip()
                    
                    html_content += f"""
                            <tr>
                                <td class="ip-address">{host}</td>
                                <td><span class="badge badge-changed">{change['port']}/{change['protocol']}</span></td>
                                <td>
                                    <div class="service-change">
                                        <div class="old-service">❌ {change['old']['name']} {old_ver}</div>
                                        <div class="new-service">✅ {change['new']['name']} {new_ver}</div>
                                    </div>
                                </td>
                            </tr>
                    """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Footer
        html_content += f"""
                <div class="footer">
                    <p>Rapor Oluşturulma: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p style="margin-top: 0.5rem; opacity: 0.8;">🔧 Internal Network Security Scanner</p>
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

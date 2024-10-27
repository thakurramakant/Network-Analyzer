from dash import dcc, html, Input, Output, State
import dash
import pandas as pd
import plotly.express as px
import psutil
import os
from threading import Thread
from network_monitor import NetworkMonitor
from dns_sniffer import DNSSniffer

# Initialize Dash app
app = dash.Dash(__name__)

# Global instances for monitoring and sniffing
network_monitor = None
dns_sniffer = None

def get_network_interfaces():
    """Fetch available network interfaces excluding loopback."""
    interfaces = [iface for iface in psutil.net_if_addrs().keys() if iface != "Loopback Pseudo-Interface 1"]
    return [{"label": iface, "value": iface} for iface in interfaces]

def load_network_data():
    """Load network usage data from CSV file."""
    file_path = 'data/network_usage.csv'
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=['Timestamp', 'Interface', 'Download (bytes)', 'Upload (bytes)'])
    return pd.read_csv(file_path)

def load_website_data():
    """Load website usage data from CSV file."""
    file_path = 'data/website_usage.csv'
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=['Website', 'Time Spent (seconds)', 'Data Transferred (MB)'])
    return pd.read_csv(file_path)

def reset_data():
    """Reset the logged data in the CSV files."""
    network_file_path = 'data/network_usage.csv'
    website_file_path = 'data/website_usage.csv'

    if os.path.exists(network_file_path):
        os.remove(network_file_path)

    if os.path.exists(website_file_path):
        os.remove(website_file_path)

app.layout = html.Div(className="app-container", children=[
    html.Div(className="header", children=[
        html.H1("Network Analyzer", className="header-title"),
        html.P("Monitor your network usage and DNS activity in real-time.", className="header-subtitle")
    ]),

    html.Div(className="control-panel", children=[
        html.Label("Select Network Interface:", className="label"),
        dcc.Dropdown(
            id="interface-dropdown",
            options=get_network_interfaces(),
            placeholder="Select Network Interface",
            className="dropdown"
        ),
        html.Div(className="button-container", children=[
            html.Button("Start Monitoring", id="start-monitoring-btn", className="button"),
            html.Button("Stop Monitoring", id="stop-monitoring-btn", className="button"),
            html.Button("Start DNS Sniffer", id="start-dns-btn", className="button"),
            html.Button("Stop DNS Sniffer", id="stop-dns-btn", className="button"),
            html.Button("Reset Data", id="reset-data-btn", className="button")
        ])
    ]),

    html.Div(className="graph-container", children=[
        dcc.Graph(id="network-usage-graph", config={'displayModeBar': False}, className="graph"),
        # Separate Div for Pie Chart
        html.Div(className="website-usage", children=[
            dcc.Graph(id="website-usage-piechart", config={'displayModeBar': False}, className="pie-chart")
        ]), 
    ]),

    dcc.Interval(id="network-interval", interval=5 * 1000, n_intervals=0),
    dcc.Interval(id="website-interval", interval=5 * 1000, n_intervals=0),

    html.Div(className="footer", children=[
        html.P("© 2024 Network Analyzer. All Rights Reserved.", className="footer-text")
    ])
])

@app.callback(
    Output("interface-dropdown", "value"),
    Input("start-monitoring-btn", "n_clicks"),
    Input("stop-monitoring-btn", "n_clicks"),
    Input("start-dns-btn", "n_clicks"),
    Input("stop-dns-btn", "n_clicks"),
    Input("reset-data-btn", "n_clicks"),
    State("interface-dropdown", "value")
)
def manage_monitoring(start_clicks, stop_clicks, start_dns_clicks, stop_dns_clicks, reset_clicks, selected_interface):
    global network_monitor, dns_sniffer

    ctx = dash.callback_context
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == "start-monitoring-btn" and selected_interface:
            if not network_monitor:
                network_monitor = NetworkMonitor(selected_interface)
                Thread(target=network_monitor.start_monitoring).start()  # Start monitoring in a separate thread
            return selected_interface

        elif button_id == "stop-monitoring-btn" and network_monitor:
            network_monitor.stop_monitoring()
            network_monitor = None
            return None

        elif button_id == "start-dns-btn" and not dns_sniffer:
            if network_monitor:
                dns_sniffer = DNSSniffer(network_monitor)
                Thread(target=dns_sniffer.start_sniffing).start()  # Start sniffing in a separate thread
            return selected_interface

        elif button_id == "stop-dns-btn" and dns_sniffer:
            dns_sniffer.stop_sniffing()  # Stop DNS sniffing
            dns_sniffer = None
            return selected_interface

        elif button_id == "reset-data-btn":
            reset_data()  # Reset the CSV files
            return selected_interface

    return selected_interface

@app.callback(
    Output("network-usage-graph", "figure"),
    Input("network-interval", "n_intervals")
)
def update_network_graph(n):
    """Update the network usage graph."""
    df = load_network_data()
    if df.empty:
        return px.line(title="No Network Data Available")

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df.dropna(subset=['Timestamp'], inplace=True)

    fig = px.line(df, x='Timestamp', y=['Download (bytes)', 'Upload (bytes)'], color='Interface',
                  title="Network Usage Over Time",
                  labels={'value': 'Data (bytes)', 'Timestamp': 'Time'})

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Data Usage (Bytes)",
        legend_title="Interface",
        title_font=dict(size=20, color='#E0E0E0'),
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#121212',
        font=dict(color='#E0E0E0'),
        xaxis=dict(showgrid=True, gridcolor='#3A3A3A'),
        yaxis=dict(showgrid=True, gridcolor='#3A3A3A')
    )
    return fig

@app.callback(
    Output("website-usage-piechart", "figure"),
    Input("website-interval", "n_intervals")
)
def update_website_graph(n):
    """Update the website usage pie chart."""
    df = load_website_data()
    if df.empty:
        return px.pie(title="No Website Data Available")

    fig = px.pie(df, names='Website', values='Time Spent (seconds)',
                 title="Website Usage Distribution",
                 color_discrete_sequence=px.colors.qualitative.Plotly)

    fig.update_layout(
        title_font=dict(size=20, color='#E0E0E0'),
        legend_title_text='Websites',
        paper_bgcolor='#121212',
        font=dict(size=14, color='#E0E0E0')
    )

    return fig

if __name__ == "__main__":
    app.run_server(debug=True,port=8051)

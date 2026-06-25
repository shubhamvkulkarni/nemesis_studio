import os
import panel as pn
import requests
import webview

# Enable Panel extensions
pn.extension()

# Server API Endpoint (for future integration)
BACKEND_URL = "http://127.0.0.1:8000"

# --- Navigation Menu (Sidebar) ---
nav_menu = pn.widgets.RadioButtonGroup(
    name="Panes",
    options=["Outreach", "Beginner", "Advance"],
    value="Outreach",
    orientation="vertical",
    button_type="light",
    styles={"width": "100%"}
)

# --- Outreach Pane (Default Page) ---
outreach_markdown = pn.pane.Markdown(
    """
    ## Welcome to NEMESIS Studio
    
    NEMESIS Studio provides a Graphical User Interface (GUI) for the original **NEMESIS** (Non-linear optimal Estimator for MultivariatE spectral AnalySIS) radiative transfer and retrieval code.
    
    For more details on the underlying model and code, check the [NEMESIS GitHub Repository](https://github.com/nemesiscode/radtrancode).
    
    *This is the Outreach pane/page.*
    """,
    styles={'font-family': 'sans-serif'}
)

# Planet Selection Dialog Box
planet_select = pn.widgets.Select(
    name="Choose from the list of planets",
    options=["Jupiter", "Venus"],
    value="Jupiter",
    width=250
)

planet_status = pn.pane.Markdown("Selected Planet: **Jupiter**")

def on_planet_change(event):
    planet_status.object = f"Selected Planet: **{event.new}**"

planet_select.param.watch(on_planet_change, 'value')

planet_dialog_card = pn.Card(
    planet_select,
    planet_status,
    title="Choose from the list of planets",
    width=320,
    collapsible=False
)

outreach_layout = pn.Column(
    outreach_markdown,
    pn.Spacer(height=15),
    planet_dialog_card,
    margin=10
)

# --- Beginner Pane ---
beginner_layout = pn.Column(
    pn.pane.Markdown(
        """
        ## Beginner Workspace
        
        *This is the Beginner pane/page.*
        
        This workspace will guide you through running standard simulations step-by-step.
        """
    ),
    margin=10
)

# --- Advance Pane ---
advance_layout = pn.Column(
    pn.pane.Markdown(
        """
        ## Advance Workspace
        
        *This is the Advance pane/page.*
        
        This workspace allows expert configuration of profiles, atmosphere files, and retrieval parameters.
        """
    ),
    margin=10
)

# --- Main Layout Router ---
@pn.depends(nav_menu)
def render_active_pane(active_pane):
    if active_pane == "Outreach":
        return outreach_layout
    elif active_pane == "Beginner":
        return beginner_layout
    elif active_pane == "Advance":
        return advance_layout
    return outreach_layout

# --- Panel App Template Layout ---
template = pn.template.FastListTemplate(
    title="NEMESIS Studio",
    logo="assets/logo.jpg",
    sidebar=[
        pn.pane.Markdown("### Workspaces"),
        nav_menu
    ],
    main=[
        render_active_pane
    ],
    accent_base_color="#2c3e50",
    header_background="#1a252f"
)

# Serve the application layout
template.show(port=5006, threaded=True, open=False)

# Define the local URL string pointing to that port
url = "http://localhost:5006"

def on_closed():
    os._exit(0)

window = webview.create_window('NEMESIS Studio', url, width=1200, height=800)
window.events.closed += on_closed
webview.start()

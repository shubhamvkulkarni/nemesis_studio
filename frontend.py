import os
import panel as pn
import requests
import webview
import f_plots

# Enable Panel extensions
pn.extension('holoviews')

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
    GUI for the **NEMESIS** radiative transfer and retrieval code. 
    [GitHub Repository](https://github.com/nemesiscode/radtrancode).
    """,
    styles={'font-family': 'sans-serif'}
)

# Planet Selection
planet_select = pn.widgets.RadioButtonGroup(
    name="Planet",
    options=["Jupiter", "Venus"],
    value="Jupiter",
    button_type="success"
)

model_button = pn.widgets.Button(name="Plot", button_type="primary", width=100)
plot_options = pn.widgets.RadioButtonGroup(
    name="Plot Options",
    options=["Pressure and Temp", "Gases", "Aerosols"],
    value="Pressure and Temp",
    button_type="success"
)

plot_pane = pn.pane.HoloViews()
plot_error = pn.pane.Markdown("")

def generate_model_plots(event):
    planet = planet_select.value.lower()
    base_path = os.path.join(os.getcwd(), "outreach", planet, f"{planet}_main")
    ref_path = os.path.join(base_path, f"{planet}.ref")
    aerosol_path = os.path.join(base_path, "aerosol.ref")
    
    selected_plot = plot_options.value
    try:
        plot_error.object = ""
        if selected_plot == "Pressure and Temp":
            plot_pane.object = f_plots.get_pressure_temp_plot(ref_path)
        elif selected_plot == "Gases":
            plot_pane.object = f_plots.get_gases_plot(ref_path)
        elif selected_plot == "Aerosols":
            plot_pane.object = f_plots.get_aerosols_plot(aerosol_path)
    except Exception as e:
        plot_error.object = f"**Error generating plot:** {str(e)}"
        plot_pane.object = None

model_button.on_click(generate_model_plots)

outreach_layout = pn.Column(
    outreach_markdown,
    pn.Row(pn.pane.Markdown("**Select the planet:**", margin=(10, 10, 0, 0)), planet_select),
    pn.layout.Divider(margin=(5, 0)),
    pn.Row(pn.pane.Markdown("**Atmospheric model:**", margin=(10, 10, 0, 0)), plot_options, model_button),
    plot_error,
    plot_pane,
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

import sys
import os
import time
import threading
import panel as pn
import requests
import webview
import f_plots
import subprocess

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

def make_model_plot(clicks):
    if clicks == 0:
        return pn.pane.Markdown("*Click Plot to view atmospheric model*")
    
    planet = planet_select.value.lower()
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(ROOT_DIR, "outreach", planet, f"{planet}_main")
    ref_path = os.path.join(base_path, f"{planet}.ref")
    aerosol_path = os.path.join(base_path, "aerosol.ref")
    
    selected_plot = plot_options.value
    try:
        if selected_plot == "Pressure and Temp":
            return f_plots.get_pressure_temp_plot(ref_path)
        elif selected_plot == "Gases":
            return f_plots.get_gases_plot(ref_path)
        elif selected_plot == "Aerosols":
            return f_plots.get_aerosols_plot(aerosol_path)
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", style={'color': 'red'})

model_plot_pane = pn.panel(pn.bind(make_model_plot, model_button.param.clicks))

radiance_button = pn.widgets.Button(name="Plot", button_type="primary", width=100)
rerun_switch = pn.widgets.Switch(name="Rerun", value=False)

def make_radiance_plot(clicks):
    if clicks == 0:
        return pn.pane.Markdown("*Click Plot to view radiative transfer simulation*")
        
    planet = planet_select.value.lower()
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(ROOT_DIR, "outreach", planet, f"{planet}_main")
    runname = planet
    runname_path = os.path.join(base_path, runname)
    
    try:
        if rerun_switch.value:
            print(f"--- Running NEMESIS simulation for {runname} ---")
            cmd = f'docker run --rm -i -v "$(pwd)":/data -w /data patrickirwinoxford/docker_nemesis Nemesis < {runname}.nam > test.prc'
            subprocess.run(cmd, shell=True, executable='/bin/zsh', cwd=base_path, check=True)
            print(f"--- NEMESIS simulation completed ---")
            
        return f_plots.get_spectrum_plot(runname_path)
    except subprocess.CalledProcessError as e:
        return pn.pane.Markdown(f"**Error running Nemesis simulation:** Process exited with code {e.returncode}.", style={'color': 'red'})
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", style={'color': 'red'})

radiance_plot_pane = pn.panel(pn.bind(make_radiance_plot, radiance_button.param.clicks))

outreach_layout = pn.Column(
    outreach_markdown,
    pn.Row(pn.pane.Markdown("**Select the planet:**", margin=(0, 0, 0, 0)), planet_select),
    pn.layout.Divider(),
    pn.Row(pn.pane.Markdown("**Atmospheric model:**", margin=(0, 0, 0, 0)), plot_options, model_button),
    model_plot_pane,
    pn.layout.Divider(),
    pn.Row(pn.pane.Markdown("**Radiative transfer simulation:**", margin=(0, 0, 0, 0)), 
           pn.pane.Markdown("**Rerun:**", margin=(0, 5, 0, 10)), rerun_switch, 
           radiance_button),
    radiance_plot_pane,
    margin=10
)

# --- Beginner Pane ---
working_dir_input = pn.widgets.TextInput(name="Working Directory", placeholder="Select directory...", width=400)
select_dir_button = pn.widgets.Button(name="Browse...", width=100, align=('end', 'center'))
runname_input = pn.widgets.TextInput(name="Runname", placeholder="e.g., venus or jupiter", width=200)

def select_working_directory(event):
    if 'window' in globals() and window is not None:
        result = window.create_file_dialog(webview.FileDialog.FOLDER)
        if result and len(result) > 0:
            working_dir_input.value = result[0]

select_dir_button.on_click(select_working_directory)

beginner_model_button = pn.widgets.Button(name="Plot", button_type="primary", width=100)
beginner_plot_options = pn.widgets.RadioButtonGroup(
    name="Plot Options",
    options=["Pressure and Temp", "Gases", "Aerosols"],
    value="Pressure and Temp",
    button_type="success"
)

def make_beginner_model_plot(clicks):
    if clicks == 0:
        return pn.pane.Markdown("*Click Plot to view atmospheric model*")
    
    base_path = working_dir_input.value
    runname = runname_input.value
    
    if not base_path or not runname:
        return pn.pane.Markdown("**Error:** Please select a working directory and enter a runname.", style={'color': 'red'})
        
    ref_path = os.path.join(base_path, f"{runname}.ref")
    aerosol_path = os.path.join(base_path, "aerosol.ref")
    
    selected_plot = beginner_plot_options.value
    try:
        if selected_plot == "Pressure and Temp":
            return f_plots.get_pressure_temp_plot(ref_path)
        elif selected_plot == "Gases":
            return f_plots.get_gases_plot(ref_path)
        elif selected_plot == "Aerosols":
            return f_plots.get_aerosols_plot(aerosol_path)
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", style={'color': 'red'})

beginner_model_plot_pane = pn.panel(pn.bind(make_beginner_model_plot, beginner_model_button.param.clicks))

beginner_radiance_button = pn.widgets.Button(name="Plot", button_type="primary", width=100)
beginner_rerun_switch = pn.widgets.Switch(name="Rerun", value=False)

def make_beginner_radiance_plot(clicks):
    if clicks == 0:
        return pn.pane.Markdown("*Click Plot to view radiative transfer simulation*")
        
    base_path = working_dir_input.value
    runname = runname_input.value
    
    if not base_path or not runname:
        return pn.pane.Markdown("**Error:** Please select a working directory and enter a runname.", style={'color': 'red'})
        
    runname_path = os.path.join(base_path, runname)
    
    try:
        if beginner_rerun_switch.value:
            print(f"--- Running NEMESIS simulation for {runname} ---")
            cmd = f'docker run --rm -i -v "$(pwd)":/data -w /data patrickirwinoxford/docker_nemesis Nemesis < {runname}.nam > test.prc'
            subprocess.run(cmd, shell=True, executable='/bin/zsh', cwd=base_path, check=True)
            print(f"--- NEMESIS simulation completed ---")
            
        return f_plots.get_spectrum_plot(runname_path)
    except subprocess.CalledProcessError as e:
        return pn.pane.Markdown(f"**Error running Nemesis simulation:** Process exited with code {e.returncode}.", style={'color': 'red'})
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", style={'color': 'red'})

beginner_radiance_plot_pane = pn.panel(pn.bind(make_beginner_radiance_plot, beginner_radiance_button.param.clicks))

beginner_input_tab = pn.Column(
    pn.pane.Markdown("*Input options are under construction.*")
)

beginner_output_tab = pn.Column(
    pn.Row(pn.pane.Markdown("**Atmospheric model:**", margin=(0, 0, 0, 0)), beginner_plot_options, beginner_model_button),
    beginner_model_plot_pane,
    pn.layout.Divider(),
    pn.Row(pn.pane.Markdown("**Radiative transfer simulation:**", margin=(0, 0, 0, 0)), 
           pn.pane.Markdown("**Rerun:**", margin=(0, 5, 0, 10)), beginner_rerun_switch, 
           beginner_radiance_button),
    beginner_radiance_plot_pane,
    margin=10
)

beginner_tabs = pn.Tabs(
    ("Input", beginner_input_tab),
    ("Output", beginner_output_tab)
)

beginner_layout = pn.Column(
    pn.pane.Markdown(
        """
        ## Beginner Workspace
        
        *This is the Beginner pane/page.*
        
        This workspace will guide you through running standard simulations step-by-step.
        """
    ),
    pn.Row(working_dir_input, select_dir_button, runname_input),
    pn.layout.Divider(),
    beginner_tabs,
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
    header_background="#1a252f",
    sidebar_width=150
)

# Serve the application layout
template.show(port=5006, threaded=True, open=False)

# Define the local URL string pointing to that port
url = "http://localhost:5006"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
splash_html_path = os.path.join(ROOT_DIR, 'assets', 'splash.html')

show_splash = '--show-splash' in sys.argv

def poll_server_and_load():
    global window
    start_time = time.time()
    
    # Poll for 200 OK status
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
        
    if show_splash:
        elapsed = time.time() - start_time
        wait_time = 10.5  # Ensure splash screen displays for ~10.5 seconds
        if elapsed < wait_time:
            time.sleep(wait_time - elapsed)
            
        # Smooth fade out
        splash_window.evaluate_js('document.body.style.transition = "opacity 1s ease-in-out"; document.body.style.opacity = "0";')
        time.sleep(1)
        
        # Create the main window
        window = webview.create_window('NEMESIS Studio', url=url, width=1200, height=800)
        window.events.closed += on_closed
        
        # Close the splash window
        splash_window.destroy()
    else:
        window.load_url(url)

def on_closed():
    os._exit(0)

# Global variable for the main window
window = None

if show_splash:
    # Initialize pywebview frameless window for the splash screen
    splash_window = webview.create_window('NEMESIS Studio Splash', url=splash_html_path, width=640, height=360, frameless=True)
else:
    # Initialize main window directly
    window = webview.create_window('NEMESIS Studio', url='data:text/html,<html><body style="background-color: #1a252f; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif;"><h2>Loading NEMESIS Studio...</h2></body></html>', width=1200, height=800)
    window.events.closed += on_closed

# Start the background thread
threading.Thread(target=poll_server_and_load, daemon=True).start()

webview.start()

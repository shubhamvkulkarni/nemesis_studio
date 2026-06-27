import sys
import os
import time
import threading
import panel as pn
import requests
import webview
import plots
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
            return plots.get_pressure_temp_plot(ref_path)
        elif selected_plot == "Gases":
            return plots.get_gases_plot(ref_path)
        elif selected_plot == "Aerosols":
            return plots.get_aerosols_plot(aerosol_path)
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", styles={'color': 'red'})

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
            
        return plots.get_spectrum_plot(runname_path)
    except subprocess.CalledProcessError as e:
        return pn.pane.Markdown(f"**Error running Nemesis simulation:** Process exited with code {e.returncode}.", styles={'color': 'red'})
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", styles={'color': 'red'})

radiance_plot_pane = pn.panel(pn.bind(make_radiance_plot, radiance_button.param.clicks))

# --- Variability Section ---
var_type_select = pn.widgets.Select(name="Variability", options=["Temperature", "Gases", "Aerosols"], value="Temperature")
var_name_select = pn.widgets.Select(name="Parameter Name", options=[])
var_name_select.visible = False
var_percent_input = pn.widgets.FloatInput(name="% Variation", value=10.0, step=1.0)
var_calc_button = pn.widgets.Button(name="Calculate", button_type="primary", width=100)

@pn.depends(var_type_select.param.value, planet_select.param.value, watch=True)
def update_var_name_select(var_type, planet):
    planet = planet.lower()
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(ROOT_DIR, "outreach", planet, f"{planet}_main")
    
    if var_type == "Temperature":
        var_name_select.visible = False
        var_name_select.options = []
    elif var_type == "Gases":
        var_name_select.visible = True
        ref_path = os.path.join(base_path, f"{planet}.ref")
        if os.path.exists(ref_path):
            import data_read
            df = data_read.read_ref_file(ref_path)
            gas_cols = [col for col in df.columns if col not in ['Height (km)', 'Pressure (atm)', 'Temp (K)']]
            var_name_select.options = gas_cols
            if gas_cols:
                var_name_select.value = gas_cols[0]
        else:
            var_name_select.options = []
    elif var_type == "Aerosols":
        var_name_select.visible = True
        aerosol_path = os.path.join(base_path, "aerosol.ref")
        if os.path.exists(aerosol_path):
            import data_read
            df = data_read.read_aerosol_file(aerosol_path)
            mode_cols = [col for col in df.columns if col.startswith('Mode')]
            var_name_select.options = mode_cols
            if mode_cols:
                var_name_select.value = mode_cols[0]
        else:
            var_name_select.options = []

def calculate_variability(clicks):
    if clicks == 0:
        return pn.pane.Markdown("*Select parameters and click Calculate to view variability*")
        
    planet = planet_select.value.lower()
    var_type = var_type_select.value
    var_name = var_name_select.value if var_name_select.visible else "temp"
    percent = var_percent_input.value
    
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    outreach_dir = os.path.join(ROOT_DIR, "outreach", planet)
    main_dir = os.path.join(outreach_dir, f"{planet}_main")
    runname = planet
    
    factor_plus = 1.0 + (percent / 100.0)
    factor_minus = 1.0 - (percent / 100.0)
    
    safe_name = var_name.replace(' ', '_').lower()
    dir_plus = os.path.join(outreach_dir, f"{planet}_{var_type.lower()}_{safe_name}_{factor_plus}")
    dir_minus = os.path.join(outreach_dir, f"{planet}_{var_type.lower()}_{safe_name}_{factor_minus}")
    
    import shutil
    import data_write
    import data_read
    
    if os.path.exists(dir_plus):
        shutil.rmtree(dir_plus)
    shutil.copytree(main_dir, dir_plus, dirs_exist_ok=True)
    
    if os.path.exists(dir_minus):
        shutil.rmtree(dir_minus)
    shutil.copytree(main_dir, dir_minus, dirs_exist_ok=True)
    
    if var_type == "Temperature":
        ivar1 = 0
    elif var_type == "Gases":
        base_var_name = var_name.split('_')[0]
        ivar1 = data_read.GAS_NAME_TO_ID.get(base_var_name, 1)
    elif var_type == "Aerosols":
        try:
            mode_num = int(var_name.split()[1])
            ivar1 = -mode_num
        except:
            ivar1 = -1
            
    ivar2 = 0
    ivar3 = 3
    varident = (ivar1, ivar2, ivar3)
    
    apr_plus = os.path.join(dir_plus, f"{runname}.apr")
    data_write.write_apr_file(apr_plus, [{'VARIDENT': varident, 'VARPARAM': (factor_plus, 1e-10)}])
    
    apr_minus = os.path.join(dir_minus, f"{runname}.apr")
    data_write.write_apr_file(apr_minus, [{'VARIDENT': varident, 'VARPARAM': (factor_minus, 1e-10)}])
    
    cmd = f'docker run --rm -i -v "$(pwd)":/data -w /data patrickirwinoxford/docker_nemesis Nemesis < {runname}.nam > test.prc'
    
    print(f"--- Running NEMESIS variability simulations in parallel ---")
    print(f"Running NEMESIS in: {dir_plus}")
    print(f"Running NEMESIS in: {dir_minus}")
    p_plus = subprocess.Popen(cmd, shell=True, executable='/bin/zsh', cwd=dir_plus)
    p_minus = subprocess.Popen(cmd, shell=True, executable='/bin/zsh', cwd=dir_minus)
    
    p_plus.wait()
    p_minus.wait()
    
    if p_plus.returncode != 0 or p_minus.returncode != 0:
        return pn.pane.Markdown("**Error running Nemesis simulation** for variability.", styles={'color': 'red'})
        
    print(f"--- NEMESIS simulations completed in both directories ---")
    
    try:
        main_mre_path = os.path.join(main_dir, f"{runname}.mre")
        plus_mre_path = os.path.join(dir_plus, f"{runname}.mre")
        minus_mre_path = os.path.join(dir_minus, f"{runname}.mre")
        
        main_data = data_read.read_mre_file(main_mre_path)
        plus_data = data_read.read_mre_file(plus_mre_path)
        minus_data = data_read.read_mre_file(minus_mre_path)
        
        NGEOM = main_data['NGEOM']
        spx_filepath = os.path.join(main_dir, f"{runname}.spx")
        if os.path.exists(spx_filepath):
            spx_data = data_read.read_spx_file(spx_filepath)
        else:
            spx_data = None
            
        inp_filepath = os.path.join(main_dir, f"{runname}.inp")
        if os.path.exists(inp_filepath):
            inp_data = data_read.read_inp_file(inp_filepath)
            ispace = inp_data.get('ISPACE', 0)
            iform = inp_data.get('IFORM', 0)
            x_label = 'Wavelength (μm)' if ispace == 1 else 'Wavenumber (cm⁻¹)'
            if iform == 0:
                y_label = 'Radiance (μW cm⁻² sr⁻¹ μm⁻¹)' if ispace == 1 else 'Radiance (nW cm⁻² sr⁻¹ (cm⁻¹)⁻¹)'
            elif iform == 1:
                y_label = 'Fplan/Fstar (dimensionless)'
            elif iform == 2:
                y_label = '100*Aplan/Astar (dimensionless)'
            elif iform == 3:
                y_label = 'Flux (W μm⁻¹)' if ispace == 1 else 'Flux (W (cm⁻¹)⁻¹)'
            elif iform == 4:
                y_label = 'Flux Density (W cm⁻² μm⁻¹)' if ispace == 1 else 'Flux Density (W cm⁻² (cm⁻¹)⁻¹)'
            else:
                y_label = 'Radiance'
        else:
            x_label = 'WAVENUMBER'
            y_label = 'SIMULATED_RADIANCE'
            
        import pandas as pd
        import holoviews as hv
        
        plots_list = []
        for g in range(NGEOM):
            if spx_data and g < len(spx_data):
                vconv = spx_data[g]['vconv']
            else:
                vconv = main_data['specs'][g, :, 1]
                
            radiance_main = main_data['specs'][g, :, 5][:len(vconv)]
            radiance_plus = plus_data['specs'][g, :, 5][:len(vconv)]
            radiance_minus = minus_data['specs'][g, :, 5][:len(vconv)]
            
            import numpy as np
            df = pd.DataFrame({
                x_label: vconv,
                'Original': radiance_main,
                'Min_Var': np.minimum(radiance_plus, radiance_minus),
                'Max_Var': np.maximum(radiance_plus, radiance_minus)
            })
            
            label_suffix = f' (Geom {g+1})' if NGEOM > 1 else ''
            p_area = hv.Area(df, kdims=[x_label], vdims=['Min_Var', 'Max_Var'], label=f'±{percent}% Variability{label_suffix}').opts(alpha=0.3, color='red', line_alpha=0)
            p_line = df.hvplot.line(x=x_label, y='Original', label=f'Original{label_suffix}', color='black')
            
            plots_list.append(p_area * p_line)
            
        if len(plots_list) > 1:
            plot = hv.Overlay(plots_list)
        else:
            plot = plots_list[0]
            
        return plot.opts(
            title=f'Variability of {var_type} ({var_name})',
            width=1200, height=500,
            show_grid=True,
            xlabel=x_label,
            ylabel=y_label
        )
        
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating variability plot:** {str(e)}", styles={'color': 'red'})

variability_plot_pane = pn.panel(pn.bind(calculate_variability, var_calc_button.param.clicks))

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
    pn.layout.Divider(),
    pn.Row(pn.pane.Markdown("**Variability:**", margin=(0, 0, 0, 0)), 
           var_type_select, var_name_select, var_percent_input, var_calc_button),
    variability_plot_pane,
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
        return pn.pane.Markdown("**Error:** Please select a working directory and enter a runname.", styles={'color': 'red'})
        
    ref_path = os.path.join(base_path, f"{runname}.ref")
    aerosol_path = os.path.join(base_path, "aerosol.ref")
    
    selected_plot = beginner_plot_options.value
    try:
        if selected_plot == "Pressure and Temp":
            return plots.get_pressure_temp_plot(ref_path)
        elif selected_plot == "Gases":
            return plots.get_gases_plot(ref_path)
        elif selected_plot == "Aerosols":
            return plots.get_aerosols_plot(aerosol_path)
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", styles={'color': 'red'})

beginner_model_plot_pane = pn.panel(pn.bind(make_beginner_model_plot, beginner_model_button.param.clicks))

beginner_radiance_button = pn.widgets.Button(name="Plot", button_type="primary", width=100)
beginner_rerun_switch = pn.widgets.Switch(name="Rerun", value=False)

def make_beginner_radiance_plot(clicks):
    if clicks == 0:
        return pn.pane.Markdown("*Click Plot to view radiative transfer simulation*")
        
    base_path = working_dir_input.value
    runname = runname_input.value
    
    if not base_path or not runname:
        return pn.pane.Markdown("**Error:** Please select a working directory and enter a runname.", styles={'color': 'red'})
        
    runname_path = os.path.join(base_path, runname)
    
    try:
        if beginner_rerun_switch.value:
            print(f"--- Running NEMESIS simulation for {runname} ---")
            cmd = f'docker run --rm -i -v "$(pwd)":/data -w /data patrickirwinoxford/docker_nemesis Nemesis < {runname}.nam > test.prc'
            subprocess.run(cmd, shell=True, executable='/bin/zsh', cwd=base_path, check=True)
            print(f"--- NEMESIS simulation completed ---")
            
        return plots.get_spectrum_plot(runname_path)
    except subprocess.CalledProcessError as e:
        return pn.pane.Markdown(f"**Error running Nemesis simulation:** Process exited with code {e.returncode}.", styles={'color': 'red'})
    except Exception as e:
        return pn.pane.Markdown(f"**Error generating plot:** {str(e)}", styles={'color': 'red'})

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

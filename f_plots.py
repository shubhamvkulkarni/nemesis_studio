import os
import numpy as np
import pandas as pd
import hvplot.pandas
import holoviews as hv
import sys

# Add ref folder to path to import lib_nemesis_py
sys.path.append(os.path.join(os.path.dirname(__file__), 'ref'))
import lib_nemesis_py

def read_ref_file(filepath):
    with open(filepath, 'r') as f:
        atm_ref = f.readlines()
        
    line_no = 0
    for i in range(len(atm_ref)):
        if not atm_ref[i].strip().startswith('#'):
            line_no = i
            break
            
    # skip AMFORM1 and AMFORM2
    NP_line = atm_ref[2 + line_no]
    vals = NP_line.split()
    IPLANET = float(vals[0])
    LATTITUDE = float(vals[1])
    NP = int(float(vals[2]))
    NVMR = int(float(vals[3]))
    MOLWT = float(vals[4])
    
    atm_profile = np.zeros((NP, NVMR + 3))
    for pres_level in range(NP):
        line = atm_ref[pres_level + 4 + NVMR + line_no]
        atm_profile[pres_level, :] = np.fromstring(line, dtype=float, sep=' ')
        
    # Create DataFrame
    columns = ['Height (km)', 'Pressure (atm)', 'Temp (K)'] + [f'Gas {i+1}' for i in range(NVMR)]
    df = pd.DataFrame(atm_profile, columns=columns)
    return df

def read_aerosol_file(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
    if not lines:
        raise ValueError("Aerosol file is empty or contains only comments.")
        
    header = lines[0].split()
    ngeo = int(header[0])
    nmode = int(header[1])
    
    flat_data = []
    for line in lines[1:]:
        for token in line.split():
            try:
                flat_data.append(float(token))
            except ValueError:
                pass
                
    flat_data = np.array(flat_data)
    expected_len = ngeo * (nmode + 1)
    if len(flat_data) < expected_len:
        padded = np.zeros(expected_len)
        padded[:len(flat_data)] = flat_data
        flat_data = padded
    elif len(flat_data) > expected_len:
        flat_data = flat_data[:expected_len]
        
    aero_grid = flat_data.reshape((ngeo, nmode + 1))
    
    columns = ['Height (km)'] + [f'Mode {i+1}' for i in range(nmode)]
    df = pd.DataFrame(aero_grid, columns=columns)
    return df

def get_pressure_temp_plot(ref_filepath):
    if not os.path.exists(ref_filepath):
        return hv.Div(f"File not found: {ref_filepath}")
        
    df = read_ref_file(ref_filepath)
    
    def twinx_hook(plot, element):
        from bokeh.models import LinearAxis, Range1d
        p = plot.state
        
        # Calculate temperature range with padding
        t_min, t_max = df['Temp (K)'].min(), df['Temp (K)'].max()
        padding = (t_max - t_min) * 0.05 if t_max != t_min else 10
        p.extra_x_ranges = {"temp_axis": Range1d(start=t_min - padding, end=t_max + padding)}
        
        # Add temperature axis to the top
        temp_axis = LinearAxis(x_range_name="temp_axis", axis_label="Temperature (K)", axis_line_color="red", axis_label_text_color="red", major_tick_line_color="red", major_label_text_color="red")
        p.add_layout(temp_axis, 'above')
        
        # Assign the second renderer (Temp) to the new x-axis
        if len(p.renderers) > 1:
            p.renderers[1].x_range_name = "temp_axis"
            
        # Add minor grids
        p.xgrid.minor_grid_line_color = 'lightgray'
        p.xgrid.minor_grid_line_alpha = 0.5
        p.ygrid.minor_grid_line_color = 'lightgray'
        p.ygrid.minor_grid_line_alpha = 0.5

    # Pressure plot (bottom axis, log scale)
    p1 = df.hvplot.line(x='Pressure (atm)', y='Height (km)', logx=True, 
                        color='blue', xlabel='Pressure (atm)', ylabel='Altitude (km)')
    
    # Temperature plot (will be mapped to top axis by the hook)
    p2 = df.hvplot.line(x='Temp (K)', y='Height (km)', 
                        color='red', xlabel='')
    
    return (p1 * p2).opts(hooks=[twinx_hook], show_grid=True, title='Pressure & Temperature Profile', width=1000, height=500)

def get_gases_plot(ref_filepath):
    if not os.path.exists(ref_filepath):
        return hv.Div(f"File not found: {ref_filepath}")
        
    df = read_ref_file(ref_filepath)
    
    gas_cols = [col for col in df.columns if col.startswith('Gas')]
    
    df_melted = df.melt(id_vars=['Height (km)'], value_vars=gas_cols, var_name='Gas', value_name='VMR')
    
    def grid_hook(plot, element):
        p = plot.state
        p.xgrid.minor_grid_line_color = 'lightgray'
        p.xgrid.minor_grid_line_alpha = 0.5
        p.ygrid.minor_grid_line_color = 'lightgray'
        p.ygrid.minor_grid_line_alpha = 0.5
    
    p = df_melted.hvplot.line(x='VMR', y='Height (km)', by='Gas', logx=True, 
                              title='Gas Volume Mixing Ratios', width=1200, height=500,
                              xlabel='VMR', ylabel='Altitude (km)').opts(show_grid=True, hooks=[grid_hook])
    return p

def get_aerosols_plot(aero_filepath):
    if not os.path.exists(aero_filepath):
        return hv.Div(f"File not found: {aero_filepath}")
        
    df = read_aerosol_file(aero_filepath)
    
    mode_cols = [col for col in df.columns if col.startswith('Mode')]
    
    df_melted = df.melt(id_vars=['Height (km)'], value_vars=mode_cols, var_name='Mode', value_name='Density')
    
    def grid_hook(plot, element):
        p = plot.state
        p.xgrid.minor_grid_line_color = 'lightgray'
        p.xgrid.minor_grid_line_alpha = 0.5
        p.ygrid.minor_grid_line_color = 'lightgray'
        p.ygrid.minor_grid_line_alpha = 0.5
        
    p = df_melted.hvplot.line(x='Density', y='Height (km)', by='Mode', logx=True,
                              title='Aerosol Profiles', width=1200, height=500,
                              xlabel='Aerosol Density', ylabel='Altitude (km)').opts(show_grid=True, hooks=[grid_hook])
    return p

def get_spectrum_plot(runname_path):
    if not os.path.exists(runname_path + '.mre'):
        return hv.Div(f"File not found: {runname_path}.mre")
        
    try:
        # read_ref returns: IPLANET, LATTITUDE, NP, NVMR, MOLWT, atm_profile
        IPLANET, LATTITUDE, NP, NVMR, MOLWT, atm_profile = lib_nemesis_py.read_ref(runname_path)
        
        # read_mre returns: iretrv, ispec, NGEOM, ny, nx, ny1, LATITUDE, LONGITUDE, height_lay, NWAVE, specs, NVAR
        res = lib_nemesis_py.read_mre(runname_path, IPLANET, LATTITUDE, NP, NVMR, MOLWT, atm_profile, if_var='no')
        NGEOM = res[2]
        specs = res[10]
        
        plots = []
        for g in range(NGEOM):
            # specs[:, :, 1] is lambda (Wavenumber), specs[:, :, 5] is R_fit (Simulated Radiance)
            df = pd.DataFrame({
                'WAVENUMBER': specs[g, :, 1],
                'SIMULATED_RADIANCE': specs[g, :, 5]
            })
            p = df.hvplot.line(x='WAVENUMBER', y='SIMULATED_RADIANCE', 
                               label=f'Geom {g+1}' if NGEOM > 1 else 'Simulated Spectra')
            plots.append(p)
            
        if len(plots) > 1:
            plot = hv.Overlay(plots)
        else:
            plot = plots[0]
            
        return plot.opts(
            title='Simulated Spectra (Radiative Transfer)', 
            width=1200, height=500, 
            show_grid=True,
            xlabel='WAVENUMBER',
            ylabel='SIMULATED_RADIANCE'
        )
    except Exception as e:
        return hv.Div(f"Error reading .mre file: {str(e)}")

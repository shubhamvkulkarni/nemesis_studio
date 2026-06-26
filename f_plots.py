import os
import numpy as np
import pandas as pd
import hvplot.pandas
import holoviews as hv

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
        aero_info = f.readlines()
        
    temp = np.fromstring(aero_info[0], dtype=int, sep=' ')
    ngeo = temp[0]
    nmode = temp[1]
    
    aero_grid = np.zeros((ngeo, nmode + 1))
    
    if nmode < 5:
        for level in range(ngeo):
            aero_grid[level, :] = np.fromstring(aero_info[1 + level], dtype=float, sep=' ')
    else:
        for level in range(ngeo):
            line_no = 1 + level * 2
            aero_grid[level, :5] = np.fromstring(aero_info[line_no], dtype=float, sep=' ')
            aero_grid[level, 5:] = np.fromstring(aero_info[1 + line_no], dtype=float, sep=' ')
            
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
        
    p = df_melted.hvplot.line(x='Density', y='Height (km)', by='Mode', 
                              title='Aerosol Profiles', width=1200, height=500,
                              xlabel='Aerosol Density', ylabel='Altitude (km)').opts(show_grid=True, hooks=[grid_hook])
    return p

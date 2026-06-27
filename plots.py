import os
import numpy as np
import pandas as pd
import hvplot.pandas
import holoviews as hv

# Import reading functions
from data_read import read_ref_file, read_aerosol_file, read_spx_file, read_inp_file, read_mre_file

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
    
    gas_cols = [col for col in df.columns if col not in ['Height (km)', 'Pressure (atm)', 'Temp (K)']]
    
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
        mre_data = read_mre_file(runname_path + '.mre')
        NGEOM = mre_data['NGEOM']
        specs = mre_data['specs']
        
        spx_filepath = runname_path + '.spx'
        if os.path.exists(spx_filepath):
            spx_data = read_spx_file(spx_filepath)
        else:
            spx_data = None
            
        inp_filepath = runname_path + '.inp'
        if os.path.exists(inp_filepath):
            inp_data = read_inp_file(inp_filepath)
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
            
        plots = []
        for g in range(NGEOM):
            if spx_data and g < len(spx_data):
                vconv = spx_data[g]['vconv']
            else:
                vconv = specs[g, :, 1]
                
            # specs[:, :, 5] is R_fit (Simulated Radiance)
            radiance = specs[g, :, 5][:len(vconv)]
            df = pd.DataFrame({
                x_label: vconv,
                y_label: radiance
            })
            p = df.hvplot.line(x=x_label, y=y_label, 
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
            xlabel=x_label,
            ylabel=y_label
        )
    except Exception as e:
        return hv.Div(f"Error reading .mre file: {str(e)}")

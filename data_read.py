import os
import numpy as np
import pandas as pd

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

def read_spx_file(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
    header = lines[0].split()
    FWHM = float(header[0])
    LATITUDE = float(header[1])
    LONGITUDE = float(header[2])
    NGEOM = int(header[3])
    
    idx = 1
    spectra = []
    
    for g in range(NGEOM):
        NCONV = int(lines[idx].split()[0])
        idx += 1
        NAV = int(lines[idx].split()[0])
        idx += 1
        
        # Skip NAV lines
        for _ in range(NAV):
            idx += 1
            
        # Read NCONV lines
        vconv = np.zeros(NCONV)
        y = np.zeros(NCONV)
        err = np.zeros(NCONV)
        for i in range(NCONV):
            vals = lines[idx].split()
            vconv[i] = float(vals[0])
            y[i] = float(vals[1])
            err[i] = float(vals[2])
            idx += 1
            
        spectra.append({
            'vconv': vconv,
            'y': y,
            'err': err
        })
        
    return spectra

def read_inp_file(filepath):
    """
    Reads a NEMESIS .inp file.
    Returns a dictionary of the parsed parameters.
    """
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
    if not lines:
        raise ValueError("INP file is empty")
        
    inp_data = {}
    
    # Line 1: ISPACE, ISCAT, ILBL
    # ISPACE: 0 = wavenumber (cm-1), 1 = wavelength (um)
    l1 = lines[0].split()
    inp_data['ISPACE'] = int(float(l1[0]))
    inp_data['ISCAT'] = int(float(l1[1]))
    inp_data['ILBL'] = int(float(l1[2]))
    
    # Line 2: WOFF
    inp_data['WOFF'] = float(lines[1].split()[0])
    
    # Line 3: ENAME
    inp_data['ENAME'] = lines[2].split()[0]
    
    # Line 4: NITER
    inp_data['NITER'] = int(float(lines[3].split()[0]))
    
    # Line 5: PHILIMIT
    inp_data['PHILIMIT'] = float(lines[4].split()[0])
    
    # Line 6: NSPEC, IOFF
    l6 = lines[5].split()
    inp_data['NSPEC'] = int(float(l6[0]))
    inp_data['IOFF'] = int(float(l6[1]))
    
    # Line 7: LIN
    inp_data['LIN'] = int(float(lines[6].split()[0]))
    
    # Line 8: IFORM (optional)
    if len(lines) > 7:
        l8 = lines[7].split()
        inp_data['IFORM'] = int(float(l8[0]))
        if len(l8) > 1:
            inp_data['PERCBOOL'] = l8[1].lower() in ['.true.', 't', 'true', '1']
            
    # Line 9: PERCBOOL (optional, if on its own line)
    if len(lines) > 8 and 'PERCBOOL' not in inp_data:
        l9 = lines[8].split()
        inp_data['PERCBOOL'] = l9[0].lower() in ['.true.', 't', 'true', '1']
        
    return inp_data

def read_mre_file(filepath):
    """
    Reads a NEMESIS .mre file and returns a dictionary with the parsed spectra.
    """
    with open(filepath, 'r') as mre_file:
        iretrv = np.fromstring(mre_file.readline(), dtype=int, sep=' ')
        ispec, NGEOM, ny, nx, ny1 = np.fromstring(mre_file.readline(), dtype=int, sep=' ')
        LATITUDE, LONGITUDE = np.fromstring(mre_file.readline(), dtype=float, sep=' ')
        NWAVE = int(ny / NGEOM)
        
        mre_file.readline()
        mre_file.readline()
        
        specs = np.zeros((NGEOM, NWAVE, 7))
        for geoms in range(NGEOM):
            for waves in range(NWAVE):
                specs[geoms, waves, :] = np.fromstring(mre_file.readline(), dtype=float, sep=' ')
                
    return {
        'NGEOM': NGEOM,
        'NWAVE': NWAVE,
        'specs': specs
    }

import os
import numpy as np
import pandas as pd

RADTRAN_GAS_IDS = {
    1: 'H2O', 2: 'CO2', 3: 'O3', 4: 'N2O', 5: 'CO', 6: 'CH4', 7: 'O2',
    8: 'NO', 9: 'SO2', 10: 'NO2', 11: 'NH3', 12: 'HNO3', 13: 'OH',
    14: 'HF', 15: 'HCL', 16: 'HBr', 17: 'HI', 18: 'ClO', 19: 'OCS',
    20: 'H2CO', 21: 'HOCl', 22: 'N2', 23: 'HCN', 24: 'CH3Cl', 25: 'H2O2',
    26: 'C2H2', 27: 'C2H6', 28: 'PH3', 29: 'C2N2', 30: 'C4H2', 31: 'HC3N',
    32: 'C2H4', 33: 'GeH4', 34: 'C3H8', 35: 'HCOOH', 36: 'H2S', 37: 'COF2',
    38: 'SF6', 39: 'H2', 40: 'He', 41: 'AsH3', 42: 'C3H4', 43: 'ClONO2',
    44: 'HO2', 45: 'O', 46: 'NO+', 47: 'CH3OH', 48: 'H', 49: 'C6H6',
    50: 'CH3CN', 51: 'CH2NH', 52: 'C2H3CN', 53: 'HCP', 54: 'CS', 55: 'HC5N',
    56: 'HC7N', 57: 'C2H5CN', 58: 'CH3NH2', 59: 'HNC', 60: 'Na', 61: 'K',
    62: 'TiO', 63: 'VO', 64: 'CH2CCH2', 65: 'C4N2', 66: 'C5H5N', 67: 'C5H4N2',
    68: 'C7H8', 69: 'C8H6', 70: 'C5H5CN', 71: 'HOBr', 72: 'CH3Br', 73: 'CF4',
    74: 'SO3', 75: 'Ne', 76: 'Ar', 77: 'COCl2', 78: 'SO', 79: 'H2SO4',
    80: 'e-', 81: 'H3+', 82: 'FeH', 83: 'AlO', 84: 'AlCl', 85: 'AlF',
    86: 'AlH', 87: 'BeH', 88: 'C2', 89: 'CaF', 90: 'CaH', 91: 'H-',
    92: 'CaO', 93: 'CH', 94: 'CH3', 95: 'CH3F', 96: 'CN', 97: 'CP',
    98: 'CrH', 99: 'HD+', 100: 'HeH+', 101: 'KCl', 102: 'KF', 103: 'LiCl',
    104: 'LiF', 105: 'LiH', 106: 'LiH+', 107: 'MgF', 108: 'MgH', 109: 'MgO',
    110: 'NaCl', 111: 'NaF', 112: 'NaH', 113: 'NH', 114: 'NS', 115: 'OH+',
    116: 'cis-P2H2', 117: 'trans-P2H2', 118: 'PH', 119: 'PN', 120: 'PO',
    121: 'PS', 122: 'ScH', 123: 'SH', 124: 'SiH', 125: 'SiH2', 126: 'SiH4',
    127: 'SiO', 128: 'SiO2', 129: 'SiS', 130: 'TiH'
}

GAS_NAME_TO_ID = {v: k for k, v in RADTRAN_GAS_IDS.items()}

def read_ref_file(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
    np_line_idx = -1
    for idx, line in enumerate(lines):
        vals = line.split()
        if len(vals) in [4, 5]:
            try:
                float(vals[0])
                float(vals[1])
                if float(vals[2]).is_integer() and float(vals[3]).is_integer():
                    np_line_idx = idx
                    break
            except ValueError:
                pass
                
    if np_line_idx == -1:
        raise ValueError("Could not find the parameter line (IPLANET LATITUDE NP NVMR [MOLWT])")
        
    vals = lines[np_line_idx].split()
    IPLANET = float(vals[0])
    LATITUDE = float(vals[1])
    NP = int(float(vals[2]))
    NVMR = int(float(vals[3]))
    
    gas_ids = []
    for i in range(NVMR):
        id_val = int(float(lines[np_line_idx + 1 + i].split()[0]))
        gas_ids.append(id_val)
        
    header_idx = np_line_idx + 1 + NVMR
    start_data_idx = header_idx
    if header_idx < len(lines):
        header_line = lines[header_idx]
        if header_line.startswith('"') or header_line.startswith("'") or header_line[0].isalpha():
            start_data_idx += 1
            
    atm_profile = np.zeros((NP, NVMR + 3))
    for i in range(NP):
        atm_profile[i, :] = np.fromstring(lines[start_data_idx + i], dtype=float, sep=' ')
        
    from collections import Counter
    base_names = [RADTRAN_GAS_IDS.get(gas_id, f'Gas_{gas_id}') for gas_id in gas_ids]
    counts = Counter(base_names)
    
    gas_names = []
    seen = {}
    for name in base_names:
        if counts[name] > 1:
            seen[name] = seen.get(name, 0) + 1
            gas_names.append(f"{name}_{seen[name]}")
        else:
            gas_names.append(name)
            
    columns = ['Height (km)', 'Pressure (atm)', 'Temp (K)'] + gas_names
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

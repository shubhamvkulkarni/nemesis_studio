import os
import f_plots
import panel as pn

base_path = os.path.join(os.getcwd(), "outreach", "jupiter", "jupiter_main")
ref_path = os.path.join(base_path, "jupiter.ref")
aerosol_path = os.path.join(base_path, "aerosol.ref")

try:
    print("Testing gases plot...")
    p1 = f_plots.get_gases_plot(ref_path)
    print("Gases plot type:", type(p1))
except Exception as e:
    print("Error in gases plot:", str(e))

try:
    print("Testing aerosols plot...")
    p2 = f_plots.get_aerosols_plot(aerosol_path)
    print("Aerosols plot type:", type(p2))
except Exception as e:
    print("Error in aerosols plot:", str(e))

import os
import f_plots
import panel as pn

# Test Jupiter
jupiter_base = os.path.join(os.getcwd(), "outreach", "jupiter", "jupiter_main")
jupiter_ref = os.path.join(jupiter_base, "jupiter.ref")
jupiter_aero = os.path.join(jupiter_base, "aerosol.ref")

print("--- Testing Jupiter ---")
try:
    df_jup_ref = f_plots.read_ref_file(jupiter_ref)
    print("Jupiter ref read successfully. Shape:", df_jup_ref.shape)
except Exception as e:
    print("Error reading Jupiter ref:", str(e))

try:
    df_jup_aero = f_plots.read_aerosol_file(jupiter_aero)
    print("Jupiter aerosol read successfully. Shape:", df_jup_aero.shape)
except Exception as e:
    print("Error reading Jupiter aerosol:", str(e))

# Test Venus
venus_base = os.path.join(os.getcwd(), "outreach", "venus", "venus_main")
venus_ref = os.path.join(venus_base, "venus.ref")
venus_aero = os.path.join(venus_base, "aerosol.ref")

print("\n--- Testing Venus ---")
try:
    df_ven_ref = f_plots.read_ref_file(venus_ref)
    print("Venus ref read successfully. Shape:", df_ven_ref.shape)
except Exception as e:
    print("Error reading Venus ref:", str(e))

try:
    df_ven_aero = f_plots.read_aerosol_file(venus_aero)
    print("Venus aerosol read successfully. Shape:", df_ven_aero.shape)
    print("Venus aerosol columns:", list(df_ven_aero.columns))
except Exception as e:
    print("Error reading Venus aerosol:", str(e))

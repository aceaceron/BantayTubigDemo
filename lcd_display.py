# lcd_display.py
import os
import time
import threading

try:
    from RPLCD.i2c import CharLCD
    _lcd_available = os.path.exists("/dev/i2c-1")
except ImportError:
    CharLCD = None
    _lcd_available = False

# ================== CONFIG ==================
_LCD_WIDTH = 20
_LCD_ROWS = 4
LCD_I2C_ADDRESS = 0x27

lcd = None
_lcd_lock = threading.Lock()
_last_error_time = 0

if _lcd_available:
    try:
        lcd = CharLCD(
            i2c_expander="PCF8574",
            address=LCD_I2C_ADDRESS,
            port=1,
            cols=_LCD_WIDTH,
            rows=_LCD_ROWS,
            dotsize=8,
            auto_linebreaks=False,
        )
        lcd.clear()
        print("LCD initialized successfully.")
    except Exception as e:
        print(f"LCD init failed: {e}. Using mock mode.")
        lcd = None
else:
    print("LCD not available. Running in mock mode.")

# --- Mock print wrapper ---
def _mock_print(msg):
    print(f"[LCD MOCK] {msg}")

def _safe_lcd_command(command, *args):
    global lcd, _last_error_time
    with _lcd_lock:
        if lcd is None:
            if command == "write_string":
                _mock_print(args[0])
            elif command == "clear":
                _mock_print("LCD cleared")
            return

        try:
            if command == "cursor_pos":
                lcd.cursor_pos = args
            else:
                func = getattr(lcd, command)
                func(*args)
        except Exception as e:
            print(f"LCD command error: {e}")
            lcd = None

# ================== HELPERS ==================
def clear_lcd(): _safe_lcd_command("clear")

def _write_row(row: int, text: str):
    _safe_lcd_command("cursor_pos", row, 0)
    _safe_lcd_command("write_string", text.ljust(_LCD_WIDTH)[:_LCD_WIDTH])

def show_startup_banner():
    clear_lcd()
    _write_row(0, "BantayTubig ready")

# ================== STATUS THREAD ==================
_status_thread = None
_status_stop = threading.Event()
_status_base = "BantayTubig ready"

def start_status(message: str, **kwargs):
    global _status_thread
    print(f"[LCD STATUS] {message}")
    if _status_thread is None or not _status_thread.is_alive():
        _status_stop.clear()
        _status_thread = threading.Thread(target=_status_loop, daemon=True)
        _status_thread.start()

def update_status(message: str):
    print(f"[LCD STATUS UPDATE] {message}")

def stop_status(final_message: str | None = None):
    _status_stop.set()
    if final_message:
        print(f"[LCD STATUS STOP] {final_message}")

def _status_loop():
    dots = ["", ".", "..", "..."]
    idx = 0
    while not _status_stop.is_set():
        line = f"{_status_base}{dots[idx]}"
        _write_row(0, line)
        idx = (idx + 1) % len(dots)
        time.sleep(0.5)

# ================== RUNTIME DISPLAYS ==================
def display_readings(temp, ph, tds, turbidity):
    clear_lcd()
    _write_row(0, f"Temp: {temp:.1f} C" if isinstance(temp, (int, float)) else "Temp: N/A")
    _write_row(1, f"pH: {ph:.1f}" if isinstance(ph, (int, float)) else "pH: N/A")
    _write_row(2, f"TDS: {tds:.0f} ppm" if isinstance(tds, (int, float)) else "TDS: N/A")
    _write_row(3, f"Turb: {turbidity:.1f} NTU" if isinstance(turbidity, (int, float)) else "Turb: N/A")

def display_water_quality(quality, ip_address=None):
    clear_lcd()
    q_map = {'good': "Good!", 'average': "Average", 'poor': "Poor!", 'bad': "BAD!"}
    _write_row(0, "Water Quality:")
    _write_row(1, q_map.get((quality or "").lower(), "Unknown"))
    if ip_address:
        _write_row(2, "View at:")
        _write_row(3, f"{ip_address}:5000")

def display_network_status():
    clear_lcd()
    _write_row(0, "Network Error:")
    _write_row(1, "WiFi Not Connected")

def display_hotspot_credentials(ssid, password):
    clear_lcd()
    _write_row(0, "Connect to Hotspot")
    _write_row(1, "to configure WiFi:")
    _write_row(2, f"SSID: {ssid}")
    _write_row(3, f"Pass: {password}")

def display_config_instructions(ip_address):
    clear_lcd()
    _write_row(0, "Device Connected!")
    _write_row(1, "Go to browser:")
    _write_row(2, f"{ip_address}:5000/setup")

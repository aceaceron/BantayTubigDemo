# lcd_display.py
import time
import threading
# --- LCD Import with Mock ---
try:
    from RPLCD.i2c import CharLCD
except ImportError:
    class MockLCD:
        def __init__(self, *args, **kwargs):
            print("[MOCK LCD] Initialized with", args, kwargs)
        def clear(self): print("[MOCK LCD] clear()")
        def write_string(self, s): print(f"[MOCK LCD] write_string: {s}")
        @property
        def cursor_pos(self): return (0, 0)
        @cursor_pos.setter
        def cursor_pos(self, pos): print(f"[MOCK LCD] cursor_pos set to {pos}")
    CharLCD = MockLCD


# ================== CONFIG ==================
_LCD_WIDTH = 20
_LCD_ROWS  = 4
LCD_I2C_ADDRESS = 0x27

# --- Global LCD Object & Lock ---
lcd = None
_lcd_lock = threading.Lock()
_last_error_time = 0  # To prevent spamming error messages

# ================== STATE ==================
_status_thread = None
_status_stop = threading.Event()
_status_base = "BantayTubig ready"
_progress_lines = ["", "", ""]
_progress_offsets = [0, 0, 0]

def _safe_lcd_command(command, *args):
    """
    A robust wrapper to execute LCD commands, preventing crashes from hardware errors.
    It will attempt to re-initialize the LCD if connection is lost.
    """
    global lcd, _last_error_time
    with _lcd_lock:
        if lcd is None:
            try:
                lcd = CharLCD(
                    i2c_expander='PCF8574',
                    address=LCD_I2C_ADDRESS,
                    port=1,
                    cols=_LCD_WIDTH,
                    rows=_LCD_ROWS,
                    dotsize=8,
                    auto_linebreaks=False
                )
                lcd.clear()
                print("LCD display initialized successfully.")
            except (OSError, Exception) as e:
                current_time = time.time()
                if current_time - _last_error_time > 15: # Print warning only every 15 seconds
                    print(f"Warning: Could not initialize LCD. Display is offline. Error: {e}")
                    _last_error_time = current_time
                lcd = None
                return

        try:
            if command == 'cursor_pos':
                lcd.cursor_pos = args
            else:
                func = getattr(lcd, command)
                func(*args)
        except (OSError, Exception) as e:
            current_time = time.time()
            if current_time - _last_error_time > 15:
                print(f"Warning: Lost connection to LCD. Cannot execute '{command}'. Error: {e}")
                _last_error_time = current_time
            lcd = None

# ================== HELPERS ==================
def _fit(text: str) -> str:
    text = (text or "")
    return text[:_LCD_WIDTH] if len(text) > _LCD_WIDTH else text.ljust(_LCD_WIDTH)

def clear_lcd():
    _safe_lcd_command('clear')

def _write_row(row: int, text: str):
    _safe_lcd_command('cursor_pos', row, 0)
    _safe_lcd_command('write_string', _fit(text))

def _marquee_view(s: str, width: int, offset: int) -> str:
    s = s or ""
    if len(s) <= width: return _fit(s)
    lead = 1 if offset > 0 else 0
    content_width = width - lead
    end_pos = offset + content_width
    trail = 1 if end_pos < len(s) else 0
    if trail: content_width -= 1
    visible = s[offset: offset + content_width]
    if len(visible) < content_width: visible = visible.ljust(content_width)
    return ("." if lead else "") + visible + ("." if trail else "")

def _render_progress_locked():
    for idx in range(3):
        row = 1 + idx
        msg = _progress_lines[idx]
        off = _progress_offsets[idx]
        text = _marquee_view(msg, _LCD_WIDTH, off) if len(msg) > _LCD_WIDTH else _fit(msg)
        _safe_lcd_command('cursor_pos', row, 0)
        _safe_lcd_command('write_string', text)

def _advance_offsets():
    for i in range(3):
        s = _progress_lines[i]
        if not s or len(s) <= _LCD_WIDTH: _progress_offsets[i] = 0; continue
        offset = _progress_offsets[i]
        lead = 1 if offset > 0 else 0
        content_width = _LCD_WIDTH - lead
        end_pos = offset + content_width
        trail = 1 if end_pos < len(s) else 0
        _progress_offsets[i] = offset + 1 if trail else 0

def _push_progress(message: str):
    msg = (message or "").strip()
    _progress_lines.insert(0, msg)
    _progress_lines.pop()
    _progress_offsets.insert(0, 0)
    _progress_offsets.pop()

# ================== STARTUP / PROGRESS ==================
def show_startup_banner():
    _safe_lcd_command('clear')
    _write_row(0, _fit(_status_base))
    for row in (1, 2, 3):
        _write_row(row, "")

def _status_loop():
    dots = ["", ".", "..", "..."]
    idx = 0
    while not _status_stop.is_set():
        base = _status_base
        room = max(0, _LCD_WIDTH - len(dots[idx]))
        line = (base[:room]) + dots[idx]
        _write_row(0, line)
        _render_progress_locked()
        idx = (idx + 1) % len(dots)
        _advance_offsets()
        time.sleep(0.5)

def start_status(message: str, **kwargs):
    global _status_thread
    if _status_thread is None or not _status_thread.is_alive():
        _status_stop.clear()
        _status_thread = threading.Thread(target=_status_loop, daemon=True)
        _status_thread.start()
    _push_progress(message)

def update_status(message: str):
    _push_progress(message)

def stop_status(final_message: str | None = None):
    _status_stop.set()
    if _status_thread and _status_thread.is_alive():
        _status_thread.join(timeout=1.0)
    if final_message is not None:
        _write_row(0, _fit(final_message))

# ========== RUNTIME DISPLAYS ==========
def display_readings(temp, ph, tds, turbidity):
    clear_lcd()
    temp_str = f"Temp: {temp:.1f} C" if isinstance(temp, (int, float)) else "Temp: N/A"
    _write_row(0, temp_str)
    _write_row(1, f"pH: {ph:.1f}")
    tds_str = f"TDS: {tds:.0f} ppm" if isinstance(tds, (int, float)) else "TDS: N/A"
    _write_row(2, tds_str)
    turb_str = f"Turb: {turbidity:.1f} NTU" if isinstance(turbidity, (int, float)) else "Turb: N/A"
    _write_row(3, turb_str)

def display_water_quality(quality, ip_address=None):
    """
    Displays water quality and, if provided, the IP address for the dashboard.
    """
    clear_lcd()
    _write_row(0, "Water Quality:")
    q_map = {'good': "Good!", 'average': "Average", 'poor': "Poor!", 'bad': "BAD!"}
    display_text = q_map.get((quality or "").lower(), "Unknown")
    _write_row(1, _fit(display_text))

    if ip_address:
        _write_row(2, "View dashboard at:")
        _write_row(3, f"{ip_address}:5000")
    else:
        _write_row(2, "")
        _write_row(3, "")

def display_network_status():
    """ Displays a message indicating the device is not connected to WiFi. """
    clear_lcd()
    _write_row(0, "Network Error:")
    _write_row(1, "WiFi Not Connected")
    _write_row(2, "")
    _write_row(3, "")


def display_hotspot_credentials(ssid, password):
    """Shows the hotspot SSID and password for the user to connect."""
    clear_lcd()
    _write_row(0, "Connect to Hotspot")
    _write_row(1, "to configure WiFi:")
    _write_row(2, f"SSID: {ssid}")
    _write_row(3, f"Pass: {password}")

def display_config_instructions(ip_address):
    """Shows clearer instructions after a client has connected."""
    clear_lcd()
    _write_row(0, "Device Connected!")
    _write_row(1, "In your browser, go")
    _write_row(2, "to this address:")
    _write_row(3, f"{ip_address}:5000/setup")

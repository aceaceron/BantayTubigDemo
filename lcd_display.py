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
            # Mock fallback
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

# --- Helpers (unchanged except using safe command) ---
def clear_lcd(): _safe_lcd_command("clear")

def _write_row(row: int, text: str):
    _safe_lcd_command("cursor_pos", row, 0)
    _safe_lcd_command("write_string", text.ljust(_LCD_WIDTH)[:_LCD_WIDTH])

def show_startup_banner():
    clear_lcd()
    _write_row(0, "BantayTubig ready")

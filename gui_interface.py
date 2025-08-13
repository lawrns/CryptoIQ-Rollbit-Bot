import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import websocket
from branding import apply_theme, COLORS, FONTS, status_badge, SPACE, CanvasCard, draw_vertical_gradient

class TradingGUI:
    def __init__(self, trading_interface):
        self.trading = trading_interface
        self.root = tk.Tk()
        self.root.title("CryptoIQ Trading Bot")
        # Increase default size so all content fits at a glance
        self.root.geometry("1200x800")
        # apply theme
        # gradient background canvas
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0, bd=0, bg=COLORS["bg_primary"])
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        def _redraw_bg(event=None):
            self.bg_canvas.delete("all")
            w = max(1, self.root.winfo_width())
            h = max(1, self.root.winfo_height())
            from branding import draw_vertical_gradient
            draw_vertical_gradient(self.bg_canvas, 0, 0, w, h, COLORS["bg_primary"], "#1A1C3B")
        self.root.bind("<Configure>", _redraw_bg)
        self.root.after(50, _redraw_bg)

        apply_theme(self.root)
        try:
            # prefer PNG icon (macOS); .ico if provided
            self.root.iconphoto(True, tk.PhotoImage(file="assets/app_icon.png"))
        except Exception:
            pass

        # WebSocket state
        self.ws_enabled = False
        self.ws_connected = False
        self.ws_app = None
        self.ws_thread = None
        self.ws_symbol_var = tk.StringVar(value="BTCUSDT")
        self.ws_status_var = tk.StringVar(value="Disconnected")

        # Risk/position management state
        self._pnl_peaks = {}
        self.active_positions_count = 0
        self.high_vol_var = tk.BooleanVar(value=False)

        # Ensure WS closes on exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)

        self.setup_gui()

    def setup_gui(self):
        # Header bar
        header = ttk.Frame(self.root, style="Crypto.TFrame")
        header.pack(fill='x', pady=SPACE)

        title = ttk.Label(header, text="CryptoIQ Trading Bot", style="Crypto.Header.TLabel")
        title.pack(side=tk.LEFT, padx=SPACE)

        # right side status badge
        self.status_label = ttk.Label(header, text="READY • Awaiting webhook", style="Crypto.StatusGood.TLabel")
        self.status_label.pack(side=tk.RIGHT, padx=SPACE)

        # Trading controls surface
        controls = ttk.Labelframe(self.root, text="Trading Controls", style="Crypto.TLabelframe")
        controls.pack(fill='x', padx=SPACE*2, pady=SPACE*2)

        # Wager
        ttk.Label(controls, text="Wager Amount", style="Crypto.Muted.TLabel").pack(pady=(SPACE, 0))
        self.wager_var = tk.StringVar(value="0.10")
        wager_entry = ttk.Entry(controls, textvariable=self.wager_var, style="Crypto.TEntry", width=18)
        wager_entry.pack(pady=(SPACE//2, SPACE))

        # Multiplier
        ttk.Label(controls, text="Multiplier", style="Crypto.Muted.TLabel").pack(pady=(SPACE, 0))
        self.multiplier_var = tk.StringVar(value="1000")
        multiplier_entry = ttk.Entry(controls, textvariable=self.multiplier_var, style="Crypto.TEntry", width=18)
        multiplier_entry.pack(pady=(SPACE//2, SPACE*2))

        # Trading buttons row
        button_row = ttk.Frame(controls, style="Crypto.Surface.TFrame")
        button_row.pack(pady=SPACE)

        up_btn = ttk.Button(button_row, text="BUY (UP)", style="Crypto.Primary.TButton", width=16, command=self.place_up_bet)
        up_btn.pack(side=tk.LEFT, padx=SPACE)

        down_btn = ttk.Button(button_row, text="SELL (DOWN)", style="Crypto.Danger.TButton", width=16, command=self.place_down_bet)
        down_btn.pack(side=tk.LEFT, padx=SPACE)

        # Cash out & close all
        cash_out_btn = ttk.Button(controls, text="Cash Out", style="Crypto.Neutral.TButton", width=30, command=self.cash_out)
        cash_out_btn.pack(pady=(SPACE, SPACE//2))

        close_all_btn = ttk.Button(controls, text="Close All Trades", style="Crypto.Danger.TButton", width=30, command=self.close_all_trades)
        close_all_btn.pack(pady=(SPACE//2, SPACE))

        # Style Treeview rows: alternate background and direction/P&L row-level colors
        # Note: configure tags after self.positions is created (below)
        self._tree_tags_ready = False

        # Active positions as a table
        table_frame = ttk.Labelframe(self.root, text="Active Positions", style="Crypto.TLabelframe")
        table_frame.pack(fill='both', expand=True, padx=SPACE*2, pady=SPACE*2)

        self.positions = ttk.Treeview(table_frame, style="Crypto.Treeview", columns=("direction","bias","wager","mult","entry","current","pnl"), show="headings")
        self.positions.heading("direction", text="Direction")
        self.positions.heading("bias", text="Bias")
        self.positions.heading("wager", text="Wager")
        self.positions.heading("mult", text="Multiplier")
        self.positions.heading("entry", text="Entry")
        self.positions.heading("current", text="Current")
        self.positions.heading("pnl", text="P&L")
        # Configure tags now that Treeview exists
        try:
            self.positions.tag_configure('odd', background="#1A1C3B")
            self.positions.tag_configure('even', background=COLORS["bg_secondary"])
            self.positions.tag_configure('dir_up', foreground=COLORS['positive'])
            self.positions.tag_configure('dir_down', foreground=COLORS['negative'])
            self.positions.tag_configure('pnl_pos', foreground=COLORS['positive'])
            self.positions.tag_configure('pnl_neg', foreground=COLORS['negative'])
            self._tree_tags_ready = True
        except Exception:
            pass
        self.positions.pack(fill='both', expand=True, padx=SPACE, pady=SPACE)

        # Configure heading styles via tag or style already set in branding.py
        # Row striping is applied in refresh_positions

        # Secondary controls
        control_row = ttk.Frame(self.root, style="Crypto.TFrame")
        control_row.pack(fill='x', padx=SPACE*2, pady=SPACE)

        refresh_btn = ttk.Button(control_row, text="Refresh Positions", style="Crypto.Secondary.TButton", command=self.refresh_positions)
        refresh_btn.pack(side=tk.LEFT)

        # WebSocket settings button
        ws_row = ttk.Frame(self.root, style="Crypto.TFrame")
        ws_row.pack(fill='x', padx=SPACE*2, pady=(0, SPACE*2))
        ws_btn = ttk.Button(ws_row, text="WebSocket Settings", style="Crypto.Purple.TButton", command=self.open_ws_settings)
        ws_btn.pack(side=tk.LEFT)

        # Auto-refresh
        self.auto_refresh()
        self.refresh_positions()

    def open_ws_settings(self):
        # Layover window for websocket settings
        win = tk.Toplevel(self.root)
        win.title("WebSocket Settings")
        win.configure(bg=COLORS["bg_secondary"])
        win.geometry("420x260")
        win.transient(self.root)
        win.grab_set()

        frame = ttk.Labelframe(win, text="Signal Stream", style="Crypto.TLabelframe")
        frame.pack(fill='both', expand=True, padx=SPACE*2, pady=SPACE*2)

        # Symbol
        ttk.Label(frame, text="Symbol", style="Crypto.Muted.TLabel").pack(pady=(SPACE, SPACE//2))
        ttk.Entry(frame, textvariable=self.ws_symbol_var, style="Crypto.TEntry", width=20).pack()

        # Toggle
        toggle_var = tk.BooleanVar(value=self.ws_enabled)

        def on_toggle():
            desired = toggle_var.get()
            if desired and not self.ws_enabled:
                self.ws_enabled = True
                self.start_websocket()
            elif not desired and self.ws_enabled:
                self.ws_enabled = False
                self.stop_websocket()
            toggle_var.set(self.ws_enabled)
        # High Volatility toggle (affects trailing buffer)
        hv_frame = ttk.Frame(frame, style="Crypto.Surface.TFrame")
        hv_frame.pack(pady=SPACE)
        ttk.Checkbutton(hv_frame, text="High Volatility Mode (wider trailing)", variable=self.high_vol_var).pack()


        ttk.Checkbutton(frame, text="Enable WebSocket Signals", variable=toggle_var, command=on_toggle).pack(pady=SPACE)

        # Status
        status_row = ttk.Frame(frame, style="Crypto.Surface.TFrame")
        status_row.pack(pady=SPACE)
        ttk.Label(status_row, text="Status:", style="Crypto.Muted.TLabel").pack(side=tk.LEFT)
        ttk.Label(status_row, textvariable=self.ws_status_var, style="Crypto.StatusGood.TLabel").pack(side=tk.LEFT, padx=SPACE)

        # Test signal & Close
        def send_test_signal():
            try:
                sample = {
                    's': (self.ws_symbol_var.get().strip().upper() or 'BTCUSDT'),
                    'ts': 1697059200000,
                    'pv': 100,
                    'cv': 120,
                    'delta': 20,
                    'strings': 10
                }
                self.handle_burst_data(sample)
            except Exception as e:
                messagebox.showerror("Test Signal Error", str(e))

        ttk.Button(frame, text="Send Test Signal", style="Crypto.Purple.TButton", command=send_test_signal).pack(pady=SPACE)
        ttk.Button(win, text="Close", style="Crypto.Secondary.TButton", command=win.destroy).pack(pady=(0, SPACE))

    def start_websocket(self):
        if self.ws_thread and self.ws_thread.is_alive():
            return

        symbol = self.ws_symbol_var.get().strip().upper() or "BTCUSDT"

        def on_open(ws):
            def _update():
                self.ws_connected = True
                self.ws_status_var.set(f"Connected ({symbol})")
                self.update_status("🟢 WebSocket connected", '#00ff00')
                try:
                    self.refresh_positions()
                except Exception:
                    pass
            self.root.after(0, _update)
            sub_msg = {"op": "sub", "symbols": symbol, "pv": 100, "strings": 10}
            ws.send(json.dumps(sub_msg))

        def on_message(ws, message):
            try:
                data = json.loads(message)
                # Only process if enabled
                if self.ws_enabled:
                    self.handle_burst_data(data)
            except Exception as e:
                print(f"WebSocket message error: {e}")

        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            self.root.after(0, lambda: self.ws_status_var.set("Error"))

        def on_close(ws, close_status_code, close_msg):
            def _update():
                self.ws_connected = False
                self.ws_status_var.set("Disconnected")
                if self.ws_enabled:
                    # Only mark as disconnected if user hasn't toggled off
                    self.update_status("🔴 WebSocket disconnected", '#ff0000')
            self.root.after(0, _update)

        ws_url = "wss://matrix.cryptoiq.com/api/sentinel/ws"
        self.ws_app = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        def run_ws():
            try:
                self.ws_app.run_forever(ping_interval=30, ping_payload=json.dumps({"op": "ping"}))
            except Exception as e:
                print(f"WebSocket thread error: {e}")

        self.ws_thread = threading.Thread(target=run_ws, daemon=True)
        self.ws_thread.start()
        self.update_status("🔄 Connecting WebSocket...", '#ffaa00')

    def stop_websocket(self):
        try:
            if self.ws_app is not None:
                try:
                    self.ws_app.keep_running = False
                except Exception:
                    pass
                try:
                    self.ws_app.close()
                except Exception:
                    pass
        finally:
            self.ws_app = None
            self.ws_connected = False
            self.ws_status_var.set("Disconnected")
            self.update_status("🟡 WebSocket disabled", '#ffaa00')

    def auto_refresh(self):  # increased frequency with idle guard
        """Auto-refresh active bets; run faster when positions exist."""
        try:
            active = self.trading.get_active_bets()
        except Exception:
            active = []
        if active:
            # Refresh now and schedule soon for near-real-time updates
            self.refresh_positions()
            delay = 1000  # 1s
        else:
            # Light refresh and back off a bit
            self.refresh_positions()
            delay = 5000  # 5s when idle
        self.root.after(delay, self.auto_refresh)

    def update_status(self, message, color=COLORS["accent_green"]):
        """Update status message badge color and text."""
        # switch style based on color intent
        style = "Crypto.StatusGood.TLabel"
        if color == COLORS["negative"]:
            style = "Crypto.StatusBad.TLabel"
        elif color in ("#ffaa00", "#F59E0B"):
            style = "Crypto.StatusWarn.TLabel"
        self.status_label.config(text=message, style=style)
        try:
            self.root.update_idletasks()
        except Exception:
            pass

    def handle_burst_data(self, data):
        # Guard symbol
        symbol = (data.get('s') or '').upper()
        if symbol != (self.ws_symbol_var.get().strip().upper() or 'BTCUSDT'):
            return

        direction = 'up' if data.get('delta', 0) > 0 else 'down'
        try:
            # Enforce max concurrent positions (4)
            if self.active_positions_count >= 4:
                self.update_status("Max positions reached - Signal ignored", COLORS["negative"])
                return
            wager = float(self.wager_var.get())
            multiplier = float(self.multiplier_var.get())
            success = self.trading.execute_trade(direction, wager, multiplier)
            if success:
                self.update_status(f"Signal received - {direction.upper()} trade placed", COLORS["positive"])
                self.refresh_positions()
            else:
                self.update_status(f"Failed to place trade on signal: {direction.upper()}", COLORS["negative"])
        except ValueError:
            self.update_status("Invalid wager/multiplier for signal trade", COLORS["negative"])
        except Exception as e:
            self.update_status(f"Signal trade error: {str(e)}", COLORS["negative"])

    def place_up_bet(self):
        try:
            if self.active_positions_count >= 4:
                self.update_status("Max positions reached - Trade blocked", COLORS["negative"])
                return
            self.update_status("🔄 Placing UP bet...", '#ffaa00')
            wager = float(self.wager_var.get())
            multiplier = float(self.multiplier_var.get())
            try:
                success = self.trading.execute_trade('up', wager, multiplier)
            except Exception as ex:
                # Handle navigation redirect cases bubbled up
                messagebox.showwarning("Redirection detected", f"Navigation occurred while placing UP trade. Retrying may help.\n\nDetails: {ex}")
                success = False
            if success:
                self.update_status("UP bet placed successfully", COLORS["positive"])
                self.refresh_positions()
            else:
                self.update_status("Failed to place UP bet", COLORS["negative"])
        except ValueError:
            self.update_status("Invalid input values", COLORS["negative"])
        except Exception as e:
            self.update_status(f"Error: {str(e)}", COLORS["negative"])

    def place_down_bet(self):
        try:
            if self.active_positions_count >= 4:
                self.update_status("Max positions reached - Trade blocked", COLORS["negative"])
                return
            self.update_status("🔄 Placing DOWN bet...", '#ffaa00')
            wager = float(self.wager_var.get())
            multiplier = float(self.multiplier_var.get())
            try:
                success = self.trading.execute_trade('down', wager, multiplier)
            except Exception as ex:
                messagebox.showwarning("Redirection detected", f"Navigation occurred while placing DOWN trade. Retrying may help.\n\nDetails: {ex}")
                success = False
            if success:
                self.update_status("DOWN bet placed successfully", COLORS["positive"])
                self.refresh_positions()
            else:
                self.update_status("Failed to place DOWN bet", COLORS["negative"])
        except ValueError:
            self.update_status("Invalid input values", COLORS["negative"])
        except Exception as e:
            self.update_status(f"Error: {str(e)}", COLORS["negative"])

    def cash_out(self):
        try:
            self.update_status("🔄 Cashing out...", '#ffaa00')
            success = self.trading.cash_out()
            if success:
                self.update_status("Successfully cashed out", COLORS["positive"])
                messagebox.showinfo("Success", "Position cashed out!")
                self.refresh_positions()
            else:
                self.update_status("Failed to cash out", COLORS["negative"])
                messagebox.showerror("Error", "Failed to cash out")
        except Exception as e:
            self.update_status(f"Error: {str(e)}", COLORS["negative"])

    def close_all_trades(self):
        try:
            self.update_status("🔄 Closing all trades...", '#ffaa00')
            success = self.trading.close_all_trades()
            if success:
                self.update_status("All trades closed successfully", COLORS["positive"])
                messagebox.showinfo("Success", "All positions closed!")
                self.refresh_positions()
            else:
                self.update_status("Failed to close all trades", COLORS["negative"])
                messagebox.showerror("Error", "Failed to close all trades")
        except Exception as e:
            self.update_status(f"Error: {str(e)}", COLORS["negative"])

    def _format_pnl(self, value: float, min_decimals: int = 2, tiny_threshold: float = 0.01, tiny_decimals: int = 4) -> str:
        """Format P&L with explicit +/− sign and 2–4 decimals.
        - For |value| < tiny_threshold, use tiny_decimals, else min_decimals
        - For zero, return "0.00" (no sign)
        """
        try:
            v = float(value or 0)
        except Exception:
            return str(value)
        if abs(v) < 1e-9:
            return f"{0:.{min_decimals}f}"
        decimals = tiny_decimals if abs(v) < tiny_threshold else min_decimals
        sign = '+' if v > 0 else '−'  # U+2212 minus for negatives
        return f"{sign}{abs(v):.{decimals}f}"

    def refresh_positions(self):
        """Refresh the positions display (now using Treeview)."""
        try:
            # Clear
            for row in self.positions.get_children():
                self.positions.delete(row)

            active_bets = self.trading.get_active_bets()

            if active_bets:
                for idx, bet in enumerate(active_bets):
                    dir_txt = bet['direction'].upper()
                    pnl_val = float(bet['pnl']) if isinstance(bet.get('pnl'), (int, float)) else 0.0
                    pnl_disp = self._format_pnl(pnl_val)
                    pnl_tag = 'pnl_pos' if pnl_val >= 0 else 'pnl_neg'
                    dir_tag = 'dir_up' if bet['direction'] == 'up' else 'dir_down'
                    stripe_tag = 'odd' if idx % 2 else 'even'
                    row_tags = (stripe_tag, dir_tag, pnl_tag)
                    item_id = self.positions.insert('', 'end', values=(
                        dir_txt,
                        bet.get('bias', 'Bullish' if bet['direction']=='up' else 'Bearish'),
                        bet['wager'],
                        bet['multiplier'],
                        bet['entry_price'],
                        bet['current_price'],
                        pnl_disp,
                    ), tags=row_tags)
                # Risk rules: update counters and apply stop-loss / trailing
                self.active_positions_count = len(active_bets)
                # Disable buttons if at limit
                try:
                    limit_reached = self.active_positions_count >= 4
                    for child in self.root.winfo_children():
                        # heuristic: disable main buy/sell buttons by text
                        if isinstance(child, ttk.Labelframe):
                            for btn in child.winfo_children():
                                if isinstance(btn, ttk.Button) and btn.cget('text') in ("BUY (UP)", "SELL (DOWN)"):
                                    btn.state(['disabled'] if limit_reached else ['!disabled'])
                except Exception:
                    pass

                # Stop loss and trailing
                buffer = 0.03 if self.high_vol_var.get() else 0.02
                for idx, bet in enumerate(active_bets):
                    key = bet.get('row_index', idx)
                    pnl = float(bet.get('pnl') or 0)
                    # Initialize peak at current pnl
                    peak = self._pnl_peaks.get(key, pnl)
                    if pnl > peak:
                        peak = pnl
                    self._pnl_peaks[key] = peak
                    # Immediate tiny stop-loss around zero to avoid degenerate losers
                    if pnl <= -0.01:
                        self.update_status(f"Stop loss hit on position {key} (pnl {pnl:.4f})", COLORS["negative"])
                        try:
                            # Attempt per-position close; fallback to global
                            if hasattr(self.trading, 'close_trade'):
                                self.trading.close_trade(int(key))
                            else:
                                self.trading.close_all_trades()
                        except Exception:
                            try:
                                self.trading.close_all_trades()
                            except Exception:
                                pass
                        continue
                    # Trailing profit lock
                    if peak >= 0.01 and pnl < (peak - buffer):
                        self.update_status(f"Trailing stop: lock profit on {key} (peak {peak:.4f} -> pnl {pnl:.4f})", COLORS["positive"])
                        try:
                            if hasattr(self.trading, 'close_trade'):
                                self.trading.close_trade(int(key))
                            else:
                                self.trading.close_all_trades()
                        except Exception:
                            try:
                                self.trading.close_all_trades()
                            except Exception:
                                pass

                self.update_status(f"ACTIVE • {len(active_bets)} position(s)", COLORS["accent_green"])
            else:
                self.update_status("READY • Awaiting webhook", COLORS["accent_green"])
        except Exception as e:
            self.update_status(f"Connection error: {str(e)}", COLORS["negative"])

    def run(self):
        print("🤖 Sentinel Awakens GUI launched!")
        self.root.mainloop()

    def _on_close_window(self):
        try:
            self.ws_enabled = False
            self.stop_websocket()
        finally:
            self.root.destroy()






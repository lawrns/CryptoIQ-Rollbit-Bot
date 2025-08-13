import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import websocket
import json

class TradingGUI:
    def __init__(self, trading_interface):
        self.trading = trading_interface
        self.root = tk.Tk()
        self.root.title("🤖 SENTINEL AWAKENS - Trading Interface")
        self.root.geometry("500x600")
        self.root.configure(bg='#1a1a1a')
        self.setup_gui()
        self.start_websocket()

    def setup_gui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#1a1a1a')
        header_frame.pack(fill='x', pady=10)

        title_label = tk.Label(header_frame, text="🤖 SENTINEL AWAKENS",
                              font=('Arial', 16, 'bold'),
                              fg='#00ff00', bg='#1a1a1a')
        title_label.pack()

        # Status indicator
        self.status_label = tk.Label(header_frame, text="🟢 SENTINEL READY... AWAITING WEBHOOK",
                                    font=('Arial', 12, 'bold'),
                                    fg='#00ff00', bg='#1a1a1a')
        self.status_label.pack(pady=5)

        # Trading controls frame
        controls_frame = tk.LabelFrame(self.root, text="Trading Controls",
                                      font=('Arial', 10, 'bold'),
                                      fg='white', bg='#2a2a2a')
        controls_frame.pack(fill='x', padx=20, pady=10)

        # Wager input
        tk.Label(controls_frame, text="Wager Amount:",
                fg='white', bg='#2a2a2a').pack(pady=5)
        self.wager_var = tk.StringVar(value="0.10")
        wager_entry = tk.Entry(controls_frame, textvariable=self.wager_var,
                              font=('Arial', 12), width=15)
        wager_entry.pack(pady=5)

        # Multiplier input
        tk.Label(controls_frame, text="Multiplier:",
                fg='white', bg='#2a2a2a').pack(pady=5)
        self.multiplier_var = tk.StringVar(value="1000")
        multiplier_entry = tk.Entry(controls_frame, textvariable=self.multiplier_var,
                                   font=('Arial', 12), width=15)
        multiplier_entry.pack(pady=5)

        # Trading buttons
        button_frame = tk.Frame(controls_frame, bg='#2a2a2a')
        button_frame.pack(pady=15)

        up_btn = tk.Button(button_frame, text="📈 BUY (UP)",
                          bg="#00aa00", fg="white", font=('Arial', 12, 'bold'),
                          width=12, height=2, command=self.place_up_bet)
        up_btn.pack(side=tk.LEFT, padx=10)

        down_btn = tk.Button(button_frame, text="📉 SELL (DOWN)",
                            bg="#aa0000", fg="white", font=('Arial', 12, 'bold'),
                            width=12, height=2, command=self.place_down_bet)
        down_btn.pack(side=tk.LEFT, padx=10)

        # Cash out button
        cash_out_btn = tk.Button(controls_frame, text="💰 CASH OUT",
                                bg="#ff8800", fg="white", font=('Arial', 12, 'bold'),
                                width=25, height=2, command=self.cash_out)
        cash_out_btn.pack(pady=10)

        # Close all trades button
        close_all_btn = tk.Button(controls_frame, text="🚨 CLOSE ALL TRADES",
                                 bg="#cc0000", fg="white", font=('Arial', 12, 'bold'),
                                 width=25, height=2, command=self.close_all_trades)
        close_all_btn.pack(pady=5)

        # Active bets frame
        bets_frame = tk.LabelFrame(self.root, text="Active Positions",
                                  font=('Arial', 10, 'bold'),
                                  fg='white', bg='#2a2a2a')
        bets_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.bets_text = tk.Text(bets_frame, height=8, width=60,
                                font=('Courier', 10), bg='#1a1a1a', fg='#00ff00')
        self.bets_text.pack(pady=10, padx=10, fill='both', expand=True)

        # Control buttons
        control_frame = tk.Frame(self.root, bg='#1a1a1a')
        control_frame.pack(fill='x', padx=20, pady=10)

        refresh_btn = tk.Button(control_frame, text="🔄 Refresh Positions",
                               bg="#0066cc", fg="white", font=('Arial', 10),
                               command=self.refresh_positions)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Auto-refresh every 5 seconds
        self.auto_refresh()

        # Initial refresh
        self.refresh_positions()

    def start_websocket(self):
        def on_open(ws):
            sub_msg = {
                "op": "sub",
                "symbols": "BTCUSDT",
                "pv": 100,
                "strings": 10
            }
            ws.send(json.dumps(sub_msg))

        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.handle_burst_data(data)
            except Exception as e:
                print(f"WebSocket message error: {e}")

        def on_error(ws, error):
            print(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("WebSocket closed")

        ws_url = "wss://matrix.cryptoiq.com/api/sentinel/ws"
        ws_app = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            ping_interval=30,
            ping_payload=json.dumps({"op": "ping"})
        )

        threading.Thread(target=ws_app.run_forever, daemon=True).start()
        print("WebSocket connection started for signal reception.")

    def handle_burst_data(self, data):
        if data.get('s') != "BTCUSDT":
            return

        direction = 'up' if data.get('delta', 0) > 0 else 'down'
        try:
            wager = float(self.wager_var.get())
            multiplier = float(self.multiplier_var.get())
            success = self.trading.execute_trade(direction, wager, multiplier)
            if success:
                self.update_status(f"✅ Signal received - {direction.upper()} trade placed!", '#00ff00')
                self.refresh_positions()
            else:
                self.update_status(f"❌ Failed to place trade on signal: {direction.upper()}", '#ff0000')
        except ValueError:
            self.update_status("❌ Invalid wager/multiplier for signal trade", '#ff0000')
        except Exception as e:
            self.update_status(f"❌ Signal trade error: {str(e)}", '#ff0000')

    def auto_refresh(self):
        """Auto-refresh active bets every 5 seconds"""
        self.refresh_positions()
        self.root.after(5000, self.auto_refresh)  # Schedule next refresh

    def update_status(self, message, color='#00ff00'):
        """Update status message"""
        self.status_label.config(text=message, fg=color)
        self.root.update()

    def place_up_bet(self):
        try:
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
                self.update_status("✅ UP bet placed successfully!", '#00ff00')
                self.refresh_positions()
            else:
                self.update_status("❌ Failed to place UP bet", '#ff0000')
        except ValueError:
            self.update_status("❌ Invalid input values", '#ff0000')
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", '#ff0000')

    def place_down_bet(self):
        try:
            self.update_status("🔄 Placing DOWN bet...", '#ffaa00')
            wager = float(self.wager_var.get())
            multiplier = float(self.multiplier_var.get())
            try:
                success = self.trading.execute_trade('down', wager, multiplier)
            except Exception as ex:
                messagebox.showwarning("Redirection detected", f"Navigation occurred while placing DOWN trade. Retrying may help.\n\nDetails: {ex}")
                success = False
            if success:
                self.update_status("✅ DOWN bet placed successfully!", '#00ff00')
                self.refresh_positions()
            else:
                self.update_status("❌ Failed to place DOWN bet", '#ff0000')
        except ValueError:
            self.update_status("❌ Invalid input values", '#ff0000')
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", '#ff0000')

    def cash_out(self):
        try:
            self.update_status("🔄 Cashing out...", '#ffaa00')
            success = self.trading.cash_out()
            if success:
                self.update_status("✅ Successfully cashed out!", '#00ff00')
                messagebox.showinfo("Success", "Position cashed out!")
                self.refresh_positions()
            else:
                self.update_status("❌ Failed to cash out", '#ff0000')
                messagebox.showerror("Error", "Failed to cash out")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", '#ff0000')

    def close_all_trades(self):
        try:
            self.update_status("🔄 Closing all trades...", '#ffaa00')
            success = self.trading.close_all_trades()
            if success:
                self.update_status("✅ All trades closed successfully!", '#00ff00')
                messagebox.showinfo("Success", "All positions closed!")
                self.refresh_positions()
            else:
                self.update_status("❌ Failed to close all trades", '#ff0000')
                messagebox.showerror("Error", "Failed to close all trades")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", '#ff0000')

    def refresh_positions(self):
        """Refresh the positions display"""
        try:
            self.bets_text.delete(1.0, tk.END)
            active_bets = self.trading.get_active_bets()

            if active_bets:
                self.bets_text.insert(tk.END, f"📊 ACTIVE POSITIONS ({len(active_bets)}):\n")
                self.bets_text.insert(tk.END, "=" * 50 + "\n\n")

                for i, bet in enumerate(active_bets, 1):
                    direction_emoji = "🟢" if bet['direction'].upper() == "UP" else "🔴"

                    self.bets_text.insert(tk.END, f"{direction_emoji} Position #{i}: {bet['direction'].upper()}\n")
                    self.bets_text.insert(tk.END, f"   💰 Wager: {bet['wager']}\n")
                    self.bets_text.insert(tk.END, f"   📈 Multiplier: {bet['multiplier']}\n")
                    self.bets_text.insert(tk.END, f"   🎯 Entry: {bet['entry_price']}\n")
                    self.bets_text.insert(tk.END, f"   📊 Current: {bet['current_price']}\n")
                    self.bets_text.insert(tk.END, f"   💵 P&L: {bet['pnl']}\n")
                    self.bets_text.insert(tk.END, "\n")

                self.update_status(f"🟢 SENTINEL ACTIVE - {len(active_bets)} position(s)", '#00ff00')
            else:
                self.bets_text.insert(tk.END, "📭 No active positions found\n")
                self.bets_text.insert(tk.END, "Waiting for trading signals...")
                self.update_status("🟢 SENTINEL READY... AWAITING WEBHOOK", '#00ff00')

        except Exception as e:
            self.bets_text.delete(1.0, tk.END)
            self.bets_text.insert(tk.END, f"❌ Error refreshing positions: {str(e)}")
            self.update_status("❌ Connection error", '#ff0000')

    def run(self):
        print("🤖 Sentinel Awakens GUI launched!")
        self.root.mainloop()
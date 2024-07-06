import customtkinter as ctk
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from datetime import datetime, timedelta, timezone
from settings import *

try:
    from ctypes import windll, byref, sizeof, c_int
except:
    pass


class StockMarket(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=BG_COLOR)

        # Window setup
        self.geometry('900x800')
        self.title('')
        self.iconbitmap('empty.ico')
        self.change_titlebar_color()

        StockFigure(self)
        BottomFrame(self)

    def change_titlebar_color(self):
        try:
            HWND = windll.user32.GetParent(self.winfo_id())
            DWMWA_ATTRIBUTE = 35
            COLOR = TITLE_HEX_COLOR
            windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_ATTRIBUTE, byref(c_int(COLOR)), sizeof(c_int))
        except:
            pass


class StockFigure(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent)
        self.pack(pady=10, expand=True, fill="both")

        self.fetch_and_plot()

    def fetch_and_plot(self):
        # Set the stock symbol
        symbol = 'AAPL'

        # Fetch data for the last week
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=8)

        # Create a Ticker object for the specified symbol
        stock = yf.Ticker(symbol)
        # data = stock.history(period='1y')
        # Fetch historical data for the specified date range
        data = stock.history(start=start_date, end=end_date)

        # Check if the data is empty
        if data.empty:
            print(f"No data available for {symbol}")
            return

        # Clear previous plot
        for widget in self.winfo_children():
            widget.destroy()

        # Create a new Figure object
        fig = Figure()
        # Add a subplot to the figure
        ax = fig.add_subplot()
        # Set the background color of the subplot
        ax.set_facecolor(BG_COLOR)

        # Plot the closing prices
        ax.plot(data.index, data['Close'], color='#20dca5')

        # Set the color of x-axis ticks
        ax.tick_params(axis='x', colors=TICK_COLOR)
        # Set the color of y-axis ticks
        ax.tick_params(axis='y', colors='#20dca5')

        # Move the y-axis to the right side
        ax.yaxis.tick_right()
        # Configure y-axis tick parameters
        ax.tick_params(axis='y', pad=-25, direction='in')

        # Keep x-axis ticks at the bottom
        ax.tick_params(axis='x', direction='in', pad=-20)

        # Create a FigureCanvasTkAgg object to embed the plot in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self)
        # Draw the canvas
        canvas.draw()
        # Get the tkinter widget from the canvas
        canvas_widget = canvas.get_tk_widget()

        canvas_widget.pack(side="top", fill="both", expand=True)

        # Remove figure edges
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)


class BottomFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent, fg_color=INPUT_BG_COLOR, height=50, corner_radius=0)
        self.pack(side="bottom", fill="x")


if __name__ == '__main__':
    app = StockMarket()
    app.mainloop()

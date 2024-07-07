import customtkinter as ctk
import yfinance as yf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from zoneinfo import ZoneInfo

from datetime import datetime, timedelta
from settings import *

try:
    from ctypes import windll, byref, sizeof, c_int
except:
    pass


def get_ny_date():
    ny_time = datetime.now(ZoneInfo("America/New_York"))
    return ny_time.date()


class StockMarket(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=BG_COLOR)

        # Window setup
        self.geometry('900x800')
        self.title('')
        self.iconbitmap('empty.ico')
        self.change_titlebar_color()

        # variables
        symbol_string = ctk.StringVar()
        period_string = ctk.StringVar(value='Max')
        self.cache = dict()

        StockFigure(self, symbol_string, period_string, self.cache)
        BottomFrame(self, symbol_string, period_string)

    def change_titlebar_color(self):
        try:
            HWND = windll.user32.GetParent(self.winfo_id())
            DWMWA_ATTRIBUTE = 35
            COLOR = TITLE_HEX_COLOR
            windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_ATTRIBUTE, byref(c_int(COLOR)), sizeof(c_int))
        except:
            pass


class StockFigure(ctk.CTkFrame):
    def __init__(self, parent, symbol_string, period_string, cache):
        super().__init__(master=parent, fg_color=BG_COLOR)
        self.pack(pady=10, expand=True, fill="both")
        self.symbol_string = symbol_string
        self.period_string = period_string
        self.cache = cache

        symbol_string.trace('w', self.fetch_and_plot)
        period_string.trace('w', self.fetch_and_plot)

    def fetch_and_plot(self, *args):
        # Get the stock symbol from user
        symbol = self.symbol_string.get().upper()
        if not symbol:
            return
        period = self.period_string.get()
        symbol_period = f'{symbol}_{period}'

        if symbol_period in self.cache:
            print('cache hit')
            data = self.cache.get(symbol_period)
        else:
            print('cache miss')
            stock = yf.Ticker(symbol)

            # Fetch historical data for the specified date range
            match period:
                case 'Max':
                    data = stock.history(period='max')
                case 'Week':
                    end_date = get_ny_date()
                    start_date = end_date - timedelta(days=8)
                    data = stock.history(start=start_date, end=end_date)
                case '1 Year':
                    data = stock.history(period='1y')

                case 'Month':
                    data = stock.history(period='1mo')

                case '6 Months':
                    data = stock.history(period='6mo')

                case _:
                    return

            # Check if the data is empty
            if data.empty:
                print(f"No data available for {symbol}")
                return

            self.cache[symbol_period] = data

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
        ax.plot(data.index, data['Close'], color=HIGHLIGHT_COLOR)

        # Set the color of x-axis ticks
        ax.tick_params(axis='x', colors=TICK_COLOR)
        # Set the color of y-axis ticks
        ax.tick_params(axis='y', colors=HIGHLIGHT_COLOR)

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
    def __init__(self, parent, symbol_string, period_string):
        super().__init__(master=parent, fg_color=INPUT_BG_COLOR, height=50, corner_radius=0)
        self.pack(side="bottom", fill="x")

        self.symbol_string = symbol_string
        self.period_string = period_string

        self.create_widgets()

    def create_widgets(self):
        self.entry = ctk.CTkEntry(self, )
        self.entry.insert(0, 'AAPL')
        self.entry.pack(side='left', pady=10, padx=10)
        self.entry.bind('<Return>', self.draw_the_figure)
        self.label_buttons = []

        for time in TIME_OPTIONS:
            self.label_buttons.append(LabelButton(self, time, self.label_buttons, self.period_string))

    def draw_the_figure(self, event):
        self.symbol_string.set(self.entry.get())


class LabelButton(ctk.CTkLabel):
    def __init__(self, parent, text, label_buttons, period_string, text_color=TEXT_COLOR):
        super().__init__(master=parent, text=text, text_color=text_color)
        self.label_buttons = label_buttons
        self.period_string = period_string
        self.pack(side='right', padx=10)
        self.bind('<Button-1>', lambda e, x=text: self.set_period(period=x))
        if text == 'Week':
            self.set_period('Max')

    def set_period(self, period):
        self.set_active(period)
        self.period_string.set(period)

    def set_active(self, period):
        for button in self.label_buttons:
            button.configure(text_color=HIGHLIGHT_COLOR if button.cget('text') == period else TEXT_COLOR)


if __name__ == '__main__':
    app = StockMarket()
    app.mainloop()

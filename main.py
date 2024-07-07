try:
    from ctypes import windll, byref, sizeof, c_int
except:
    pass
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

import customtkinter as ctk
import yfinance as yf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from settings import *


def get_ny_date() -> datetime.date:
    """
    Get the current date in New York.

    We use NY as a reference because the stock exchange is
    based on NY city.

    :return: a date object representing the current date in NY
    """
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

        # Variables
        symbol_string = ctk.StringVar()  # current stock symbol
        period_string = ctk.StringVar()  # current time period

        # A dictionary to store already searched infos
        self.cache = dict()

        StockFigure(self, symbol_string, period_string, self.cache)
        BottomFrame(self, symbol_string, period_string)

    def change_titlebar_color(self) -> None:
        """
        Sets the title bar's color to the same color as our app background

        :return: None
        """
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

        # Binding the drawing mechanism to run every time
        # a new symbol or time frame is selected
        symbol_string.trace('w', self.fetch_data)
        period_string.trace('w', self.fetch_data)

    def fetch_data(self, *args) -> None:
        """
        This function is responsible for fetching the historical data
        of selected symbol.

        It has a caching mechanism in place that will avoid repeated requests.

        After the function is finished it will run the function that is responsible for draw logic

        :param args: [Not used] Necessary for trace function to work.
        :return: None
        """
        # Get the stock symbol from entry box and make sure it's uppercase
        symbol = self.symbol_string.get().upper()

        # If the entry box is empty abort
        if not symbol:
            return
        # Get the current selected time period
        period = self.period_string.get()
        # Generate a name for soon to be cached data
        symbol_period = f'{symbol}_{period}'

        # If it already exists use that data
        if symbol_period in self.cache:
            print('cache hit')
            data = self.cache[symbol_period]
        else:  # If not in cache fetch data
            print('cache miss')
            # Get the ticker object for chosen symbol
            stock = yf.Ticker(symbol)

            # Fetch historical data for the specified date range
            match period:
                case 'Week':
                    end_date = get_ny_date()
                    start_date = end_date - timedelta(days=8)
                    data = stock.history(start=start_date, end=end_date)
                case 'Month':
                    data = stock.history(period='1mo')
                case '6 Months':
                    data = stock.history(period='6mo')
                case '1 Year':
                    data = stock.history(period='1y')
                case 'Max':
                    data = stock.history(period='max')
                case _:  # If none of the above is selected abort
                    return

            # Check if the data is empty (Abort if yes)
            if data.empty:
                print(f"No data available for {symbol}")
                return
            # Add the Generated data to the cache
            self.cache[symbol_period] = data
        # Pass the data to the helper function that will draw the plot
        self._draw_plot(data)

    def _draw_plot(self, data) -> None:
        """
        This function is responsible for drawing the stock data.

        :param data: Data that is passed from fetch_data function
        :return: None
        """
        # Clear previous plot by destroying all the children widgets
        # inside the frame
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
        # Configure x-axis tick parameters
        ax.tick_params(axis='x', direction='in', pad=-20)

        # Create a FigureCanvasTkAgg object to embed the plot in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self)
        # Draw the canvas
        canvas.draw()
        # Get the tkinter widget from the canvas
        canvas_widget = canvas.get_tk_widget()

        canvas_widget.pack(fill="both", expand=True)

        # Remove figure edges
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)


class BottomFrame(ctk.CTkFrame):
    def __init__(self, parent, symbol_string, period_string):
        super().__init__(master=parent, fg_color=INPUT_BG_COLOR, height=50, corner_radius=0)
        self.pack(side="bottom", fill="x")

        self.symbol_string = symbol_string
        self.period_string = period_string
        self.label_buttons = []  # A list containing all the button widgets

        self.create_widgets()

    def create_widgets(self) -> None:
        """
        Creates all the widgets.

        :return: None
        """
        # Create the entry box and place it on the left side
        self.entry = ctk.CTkEntry(self)
        self.entry.pack(side='left', pady=10, padx=10)
        # Add a default text
        self.entry.insert(0, 'AAPL')
        # Bind the Enter key on keyboard to draw_the_figure function
        self.entry.bind('<Return>', self.draw_the_figure)

        for time in TIME_OPTIONS:
            # Create the widget and add it to the list
            self.label_buttons.append(
                LabelButton(self, time, self.label_buttons, self.period_string)
            )

    def draw_the_figure(self, event) -> None:
        """
        Gets the user input from entry box and add it to symbol variable
        And as a result will trigger the functions that will fetch data and draw the plot.

        :param event: [Not used] Is necessary for the binding mechanism
        :return: None
        """
        self.symbol_string.set(self.entry.get())


class LabelButton(ctk.CTkLabel):
    def __init__(self, parent, text, label_buttons, period_string, text_color=TEXT_COLOR):
        super().__init__(master=parent, text=text, text_color=text_color)
        self.label_buttons = label_buttons
        self.period_string = period_string
        self.pack(side='right', padx=10)
        # Binding left click to run set_period function
        self.bind('<Button-1>', lambda e: self.set_period(period=text))
        # If it's the last LabelButton object that is created
        # Set the 'Max' as default time period
        if text == 'Week':
            self.set_period('Max')

    def set_period(self, period: str) -> None:
        """
        Set the period based on which label user has clicked on

        :param period: The selected period
        :return: None
        """
        # Make the selected period visually distinct
        self._set_active(period)
        # Change the period_string variable that in turn will set off the
        # drawing logic
        self.period_string.set(period)

    def _set_active(self, period: str) -> None:
        """
        This function will change the color of the selected label to green
        and also will change all the other labels to white

        :param period: The selected period
        :return: None
        """
        for button in self.label_buttons:
            button.configure(text_color=HIGHLIGHT_COLOR if button.cget('text') == period else TEXT_COLOR)


if __name__ == '__main__':
    app = StockMarket()
    app.mainloop()

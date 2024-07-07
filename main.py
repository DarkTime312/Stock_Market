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


class StockMarket(ctk.CTk):
    """
    This class represents the main application window for the Stock Market app.
    It initializes the window, sets up variables, and creates instances of other components.

    Attributes:
        symbol_string (ctk.StringVar): Variable to store the current stock symbol.
        period_string (ctk.StringVar): Variable to store the current time period.
        cache (dict): A dictionary to store already searched information.
    """

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
        UserInputPanel(self, symbol_string, period_string)

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
    """
    This class represents the frame where the stock data plot is displayed.
    """
    def __init__(self, parent, symbol_string, period_string, cache):
        super().__init__(master=parent, fg_color=BG_COLOR)
        self.pack(expand=True, fill="both")

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
        # Get the stock symbol from symbol_string and make sure it's uppercase
        symbol = self.symbol_string.get().upper()

        # If user still haven't selected a symbol, abort
        if not symbol:
            return
        # Get the current selected time period
        period = self.period_string.get()
        # Generate a name for soon to be cached data
        symbol_period = f'{symbol}_{period}'

        # If it already exists use that data
        if symbol_period in self.cache:
            print('Cache hit')
            data = self.cache[symbol_period]
        else:  # If not in cache fetch data
            print('Cache miss')
            # Get the ticker object for chosen symbol
            stock = yf.Ticker(symbol)

            # Fetch historical data for the specified date range
            match period:
                case 'Week':
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=10)
                    # Get the last 5 working days
                    data = stock.history(start=start_date, end=end_date).iloc[-5:]
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
        ax = fig.add_subplot(111)
        # Set the background color of the subplot
        ax.set_facecolor(BG_COLOR)

        # Plot the closing prices
        ax.plot(data['Close'], color=HIGHLIGHT_COLOR)

        # Move the y-axis to the right side
        ax.yaxis.tick_right()
        # Configure y-axis tick parameters
        ax.tick_params(axis='y', pad=-25, direction='in', colors=HIGHLIGHT_COLOR)
        # Configure x-axis tick parameters
        ax.tick_params(axis='x', pad=-20, direction='in', colors=TICK_COLOR)

        # Create a FigureCanvasTkAgg object to embed the plot in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self)
        # Get the tkinter widget from the canvas
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)

        # Remove figure edges
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)


class UserInputPanel(ctk.CTkFrame):
    """
    This class represents the panel where user input elements are displayed.
    """
    def __init__(self, parent, symbol_string, period_string):
        super().__init__(master=parent, fg_color=INPUT_BG_COLOR, corner_radius=0)
        self.pack(side="bottom", fill="both")

        self.symbol_string = symbol_string
        self.period_string = period_string
        # Store a reference to the last clicked label
        self.last_chosen_button = None

        self.create_widgets()

    def create_widgets(self) -> None:
        """
        Create entry box and label buttons for user input.

        :return: None
        """
        # Create the entry box and place it on the left side
        self.entry = ctk.CTkEntry(self, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.entry.pack(side='left', pady=10, padx=10)

        # Add a default text
        self.entry.insert(0, 'AAPL')
        # Bind the Enter key on keyboard to draw_the_figure function
        self.entry.bind('<Return>', self.draw_the_figure)

        # Create the LabelButtons
        for time in TIME_OPTIONS:
            LabelButton(self, time, self.period_string)

    def draw_the_figure(self, event) -> None:
        """
        Gets the user input from entry box and adds it to symbol_string variable
        And as a result it will trigger the functions that will fetch data and draw the plot.

        :param event: [Not used] Is necessary for the binding mechanism.
        :return: None
        """
        self.symbol_string.set(self.entry.get())


class LabelButton(ctk.CTkLabel):
    """
    This class represents a label button used for selecting time periods in the UserInputPanel.
    """
    def __init__(self, parent, text, period_string):
        super().__init__(master=parent, text=text, text_color=TEXT_COLOR)
        self.parent = parent
        self.period_string = period_string
        self.pack(side='right', padx=10, pady=10)

        # Binding left click to run set_period function
        self.bind('<Button-1>', lambda e: self.set_period(period=text))
        # Set the 'Max' as default time period
        if text == 'Max':
            self.set_period('Max')

    def set_period(self, period: str) -> None:
        """
        Set the time period based on the selected label button.

        :param period: The selected time period
        :return: None
        """
        # Make the selected period visually distinct
        self._set_active()
        # Change the period_string variable that in turn will set off the
        # drawing logic
        self.period_string.set(period)

    def _set_active(self) -> None:
        """
        This function will change the color of the selected label to green
        and all the other labels to white

        :return: None
        """
        # If user clicked on the same label again do nothing
        if self.parent.last_chosen_button is self:
            return

        # If there's already a label clicked change its color to normal
        if self.parent.last_chosen_button:
            self.parent.last_chosen_button.configure(text_color=TEXT_COLOR)
        # Change the color of the current selected label to green
        self.configure(text_color=HIGHLIGHT_COLOR)
        # Store a reference to the current label in parent class
        self.parent.last_chosen_button = self


if __name__ == '__main__':
    app = StockMarket()
    app.mainloop()

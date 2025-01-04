#logging
import logging
import time

import customtkinter as ctk

from eBird_methods import UserBridge, EBirdBridge

logger = logging.getLogger('interface')

def logged(print_args: bool = True):
    def logged_decorator(func):
        def log_wrapper(*args, **kwargs):
            start = time.time()
            start_message = f'Started running {func.__name__}'
            if print_args:
                start_message += f' with the arguments \n {args}, {kwargs}'
            logger.info(start_message)
            result = func(*args, **kwargs)
            end = time.time()
            end_message = f'Finished running {func.__name__}'
            try:
                result_length = len(result)
            except TypeError:
                result_length = 0
            if result_length > 20:
                end_message += f' with result of length {result_length}'
            elif not result == None:
                end_message += f' with the result \n {result}'
            end_message += f' \n taking {end - start} seconds.'
            logger.info(end_message)
            return result
            
        return log_wrapper
    return logged_decorator


ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        # Basic config
        self.title("Pin-Tailed Whydah Database")
        self.geometry(f"{400}x{290}")

        # Bridge to backend
        self.ebird_bridge = EBirdBridge()

        # Screens
        self.current_window: ctk.CTkFrame
        self.screens: dict[str, ctk.CTkFrame] = {'Welcome': ScreenWelcome(self),
                              'New pin': ScreenEnterNewPin(self),
                              'Edit pin': ScreenEditPin(self),
                              'New source': ScreenEnterNewSource(self),
                              'Edit source': ScreenEditSource(self)}


        # Initialise the welcome screen
        self.screens['Welcome'].pack(padx=20, pady=20, fill="both", expand=True)
        self.current_window = 'Welcome'

    def switch_window(self, new_window: str) -> None:
        self.screens[self.current_window].pack_forget()
        self.current_window = new_window
        self.screens[self.current_window].pack(padx=20, pady=20, fill="both", expand=True)

class ScreenWelcome(ctk.CTkFrame):

    def test(self):
        print('not implemented')

    def __init__(self, master: App, **kwargs) -> None:
        super().__init__(master, **kwargs)

        self.master = master

        self.title = ctk.CTkLabel(self, text='Welcome to your bird pin database!', font=ctk.CTkFont("Arial", 20, "bold"))
        self.title.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.subtitle = ctk.CTkLabel(self, text='What would you like to do?', font=ctk.CTkFont("Arial", 15, "bold"))
        self.subtitle.grid(row=1, column=0, columnspan=3)

        BUTTON_WIDTH: int = 20

        self.new_pin_button = ctk.CTkButton(self, 
                                            width=BUTTON_WIDTH, 
                                            text='Enter new pin', 
                                            command=lambda: master.switch_window('New pin'))
        self.new_pin_button.grid(row=3, column=0)
        self.edit_pin_button = ctk.CTkButton(self, 
                                             width=BUTTON_WIDTH, 
                                             text='Edit existing pin entry', 
                                             command=lambda: master.switch_window('Edit pin'))
        self.edit_pin_button.grid(row=4, column=0)
        self.new_source_button = ctk.CTkButton(self, 
                                               width=BUTTON_WIDTH, 
                                               text='Enter new source', 
                                               command=lambda: master.switch_window('New source'))
        self.new_source_button.grid(row=3, column=2)
        self.edit_source_button = ctk.CTkButton(self, 
                                                width=BUTTON_WIDTH, 
                                                text='Edit existing source', 
                                                command=lambda: master.switch_window('Edit source'))
        self.edit_source_button.grid(row=4, column=2)
        self.update_database_button = ctk.CTkButton(self, 
                                                    width=BUTTON_WIDTH, 
                                                    text='Update local bird database', 
                                                    command=master.ebird_bridge.update_database)
        self.update_database_button.grid(row=5, column=0, columnspan=3)

class ScreenEnterNewPin(ctk.CTkFrame):
    pass

class ScreenEditPin(ctk.CTkFrame):
    pass

class ScreenEnterNewSource(ctk.CTkFrame):
    pass

class ScreenEditSource(ctk.CTkFrame):
    pass



@logged()
def main(auto_test: bool = False):
    if auto_test:
        import doctest
        doctest.testmod()
        return None
    app = App()
    app.mainloop()

if __name__ == '__main__':
    logging.basicConfig(filename='interface.log', level=logging.INFO)
    logger.info(f'{"begin log":{"-"}^40}')
    try:
        main()
    except Exception as err:
        logger.exception(f'Got exception on main handler: {err}')
        raise
    finally:
        logger.info(f'{"end log":{"-"}^40}')


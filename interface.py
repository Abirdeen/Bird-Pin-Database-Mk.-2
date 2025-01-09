#logging
import logging
import time

from typing import Optional, Literal

from PIL import Image
import customtkinter as ctk

from eBird_methods import UserLocalDBBridge, EBirdBridge
from eBird_methods import DataDict, DictWithScore, BirdDict, SubspeciesDict, SupergroupDict, SourceDict, SubgroupDict, PinDict

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
        DEFAULT_APP_HEIGHT: int = 400
        DEFAULT_APP_WIDTH: int = 550
        self.geometry(f"{DEFAULT_APP_WIDTH}x{DEFAULT_APP_HEIGHT}")
        self.WINDOW_SETTINGS: dict[str, object] = {'row': 1, 'column': 0, 'columnspan': 2, 
                                                   'padx': 20, 'pady': 20, 
                                                   'sticky': ctk.NSEW}

        # Home button
        home_icon = Image.open("./assets/Birdhouse icon blue.png")
        home_icon_ctk = ctk.CTkImage(light_image=home_icon, size = (40,40))
        self.home_button = ctk.CTkButton(self, 
                                         fg_color='transparent', width=20, height=20,
                                         image=home_icon_ctk, text='',
                                         command=lambda: self.switch_window(self.WELCOME))

        # Refresh button
        refresh_icon = Image.open("./assets/BirdRefresh.png")
        refresh_icon_ctk = ctk.CTkImage(light_image=refresh_icon, size = (40,40))
        self.refresh_button = ctk.CTkButton(self, 
                                         fg_color='transparent', width=20, height=20,
                                         image=refresh_icon_ctk, text='',
                                         command=self.refresh_window)

        # Dictionary of screens
        self.LOADING: str = 'Loading'
        self.WELCOME: str = 'Welcome'
        self.NEW_PIN: str = 'New pin'
        self.EDIT_PIN: str = 'Edit pin'
        self.NEW_SOURCE: str = 'New source'
        self.EDIT_SOURCE: str = 'Edit source'
        self.screen_types: dict[str, type[ctk.CTkFrame]] = {self.LOADING: ScreenLoading, 
                                                            self.WELCOME: ScreenWelcome,
                                                            self.NEW_PIN: ScreenEnterNewPin,
                                                            self.EDIT_PIN: ScreenEditPin,
                                                            self.NEW_SOURCE: ScreenEnterNewSource,
                                                            self.EDIT_SOURCE: ScreenEditSource}
        self.screens: dict[str, ctk.CTkFrame | None] = {self.LOADING: None, 
                                                        self.WELCOME: ScreenWelcome(self),
                                                        self.NEW_PIN: None,
                                                        self.EDIT_PIN: None,
                                                        self.NEW_SOURCE: None,
                                                        self.EDIT_SOURCE: None}

        # Initialise the window
        self.current_window_name: str = self.WELCOME
        self.current_window: ctk.CTkFrame = self.screens[self.current_window_name]
        self.refresh_button.grid(row=0, column=0)        
        self.home_button.grid(row=0, column=1)
        self.current_window.grid(**self.WINDOW_SETTINGS)

    def switch_window(self, new_window_name: str) -> None:
        self.current_window.grid_forget()
        possible_new_window: ctk.CTkFrame | None = self.screens[new_window_name]
        new_window: ctk.CTkFrame
        if possible_new_window == None:
            new_window = self.screen_types[new_window_name](self)
        else:
            new_window = possible_new_window
        self.current_window_name = new_window_name
        self.screens[new_window_name], self.current_window = (new_window,)*2
        self.current_window.grid(**self.WINDOW_SETTINGS)

    def refresh_window(self) -> None:
        self.current_window.destroy()
        self.screens[self.current_window_name], self.current_window = (self.screen_types[self.current_window_name](self),)*2
        self.current_window.grid(**self.WINDOW_SETTINGS)

class ScreenLoading(ctk.CTkFrame):
    def __init__(self, master: App, **kwargs) -> None:
        super().__init__(master, **kwargs)
        background = Image.open("./assets/Bird in cosmos.jpg")
        background_ctk = ctk.CTkImage(light_image=background, 
                                      size=(master._current_width,master._current_height))
        background_label = ctk.CTkLabel(self, image=background_ctk, text='')
        background_label.place(x=0, y=0)

    def loaded(self, master: App) -> None:
        time.sleep(2)
        master.switch_window('Welcome')

class ScreenWelcome(ctk.CTkFrame):

    def _update_database(self):
        bridge = EBirdBridge()
        bridge.update_database()
        bridge.close_connection()

    def __init__(self, master: App, **kwargs) -> None:
        super().__init__(master, **kwargs)

        #Local constants
        self.BUTTON_WIDTH: int = 20

        # Layout
        self._title = ctk.CTkLabel(self, text='Welcome to your bird pin database!', 
                                  font=ctk.CTkFont("Arial", 20, "bold"))
        self.subtitle = ctk.CTkLabel(self, text='What would you like to do?', 
                                     font=ctk.CTkFont("Arial", 15, "bold"))

        self.new_pin_button = ctk.CTkButton(self, 
                                            width=self.BUTTON_WIDTH, 
                                            text='Enter new pin', 
                                            command=lambda: master.switch_window(master.NEW_PIN))
        self.edit_pin_button = ctk.CTkButton(self, 
                                             width=self.BUTTON_WIDTH, 
                                             text='Edit existing pin entry', 
                                             command=lambda: master.switch_window(master.EDIT_PIN))
        self.new_source_button = ctk.CTkButton(self, 
                                               width=self.BUTTON_WIDTH, 
                                               text='Enter new source', 
                                               command=lambda: master.switch_window(master.NEW_SOURCE))
        self.edit_source_button = ctk.CTkButton(self, 
                                                width=self.BUTTON_WIDTH, 
                                                text='Edit existing source', 
                                                command=lambda: master.switch_window(master.EDIT_SOURCE))
        self.update_database_button = ctk.CTkButton(self, 
                                                    width=self.BUTTON_WIDTH, 
                                                    text='Update local bird database', 
                                                    command=self._update_database)

        self._title.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.subtitle.grid(row=1, column=0, columnspan=3)

        self.new_pin_button.grid(row=3, column=0)
        self.edit_pin_button.grid(row=4, column=0)
        self.new_source_button.grid(row=3, column=2)
        self.edit_source_button.grid(row=4, column=2)
        self.update_database_button.grid(row=5, column=0, columnspan=3)

class ScreenEnterNewPin(ctk.CTkFrame):

    def _layout_species_frame_initial(self) -> None:
        self.species_name_input = ctk.StringVar()
        self._species_entry_box = ctk.CTkEntry(self.species_frame_initial, 
                                              textvariable=self.species_name_input,
                                              width=self.LONG_BOX_WIDTH)
        self._species_entry_box.grid(**self.SPECIES_FRAME_LAYOUT['NAME_LOCATION'])
        self._species_find_button = ctk.CTkButton(self.species_frame_initial, text='Find', 
                                                    width=self.BUTTON_WIDTH, 
                                                    command=self._find_species_pressed)
        self._species_find_button.grid(**self.SPECIES_FRAME_LAYOUT['BUTTON_LOCATION'])
        self.species_error_label = ctk.CTkLabel(self.species_frame_initial, text='', text_color='red', 
                                                font=ctk.CTkFont(family="Arial", size=10))
        self.species_error_label.grid_configure(**self.SPECIES_FRAME_LAYOUT['ERROR_LABEL_LOCATION'])
        return None

    def _layout_species_frame_dropdown(self) -> None: 
        self.picked_species = ctk.StringVar()
        self._species_dropdown = ctk.CTkComboBox(self.species_frame_dropdown, values=[], 
                                                variable=self.picked_species,
                                                width=self.LONG_BOX_WIDTH)
        self._species_dropdown.grid(**self.SPECIES_FRAME_LAYOUT['NAME_LOCATION'])
        self.species_confirmed: bool = False
        self._species_confirm_button = ctk.CTkButton(self.species_frame_dropdown, text='Confirm',
                                                    width=self.BUTTON_WIDTH,
                                                    command=self._confirm_species_pressed)
        self._species_confirm_button.grid(**self.SPECIES_FRAME_LAYOUT['BUTTON_LOCATION'])
        return None

    def _layout_species_frame_confirmed(self) -> None:
        self.picked_species_label = ctk.CTkLabel(self.species_frame_confirmed, text = '',
                                                 width=self.LONG_BOX_WIDTH)
        self.picked_species_label.grid(**self.SPECIES_FRAME_LAYOUT['NAME_LOCATION'])
        self.subspecies_toggle_var = ctk.BooleanVar(value=False)
        self._subspecies_toggle = ctk.CTkSwitch(self.species_frame_confirmed, text='Subspecies?',
                                               variable=self.subspecies_toggle_var,
                                               command=self._subspecies_toggle_pressed)
        self._subspecies_toggle.grid(**self.SPECIES_FRAME_LAYOUT['BUTTON_LOCATION'])
        return None


    def _layout_subspecies_frame_initial(self) -> None:
        self.picked_subspecies = ctk.StringVar()
        self._subspecies_dropdown = ctk.CTkComboBox(self.subspecies_frame_initial, 
                                                   values=[], 
                                                   variable=self.picked_subspecies,
                                                   width=self.LONG_BOX_WIDTH)
        self._subspecies_dropdown.grid(**self.SUBSPECIES_FRAME_LAYOUT['NAME_LOCATION'])        
        self._subspecies_confirm_button = ctk.CTkButton(self.subspecies_frame_initial, 
                                                       text='Confirm',
                                                       width=self.BUTTON_WIDTH,
                                                       command=self._confirm_subspecies_pressed)
        self._subspecies_confirm_button.grid(**self.SUBSPECIES_FRAME_LAYOUT['BUTTON_LOCATION'])
        return None

    def _layout_subspecies_frame_confirmed(self) -> None:
        self.picked_subspecies_label = ctk.CTkLabel(self.subspecies_frame_confirmed, text='',
                                                    width=self.LONG_BOX_WIDTH)
        self.picked_subspecies_label.grid(**self.SUBSPECIES_FRAME_LAYOUT['NAME_LOCATION'])
        return None


    def _layout_source_frame_initial(self) -> None:
        self.picked_source_type = ctk.StringVar()
        self.source_type_dropdown = ctk.CTkComboBox(self.source_frame_initial, 
                                                   values=['Charity', 'Artist', 'Other'], 
                                                   variable=self.picked_source_type,
                                                   command=self._source_type_dropdown_changed)
        self.source_type_dropdown.grid(**self.SOURCE_FRAME_LAYOUT['TYPE_DROPDOWN_LOCATION'])    
        self.picked_source = ctk.StringVar()
        self.source_dropdown = ctk.CTkComboBox(self.source_frame_initial, 
                                               values=[], 
                                               variable=self.picked_source, 
                                               command=self._source_dropdown_activated,
                                               state=ctk.DISABLED)
        self.source_dropdown.grid(**self.SOURCE_FRAME_LAYOUT['SOURCE_DROPDOWN_LOCATION'])     
        self.source_confirmed: bool = False
        self._source_confirm_button = ctk.CTkButton(self.source_frame_initial, 
                                                       text='Confirm',
                                                       width=self.BUTTON_WIDTH,
                                                       command=self._confirm_source_pressed,
                                                       state=ctk.DISABLED)
        self._source_confirm_button.grid(**self.SOURCE_FRAME_LAYOUT['BUTTON_LOCATION']) 
        return None 

    def _layout_source_frame_confirmed(self) -> None:
        self.picked_source_label = ctk.CTkLabel(self.source_frame_confirmed, text='')
        self.picked_source_label.grid(**self.SOURCE_FRAME_LAYOUT['LONG_LABEL_LOCATION'])
        self.subgroup_toggle_var = ctk.BooleanVar(value=False)
        self._subgroup_toggle = ctk.CTkSwitch(self.source_frame_confirmed, text='Subgroup?',
                                               variable=self.subgroup_toggle_var,
                                               command=self._subgroup_toggle_pressed)
        self._subgroup_toggle.grid(**self.SOURCE_FRAME_LAYOUT['BUTTON_LOCATION'])
        return None


    def _layout_subgroup_frame_initial(self) -> None:
        self.picked_subgroup = ctk.StringVar()
        self._subgroup_dropdown = ctk.CTkComboBox(self.subgroup_frame_initial, 
                                               values=[], 
                                               variable=self.picked_subgroup,
                                               width=self.BUTTON_WIDTH)
        self._subgroup_dropdown.grid(**self.SUBGROUP_FRAME_LAYOUT['DROPDOWN_LOCATION'])    
        self._subgroup_confirm_button = ctk.CTkButton(self.subgroup_frame_initial, 
                                                       text='Confirm',
                                                       width=self.BUTTON_WIDTH,
                                                       command=self._confirm_subgroup_pressed)
        self._subgroup_confirm_button.grid(**self.SUBGROUP_FRAME_LAYOUT['BUTTON_LOCATION']) 
        return None         
    
    def _layout_subgroup_frame_confirmed(self) -> None:
        self.picked_subgroup_label = ctk.CTkLabel(self.subgroup_frame_confirmed, text='')
        self.picked_subgroup_label.grid(**self.SUBGROUP_FRAME_LAYOUT['DROPDOWN_LOCATION'])
        return None


    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)

        # Class-scoped variables
        self.picked_species_data: BirdDict
        self.picked_subspecies_data: SubspeciesDict

        # --------------------Layout-------------------- #

        # Local constants
        self.BUTTON_WIDTH: int = 20
        self.LONG_BOX_WIDTH: int = 300
        self.REJECT_OPTIONS: str = 'None of the above'

        self.TITLE_LOCATION: dict[str, int] = {'row': 0, 'column': 0, 'columnspan': 4, 
                                               'padx': 10, 'pady': 10}
        self.SPECIES_LABEL_LOCATION: dict[str, int] = {'row': 1, 'column': 0, 
                                                       'padx': 10}
        self.SPECIES_FRAME_LOCATION: dict[str, int] = {'row': 1, 'column': 1, 'columnspan': 4, 'rowspan': 2}
        self.SUBSPECIES_FRAME_LOCATION: dict[str, int | str] = {'row': 3, 'column': 0, 'columnspan': 4, 
                                                                'sticky': 'W'}
        self.SOURCE_LABEL_LOCATION: dict[str, int] = {'row': 4, 'column': 0, 
                                                       'padx': 10}
        self.SOURCE_FRAME_LOCATION: dict[str, int] = {'row': 4, 'column': 1, 'columnspan': 4}
        self.SUBGROUP_FRAME_LOCATION: dict[str, int] = {'row': 5, 'column': 0, 'columnspan': 4}
        self.VALIDATE_BUTTON_LOCATION:  dict[str, int] = {'row': 6, 'column': 1, 'columnspan': 2}

        self.SPECIES_FRAME_LAYOUT: dict[str, dict[str, int]] = {'NAME_LOCATION': {'row': 0, 'column': 1, 
                                                                                  'columnspan': 2}, 
                                                                'BUTTON_LOCATION':{'row': 0, 'column': 3},
                                                                'ERROR_LABEL_LOCATION':{'row': 1, 'column': 1,
                                                                                        'columnspan': 2}}
        self.SUBSPECIES_FRAME_LAYOUT: dict[str, dict[str,int]] = self.SPECIES_FRAME_LAYOUT
        self.SOURCE_FRAME_LAYOUT: dict[str, dict[str,int]] = {'TYPE_DROPDOWN_LOCATION': {'row': 0, 'column': 1}, 
                                                              'SOURCE_DROPDOWN_LOCATION':{'row': 0, 'column': 2},
                                                              'BUTTON_LOCATION':{'row': 0, 'column': 3},
                                                              'LONG_LABEL_LOCATION': {'row': 0, 'column': 1,
                                                                                      'columnspan': 2}}
        self.SUBGROUP_FRAME_LAYOUT: dict[str, dict[str,int]] = {'DROPDOWN_LOCATION': {'row': 0, 'column': 1},
                                                              'BUTTON_LOCATION':{'row': 0, 'column': 2}}

        # Title
        self._title = ctk.CTkLabel(self, text='Enter new pin details', 
                                  font=ctk.CTkFont(family="Arial", size=20, weight="bold"))

        # Possible states for the first row
        self._species_label = ctk.CTkLabel(self, text='Species: ')

        self.species_frame_initial = ctk.CTkFrame(self)
        self._layout_species_frame_initial()
        self.species_frame_dropdown = ctk.CTkFrame(self)
        self._layout_species_frame_dropdown()
        self.species_frame_confirmed = ctk.CTkFrame(self)
        self._layout_species_frame_confirmed()

        # Possible states for the second row
        self.subspecies_frame_parent = ctk.CTkFrame(self)
        self._subspecies_label = ctk.CTkLabel(self.subspecies_frame_parent, text='Subspecies: ')

        self.subspecies_frame_initial = ctk.CTkFrame(self.subspecies_frame_parent)
        self._layout_subspecies_frame_initial()
        self.subspecies_frame_confirmed = ctk.CTkFrame(self.subspecies_frame_parent)
        self._layout_subspecies_frame_confirmed()

        self._subspecies_label.grid(row=0, column=0)
        self.subspecies_frame_initial.grid(row=0, column=1)

        # Possible states for the third row
        self._source_label = ctk.CTkLabel(self, text='Source: ')

        self.source_frame_initial = ctk.CTkFrame(self)
        self._layout_source_frame_initial()
        self.source_frame_confirmed = ctk.CTkFrame(self)
        self._layout_source_frame_confirmed()

        # Possible states for the fourth row
        self.subgroup_frame_parent = ctk.CTkFrame(self)
        self.subgroup_label = ctk.CTkLabel(self.subgroup_frame_parent, text='Subgroup: ')

        self.subgroup_frame_initial = ctk.CTkFrame(self.subgroup_frame_parent)
        self._layout_subgroup_frame_initial()
        self.subgroup_frame_confirmed = ctk.CTkFrame(self.subgroup_frame_parent)
        self._layout_subgroup_frame_confirmed()

        self.subgroup_label.grid(row=0, column=0)
        self.subgroup_frame_initial.grid(row=0, column=1)

        # Fifth row
        self._validate_button = ctk.CTkButton(self, text='Validate', 
                                             width=self.BUTTON_WIDTH, 
                                             command=self._validate_button_pressed,
                                             state='disabled')
 

        # Grid the initial state
        self._title.grid(**self.TITLE_LOCATION)
        self._species_label.grid(**self.SPECIES_LABEL_LOCATION)   
        self.species_frame_initial.grid(**self.SPECIES_FRAME_LOCATION)
        self._source_label.grid(**self.SOURCE_LABEL_LOCATION)
        self.source_frame_initial.grid(**self.SOURCE_FRAME_LOCATION)
        self._validate_button.grid(**self.VALIDATE_BUTTON_LOCATION)


    def _search_in_database(self, test_name: str) -> list[DictWithScore[BirdDict]]:
        bridge = UserLocalDBBridge()
        possible_species_with_scores: list[DictWithScore[BirdDict]] = bridge.fuzzy_search_species_ebird(test_name)
        bridge.close_connection()
        return possible_species_with_scores

    def _add_species_to_menu(self, species_with_scores: list[DictWithScore[BirdDict]]) -> None:
        dropdown_options: list[str] = [self.REJECT_OPTIONS]
        for species_data, score in species_with_scores:
            dropdown_options.append(f"{species_data['common_name']} ({score}% match)")
        self._species_dropdown.configure(values = dropdown_options)
        return None

    def _add_subspecies_to_menu(self, subspecies_list: list[SubspeciesDict]) -> None:
        dropdown_options: list[str] = []
        for subspecies in subspecies_list:
            dropdown_options.append(subspecies['common_name'])
        self._subspecies_dropdown.configure(values = dropdown_options)
        return None

    def _add_subgroups_to_menu(self, subgroups_list: list[SubgroupDict]) -> None:
        dropdown_options: list[str] = []
        for subgroup in subgroups_list:
            dropdown_options.append(subgroup['name'])
        self._subgroup_dropdown.configure(values = dropdown_options)
        return None

    def _try_activate_validate_button(self) -> None:
        if self.source_confirmed and self.species_confirmed:
            self._validate_button.configure(state=ctk.NORMAL)
        return None


    def _find_species_pressed(self) -> None:
        self.species_error_label.grid_forget()
        species_name: str = self.species_name_input.get()
        if species_name == '':
            return None
        self.possible_species_with_scores: list[DictWithScore[BirdDict]] = self._search_in_database(species_name)
        if self.possible_species_with_scores == []:
            self.species_error_label.configure(text='No species found. Double check the name!')
            self.species_error_label.grid(**self.SPECIES_FRAME_LAYOUT['ERROR_LABEL_LOCATION'])
            return None
        if len(self.possible_species_with_scores) > 10:
            self.species_error_label.configure(text='Too many possible matches. Try being more specific!')
            self.species_error_label.grid(**self.SPECIES_FRAME_LAYOUT['ERROR_LABEL_LOCATION'])
            return None
        
        self.species_frame_initial.grid_forget()

        self._add_species_to_menu(self.possible_species_with_scores)

        self.species_frame_dropdown.grid(**self.SPECIES_FRAME_LOCATION)
        return None

    def _confirm_species_pressed(self) -> None:
        picked_option: str = self._species_dropdown.get()
        if picked_option == self.REJECT_OPTIONS:
            # Reset to previous state
            self._species_dropdown.configure(values=[self.REJECT_OPTIONS])
            self.species_frame_dropdown.grid_forget()
            self.species_frame_initial.grid()
            return None
        for data in self.possible_species_with_scores:
            if f"{data[0]['common_name']} ({data[1]}% match)" == picked_option:
                self.picked_species_data=data[0]
        self.species_frame_dropdown.grid_forget()
        self.picked_species_label.configure(text = picked_option)
        self.species_frame_confirmed.grid(**self.SPECIES_FRAME_LOCATION)
        self.species_confirmed = True
        self._try_activate_validate_button()

        species_code: str = self.picked_species_data['eBird_code']
        bridge = EBirdBridge()
        possible_subspecies: Optional[list[SubspeciesDict]] = bridge.retrieve_subspecies(species_code)
        bridge.close_connection()        
        if possible_subspecies is None:
            raise ConnectionError('Something went wrong while connecting to eBird')
        if len(possible_subspecies) == 1:
            self._subspecies_toggle.grid_forget()
            return None
        self.possible_subspecies: list[SubspeciesDict] = possible_subspecies
        self._add_subspecies_to_menu(self.possible_subspecies)
        return None

    def _subspecies_toggle_pressed(self) -> None:
        state:bool = self.subspecies_toggle_var.get()
        if not state:
            self.subspecies_frame_parent.grid_forget()
            return None
        self.subspecies_frame_parent.grid(**self.SUBSPECIES_FRAME_LOCATION)
        return None

    def _confirm_subspecies_pressed(self) -> None:
        picked_option: str = self._subspecies_dropdown.get()
        if picked_option is None:
            return None
        for data in self.possible_subspecies:
            if data['common_name'] == picked_option:
                self.picked_subspecies_data=data
        self.subspecies_frame_initial.grid_forget()
        self.picked_subspecies_label.configure(text = picked_option)
        self.subspecies_frame_confirmed.grid(row=0, column=1)
        return None

    def _source_type_dropdown_changed(self, source_type: Literal['Charity', 'Artist', 'Other']) -> None:
        bridge = UserLocalDBBridge()
        source_list: list[SourceDict] = bridge.retrieve_sources(source_type)
        bridge.close_connection()
        if source_list == []:
            self.source_dropdown.configure(state=ctk.DISABLED)
            return None
        options: list[str] = []
        for source in source_list:
            options.append(source['name'])
        self.source_dropdown.configure(state=ctk.NORMAL)
        self.source_dropdown.configure(values=options)
        return None

    def _source_dropdown_activated(self, source: str) -> None:
        if not source:
            return None
        self._source_confirm_button.configure(state=ctk.NORMAL)
        return None

    def _confirm_source_pressed(self) -> None:
        picked_source: str = self.source_dropdown.get()
        if picked_source == '':
            return None
        self.picked_source_label.configure(text=picked_source)
        self.source_frame_initial.grid_forget()
        self.source_frame_confirmed.grid(**self.SOURCE_FRAME_LOCATION)
        self.source_confirmed = True
        self._try_activate_validate_button()

        bridge = UserLocalDBBridge()
        subgroups: list[SubgroupDict] = bridge.retrieve_subgroups(picked_source)
        bridge.close_connection()
        if subgroups == []:
            self._subgroup_toggle.grid_forget()
            return None
        self._add_subgroups_to_menu(subgroups)
        return None

    def _subgroup_toggle_pressed(self) -> None:
        state: bool = self.subgroup_toggle_var.get()
        if not state:
            self.subgroup_frame_parent.grid_forget()
            return None
        self.subgroup_frame_parent.grid(**self.SUBGROUP_FRAME_LOCATION)
        return None

    def _confirm_subgroup_pressed(self) -> None:
        picked_subgroup: str = self._subgroup_dropdown.get()
        if picked_subgroup == '':
            return None
        self.picked_subgroup_label.configure(text=picked_subgroup)
        self.subgroup_frame_initial.grid_forget()
        self.subgroup_frame_confirmed.grid(row=0, column=1)
        return None

    def _validate_button_pressed(self) -> None:
        picked_species: str = self._species_dropdown.get()
        is_subspecies: bool = self._subspecies_toggle.get()
        picked_subspecies: str | None = None
        if is_subspecies:
            picked_subspecies = self._subspecies_dropdown.get()
        picked_source: str = self.source_dropdown.get()
        is_subgroup: bool = self._subgroup_toggle.get()
        picked_subgroup: str | None = None
        if is_subgroup:
            picked_subgroup = self._subgroup_dropdown.get()
        pin: PinDict
        # Splitting into cases so can return an appropriate error message later.
        if not picked_species:
            return None
        if is_subspecies and not picked_subspecies:
            return None
        if not picked_source:
            return None
        if is_subgroup and not picked_subgroup:
            return None
        pin = {'id': None, 
               'species': picked_species, 
               'subspecies': picked_subspecies, 
               'source': picked_source,
               'subgroup': picked_subgroup}
        
        bridge = UserLocalDBBridge()
        bridge.LocalDBInterface.pin_table.add_data([pin])
        bridge.close_connection()

        self._validate_button.configure(state=ctk.DISABLED, text='Validated')
        return None

class ScreenEditPin(ctk.CTkFrame):

    def _test(self):
        print('not implemented')

    pass

class ScreenEnterNewSource(ctk.CTkFrame):

    def _test(self):
        print('not implemented')
    pass

class ScreenEditSource(ctk.CTkFrame):

    def _test(self):
        print('not implemented')
    pass



@logged()
def main(auto_test: bool = False):
    if auto_test:
        import doctest
        doctest.testmod()
        return None
    app = App()
    # app.bind("<Configure>", app.bg_resizer)
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


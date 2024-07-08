# time_config_menu.py
from menu import Menu

class TimeConfigMenu(Menu):
    def __init__(
        self,
        screen_width,
        screen_height,
        spi_device,
        spi_sck,
        spi_sda,
        spi_cs,
        res,
        dc,
        encoder_pins,
        led_pin,
        header,
        selectables,
        cursor=">"
    ):
        super().__init__(
            screen_width,
            screen_height,
            spi_device,
            spi_sck,
            spi_sda,
            spi_cs,
            res,
            dc,
            encoder_pins,
            led_pin,
            header,
            selectables,
            cursor
        )

        # Time configuration variables
        self.hours = 0
        self.minutes = 0
        self.seconds = 0

    def set_display(self):
        """
        Description: Initializes display from an array of text strings.
            Header is the first row.
            Remaining rows are selectable items.
            The cursor is assigned to a selectable item associated with the counter.
        """

        # set the cursor at the encoder position
        current = self.get_cursor_position()
        print(f"counter position: {current}")
        
        # Get a copy of selectables for cursor mutation
        selectables = list(self.selectables)

        original_text = selectables[current]
        selectables[current] = f"{self.cursor_icon} {original_text}"
        
        # update display
        col = 0
        
        # Update display for the number of selectable items present
        for i in range(len(selectables)):
            self.display.update_text(selectables[i], col, i + 2)
        
        # Display current time settings
        self.display.update_text(f"Hours: {self.hours}", col, self.selectables_count + 3)
        self.display.update_text(f"Minutes: {self.minutes}", col, self.selectables_count + 4)
        self.display.update_text(f"Seconds: {self.seconds}", col, self.selectables_count + 5)
        
    def track_encoder(self):
        """
        Description: Tracks for encoder rotations and button response
        """

        while not self.stop_event.is_set():
            current_count = self.get_cursor_position()

            if current_count != self.last_count:
                print(f"Counter changed: {current_count}")
                self.last_count = current_count
                
                self.set_display()
                
            # Handle button press to update hours, minutes, and seconds
            if self.get_button_state() != self.last_button_state:
                self.last_button_state = self.get_button_state()
                if self.last_button_state:  # Button pressed
                    if current_count == 0:  # Hours
                        self.hours = (self.hours + 1) % 24
                    elif current_count == 1:  # Minutes
                        self.minutes = (self.minutes + 1) % 60
                    elif current_count == 2:  # Seconds
                        self.seconds = (self.seconds + 1) % 60
                    self.set_display()
            
            # Add a small delay to avoid a busy loop
            time.sleep(0.1)
        print("Thread exiting gracefully")

from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
from ui import UI
import copy
import time
import sys

#from ui import UI
#import copy
#import sys
#from encoder import RotaryEncoder


class Menu(UI):
    def __init__(
        self,
        display,
        encoder_pins,
        led_pin,
        header,
        selectables,
        id,
        cursor=">",
        context=None
    ):
        self.display = display
        self.header = header
        self.selectables = selectables
        self.selectables_count = len(selectables)
        self.cursor_icon = cursor
        self.id = id
        
        # stores information to pass to the next UI
        self.context = context or {}

        try:
            self.encoder = RotaryEncoder(
                pin_a=encoder_pins[0], 
                pin_b=encoder_pins[1], 
                pin_switch=encoder_pins[2], 
                led_pin=led_pin, 
                rollover=True,
                max=self.selectables_count,
                min=1
            )
        except Exception as e:
            sys.print_exception(e)
            print("ENCODER NOT CREATED FOR MENU")
            raise
        
        self.last_count = self._get_cursor_position_modulus()
        self._update_count_and_display(self.last_count)
        
    def _get_cursor_position_modulus(self):
        current_count = self.encoder.get_counter()[0]
        current_count -= 1
        if current_count < 0:
            current_count = 0
        return current_count

    def _has_selection_changed(self):
        count = self.last_count
        if self._get_cursor_position_modulus() != self.last_count:
            return True
        return False
    
    def _update_cursor_to_current_selection(self, current_count):
        selectables = copy.deepcopy(list(self.selectables))
        selected = selectables[current_count]
        original_text = selected.get("display_text")
        selected["display_text"] = f"{self.cursor_icon} {original_text}"
        col = 0
        for i in range(len(selectables)):
            current = selectables[i]
            self.display.update_text(current.get("display_text"), col, i)

    def _update_count_and_display(self, current_count):
        self.last_count = current_count
        self._update_cursor_to_current_selection(current_count)

    def poll_selection_change_and_update_display(self):
        current_count = self._get_cursor_position_modulus()
        if self._has_selection_changed():
            self._update_count_and_display(current_count)
            return True
        return False
    
    def is_encoder_button_pressed(self):
        return self.encoder.get_button_state()
    
    #def get_selection(self):
    def get_context(self):
        """
        If the encoder button is pressed, perform duties
        associated with the selected item and return the
        next menu ID and context.
        """
        if self.is_encoder_button_pressed():
            selected_index = self.encoder.get_counter()[0]-1
            print(f"INDEX: {selected_index}")
            selected_item = self.selectables[selected_index]
            return {"id": selected_item["id"], "context": self.context}
        return None
    
    #def get_selection(self):
    #    selected_index = self._get_cursor_position_modulus()
    #    print(f"get_selection: {self.selectables[selected_index]}")
    #    return {"id": self.selectables[selected_index]["id"], "display_text": self.selectables[selected_index]["display_text"]}

    def resetNOTUSING(self):
        self.encoder.reset_counter()
        self.update_display()

    def stopNOTUSING(self):
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.button.disable_irq()
        
    def _disable_interrupts(self):
        print("disable interrupts")
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.button.disable_irq()
        self.display.clear()

    def stop(self):
        self._disable_interrupts()


class MenuBak(UI):
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
        id,
        cursor=">"
    ):
        super().__init__(screen_width, screen_height, spi_device, spi_sck, spi_sda, spi_cs, res, dc, encoder_pins, led_pin, header)
        self.selectables = selectables
        self.selectables_count = len(selectables)
        self.cursor_icon = cursor
        self.id = id
        
        # Initialize clock radio display for SPI
        # doesn't work
        #self.display = self.initialize_display(screen_width, screen_height, spi_device, spi_sck, spi_sda, spi_cs, res, dc)
      
        try:
            self.display = CR_SPI_Display(
                screen_width=screen_width,
                screen_height=screen_height,
                spi_dev=spi_device,
                spi_sck=spi_sck,
                spi_sda=spi_sda,
                spi_cs=spi_cs,
                res=res,
                dc=dc
            )
        except Exception as e:
            sys.print_exception(e)
            print("DISPLAY NOT CREATED FOR MENU")
            raise
        
        # Create an instance of the RotaryEncoder
        self.encoder = RotaryEncoder(
            pin_a=encoder_pins[0], 
            pin_b=encoder_pins[1], 
            pin_switch=encoder_pins[2], 
            led_pin=led_pin, 
            rollover=True, 
            max=self.selectables_count # modulus rollover 
        )
        self.last_count = self._get_cursor_position_modulus()
        self._update_count_and_display(self.last_count)
        
    def _get_cursor_position_modulus(self):
        """
        Currently ignoring direction
        """
        current_count = self.encoder.get_counter()[0]
        current_count -= 1
        if current_count < 0:
            current_count = 0
        return current_count

    def _has_selection_changed(self):
        """
        Description: selection currently maps to an encoder rotation
        """
        count = self.last_count
        if self._get_cursor_position_modulus() != self.last_count:
            return True
        return False
    
    def _update_cursor_to_current_selection(self, current_count):
        """
        Shows cursor icon on currently selected item in menu
        """
        # Update cursor to reflect new selection
        # Don't save the cursor modification the raw selectables list
        selectables = copy.deepcopy(list(self.selectables))
        selected = selectables[current_count]
        #print(f"selected: {selected}")

        original_text = selected.get("display_text")
        selected["display_text"] = f"{self.cursor_icon} {original_text}"
        
        # Update display for the number of selectable items present
        col = 0
        for i in range(len(selectables)):
            current = selectables[i]
            self.display.update_text(current.get("display_text"), col, i)

        
    def _update_count_and_display(self, current_count):
        """
        Call this to update last_count if user input detected
        """
        # Update last_count and cursor to rotated item
        self.last_count = current_count
        self._update_cursor_to_current_selection(current_count)


    def poll_selection_change_and_update_display(self):
        """
        Check for user input change (encoder rotation) and update the
        active selection appropriately. Should be called frequently by
        caller thread.
        Return (bool): False if a user input has not been detected.
        """
        current_count = self._get_cursor_position_modulus()
        if self._has_selection_changed():
            self._update_count_and_display(current_count)
            return True
        return False
    
    def is_encoder_button_pressed(self):
        return self.encoder.get_button_state()
    
    def get_selection(self):
        selected_index = self._get_cursor_position_modulus()
        print(f"get_selection: {self.selectables[selected_index]}")
        return {"id": self.selectables[selected_index]["id"], "display_text": self.selectables[selected_index]["display_text"]}


    def _disable_interrupts(self):
        print("disable interrupts")
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        #self.encoder.pin_switch.irq(handler=None)
        self.encoder.button.disable_irq()

    def stop(self):
        self._disable_interrupts()
        # TODO: loaded menu should have name property - log that menu was disabled.
        #self.display.release()
        #print("powered off....")

'''
    def track_encoder(self):
        """
        EXPIRED: this consumes the thread.  No while True loops here
        Description: tracks current position of the encoder and
            updates display.  We can stop/start polling the encoder position
            with the tracking property to remap it to a new set of menu
            'selectables' defined in the menu scheme.
        """
        while self.tracking:
            current_count = self.get_cursor_position_modulus()

            if current_count != self.last_count:
                print(f"Counter changed: {current_count}")
                self.last_count = current_count
                self.update_display()
                
            time.sleep(0.1)
        print("Exiting encoder tracking")

    def stop_tracking(self):
        # EXPIRED
        self.tracking = False

    def start_tracking(self):
        # EXPIRED
        self.tracking = True
'''
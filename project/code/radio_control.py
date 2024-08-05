from fm_radio import Radio


class RadioControl:
    def __init__(self):
        print("Initializing RadioControl")
        self.muted = True
        # GP 26 and 27
        # self.radio = Radio(100.3, 2, self.muted, 26, 27) # uvic
        # self.radio = Radio(98.5, 2, self.muted, 26, 27)
        self.radio = Radio(103.1, 2, self.muted, 26, 27)

        print("RadioControl initialized")

    def toggle_mute(self):
        self.muted = not self.muted
        self.radio.SetMute(self.muted)
        self.radio.ProgramRadio()

    def set_volume(self, volume):
        self.radio.SetVolume(volume)
        self.radio.ProgramRadio()
        print("RadioControl volume set to {volume}")

    def scan(self):
        "50 to 115Mhz"
        pass

    def set_frequency(self, frequency):
        self.radio.SetFrequency(frequency)
        self.radio.ProgramRadio()

    def get_volume(self):
        return self.radio.Volume

    def get_frequency(self):
        # Return the current frequency from the Radio instance
        return self.radio.Frequency

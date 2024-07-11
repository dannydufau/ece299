# display_config.py

from display import CR_SPI_Display, CR_SPI_Display_Second

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SPI_DEVICE = 0

REPORT_SCREEN_WIDTH = 128
REPORT_SCREEN_HEIGHT = 64
SPI_DEVICE_REPORT = 1

def create_navigation_display():
    return CR_SPI_Display(
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        spi_dev=SPI_DEVICE,
        spi_sck=2,
        spi_sda=3,
        spi_cs=5,
        res=4,
        dc=6
    )

def create_report_display():
    return CR_SPI_Display_Second(
        screen_width=REPORT_SCREEN_WIDTH,
        screen_height=REPORT_SCREEN_HEIGHT,
        spi_dev=SPI_DEVICE_REPORT,
        spi_sck=10,
        spi_sda=11,
        spi_cs=13,
        res=14,
        dc=12
    )

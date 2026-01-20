# Minimal Anvil Kernel printk implementation
# This is a placeholder to get a basic boot sequence working.
# It bypasses the complex buffering and log level logic of the C original.

# A global list to hold registered console drivers.
# In a real scenario, this would be populated by device drivers.
_console_drivers = []

def register_console(driver):
    """
    Adds a console driver to the list of output devices.
    A driver is expected to be an object with a 'write(string)' method.
    """
    if hasattr(driver, 'write') and callable(driver.write):
        _console_drivers.append(driver)
        # In a more complex system, we might print a confirmation here,
        # but for the minimal kernel, we do nothing to avoid circular dependencies.

def printk(message):
    """
    Writes a message to all registered consoles.
    Appends a newline character for simplicity.
    """
    # Ensure the message ends with a newline, as is common for console output.
    if not message.endswith('\n'):
        message += '\n'

    if not _console_drivers:
        # This is a critical problem: the kernel is trying to print a message,
        # but no output device has been registered. There's nowhere for the
        # message to go. In a real kernel, this might trigger a specific
        # hardware action (like beeping), but here we are helpless.
        # We cannot print an error because... that's what we're trying to do.
        # We simply have to return.
        return

    for driver in _console_drivers:
        try:
            driver.write(message)
        except Exception as e:
            # A console driver has failed. This is another critical error.
            # We can't report the error through the failing driver.
            # We also can't easily remove the driver from the list without
            # potential concurrency issues (which we are ignoring for now).
            # The best we can do is try the other drivers and hope one works.
            pass

# --- Example/Placeholder Console Driver ---
# This would typically be in its own file, e.g., `drivers/char/serial.mpy`
class SerialConsole:
    """
    A placeholder for a real serial console driver.
    In a real implementation, the write() method would interact with
    hardware registers (e.g., UART) to send characters.
    """
    def write(self, message):
        # This is where the magic would happen. For now, we simulate by
        # writing to the host system's stdout. When running in a real
        # VM or on bare metal, this would be replaced with low-level code.
        # For example:
        # for char in message:
        #     while not (mmio_read(UART_LSR) & 0x20):
        #         pass
        #     mmio_write(UART_THR, ord(char))
        
        # The Python `print` function is our stand-in for a hardware serial port.
        print(f"[SERIAL] {message}", end='')

# --- Early Kernel Initialization ---
# During boot, a platform-specific setup function would create an
# instance of the appropriate console driver and register it.
def early_init_console():
    """
    This function would be called very early in the boot process to
    set up a basic console for kernel messages.
    """
    # For our minimal kernel, we'll just register our placeholder.
    console = SerialConsole()
    register_console(console)


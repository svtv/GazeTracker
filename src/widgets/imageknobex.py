from tkdial import ImageKnob

class ImageKnobEx(ImageKnob):
    def __init__(self, *args,
                 scroll_steps_precise=0.001,
                 variable=None,
                 **kwargs):
        self.scroll_steps_precise = scroll_steps_precise
        self.variable = variable
        super().__init__(*args, **kwargs)
        if self.variable:
            self.set(self.variable.get())

    def set(self, value):
        """Override set method to ensure value stays within bounds and update variable"""
        value = max(self.start, min(self.max, value))
        if self.variable:
            self.variable.set(value)
        return super().set(value)

    def scroll_command(self, event):
        """Handle mouse wheel events"""
        if isinstance(event, int):
            event_delta = event
            ctrl_pressed = False
        else:
            event_delta = event.delta
            ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed

        # Set step based on Ctrl press
        current_step = self.scroll_steps_precise if ctrl_pressed else self.scroll_steps

        # Calculate new value
        delta = current_step if event_delta > 0 else -current_step
        self.set(self.value + delta)

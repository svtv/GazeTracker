from tkdial import ImageKnob

class ImageKnobEx(ImageKnob):
    def __init__(self, *args, 
                 scroll_steps_precise=0.001, 
                 **kwargs):
                 
        self.scroll_steps_precise = scroll_steps_precise
        super().__init__(*args, **kwargs)
        
    def set(self, value):
        """Override set method to ensure value stays within bounds"""
        value = max(self.start, min(self.max, value))
        return super().set(value)
        
    def scroll_command(self, event):
        """Handle mouse wheel events"""
        if type(event) is int:
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

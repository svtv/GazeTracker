from tkdial import ImageKnob

class ImageKnobEx(ImageKnob):
    def __init__(self, *args, 
                 scroll_steps_precise=0.001, 
                 **kwargs):
                 
        self.scroll_steps_precise = scroll_steps_precise
        super().__init__(*args, **kwargs)
        
    def scroll_command(self, event):
        """
        Overridden function
        """
        if type(event) is int:
            event_delta = event
            ctrl_pressed = False
        else:
            event_delta = event.delta
            ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed
            
        # Set step based on Ctrl press
        current_step = self.scroll_steps_precise if ctrl_pressed else self.scroll_steps
            
        if event_delta > 0:        
            if self.value < self.max:
                self.set(self.value + current_step)
            elif self.value == self.max:
                self.set(self.max)
            else:
                self.set(self.value - current_step)
        else:
            if self.value > self.start:
                self.set(self.value - current_step)
            elif self.value == self.start:
                self.set(self.start)
            else:
                self.set(self.value + current_step)

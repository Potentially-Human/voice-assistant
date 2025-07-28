from pynput import keyboard
from asyncio import sleep, run
from queue import Queue
import threading

class KeyboardManager:
    def __init__(self, activation_keys: list, keydown_function, keyup_function):
        self.activation_keys = activation_keys
        self.keypressed = False
        self.keydown_function = keydown_function
        self.keyup_function = keyup_function
        self.events = Queue()

    def keydown(self, key):
        try: 
            if key.char in self.activation_keys:
                if not self.keypressed:
                    self.keypressed = True
                    self.events.put("keydown")
                
        except AttributeError:
            pass
    
    def keyup(self, key):
        try: 
            if key.char in self.activation_keys:
                if self.keypressed:
                    self.keypressed = False
                    self.events.put("keyup")

        except AttributeError:
            pass

        if key == keyboard.Key.esc:
            return False
        
    def activate(self):
        threading.Thread(target = self.process_events, daemon = True).start()
        listener = keyboard.Listener(on_press = self.keydown, on_release = self.keyup)
        listener.start()

    def process_events(self):
        while True:
            if not self.events.empty():
                match self.events.get():
                    case "keydown":
                        self.keydown_function()
                    case "keyup":
                        self.keyup_function()
                    case _:
                        raise NameError("Unknown event recieved.")
                    


# if __name__ == "__main__":
#     async def main():
#         keyboard_manager = KeyboardManager(["a", "b" , "c"])
#         keyboard_manager.activate()
#         for i in range(20):
#             if keyboard_manager.keypressed:
#                 print("Key pressed")
#             else:
#                 print("Key not pressed")
#             await sleep(0.2)

#     run(main())

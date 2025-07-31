from pynput import keyboard
from queue import Queue
import threading

class KeyboardManager:
    def __init__(self, activation_shortcuts: list, keydown_function, keyup_function):
        """
        activation_shortcuts: list of tuples, e.g. [('ctrl', 'q'), ('shift', 'a')]
        """
        self.activation_shortcuts = [tuple(map(str.lower, shortcut)) for shortcut in activation_shortcuts]
        self.keypressed = False
        self.keydown_function = keydown_function
        self.keyup_function = keyup_function
        self.events = Queue()
        self.current_keys = set()

    def key_to_str(self, key):
        if isinstance(key, keyboard.KeyCode):
            return key.char.lower() if key.char else ''
        elif isinstance(key, keyboard.Key):
            return str(key).split('.')[-1].lower()
        return ''

    def keydown(self, key):
        key_str = self.key_to_str(key)
        if key_str:
            self.current_keys.add(key_str)
        for shortcut in self.activation_shortcuts:
            if all(k in self.current_keys for k in shortcut):
                if not self.keypressed:
                    self.keypressed = True
                    #self.events.put("keydown")
                    self.keydown_function()

    def keyup(self, key):
        key_str = self.key_to_str(key)
        if key_str and key_str in self.current_keys:
            self.current_keys.remove(key_str)
        for shortcut in self.activation_shortcuts:
            if not all(k in self.current_keys for k in shortcut):
                if self.keypressed:
                    self.keypressed = False
                    # self.events.put("keyup")
                    self.keyup_function()
        if key == keyboard.Key.esc:
            return False

    def activate(self):
        # threading.Thread(target=self.process_events, daemon=True).start()
        listener = keyboard.Listener(on_press=self.keydown, on_release=self.keyup)
        listener.start()

    # def process_events(self):
    #     while True:
    #         if not self.events.empty():
    #             event = self.events.get()
    #             match event:
    #                 case "keydown":
    #                     self.keydown_function()
    #                 case "keyup":
    #                     self.keyup_function()
    #                 case _:
    #                     raise NameError("Unknown event received.")
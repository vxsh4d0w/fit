from model.configurations.tabs.option.option import Option as OptionModel

class Option():

    def __init__(self):
        self.model = OptionModel()
        self._options = self.model.get()
        if self._options:
           self._options = {key: value for key, value in self._options[0].__dict__.items() if not key.startswith("_") and not key.startswith("__") and not key.startswith("db")}

    @property
    def configuration(self):
        return self._options

    @configuration.setter
    def options(self, options):
        self.model.update(options)

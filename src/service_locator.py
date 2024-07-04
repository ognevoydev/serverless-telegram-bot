class ServiceLocator:
    """
    Service locator class.
    It allows to register and get services by their code.
    """
    _services = {}
    _instantiated = {}
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def add_instance(self, code, service):
        """
        Adds an instance of a service to the locator.
        """
        self._instantiated[code] = service

    def add_class(self, code, config=None):
        """
        Adds a class to the locator.
        If the class has a constructor, it can also be passed in the config.
        """
        if 'className' not in config and 'constructor' not in config:
            raise Exception("Could not register service. There is no className or constructor")

        class_ = config['className'] if 'className' in config else config['constructor']

        self._services[code] = [class_, config.get('constructorParams', [])]

    def register_by_config(self, config):
        """
        Registers multiple services using a config dictionary in format:
        {
            'service': {
                'className': 'Service',
                'constructorParams': [param1, param2]
            },
        }
        """
        for code, settings in config.items():
            if self.has(code):
                continue

            self.add_class(code, settings)

    def has(self, code):
        """
        Checks if a service is registered or instantiated.
        """
        return code in self._services or code in self._instantiated

    def get(self, code):
        """
        Gets an instance of a service by its code.
        If the service is not instantiated, it instantiates it first.
        """
        if code in self._instantiated:
            return self._instantiated[code]

        if code not in self._services:
            raise Exception(f"Could not find service by code {code}")

        class_, args = self._services[code]

        if isinstance(class_, type(lambda: None)):
            object_ = class_()
        else:
            if isinstance(args, type(lambda: None)):
                args = args()
            object_ = class_(*args)

        self._instantiated[code] = object_

        return object_

from modules.module import ModuleHandler, ModuleException

class ExampleHandler(ModuleHandler):

    def preflight_check(self):
        # Do something for checking if all needed preconditions are met else throw ModuleException
        raise ModuleException('Example module was loaded, so aborting!')
    
    def run(self) -> dict:
        # Run the migration tasks
        pass
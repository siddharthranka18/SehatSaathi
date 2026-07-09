import os
import sys
import types
from types import SimpleNamespace

# Ensure backend package is importable
ROOT = __file__ and __file__
ROOT = __file__ and __file__
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))

# Inject a fake groq module that simulates a 413 on first create and success on retry
fake = types.ModuleType('groq')

class FakeGroq:
    def __init__(self, api_key=None):
        self._calls = 0
        # create a completions helper object
        class Comps:
            def __init__(self, parent):
                self._parent = parent
            def create(self, model=None, messages=None, temperature=None, response_format=None):
                self._parent._calls += 1
                if self._parent._calls == 1:
                    raise Exception('413 Payload Too Large')
                # Return a fake response object with the expected structure
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Compact retry answer: general safe guidance.'))])
        self.chat = SimpleNamespace(completions=Comps(self))

fake.Groq = FakeGroq
sys.modules['groq'] = fake

# Ensure GROQ_API_KEY is set so web_search_service.get_client() doesn't raise
os.environ['GROQ_API_KEY'] = 'testkey'

# Now import the service and call the fallback
from app.services import web_search_service

long_query = 'Continuous stomachache ' + ('very long detail ' * 200)
print('Query length:', len(long_query))

result = web_search_service.web_search_fallback(long_query)
print('\nWEB FALLBACK RESULT:')
print(result)

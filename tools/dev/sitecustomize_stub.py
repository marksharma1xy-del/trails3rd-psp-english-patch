# Auto-stub packages that are unavailable offline and only used by network/crypto code paths we never run.
import sys, types, importlib.abc, importlib.machinery
NAMES = ('aiohttp', 'rsa', 'hexdump', 'pyasn1', 'pyasn1_modules', 'xmltodict')
class _Meta(type):
    def __getattr__(cls, n):
        if n.startswith('__'): raise AttributeError(n)
        return _mk(n)
def _mk(n): return _Meta(n, (), {})
class _M(types.ModuleType):
    __path__ = []
    def __getattr__(self, n):
        if n.startswith('__'): raise AttributeError(n)
        return _mk(n)
class _F(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path, target=None):
        if name.split('.')[0] in NAMES:
            return importlib.machinery.ModuleSpec(name, self, is_package=True)
    def create_module(self, spec): return _M(spec.name)
    def exec_module(self, m): pass
sys.meta_path.append(_F())

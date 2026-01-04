import importlib
modules=["app.services.indicators","app.services.patterns","app.services.renko","app.services.strategies","app.services.instruments"]
for m in modules:
    importlib.import_module(m)
print('SERVICES_OK')

To run examples from command line:

```bash
pyvenv venv
source venv/bin/activate
pip install -r examples/requirements.txt
python setup.py develop
python examples/simple_failsafe.py
python examples/failsafe_with_fallback.py
python examples/fallback_failsafe.py
```

To test examples:

```bash
pyvenv venv
source venv/bin/activate
pip install -r examples/requirements.txt
python setup.py develop
py.test examples/test.py
```

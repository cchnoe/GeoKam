import sys
print('Python executable:', sys.executable)

try:
    import openpyxl
    print('openpyxl version:', openpyxl.__version__)
    print('openpyxl import successful!')
except ImportError as e:
    print('openpyxl import failed:', e)

try:
    import pandas as pd
    print('pandas version:', pd.__version__)
    print('pandas import successful!')
except ImportError as e:
    print('pandas import failed:', e)
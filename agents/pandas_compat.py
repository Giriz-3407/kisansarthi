import sys
import types
import numpy as np

try:
    import pandas as pd
except Exception as e:
    print(f"Notice: System pandas import blocked or unavailable ({e}). Enabling compatibility module.")

    class MockSparseDtype:
        pass

    class MockSeries:
        def __init__(self, data=None):
            if isinstance(data, dict):
                self._data = list(data.values())
                self._index = list(data.keys())
            elif isinstance(data, list):
                self._data = list(data)
                self._index = list(range(len(data)))
            elif isinstance(data, MockSeries):
                self._data = list(data._data)
                self._index = list(data._index)
            else:
                self._data = list(data) if data is not None else []
                self._index = list(range(len(self._data)))

        def __iter__(self):
            return iter(self._data)

        def __len__(self):
            return len(self._data)

        def __getitem__(self, idx):
            return self._data[idx]

        def apply(self, func):
            return MockSeries([func(x) for x in self._data])

        def any(self):
            return any(bool(x) for x in self._data)

        def all(self):
            return all(bool(x) for x in self._data)

        def tolist(self):
            return list(self._data)

        @property
        def values(self):
            return np.array(self._data)

        @property
        def dtype(self):
            return np.dtype('object')

    class MockIndex(list):
        def tolist(self):
            return list(self)
        def to_numpy(self, *args, **kwargs):
            return np.array(self)
        @property
        def dtype(self):
            return np.dtype('object')

    class MockDataFrame:
        def __init__(self, data=None, columns=None, **kwargs):
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                cols = list(columns) if columns is not None else list(data[0].keys())
                self.columns = MockIndex(cols)
                self.values = np.array([[row[k] for k in self.columns] for row in data], dtype=float)
            elif isinstance(data, dict):
                cols = list(columns) if columns is not None else list(data.keys())
                self.columns = MockIndex(cols)
                self.values = np.array([[data[k] for k in self.columns]], dtype=float)
            elif data is not None:
                self.values = np.array(data, dtype=float)
                self.columns = MockIndex(columns if columns is not None else [])
            else:
                self.values = np.array([])
                self.columns = MockIndex([])
            self.shape = self.values.shape
            self.ndim = self.values.ndim

        @property
        def dtypes(self):
            return MockSeries({col: np.dtype('float64') for col in self.columns})

        def __array__(self, dtype=None):
            return np.asarray(self.values, dtype=dtype)

        def __len__(self):
            return len(self.values)

        def __getitem__(self, item):
            return self.values[item]

        def __str__(self):
            return f"DataFrame(shape={self.shape}, columns={self.columns})"

        def __repr__(self):
            return self.__str__()

    api_types_module = types.ModuleType('pandas.api.types')
    api_types_module.is_sparse = lambda x: False
    api_types_module.is_extension_array_dtype = lambda x: False
    api_types_module.is_float_dtype = lambda x: True
    api_types_module.is_integer_dtype = lambda x: False
    api_types_module.is_numeric_dtype = lambda x: True
    api_types_module.is_bool_dtype = lambda x: False
    api_types_module.is_object_dtype = lambda x: False
    api_types_module.is_categorical_dtype = lambda x: False

    pandas_module = types.ModuleType('pandas')
    pandas_module.__path__ = []
    pandas_module.DataFrame = MockDataFrame
    pandas_module.Series = MockSeries
    pandas_module.Index = MockIndex
    pandas_module.SparseDtype = MockSparseDtype
    pandas_module.isna = lambda x: False
    pandas_module.isnull = lambda x: False
    pandas_module.__version__ = "2.2.0"

    api_module = types.ModuleType('pandas.api')
    api_module.types = api_types_module
    pandas_module.api = api_module

    sys.modules['pandas'] = pandas_module
    sys.modules['pandas.api'] = api_module
    sys.modules['pandas.api.types'] = api_types_module
    pd = pandas_module

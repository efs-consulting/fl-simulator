import numpy as np
from flwr.common import NDArrays , ArrayRecord , MetricRecord
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import IidPartitioner
from sklearn.linear_model import LogisticRegression
from scipy.io import loadmat
import numpy as np
import pandas as pd
# from torch.utils.data import TensorDataset,DataLoader
from sklearn.model_selection import train_test_split
import os
import matplotlib.pyplot as plt

# This information is needed to create a correct scikit-learn model
from sklearn.linear_model import Ridge # Import the appropriate regression model
from sklearn.linear_model import LogisticRegression # Keep this import, but it won't be used
from typing import List
import numpy as np

# --- Configuration Constants (Must be defined based on your data) ---
# Your features are 4 * 128, which must be flattened for scikit-learn
FEATURES = 4 * 128  # 512
# Your target is a single ratio (SOH)
UNIQUE_LABELS = 1 
NDArrays = List[np.ndarray]
# -------------------------------------------------------------------


# NOTE: Type hints are updated to Ridge, but function names remain the same
# task.py
def get_model_parameters(model) -> NDArrays:
    """Works for Ridge, SGDRegressor, etc."""
    params = [model.coef_.copy()]
    if getattr(model, "intercept_", None) is not None:
        params.append(np.array([model.intercept_.item()]))  # force 1-element array
    return params

def set_model_params(model, params: NDArrays):
    model.coef_ = params[0]
    if len(params) > 1:
        model.intercept_ = params[1]
    return model

def set_initial_params(model, n_classes: int, n_features: int):
    model.coef_ = np.zeros(n_features, dtype=np.float64)
    if getattr(model, "fit_intercept", True):
        model.intercept_ = np.zeros(1, dtype=np.float64)

# NOTE: The model is switched to Ridge, but the function name remains the same
# === task.py ===
from sklearn.linear_model import SGDRegressor

def create_log_reg_and_instantiate_parameters(penalty):
    # In task.py → create_log_reg_and_instantiate_parameters
    model = SGDRegressor(
    penalty="l2",
    alpha=0.0001,              # reasonable L2
    learning_rate="constant",
    eta0=1e-5,                 # ← 0.00001 instead of 0.001 or 0.0001
    max_iter=1,
    tol=None,
    shuffle=True,
    random_state=42,
    warm_start=True,
    fit_intercept=True,        # make sure this is True (default)
)
    set_initial_params(model, n_classes=UNIQUE_LABELS, n_features=FEATURES)
    return model


fds = None  # Cache FederatedDataset

import pandas as pd
import os





# Data loading function




def load_data(partition_id: int , is_fit , test_battery_id=1 ):
    # Each client has its own data file:
    import os
    import shutil

    if partition_id == 1 or partition_id == 2 or partition_id == 3 or partition_id == 4 or partition_id == 5:
        folder = "/app1/Data"
        done_dir = "/app1/Done"


    elif partition_id == 0 or partition_id == 15:
        folder = "/app/Data"
        done_dir = "/app/Done"

    else:
        raise ValueError("Invalid partition_id")

    # --- NEW: get all files in folder ---
    files = [os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))]
    if len(files) == 0:
#  When there are no data, the client will be disconnected.
        print("No files found in folder: " + folder)

    files.sort()  # to ensure deterministic first element
    file = files[0]   # path of the first file
    print(f"Loading data from: {file}")
    # --- use the file as before ---
    dataset = XJTUDdataset()

    train_x, train_y, test_x, test_y = dataset.get_charge_data(path=file,is_fit= is_fit,  test_battery_id=test_battery_id) 

    # --- NEW: move processed file to /app1/Done ---
    # os.makedirs(done_dir, exist_ok=True)

    if partition_id != 15 and is_fit == False :
        shutil.copy2(file, done_dir)  # copy file
        os.remove(file) 

    return train_x, train_y, test_x, test_y

    # if partition_id == 1 or partition_id == 2 or partition_id ==3 or partition_id ==4 or partition_id ==5:
    #     file = os.path.join("/app1/Data", "data.mat")

    # elif partition_id == 0 or partition_id ==15:
    #     file = os.path.join("/app/Data", "data.mat")
    # else:
    #     raise ValueError("Invalid partition_id")
    
    # dataset = XJTUDdataset()
    # train_x, train_y, test_x, test_y = dataset.get_charge_data(path=file,test_battery_id=test_battery_id)
    # return train_x, train_y, test_x, test_y



class XJTUDdataset():
    def __init__(self):
        super(XJTUDdataset).__init__()
        self.max_capacity = 2.0
        

    def _parser_mat_data(self,battery_i_mat):
        '''
        :param battery_i_mat: shape:(1,len)
        :return: np.array
        '''
        data = []
        label = []
        for i in range(battery_i_mat.shape[0]):
            cycle_i_data = battery_i_mat[i]
            time = cycle_i_data['relative_time_min'] # (1,128)
            current = cycle_i_data['current_A'] # (1,128)
            voltage = cycle_i_data['voltage_V'] # (1,128)
            temperature = cycle_i_data['temperature_C'] # (1,128)
            capacity = cycle_i_data['capacity'][0]
            label.append(capacity)
            cycle_i = np.concatenate([time,current,voltage,temperature],axis=0)
            data.append(cycle_i)
        data = np.array(data,dtype=np.float32)
        label = np.array(label,dtype=np.float32)
        print(data.shape,label.shape)

        scaler = Scaler(data)
        data = scaler.standerd()
        
        soh = label / self.max_capacity

        return data,soh

    

    def _get_raw_data(self,path,test_battery_id , is_fit ):


         
        battery = loadmat(path)
        battery = battery['data']
        battery = battery[0]

        if is_fit == True : 
            
            train_data = battery[0 : int(0.8 * len(battery))]
            x, y = self._parser_mat_data(train_data)
            train_x, train_y = [], []
            train_x.append(x)
            train_y.append(y)
            train_x = np.concatenate(train_x, axis=0)
            train_y = np.concatenate(train_y, axis=0)
            return train_x, train_y , None ,None
        else:
            test_data = battery[int(0.8 * len(battery)) : ]
            x, y = self._parser_mat_data(test_data)
            test_x, test_y = [], []
            test_x.append(x)
            test_y.append(y)
            test_x = np.concatenate(test_x, axis=0)
            test_y = np.concatenate(test_y, axis=0)
            return None , None , test_x, test_y
            

      




        # mat = loadmat(path)
        # battery = mat['battery']
        # battery_ids = list(range(1, battery.shape[1] + 1))
        # if test_battery_id not in battery_ids:
        #     raise IndexError(f'"test_battery" must be in the {battery_ids}, but got {test_battery_id}. ')

        # test_battery = battery[0, test_battery_id - 1][0]
        # print(f'test battery id: {test_battery_id}, test data shape: ', end='')
        # test_x, test_y = self._parser_mat_data(test_battery)
        # train_x, train_y = [], []
        # for id in battery_ids:
        #     if id == test_battery_id:
        #         continue
        #     print(f'train battery id: {id}, ', end='')
        #     train_battery = battery[0, id - 1][0]
        #     x, y = self._parser_mat_data(train_battery)
        #     train_x.append(x)
        #     train_y.append(y)
        # train_x = np.concatenate(train_x, axis=0)
        # train_y = np.concatenate(train_y, axis=0)
        # print('train data shape: ', train_x.shape, train_y.shape)


    def get_charge_data(self,path , is_fit, test_battery_id=1 ,  ):
        print('----------- load charge data -------------')

        self.charge_path = path
        train_x, train_y, test_x, test_y = self._get_raw_data(path=self.charge_path,test_battery_id=test_battery_id, is_fit =is_fit )

        
        print('-------------  finished !  ---------------')
        return train_x, train_y, test_x, test_y





class Scaler():
    def __init__(self,data):  # data.shape (N,C,L)  or (N,C)
        self.data = data
        if self.data.ndim == 3: # (N,C,L)
            self.mean = self.data.mean(axis=(0,2)).reshape(1,-1,1)
            self.var = self.data.var(axis=(0,2)).reshape(1,-1,1)
            self.max = self.data.max(axis=(0,2)).reshape(1,-1,1)
            self.min = self.data.min(axis=(0,2)).reshape(1,-1,1)
        elif self.data.ndim == 2: # (N,C)
            self.mean = self.data.mean(axis=0).reshape(1, -1)
            self.var = self.data.var(axis=0).reshape(1, -1)
            self.max = self.data.max(axis=0).reshape(1, -1)
            self.min = self.data.min(axis=0).reshape(1, -1)
        else:
            raise ValueError('data dim error!')

    def standerd(self):
        X = (self.data - self.mean) / (self.var + 1e-6)
        return X

    def minmax(self,feature_range=(0,1)):
        if feature_range == (0,1):
            X = (self.data - self.min) / ((self.max - self.min) + 1e-6)
        elif feature_range == (-1,1):
            X = 2*(self.data - self.min) / ((self.max - self.min) + 1e-6)-1
        else:
            raise ValueError('feature_range error!')
        return X


from flwr.common import ndarrays_to_parameters, parameters_to_ndarrays
from sklearn.metrics import mean_squared_error, r2_score

def central_evaluate(server_round: int, parameters, config) -> MetricRecord:
    """Evaluate model on the server side."""

    # Load the model and initialize it with the received weights
    model = create_log_reg_and_instantiate_parameters("l2")
    set_model_params(model, parameters)
    X_test, y_test, X_train, y_train = load_data(15 , is_fit = True)
    num_samples = X_test.shape[0]
    X_test_flat = X_test.reshape(num_samples, -1).astype(np.float64)
    y_test = y_test.astype(np.float64)

    y_pred = model.predict(X_test_flat)
    mse_loss = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)





    # Return the evaluation metrics
    return      mse_loss, {"r2": r2}

























def aa(partition_id: int, num_partitions: int):
    """Load local CSV data stored inside /app/data for each client."""


    print(partition_id)
    # Each client has its own data file:
    if partition_id == 1:
        file = os.path.join("/app1/Data", "data.csv")

    elif partition_id == 0:
        file = os.path.join("/app/Data", "data.csv")
    else:
        raise ValueError("Invalid partition_id")

    print(f"Loading data from: {file}")

    df = pd.read_csv(file)

    # Features and labels
    X = df[FEATURES]
    y = df["label"]

    # 80/20 train-test split
    split = int(0.8 * len(df))
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    return X_train, y_train, X_test, y_test

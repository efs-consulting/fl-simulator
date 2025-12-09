import numpy as np
from flwr.common import NDArrays , ArrayRecord , MetricRecord
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import IidPartitioner
from sklearn.linear_model import LogisticRegression
from scipy.io import loadmat
import pandas as pd
from sklearn.model_selection import train_test_split
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.linear_model import LogisticRegression 
from torch import nn
from typing import List, Tuple
from flwr.common import ndarrays_to_parameters, parameters_to_ndarrays
from sklearn.metrics import mean_squared_error, r2_score,recall_score , f1_score
import torch






class Net(nn.Module):
    def __init__(self, n_input: int = 6, n_hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_input, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, n_hidden),
            nn.ReLU(),
            # MODIFICATION 1: Change output dimension from 1 to 2
            nn.Linear(n_hidden, 2)  
        )

    def forward(self, x):
        return self.net(x).squeeze(1)  # (batch,) logits


# -------------------------
# Parameter conversion utils (PyTorch <-> NumPy NDArrays)
# -------------------------
def get_numpy_parameters(model: nn.Module) -> List[np.ndarray]:
    """Return model parameters as list of NumPy arrays (weights then biases)."""
    params: List[np.ndarray] = []
    for param in model.state_dict().values():
        params.append(param.cpu().numpy())
    return params


def set_numpy_parameters(model: nn.Module, params: List[np.ndarray]) -> None:
    """Load parameters from list of NumPy arrays (same ordering as state_dict())."""
    state_dict = model.state_dict()
    if len(params) != len(state_dict):
        raise ValueError(f"Expected {len(state_dict)} arrays but got {len(params)}")
    new_state = {}
    for (k, v), p in zip(state_dict.items(), params):
        new_state[k] = torch.tensor(p, dtype=state_dict[k].dtype)
    model.load_state_dict(new_state)


def initialize_model_parameters(model: nn.Module) -> List[np.ndarray]:
    """Return initial parameters (zeros or default init). Useful for server init."""
    return get_numpy_parameters(model)


# -------------------------
# Training / Eval helpers
# -------------------------
def train_one_epoch(model: nn.Module, train_loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    for X, y in train_loader:
        X = X.to(device).float()
        y = y.to(device).float()  
        optimizer.zero_grad()
        logits = model(X)  
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * X.size(0)
    return total_loss / len(train_loader.dataset)


def evaluate_model(model: nn.Module, test_loader, criterion, device) -> Tuple[float, float]:
    """Returns (loss, accuracy)."""
    model.eval()
    total_loss = 0.0
    correct = 0
    n = 0
    with torch.no_grad():
        for X, y in test_loader:
            X = X.to(device).float()
            y = y.to(device).float()
            logits = model(X)
            loss = criterion(logits, y)
            total_loss += loss.item() * X.size(0)
            probs = torch.sigmoid(logits)
            preds = (probs >= 0.5).long()
            correct += (preds.cpu().numpy() == y.cpu().numpy()).sum()
            n += X.size(0)
    return total_loss / n, correct / n



fds = None  # Cache FederatedDataset



def load_data(partition_id: int , is_fit , test_battery_id=1 ):
    # Each client has its own data file:
    import os
    import shutil


    if partition_id == 1 or partition_id == 2 or partition_id == 3 or partition_id == 4 or partition_id == 5:
        folder = "/app1/Data"
        done_dir = "/app1/Done"


    elif  partition_id == 15: # Partion 15 is the central test set in the server
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
   

    df = pd.read_csv(file)

    
    cutoff = int(len(df) * 0.8)
    data = df.iloc[:cutoff]
    data = data.iloc[:, [8,0,1,2,3,4,5]]

    train_x = data.iloc[:, :-1].values
    train_y = data.iloc[:, -1].values

# Scaling (Z-score normalization)
    INDICES_TO_SCALE = [1, 2, 3, 4] 
    scaler = StandardScaler()
    train_x_to_scale = train_x[:, INDICES_TO_SCALE]
    scaler.fit(train_x_to_scale)
    train_x[:, INDICES_TO_SCALE] = scaler.transform(train_x_to_scale)



# Get first 80% of the rows
    if is_fit == True :
          
        train_y = train_y.squeeze()
        type_mapping = {'L': 1, 'M': 2, 'H': 3}
        train_x[:, 0] = np.vectorize(type_mapping.get)(train_x[:, 0])

        test_x = None
        test_y = None


    elif is_fit == False  and partition_id != 15:
        df = pd.read_csv(file)
        cutoff = int(len(df) * 0.8)
        data = df.iloc[cutoff:]
        data = data.iloc[:, [8,0,1,2,3,4,5]]


        test_x = data.iloc[:, :-1].values
        INDICES_TO_SCALE = [1, 2, 3, 4] 
        test_x_to_scale = test_x[:, INDICES_TO_SCALE]
        test_x[:, INDICES_TO_SCALE] = scaler.transform(test_x_to_scale)
        test_y = data.iloc[:, -1].values
        test_y = test_y.squeeze()
        type_mapping = {'L': 1, 'M': 2, 'H': 3}
        test_x[:, 0] = np.vectorize(type_mapping.get)(test_x[:, 0])

        train_x = None
        train_y = None
        shutil.copy2(file, done_dir)  # copy file
        os.remove(file) 

    if partition_id == 15 and is_fit == False :
        data = pd.read_csv(file)
        directory_data_scaling = "/app/model/data.csv"
        data_for_scaling = pd.read_csv(directory_data_scaling)
 
        data = data.iloc[:, [8,0,1,2,3,4,5]]
        data_scaling = data_for_scaling.iloc[:, [8,0,1,2,3,4,5]]
        data_scaling_x = data_scaling.iloc[:, :-1].values
        test_x = data.iloc[:, :-1].values


        scaler = StandardScaler()
        INDICES_TO_SCALE = [1, 2, 3, 4] 
        data_scaling_x_to_scale = data_scaling_x[:, INDICES_TO_SCALE]
        scaler.fit(data_scaling_x_to_scale)
        

        test_x_to_scale = test_x[:, INDICES_TO_SCALE]
        test_x[:, INDICES_TO_SCALE] = scaler.transform(test_x_to_scale)
        test_y = data.iloc[:, -1].values
        test_y = test_y.squeeze()
        type_mapping = {'L': 1, 'M': 2, 'H': 3}
        test_x[:, 0] = np.vectorize(type_mapping.get)(test_x[:, 0])

        train_x = None
        train_y = None
        shutil.copy2(file, done_dir)  # copy file
        os.remove(file) 


    return train_x, train_y, test_x, test_y



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



def central_evaluate(server_round: int, parameters, config) -> MetricRecord:
    """Evaluate the NN model on server-side dataset."""

    # ---- Recreate Model ----
    model = Net()
    # Assuming you have the correct implementation of set_numpy_parameters
    set_numpy_parameters(model, parameters)     
    model.eval()
    
    # Assuming device is defined somewhere (standard PyTorch setup)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # ---- Load Evaluation Data (partition 15 is your central test set) ----
    _,_,X_test, y_test= load_data(15, is_fit=False)

    
    # Convert features to correct shape: (N, 6)
    X_test = X_test.reshape(X_test.shape[0], -1).astype(np.float32)
    
    # 1. TARGET CONVERSION: y_test must be integers (np.int64) for CrossEntropyLoss
    y_test_int = y_test.astype(np.int64)
    
    # Torch tensors
    X_test_t = torch.tensor(X_test, dtype=torch.float32, device=device)
    # y_test_t must be 1D torch.Long tensor of class indices (0 or 1)
    y_test_t = torch.tensor(y_test_int, dtype=torch.long, device=device).flatten()
    
    # 2. DEFINE WEIGHTED LOSS (for consistency with training)
    # Use the 72%/28% ratio weight [1.0, 2.57]
    class_weights = torch.tensor([1.0, 2.57], dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    # ---- Forward Pass ----
    with torch.no_grad():
        y_pred_logits = model(X_test_t) # Output shape: (N, 2)
        
        # Calculate loss using the weighted CrossEntropyLoss
        loss = criterion(y_pred_logits, y_test_t).item()

        # 3. PREDICTION: Use argmax to get the predicted class index (0 or 1)
        y_pred_indices = torch.argmax(y_pred_logits, dim=1).cpu().numpy()

    # 4. ACCURACY CALCULATION: Compare predicted indices against true indices (y_test_int)
    accuracy = (y_pred_indices == y_test_int).mean()
    recall = recall_score(
            y_test_int,
            y_pred_indices,
            average='binary'
        )
    f1score = f1_score(
            y_test_int,
            y_pred_indices,
            average='binary'
        )

    return loss, {
        "accuracy": float(accuracy)
        ,"recall": float(recall),
        "f1_score": float(f1score)
    }





import warnings
from sklearn.metrics import mean_squared_error, r2_score
from flwr.client import NumPyClient
from flwr.clientapp import ClientApp
from flwr.common import Context
from sklearn.metrics import log_loss , f1_score , recall_score
import numpy as np
import os
from prometheus_client import start_http_server, Gauge, Counter
import torch.optim as optim
from prometheus_client import REGISTRY
import psutil
import time
import torch
import torch.nn as nn
import warnings



from sklearnexample.task import (

    load_data,
    Net,
    get_numpy_parameters,
    set_numpy_parameters,
    initialize_model_parameters,
    train_one_epoch,
    evaluate_model,
)

# client.py
warnings.filterwarnings("ignore")

from sklearn.metrics import mean_squared_error, r2_score
from flwr.client import NumPyClient
from flwr.common import Context
import numpy as np
import psutil
import time
import os
import torch

class FlowerClient(NumPyClient):
    def __init__(self, partition_id: int, num_partitions: int, penalty: str):
        self.partition_id = partition_id
        self.num_partitions = num_partitions


        self.model = Net()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)


        self.X_train = None
        self.y_train = None
        self.X_test  = None 
        self.y_test = None
        self.class_weight = torch.tensor([2.57], dtype=torch.float32, device=self.device)
         


    def fit(self, parameters, config):
        print("\n[Client", self.partition_id, "] fit called")

        # Load local partition
        X_train, y_train, X_test, y_test = load_data(self.partition_id, is_fit=True)
        X_train = X_train.astype(np.float32)
        self.X_train = torch.tensor(
            X_train.reshape(len(X_train), -1), dtype=torch.float32, device=self.device
        )
        self.y_train = torch.tensor(
          y_train.astype(np.int64), dtype=torch.long, device=self.device
)

        # Set global model weights
        set_numpy_parameters(self.model, parameters)

        # Profiling
        process = psutil.Process(os.getpid())
        start = time.perf_counter()
        cpu_before = process.cpu_times()
        mem_before = process.memory_info().rss

        # Training
        # epochs = config.get("local_epochs", 5)
        class_weights = torch.tensor([1.0, 2.57], dtype=torch.float32, device=self.device)
        optimizer = optim.Adam(self.model.parameters(), lr=0.01)
        criterion = nn.CrossEntropyLoss(weight=class_weights)
        y_train = self.y_train

        for _ in range(100):
            optimizer.zero_grad()
            logits = self.model(self.X_train)
            loss = criterion(logits, y_train) # Use 1D target
            loss.backward()
            optimizer.step()

        # ---- Compute TRAIN ACCURACY ----
        with torch.no_grad():
            logits = self.model(self.X_train)          # shape (batch, 2)
            preds = torch.argmax(logits, dim=1)        # shape (batch,)
            y_true = self.y_train                      # long
            accuracy = (preds == y_true).float().mean().item()

        f1 = f1_score(
        y_true.cpu().numpy(),
        preds.cpu().numpy(),
        average='binary'
    )
        recall = recall_score(
        y_true.cpu().numpy(),
        preds.cpu().numpy(),
        average='binary'
    )
        # Profiling end
        cpu_after = process.cpu_times()
        mem_after = process.memory_info().rss
        wall_time = time.perf_counter() - start
        cpu_time = (cpu_after.user + cpu_after.system) - (cpu_before.user + cpu_before.system)
        cpu_percent = (cpu_time / wall_time * 100) if wall_time > 0 else 0
        mem_mb = (mem_after - mem_before) / (1024 * 1024)

        return (
            get_numpy_parameters(self.model),
            len(self.X_train),
            {
                "train_accuracy": float(accuracy),
                "train_loss": float(loss.item()),
                "train_f1": float(f1),
                "train_recall": float(recall),
                "cid": str(self.partition_id),
                "cpu_percent_fit": float(cpu_percent),
                "memory_mb_fit": float(mem_mb),
                "cpu_time_sec": round(cpu_time, 3),
                "stage": "fit",
            }
        )

    # -----------------------------
    # EVALUATE
    # -----------------------------
    def evaluate(self, parameters, config):
        print("\n[Client", self.partition_id, "] evaluate called")

        # Load data
        X_train, y_train, X_test, y_test = load_data(self.partition_id, is_fit=False)


        X_test = X_test.astype(np.float32) 

        # 3. Convert to PyTorch tensor
        self.X_test = torch.tensor(
            X_test, 
            dtype=torch.float32  
        )
        self.y_test = torch.tensor(
            y_test.astype(np.int64), dtype=torch.long, device=self.device
        )

        # Set weights
        set_numpy_parameters(self.model, parameters)
        class_weights = torch.tensor([1.0, 2.57], dtype=torch.float32, device=self.device)
        criterion = nn.CrossEntropyLoss(weight=class_weights)
        # Predictions
        with torch.no_grad():
            logits = self.model(self.X_test)
            pred = logits.argmax(dim=1)
            accuracy = (pred == self.y_test).float().mean().item()
            eval_loss = criterion(logits, self.y_test).item()
        f1 = f1_score(
            self.y_test.cpu().numpy(),
            pred.cpu().numpy(),
            average='binary'
                )
        recall = recall_score(
            self.y_test.cpu().numpy(),
            pred.cpu().numpy(),
            average='binary'
        )

        return (eval_loss , len(self.X_test), {
            "test_accuracy": float(accuracy),
            "test_f1": float(f1),
            "test_recall": float(recall),
            "loss": float(eval_loss),
            "cid": str(self.partition_id),
            "stage": "evaluate",
        })
    


       

# NEW MODERN client_fn using Context (no more warnings)
def client_fn(context: Context):
    partition_id = context.node_config["partition-id"]
    num_partitions = context.node_config["num-partitions"]
    penalty = context.run_config.get("penalty", "l2")  # safe default

    client = FlowerClient(partition_id, num_partitions, penalty)
    return client.to_client()   # This removes the warning!


# This is all you need
app = ClientApp(client_fn)

























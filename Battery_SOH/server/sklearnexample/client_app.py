




import warnings
from sklearn.metrics import mean_squared_error, r2_score
from flwr.client import NumPyClient
from flwr.clientapp import ClientApp
from flwr.common import Context
from sklearn.metrics import log_loss
import numpy as np
import os
# === PROMETHEUS METRICS – CLEANED AND FIXED ===
from prometheus_client import start_http_server, Gauge, Counter
import os
from prometheus_client import REGISTRY
import psutil
import time


import os

from sklearnexample.task import (
    UNIQUE_LABELS,
    create_log_reg_and_instantiate_parameters,
    get_model_parameters,
    load_data,
    set_model_params,
)

# client.py
import warnings
warnings.filterwarnings("ignore")

from sklearn.metrics import mean_squared_error, r2_score
from flwr.client import NumPyClient
from flwr.common import Context
import numpy as np
import psutil
import time
import os

from sklearnexample.task import (
    create_log_reg_and_instantiate_parameters,
    get_model_parameters,
    load_data,
    set_model_params,
)

class FlowerClient(NumPyClient):
    def __init__(self, partition_id: int, num_partitions: int, penalty: str):
        self.partition_id = partition_id
        self.num_partitions = num_partitions

        self.X_train = None
        self.y_train = None
        self.X_test  = None 
        self.y_test = None
         
        self.model = create_log_reg_and_instantiate_parameters(penalty)

    def fit(self, parameters, config):
        print("Client fit called-----------------")


        X_train, y_train, X_test, y_test = load_data(self.partition_id, is_fit=True)

        # Flatten and fix types once
        self.X_train = X_train.reshape(X_train.shape[0], -1).astype(np.float64)
        self.y_train = y_train.ravel().astype(np.float64)
        

        process = psutil.Process(os.getpid())
        start = time.perf_counter()
        cpu_before = process.cpu_times()
        mem_before = process.memory_info().rss

        set_model_params(self.model, parameters)
        local_epochs = config.get("local_epochs", 20)

        for _ in range(local_epochs):
            self.model.partial_fit(self.X_train, self.y_train)

        r2 = self.model.score(self.X_train, self.y_train)

        # Metrics
        cpu_after = process.cpu_times()
        mem_after = process.memory_info().rss
        wall_time = time.perf_counter() - start
        cpu_time = (cpu_after.user + cpu_after.system) - (cpu_before.user + cpu_before.system)
        cpu_percent = (cpu_time / wall_time * 100) if wall_time > 0 else 0
        mem_mb = (mem_after - mem_before) / (1024 * 1024)

        return get_model_parameters(self.model), len(self.X_train), {
            "train_r_squared": float(r2),
            "cid": str(self.partition_id),
            "cpu_percent_fit": float(cpu_percent),
            "memory_mb_fit": float(mem_mb),
            "cpu_time_sec": round(cpu_time, 3),
            "stage": "fit"
        }

    def evaluate(self, parameters, config):
        print("Client evaluate called-----------------")

        X_train, y_train, X_test, y_test = load_data(self.partition_id, is_fit=False)

        # Flatten and fix types once
       
        self.X_test = X_test.reshape(X_test.shape[0], -1).astype(np.float64)
        self.y_test = y_test.ravel().astype(np.float64)

        set_model_params(self.model, parameters)
        y_pred = self.model.predict(self.X_test)
        mse = mean_squared_error(self.y_test, y_pred)
        r2 = r2_score(self.y_test, y_pred)

        return float(mse), len(self.X_test), {
            "test_r_squared": float(r2),
            "loss": float(mse),
            "cid": str(self.partition_id),
            "stage": "evaluate"
        }


# NEW MODERN client_fn using Context (no more warnings)
def client_fn(context: Context):
    partition_id = context.node_config["partition-id"]
    num_partitions = context.node_config["num-partitions"]
    penalty = context.run_config.get("penalty", "l2")  # safe default

    client = FlowerClient(partition_id, num_partitions, penalty)
    return client.to_client()   # This removes the warning!


# This is all you need
app = ClientApp(client_fn)




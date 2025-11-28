




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














































# import warnings
# from sklearn.metrics import mean_squared_error, r2_score
# from flwr.client import NumPyClient
# from flwr.clientapp import ClientApp
# from flwr.common import Context
# from sklearn.metrics import log_loss
# import numpy as np
# import os
# # === PROMETHEUS METRICS – CLEANED AND FIXED ===
# from prometheus_client import start_http_server, Gauge, Counter
# import os
# from prometheus_client import REGISTRY
# import psutil
# import time


# import os

# from sklearnexample.task import (
#     UNIQUE_LABELS,
#     create_log_reg_and_instantiate_parameters,
#     get_model_parameters,
#     load_data,
#     set_model_params,
# )


# import os
# import socket
# import logging
# from flwr.client import NumPyClient

# class FlowerClient(NumPyClient):
#     def __init__(self, model, X_train, y_train, X_test, y_test , partition_id):

#         self.model = model
#         self.X_train = X_train
#         self.y_train = y_train
#         self.X_test = X_test
#         self.y_test = y_test
#         self.unique_labels = UNIQUE_LABELS
#         self.partition_id = partition_id
#         # start_http_server(port)

    	
#     def fit(self, parameters, config):
#         print("Client fit called-----------------")
#         process = psutil.Process()

#         start_wall = time.perf_counter()
#         cpu_times_before = process.cpu_times()
#         mem_before = process.memory_info().rss  # bytes





#         set_model_params(self.model, parameters)

#         num_samples = self.X_train.shape[0]
#         X_flat = self.X_train.reshape(num_samples, -1).astype(np.float64)
#         y_train = self.y_train.astype(np.float64)

#         local_epochs = config.get("local_epochs", 5)

#         for _ in range(local_epochs):
#             self.model.partial_fit(X_flat, y_train)

#         r2 = self.model.score(X_flat, y_train)
#         # self.metrics["CLIENT_ROUND"].labels(partition_id=self.partition_id).inc()
#         # self.metrics["CLIENT_TRAIN_R2"].labels(partition_id=self.partition_id).set(r2)
     





#         cpu_times_after = process.cpu_times()
#         mem_after = process.memory_info().rss  # bytes

#         # CPU usage for fit only (user + system time)
#         cpu_user = cpu_times_after.user - cpu_times_before.user
#         cpu_system = cpu_times_after.system - cpu_times_before.system
#         cpu_total = cpu_user + cpu_system  # seconds of CPU used by THIS function

#         # CPU % = CPU time / wall-clock time of fit
#         # (We need wall clock time)
#         wall_clock_time = (cpu_times_after.user + cpu_times_after.system) - \
#                         (cpu_times_before.user + cpu_times_before.system)
        


#         cpu_time_sec = (cpu_times_after.user - cpu_times_before.user) + \
#                (cpu_times_after.system - cpu_times_before.system)

#         if wall_clock_time == 0:
#             cpu_percent = 0.0
#         else:
#             cpu_percent = (cpu_total / wall_clock_time) * 100

#         # Memory usage difference in MB
#         mem_diff_mb = (mem_after - mem_before) / (1024 * 1024)



#         return get_model_parameters(self.model), len(self.X_train), {
#                 "train_r_squared": r2,
#                 "cid": str(self.partition_id),
#                 "cpu_percent_fit": float(cpu_percent),
#                 "memory_mb_fit": float(mem_diff_mb),
#                 "cpu_time_sec":  round(cpu_time_sec, 3),
#                 "stage": "fit"
#             }
                

#     def evaluate(self, parameters, config):
#         print("Client evaluate called-----------------")
#         set_model_params(self.model, parameters)

#         num_samples = self.X_test.shape[0]
#         X_test_flat = self.X_test.reshape(num_samples, -1).astype(np.float64)
#         y_test = self.y_test.astype(np.float64)

#         y_pred = self.model.predict(X_test_flat)
#         mse_loss = mean_squared_error(y_test, y_pred)
#         r2 = r2_score(y_test, y_pred)

#         # self.metrics["CLIENT_LOSS"].labels(partition_id=self.partition_id).set(mse_loss)
#         # self.metrics["CLIENT_TEST_R2"].labels(partition_id=self.partition_id).set(r2)

#         return mse_loss, len(self.X_test), {
#             "test_r_squared": r2,
#             "loss": mse_loss,
#             "cid": str(self.partition_id),
#             "stage": "evaluate"
#         }




# _cached_data = None

# def client_fn(context: Context):
#     global _cached_data

#     partition_id = context.node_config["partition-id"]
#     num_partitions = context.node_config["num-partitions"]
#     penalty = context.run_config["penalty"]

#     if _cached_data is not None:
#         # Cache has data → TAKE IT and REMOVE from cache
#         print(f"Reusing cached data for partition {partition_id} and clearing cache")
#         X_train, y_train, X_test, y_test = _cached_data
#         _cached_data = None  # <-- IMPORTANT: remove from cache!
#     else:
#         # Cache empty → load fresh data
#         print(f"Cache empty. Loading data for partition {partition_id}")
#         X_train, y_train, X_test, y_test = load_data(partition_id, num_partitions)
#         print(f"Loaded: X_train {X_train.shape}, y_train {y_train.shape}")

#     # FIX LABEL SHAPE ONCE (whether from cache or fresh)
#     y_train = y_train.ravel()
#     y_test = y_test.ravel()

#     # Create fresh model every time (normal behavior)
#     model = create_log_reg_and_instantiate_parameters(penalty)

#     # Give data to client
#     client = FlowerClient(
#         model=model,
#         X_train=X_train,
#         y_train=y_train,
#         X_test=X_test,
#         y_test=y_test,
#         partition_id=partition_id
#     ).to_client()

#     # BEFORE returning, put the data back into cache for the next call (evaluate)
#     if _cached_data is None:
#         print("Putting data into cache for next call (evaluate)")
#         _cached_data = (X_train, y_train, X_test, y_test)

#     return client


# app = ClientApp(client_fn=client_fn)








# def client_fn(context: Context):
#     """Construct a Client that will be run in a ClientApp."""

#     # Read the node_config to fetch data partition associated to this node
#     partition_id = (context.node_config["partition-id"])
#     partition_id = (partition_id)
#     print(partition_id)
#     # Start prometheus server in this client process and create metrics here
  
#     # client_metrics = _create_metrics()


#     num_partitions = context.node_config["num-partitions"]
#     print("0000000000000000000000000000000000000000000000000")
#     X_train, y_train, X_test, y_test = load_data(partition_id, num_partitions)

#     # Read the run config to get settings to configure the Client
#     penalty = context.run_config["penalty"]

#     # Create LogisticRegression Model
#     model = create_log_reg_and_instantiate_parameters(penalty)
#     print("client----------------")
#     import os
#     print(f"Client running in directory: {os.getcwd()}")


#     # Return Client instance
#     return FlowerClient(model, X_train, y_train, X_test, y_test,partition_id).to_client()


# # Flower ClientApp
# app = ClientApp(client_fn=client_fn)





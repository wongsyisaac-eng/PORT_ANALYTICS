
from ib_async import IB
import pandas as pd
from backend/env_config import IB_host, IB_port, IB_clientID, DB_path
# create instance of IB class and connect to 
# local IB gateway
ib = IB()
ib.connect("127.0.0.1", 4002, clientId=1)

print("Accounts:", ib.managedAccounts())

positions = ib.positions()
print("Number of Positions:", len(positions))

for p in positions:
    print(f"Symbol: {p.contract.symbol}, Position: {p.position}, Avg Cost: {p.avgCost}")



ib.disconnect()

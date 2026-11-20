
from ib_async import IB
import pandas as pd
from env_config import IB_HOST, IB_PORT, IB_CLIENT_ID
# create instance of IB class and connect to
# local IB gateway
ib = IB()
ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)

print("Accounts:", ib.managedAccounts())

positions = ib.positions()
print("Number of Positions:", len(positions))

for p in positions:
    print(f"Symbol: {p.contract.symbol}, Position: {p.position}, Avg Cost: {p.avgCost}")



ib.disconnect()

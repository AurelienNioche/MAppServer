import os

# scp local_file user@remote_host:remote_file
out = os.system("scp data/user_creation/rewards.csv aurelien@pearse.dcs.gla.ac.uk:data/user_creation/rewards.csv")
print(out)

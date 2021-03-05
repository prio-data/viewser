from environs import Env

env = Env()
env.read_env()

BASE_DATA_RETRIEVER_URL = env.str("BASE_DATA_RETRIEVER_URL")
DATA_ROUTER_URL = env.str("DATA_ROUTER_URL")
        

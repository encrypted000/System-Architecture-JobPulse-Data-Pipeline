from database.db_connection import engine
import pandas as pd

df = pd.read_sql("SELECT 1 as test", engine)

print(df)
import pandas as pd
df = pd.read_excel("../database/students_2022-23.xlsx")
df.columns = df.columns.str.strip().str.lower()
print("কলামগুলো:", list(df.columns))
if "semester" in df.columns:
    print("Semester column-এর unique ভ্যালুগুলো:")
    print(df["semester"].unique())
else:
    print("[ERROR] 'semester' কলামই খুঁজে পাওয়া যাচ্ছে না!")
print("\nমোট রো:", len(df))
print(df.head(3))

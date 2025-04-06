import joblib

try:
    model = joblib.load("ml_models/model_iris.pkl")
    print("Modelo carregado com sucesso")
except Exception as e:
    print(e)
    

from main import app, logger, predictions_cache
from models.jwt import token_required
from flask import jsonify, request
import numpy as np
from models.ml_models import model
from models.database import SessionLocal, Prediction

@app.route("/predict", methods=["POST"])
@token_required
def predict():
    """
    Endpoint protegido por token para obter predição.

    Corpo (JSON):
    {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    }
    """
    data = request.get_json(force=True)
    try:
        sepal_length = float(data["sepal_length"])
        sepal_width = float(data["sepal_width"])
        petal_length = float(data["petal_length"])
        petal_width = float(data["petal_width"])
    except (ValueError, KeyError) as e:
        logger.error(f"Dados de entrada inválidos: {e}", exc_info=True)
        return jsonify({"error": "Dados inválidos, verifique parâmetros"}), 400

    features = (sepal_length, sepal_width, petal_length, petal_width)

    # Verifica cache
    if features in predictions_cache:
        logger.info(f"Cache hit para {features}")
        predicted_class = predictions_cache[features]
    else:
        input_data = np.array([features])
        prediction = model.predict(input_data)
        predicted_class = int(prediction[0])
        predictions_cache[features] = predicted_class
        logger.info(f"Cache updated para {features}")
    
    # Salvar no banco de dados
    db = SessionLocal()
    try:
        new_pred = Prediction(
            sepal_length=sepal_length,
            sepal_width=sepal_width,
            petal_length=petal_length,
            petal_width=petal_width,
            predicted_class=predicted_class
        )
        db.add(new_pred)
        db.commit()
    except Exception as e:
        logger.error(f"Erro ao salvar no banco: {e}", exc_info=True)
        db.rollback()
        return jsonify({"error": "Erro ao salvar predição"}), 500
    finally:
        db.close()

    return jsonify({"predicted_class": predicted_class})


@app.route("/predictions", methods=["GET"])
@token_required
def list_predictions():
    """
    Lista as predições armazenadas no banco.

    Parâmetros opcionais (via query string):
    - limit (int): quantos registros retornar, padrão 10
    - offset (int): a partir de qual registro começar, padrão 0
    Exemplo:
    /predictions?limit=5&offset=10
    """
    try:
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"error": "Parâmetros 'limit' e 'offset' devem ser inteiros"}), 400

    db = SessionLocal()
    try:
        preds = (
            db.query(Prediction)
            .order_by(Prediction.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        results = [
            {
                "id": p.id,
                "sepal_length": p.sepal_length,
                "sepal_width": p.sepal_width,
                "petal_length": p.petal_length,
                "petal_width": p.petal_width,
                "predicted_class": p.predicted_class,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in preds
        ]
    except Exception as e:
        logger.error(f"Erro ao consultar predições: {e}", exc_info=True)
        return jsonify({"error": "Erro ao consultar banco"}), 500
    finally:
        db.close()

    return jsonify(results)

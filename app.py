from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import joblib
import tensorflow as tf
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Urban Optimizer AI API")

# Essential: Allows the Vercel frontend to bypass browser CORS blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load your Colab files
try:
    model = tf.keras.models.load_model('urban_optimizer_model.keras')
    scaler = joblib.load('scaler.pkl')
except Exception as e:
    print(f"Error loading model: {e}")

# Define the JSON structure your friend needs to send
class EnergyData(BaseModel):
    history_48_hours: list[float]  

@app.get("/")
def read_root():
    return {"message": "API is online."}

@app.post("/predict")
def predict_load(data: EnergyData):
    if len(data.history_48_hours) != 48:
        raise HTTPException(status_code=400, detail="Must provide exactly 48 hours of data.")
    
    # Scale incoming data using the Colab scaler
    input_array = np.array(data.history_48_hours).reshape(-1, 1)
    scaled_input = scaler.transform(input_array)
    
    # Reshape for LSTM (1 sample, 48 timesteps, 1 feature)
    model_input = scaled_input.reshape(1, 48, 1)
    
    # Predict and convert back to normal Megawatts
    scaled_prediction = model.predict(model_input)
    raw_prediction = scaler.inverse_transform(scaled_prediction)[0][0]
    
    # Hackathon Logic: The "Urban Optimization"
    peak_threshold = 35000 # MW
    optimized_prediction = raw_prediction
    optimization_triggered = False
    
    if raw_prediction > peak_threshold:
        optimized_prediction = raw_prediction * 0.85 # Simulate 15% energy reduction
        optimization_triggered = True
        
    # Send this JSON block back to the Vercel frontend
    return {
        "raw_predicted_load_mw": float(raw_prediction),
        "optimized_load_mw": float(optimized_prediction),
        "optimization_triggered": optimization_triggered,
        "action_simulated": "Dimmed smart lights & pre-cooled buildings" if optimization_triggered else "None"
    }
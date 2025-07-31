from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load dataset
file_path = "Crop_Yield_Prediction.csv"
df = pd.read_csv(file_path)

# Season adjustments
SEASON_ADJUSTMENTS = {
    'Kharif': {'temp': +2, 'rain': +80, 'yield_factor': 1.0},
    'Rabi': {'temp': -2, 'rain': -30, 'yield_factor': 1.1},
    'Zaid': {'temp': +4, 'rain': -50, 'yield_factor': 0.9}
}

# Region data
REGION_DATA = {
    'North India': {'temp_offset': -2, 'rain_offset': +10, 'yield_adjust': 1.0},
    'South India': {'temp_offset': +3, 'rain_offset': +50, 'yield_adjust': 0.9},
    'East India': {'temp_offset': +1, 'rain_offset': +80, 'yield_adjust': 1.1},
    'West India': {'temp_offset': +4, 'rain_offset': -20, 'yield_adjust': 0.8},
    'Central India': {'temp_offset': +2, 'rain_offset': +30, 'yield_adjust': 1.0},
    'Northeast India': {'temp_offset': -1, 'rain_offset': +150, 'yield_adjust': 1.2}
}

# Soil type adjustments
SOIL_ADJUSTMENTS = {
    'Loamy': {'ph_adjust': 0, 'yield_factor': 1.2},
    'Clay': {'ph_adjust': +0.3, 'yield_factor': 0.9},
    'Sandy': {'ph_adjust': -0.2, 'yield_factor': 0.8},
    'Silt': {'ph_adjust': +0.1, 'yield_factor': 1.1},
    'Peaty': {'ph_adjust': -0.5, 'yield_factor': 0.7},
    'Chalky': {'ph_adjust': +0.8, 'yield_factor': 0.6},
    'Black': {'ph_adjust': 0, 'yield_factor': 1.3},
    'Red': {'ph_adjust': -0.3, 'yield_factor': 1.0}
}

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        crop = data['crop']
        region = data['region']
        season = data['season']
        soil = data['soil']

        # Filter dataset for the given crop
        crop_data = df[df['Crop'] == crop]
        if crop_data.empty:
            return jsonify({'error': f'Crop "{crop}" not found in dataset'}), 400

        # Compute base values
        avg_yield = round(crop_data['Yield'].mean(), 2)
        avg_npk = (
            round(crop_data['Nitrogen'].mean(), 1),
            round(crop_data['Phosphorus'].mean(), 1),
            round(crop_data['Potassium'].mean(), 1)
        )
        avg_ph = round(crop_data['pH_Value'].mean(), 2)
        avg_temp = round(crop_data['Temperature'].mean(), 2)
        avg_rain = round(crop_data['Rainfall'].mean(), 2)

        # Adjust for region, season and soil
        temp_adjusted = avg_temp + REGION_DATA[region]['temp_offset'] + SEASON_ADJUSTMENTS[season]['temp']
        rain_adjusted = avg_rain + REGION_DATA[region]['rain_offset'] + SEASON_ADJUSTMENTS[season]['rain']
        ph_adjusted = round(avg_ph + SOIL_ADJUSTMENTS[soil]['ph_adjust'], 2)
        
        # Calculate final yield with all adjustments
        yield_factor = (
            REGION_DATA[region]['yield_adjust'] * 
            SEASON_ADJUSTMENTS[season]['yield_factor'] * 
            SOIL_ADJUSTMENTS[soil]['yield_factor']
        )
        final_yield = round(avg_yield * yield_factor, 2)

        # Generate insights
        insights = [
            f"Recommended NPK ratio: {avg_npk[0]}-{avg_npk[1]}-{avg_npk[2]}",
            f"Ideal pH level for {soil} soil: {ph_adjusted}",
            f"Optimal temperature: {temp_adjusted}°C",
            f"Expected rainfall: {rain_adjusted}mm",
            f"Soil preparation tips: {get_soil_tips(soil)}",
            f"Best planting time: {get_planting_time(crop, season)}"
        ]

        return jsonify({
            'prediction': final_yield,
            'insights': insights
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def get_soil_tips(soil_type):
    tips = {
        'Loamy': "Loamy soil is ideal. Maintain organic matter with regular compost.",
        'Clay': "Improve drainage by adding organic matter and sand. Avoid compaction.",
        'Sandy': "Add organic matter to improve water retention. Mulch heavily.",
        'Silt': "Prone to compaction. Add organic matter and avoid working when wet.",
        'Peaty': "May need lime to reduce acidity. Improve drainage with sand.",
        'Chalky': "Add organic matter and acidic fertilizers to balance pH.",
        'Black': "Rich in nutrients. Maintain with regular organic additions.",
        'Red': "Good drainage but may need organic matter. Check iron content."
    }
    return tips.get(soil_type, "Maintain soil health with regular organic additions.")

def get_planting_time(crop, season):
    planting_times = {
        'Rice': {
            'Kharif': "June-July (ideal for Kharif season)",
            'Rabi': "November-December (for Rabi varieties)",
            'Zaid': "Not typically planted in Zaid season"
        },
        'Maize': {
            'Kharif': "June-July (main Kharif crop)",
            'Rabi': "October-November (in some regions)",
            'Zaid': "March-April (early summer crop)"
        },
        'ChickPea': {
            'Kharif': "Not typically grown in Kharif",
            'Rabi': "October-November (ideal Rabi crop)",
            'Zaid': "Not recommended"
        },
        'Banana': {
            'Kharif': "June-July (with good irrigation)",
            'Rabi': "October-November (in tropical regions)",
            'Zaid': "March-April (with irrigation)"
        },
        'Mango': {
            'Kharif': "Monsoon months for planting",
            'Rabi': "October-November in some regions",
            'Zaid': "March-April with irrigation"
        },
        'Cotton': {
            'Kharif': "May-June (main Kharif crop)",
            'Rabi': "Not typically grown",
            'Zaid': "Not recommended"
        },
        'Coffee': {
            'Kharif': "June-July (with monsoon onset)",
            'Rabi': "October-November in some regions",
            'Zaid': "Not recommended"
        }
    }
    
    # Default planting time if specific crop/season not found
    default_times = {
        'Kharif': "June-July planting recommended",
        'Rabi': "October-November planting recommended",
        'Zaid': "March-April planting with irrigation"
    }
    
    return planting_times.get(crop, {}).get(season, default_times.get(season, "Depends on local conditions"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
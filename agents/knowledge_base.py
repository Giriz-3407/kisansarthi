CROP_DATA = {
    "rice": {
        "Match": 0.95,
        "Description": "Rice is a staple cereal grain, primarily grown as a lowland crop in standing water.",
        "Explanation": "Your soil's high clay content and excellent moisture retention are ideal for Rice. The slightly acidic pH in your data perfectly matches Rice's requirements.",
        "growing_season": "Kharif Season (June to November)",
        "water_requirement": "High; requires 120-150 days of consistent irrigation or rainfall.",
        "expected_yield": "4.0 - 6.0 tons per hectare",
        "Recommendations": "Maintain 5cm water level during tillering stage.\\nApply Nitrogen in 3 split doses."
    },
    "maize": {
        "Match": 0.89,
        "Description": "Maize (Corn) is a versatile grain and fodder crop grown across various climates.",
        "Explanation": "Maize prefers well-drained loamy soils. Your soil data indicates good aeration and nutrient levels, supporting strong stalk development.",
        "growing_season": "Kharif (June-July) and Rabi (October-November)",
        "water_requirement": "Moderate; sensitivity peak is during silking and tasseling.",
        "expected_yield": "3.0 - 5.5 tons per hectare",
        "Recommendations": "Avoid waterlogging by ensuring proper drainage.\\nUse high-quality hybrid seeds for better resistance."
    },
    "cotton": {
        "Match": 0.92,
        "Description": "Cotton is a fiber crop known as 'White Gold', thriving in deep black soils.",
        "Explanation": "The heavy black soil mentioned in your profile is perfect for Cotton. It needs a long frost-free period and moderate rainfall.",
        "growing_season": "Kharif (May-June sowing)",
        "water_requirement": "Moderate; high water need during flowering and boll formation.",
        "expected_yield": "2.0 - 3.5 tons per hectare",
        "Recommendations": "Monitor for Pink Bollworm regularly.\\nAdopt Bt-Cotton varieties for pest resistance."
    },
    "tur": {
        "Match": 0.87,
        "Description": "Tur (Pigeon Pea) is a protein-rich legume and a primary pulse crop in India.",
        "Explanation": "Your well-drained soil is excellent for Tur. It is a hardy crop that improves soil nitrogen naturally.",
        "growing_season": "Kharif (June sowing)",
        "water_requirement": "Low; highly drought-resistant after establishment.",
        "expected_yield": "1.5 - 2.5 tons per hectare",
        "Recommendations": "Avoid planting in saline or waterlogged soils.\\nIntercropping with Bajra or Maize is beneficial."
    },
    "pigeonpeas": { "alias": "tur" },
    "apple": {
        "Match": 0.80,
        "Description": "Apple is a temperate fruit crop usually grown at higher altitudes.",
        "Explanation": "Your soil pH (around 6.5) is suitable for Apple. Some low-chill varieties can be explored if your local winter temperatures are sufficient.",
        "growing_season": "Autumn/Winter (Dormant period)",
        "water_requirement": "Moderate; regular watering ensures juicy fruit development.",
        "expected_yield": "15-25 tons per hectare (Mature orchard)",
        "Recommendations": "Focus on pest management for San Jose scale.\\nPrune annually for better sunlight penetration."
    },
    "banana": {
        "Match": 0.94,
        "Description": "Banana is a high-reward perennial tropical fruit crop.",
        "Explanation": "Your soil's rich organic matter and neutral pH are excellent. It requires consistent moisture and protection from strong winds.",
        "growing_season": "Year-round (Planting usually in June-July or Oct-Nov)",
        "water_requirement": "Very High; requires regular irrigation throughout the year.",
        "expected_yield": "30-50 tons per hectare",
        "Recommendations": "Use tissue-cultured plants for disease-free growth.\\nPropping of plants is necessary during fruit development."
    },
    "grapes": {
        "Match": 0.93,
        "Description": "Grapes are high-value commercial vines, popular in Maharashtra.",
        "Explanation": "Your well-drained sandy-loam soil is ideal for quality grape production. The low humidity in your region helps prevent fungal diseases.",
        "growing_season": "Pruning in April and October",
        "water_requirement": "Moderate; uses drip irrigation efficiently.",
        "expected_yield": "20-30 tons per hectare",
        "Recommendations": "Implement trellis systems for better vine management.\\nRegular thinning improves fruit size and cluster quality."
    },
    "mango": {
        "Match": 0.91,
        "Description": "Mango, the 'King of Fruits', is the most popular tropical fruit in India.",
        "Explanation": "Your deep soil allows for deep root penetration. Mango trees are very resilient once established in your climate.",
        "growing_season": "Summer (Fruit harvest)",
        "water_requirement": "Moderate; young trees need regular water, mature trees are hardy.",
        "expected_yield": "8-12 tons per hectare",
        "Recommendations": "Focus on pruning after harvest.\\nMonitor for Hopper pests during flowering season."
    },
    "pomegranate": {
        "Match": 0.95,
        "Description": "Pomegranate (Anar) is a nutritious, drought-hardy fruit crop.",
        "Explanation": "Your soil is very suitable for Pomegranate. It requires a hot and dry climate which matches your region's profile.",
        "growing_season": "Managed through Bahar treatment (Oct/Feb/June)",
        "water_requirement": "Low to Moderate; very efficient water user.",
        "expected_yield": "10-15 tons per hectare",
        "Recommendations": "Bagging the fruits prevents sun-scald and pest damage.\\nRegular training of the plant into 3-4 stems is advised."
    },
    "orange": {
        "Match": 0.88,
        "Description": "Orange (Citrus) is a major commercial fruit, especially in Vidarbha.",
        "Explanation": "Your soil's texture and pH are well-aligned with Citrus needs. It requires good drainage to prevent root rot.",
        "growing_season": "Ambia and Mrig Bahar",
        "water_requirement": "Moderate; consistent supply is needed during fruit growth.",
        "expected_yield": "15-20 tons per hectare",
        "Recommendations": "Manage Citrus Gummosis through proper drainage.\\nApply foliar micronutrients for better color."
    },
    "papaya": {
        "Match": 0.86,
        "Description": "Papaya is a fast-growing, high-yield tropical fruit.",
        "Explanation": "Your soil fertility and warm climate will support rapid papaya growth. It starts yielding within 10-12 months.",
        "growing_season": "Year-round",
        "water_requirement": "Moderate; susceptible to root rot if waterlogged.",
        "expected_yield": "40-60 tons per hectare",
        "Recommendations": "Ensure male-female plant ratios or use hermaphrodite varieties.\\nProtect from frost in northern regions."
    },
    "chickpea": {
        "Match": 0.90,
        "Description": "Chickpea (Gram) is the most important Rabi pulse crop.",
        "Explanation": "The cooling temperatures and residual soil moisture in your area make it perfect for Chickpea.",
        "growing_season": "Rabi (October-November sowing)",
        "water_requirement": "Low; usually grown on residual moisture.",
        "expected_yield": "1.5 - 2.5 tons per hectare",
        "Recommendations": "Sow when soil temperature is around 25°C.\\nNipping of top shoots increases branching and yield."
    },
    "lentil": {
        "Match": 0.85,
        "Description": "Lentil (Masoor) is a nutritious cold-weather pulse crop.",
        "Explanation": "Lentils grow well in your loamy soil and the milder winter temperatures predicted.",
        "growing_season": "Rabi (October-November)",
        "water_requirement": "Low; highly drought resistant.",
        "expected_yield": "1.0 - 1.8 tons per hectare",
        "Recommendations": "Proper weed management in the first 30 days is critical.\\nAvoid high nitrogen fertilizers as lentils fix their own N."
    },
    "blackgram": {
        "Match": 0.87,
        "Description": "Blackgram (Urad) is an important pulse crop with high protein content.",
        "Explanation": "The hot and humid conditions in your profile are good for Blackgram growth. It also improves soil fertility.",
        "growing_season": "Kharif and Summer",
        "water_requirement": "Moderate; sensitivity during flowering.",
        "expected_yield": "0.8 - 1.2 tons per hectare",
        "Recommendations": "Ensure the field is free of weeds during early growth.\\nMonitor for Yellow Mosaic Virus."
    },
    "mungbean": {
        "Match": 0.88,
        "Description": "Mungbean (Moong) is a short-duration pulse crop.",
        "Explanation": "Moong can be grown in the gap between your major seasons, providing extra income and improving soil health.",
        "growing_season": "Kharif and Summer (60-70 days crop)",
        "water_requirement": "Low; very water-efficient.",
        "expected_yield": "0.7 - 1.0 tons per hectare",
        "Recommendations": "Pick mature pods timely to avoid shattering.\\nSeed treatment with Rhizobium culture is beneficial."
    },
    "watermelon": {
        "Match": 0.92,
        "Description": "Watermelon is a high-water, warm-season dessert fruit crop.",
        "Explanation": "Your warm temperatures and well-drained sandy loam conditions support rapid vine spreading and high sugar content in fruits.",
        "growing_season": "Summer / Zaid (January-March sowing)",
        "water_requirement": "Moderate; requires regular light irrigation, avoid overwatering near ripening.",
        "expected_yield": "25 - 40 tons per hectare",
        "Recommendations": "Adopt plastic mulching to conserve moisture and suppress weeds.\\nEnsure bee pollination during morning flowering."
    },
    "muskmelon": {
        "Match": 0.90,
        "Description": "Muskmelon (Kharbooja) is a sweet commercial cucurbit fruit crop.",
        "Explanation": "The hot and dry maturation climate in your region is ideal for developing high fruit sweetness and characteristic netting.",
        "growing_season": "Summer / Zaid (February-March sowing)",
        "water_requirement": "Moderate; drip irrigation with fertigation gives optimal brix levels.",
        "expected_yield": "15 - 25 tons per hectare",
        "Recommendations": "Withhold irrigation 5-7 days before harvest for sweeter fruits.\\nMonitor for fruit fly infestations."
    },
    "coconut": {
        "Match": 0.93,
        "Description": "Coconut is a perennial plantation palm thriving in humid tropical climates.",
        "Explanation": "Your high relative humidity and warm coastal or tropical conditions are well-suited for sustained coconut bunch development.",
        "growing_season": "Perennial (Planting in June-September monsoon)",
        "water_requirement": "High; requires 40-50 liters/palm/day through basin or drip irrigation.",
        "expected_yield": "80 - 120 nuts per palm per year",
        "Recommendations": "Apply organic mulch around palm basins to retain soil moisture.\\nApply split doses of Potash and Magnesium."
    },
    "coffee": {
        "Match": 0.91,
        "Description": "Coffee (Arabica / Robusta) is a premier shade-grown plantation beverage crop.",
        "Explanation": "Your elevation, moderate temperature range, and shaded organic soil profile provide ideal microclimate for coffee berry development.",
        "growing_season": "Perennial (Harvesting in November-February)",
        "water_requirement": "Moderate to High; blossom showers in March-April are crucial.",
        "expected_yield": "1.0 - 2.5 tons of clean coffee per hectare",
        "Recommendations": "Maintain 2-tier shade canopy to prevent sun scorch.\\nMonitor for coffee berry borer and white stem borer."
    },
    "jute": {
        "Match": 0.90,
        "Description": "Jute is a natural bast fiber crop termed the 'Golden Fiber'.",
        "Explanation": "Your warm humid climate and alluvial soil with good monsoon rainfall facilitate tall vegetative growth and clean fiber retting.",
        "growing_season": "Kharif (March-May sowing, 120 days crop)",
        "water_requirement": "High; thrives in wet floodplains with 150+ mm monthly rainfall.",
        "expected_yield": "2.5 - 3.5 tons of dry fiber per hectare",
        "Recommendations": "Harvest at small-pod stage for optimum fiber strength and luster.\\nEnsure clean running water for retting."
    },
    "kidneybeans": {
        "Match": 0.88,
        "Description": "Kidney Beans (Rajma) is a high-protein, cool-weather legume.",
        "Explanation": "Your mild temperature conditions and slightly acidic, well-aerated soil are well-matched for Rajma root development.",
        "growing_season": "Rabi (Plains: Oct-Nov) / Kharif (Hills: May-June)",
        "water_requirement": "Moderate; critical irrigation at flowering and pod filling.",
        "expected_yield": "1.5 - 2.2 tons per hectare",
        "Recommendations": "Since Rajma does not nodulate extensively, apply starter Nitrogen (40-60 kg/ha).\\nAvoid waterlogging."
    },
    "mothbeans": {
        "Match": 0.87,
        "Description": "Moth Bean (Matki) is an exceptionally drought-hardy, semi-arid pulse crop.",
        "Explanation": "Your arid to semi-arid climate with light soil supports Moth Bean's low moisture needs and deep taproot system.",
        "growing_season": "Kharif (July sowing)",
        "water_requirement": "Very Low; survives with 250-400 mm total rainfall.",
        "expected_yield": "0.6 - 1.0 ton per hectare",
        "Recommendations": "Excellent cover crop to prevent soil erosion in drylands.\\nHarvest early in the morning to prevent pod shattering."
    },
    "wheat": {
        "Match": 0.94,
        "Description": "Wheat is the premier Rabi cereal staple in northern and central India.",
        "Explanation": "Your cool winter temperatures and loamy, well-drained soil provide the ideal environment for tillering and grain filling.",
        "growing_season": "Rabi Season (November sowing, March-April harvest)",
        "water_requirement": "Moderate; requires 4-6 critical irrigations (Crown root initiation, flowering, milk stage).",
        "expected_yield": "4.5 - 6.0 tons per hectare",
        "Recommendations": "Apply Crown Root Initiation (CRI) irrigation at 21 days after sowing.\\nEnsure balanced NPK + Zinc fertilization."
    },
    "sugarcane": {
        "Match": 0.93,
        "Description": "Sugarcane is a long-duration commercial cash and sugar crop.",
        "Explanation": "Your high nutrient availability, deep soil profile, and warm sunshine support robust cane elongation and high sucrose accumulation.",
        "growing_season": "Year-round (Adsali: July-Aug, Pre-seasonal: Oct-Nov, Suru: Jan-Feb)",
        "water_requirement": "Very High; requires 1500-2500 mm water across its 12-18 month cycle.",
        "expected_yield": "80 - 130 tons per hectare",
        "Recommendations": "Adopt drip irrigation to save 40% water.\\nTrash mulching between cane rows preserves soil moisture."
    },
    "groundnut": {
        "Match": 0.89,
        "Description": "Groundnut (Peanut) is an important oilseed and food legume.",
        "Explanation": "Your light sandy loam soil enables easy peg penetration and uniform pod development without pod rot.",
        "growing_season": "Kharif (June-July) and Summer (Jan-Feb)",
        "water_requirement": "Moderate; critical moisture needed at pegging and pod formation.",
        "expected_yield": "2.0 - 3.5 tons per hectare",
        "Recommendations": "Apply Gypsum (400-500 kg/ha) at flowering to supply Calcium and Sulphur for bold pods.\\nAvoid deep hoeing after pegging."
    },
    "tea": {
        "Match": 0.91,
        "Description": "Tea is a high-value plantation perennial harvested for its tender shoots.",
        "Explanation": "Your acidic soil pH (4.5-5.5) and high rainfall with excellent hillside drainage prevent water stagnation and foster tender leaf flushes.",
        "growing_season": "Perennial (Plucking from March to November)",
        "water_requirement": "High; requires 1500-2500 mm annual rainfall distributed well.",
        "expected_yield": "2.0 - 3.5 tons of made tea per hectare",
        "Recommendations": "Maintain soil acidity with ammonium sulphate.\\nPrune bushes systematically to encourage vegetative flush."
    },
    "tobacco": {
        "Match": 0.88,
        "Description": "Tobacco is a specialized commercial cash crop grown for cured leaf production.",
        "Explanation": "Your soil texture and potassium levels support good leaf burning quality, elasticity, and uniform nicotine content.",
        "growing_season": "Rabi (October-November transplanting)",
        "water_requirement": "Moderate; avoid chlorine-rich water to maintain leaf quality.",
        "expected_yield": "1.8 - 2.8 tons of cured leaf per hectare",
        "Recommendations": "Topping and de-suckering are vital for leaf expansion.\\nApply high Potash (K2O) for superior leaf grade."
    },
    "millet": {
        "Match": 0.90,
        "Description": "Millets (Bajra, Jowar, Ragi) are climate-resilient, nutrient-rich nutri-cereals.",
        "Explanation": "Your dryland climate, lower rainfall, and warm temperatures are perfectly matched with millet's high water-use efficiency and drought resistance.",
        "growing_season": "Kharif (July sowing) and Summer",
        "water_requirement": "Low; produces sustainable yields with only 350-500 mm rainfall.",
        "expected_yield": "2.5 - 4.0 tons per hectare",
        "Recommendations": "Practice line sowing with 45cm row spacing.\\nApply basal Phosphorus for vigorous seedling root establishment."
    },
    "peas": {
        "Match": 0.90,
        "Description": "Green Peas (Matar) is a nutritious, cool-season short-duration vegetable and pulse.",
        "Explanation": "Your mild winter temperatures and well-drained neutral pH soil promote rapid flowering and sweet pod filling in 65-80 days.",
        "growing_season": "Rabi (October-November sowing)",
        "water_requirement": "Low to Moderate; 2-3 light irrigations at flowering and pod filling.",
        "expected_yield": "6 - 10 tons of green pods per hectare",
        "Recommendations": "Inoculate seeds with Rhizobium leguminosarum culture.\\nHarvest green pods when fully developed but still tender."
    },
    "adzuki": {
        "Match": 0.88,
        "Description": "Adzuki Bean is an antioxidant-rich, high-value specialty red pulse crop.",
        "Explanation": "Your well-drained loamy soil and moderate temperate-subtropical conditions support uniform flowering and pod maturation.",
        "growing_season": "Kharif (June-July) / Spring",
        "water_requirement": "Low to Moderate; sensitive to waterlogging.",
        "expected_yield": "1.2 - 2.0 tons per hectare",
        "Recommendations": "Maintain optimum row spacing of 30-40 cm.\\nAvoid high nitrogen fertilizers as the plant fixes atmospheric nitrogen."
    },
    "rubber": {
        "Match": 0.90,
        "Description": "Natural Rubber (Hevea brasiliensis) is a major tropical plantation tree.",
        "Explanation": "Your high annual rainfall, humid tropical atmosphere, and acidic loamy soil provide the necessary climate for high latex yield.",
        "growing_season": "Perennial (Planting in June-July monsoon, tapping starts after 7 years)",
        "water_requirement": "High; requires 2000-3000 mm well-distributed rainfall with no prolonged dry season.",
        "expected_yield": "1.5 - 2.5 tons of dry rubber per hectare per year",
        "Recommendations": "Adopt controlled tapping systems to protect bark.\\nUse rain guards during monsoon for uninterrupted tapping."
    }
}

FERTILIZER_DATA = {
    "Urea": {
        "Product": "Kisan Shaktiman Urea (46% N)",
        "Buy at": "Local Agri-Cooperative or IFFCO Bazaar",
        "Amount": "100-150 kg per hectare (Split into 2-3 doses)",
        "Price": "266 INR per 45kg bag (Subsidized)",
        "Description": "Urea is the most common nitrogenous fertilizer.",
        "Explanation": "Your soil shows low nitrogen. Urea provides a quick boost for vegetative growth and lush green foliage."
    },
    "DAP": {
        "Product": "IFFCO DAP (18:46:0)",
        "Buy at": "Authorized Fertilizer Dealers",
        "Amount": "100-125 kg per hectare at the time of sowing",
        "Price": "1350 INR per 50kg bag",
        "Description": "Diammonium Phosphate is a concentrated phosphate fertilizer with 18% Nitrogen.",
        "Explanation": "Phosphorus is critical for root development. DAP is highly recommended for the initial growth phase of your crop."
    },
    "MOP": {
        "Product": "IPL Muriate of Potash (60% K)",
        "Buy at": "Agri-Input Stores",
        "Amount": "50-80 kg per hectare",
        "Price": "1700 INR per 50kg bag",
        "Description": "Muriate of Potash provides high potassium content.",
        "Explanation": "Potassium improves disease resistance and fruit quality. Your soil needs this for better stress tolerance."
    },
    "17-17-17": {
        "Product": "Complex NPK 17:17:17",
        "Buy at": "Local Agri Dealers",
        "Amount": "150-200 kg per hectare",
        "Price": "1200 INR per 50kg bag",
        "Description": "A balanced NPK fertilizer with equal proportions of N, P, and K.",
        "Explanation": "Recommended for balanced growth. This ensures your crop gets all primary nutrients simultaneously."
    },
    "10-26-26": {
        "Product": "Mahadhan 10:26:26 NPK Compound",
        "Buy at": "Local Agri Stores",
        "Amount": "125-150 kg per hectare",
        "Price": "1450 INR per 50kg bag",
        "Description": "A balanced NPK fertilizer with high phosphorus and potassium content.",
        "Explanation": "Ideal for crops requiring high initial energy and strong disease resistance."
    },
    "20-20-0": {
        "Product": "IFFCO 20-20-0-13P",
        "Buy at": "Agri Outlets",
        "Amount": "100-150 kg per hectare",
        "Price": "1150 INR per 50kg bag",
        "Description": "Nitrogen and Phosphorus complex with Sulphur.",
        "Explanation": "Good for pulse crops and oilseeds requiring high initial P and some N."
    },
    "28-28-0": {
        "Product": "Gromor 28:28:0 APS",
        "Buy at": "Agri Dealers",
        "Amount": "120 kg per hectare",
        "Price": "1400 INR per 50kg bag",
        "Description": "Ammonium Phosphate Sulphate, high in Nitrogen and Phosphorus.",
        "Explanation": "Drives rapid early growth in cereal crops like Maize and Rice."
    },
    "14-35-14": {
        "Product": "Gromor 14-35-14",
        "Buy at": "Authorized Dealers",
        "Amount": "100-120 kg per hectare",
        "Price": "1550 INR per 50kg bag",
        "Description": "High phosphorus NPK complex for strong root establishment.",
        "Explanation": "Ideal for fruit trees and transplanted crops that need deep root anchoring."
    },
    "Generic NPK": {
        "Product": "Balanced NPK 19-19-19",
        "Buy at": "Any Agri Store",
        "Amount": "5 kg per acre via foliar spray/fertigation",
        "Price": "150-200 INR per kg",
        "Description": "Fully water-soluble NPK fertilizer.",
        "Explanation": "Used for quick nutrient absorption through leaves or drip systems."
    }
}

# Mapping for models that return integer labels or index-based results
FERT_LABEL_MAP = {
    "0": "Urea",
    "1": "DAP",
    "2": "MOP",
    "3": "14-35-14",
    "4": "28-28-0",
    "5": "17-17-17",
    "6": "20-20-0",
    "7": "Generic NPK"
}

DEFAULT_CROP = {
    "Match": 0.50,
    "Description": "General suggestion based on region climate.",
    "Explanation": "Your specific soil data points to this crop as a viable option. We recommend a lab test for more precise planning.",
    "growing_season": "Local Kharif or Rabi cycles.",
    "water_requirement": "Moderate; check soil moisture daily.",
    "expected_yield": "Varies by management.",
    "Recommendations": "Maintain proper weed control and monitor for pests."
}

DEFAULT_FERT = {
    "Product": "Balanced NPK Mix",
    "Buy at": "Local Fertilizer Shop",
    "Amount": "Apply as per bag instructions",
    "Price": "Varies by brand",
    "Description": "General purpose nutrient boost.",
    "Explanation": "This balanced formula supports overall plant health across most soil types."
}

def get_crop_details(crop_name):
    name = str(crop_name).lower().strip()
    
    # Handle aliases
    if name in CROP_DATA and "alias" in CROP_DATA[name]:
        name = CROP_DATA[name]["alias"]

    if name in CROP_DATA:
        return CROP_DATA[name]

    raise ValueError(f"Crop details for '{crop_name}' are not available.")

def get_fert_details(fert_name):
    # 1. Handle integer labels
    name_str = str(fert_name).strip()
    if name_str in FERT_LABEL_MAP:
        name_str = FERT_LABEL_MAP[name_str]

    # 2. Strict Match
    lookup = name_str.lower()
    for key in FERTILIZER_DATA:
        if key.lower() == lookup:
            return FERTILIZER_DATA[key]

    raise ValueError(f"Fertilizer details for '{fert_name}' are not available.")

# Model Mappings Reference

This document provides a complete mapping reference for the ML models used in the KisanSarthi backend.

---

## Crop Recommendation Model

**Model File:** `agents/model/crop_recommendation1.pkl`

### Input Feature Structure

| Index | Feature | Description |
|-------|---------|-------------|
| 0 | `soil` | Soil type encoded value (0-32) |
| 1 | `ph` | pH value (float, typically 4.5-8.5) |
| 2 | `temperature` | Temperature in Celsius (float) |
| 3 | `humidity` | Humidity percentage (float, 0-100) |
| 4 | `nitrogen` | Nitrogen content (int, 0-150) |
| 5 | `phosphorus` | Phosphorus content (int, 0-150) |
| 6 | `potassium` | Potassium content (int, 0-150) |
| 7 | `water` | Moisture/Water availability (float, 0-100) |

### Supported Soil Types (SOIL_DICT)

| Encoded Value | Soil Type |
|--------------|-----------|
| 0 | Alluvial soil |
| 1 | Black Soil |
| 2 | Clay soil |
| 3 | Laterite soil |
| 4 | Loamy soil |
| 5 | Red soil |
| 6 | Sandy soil |
| 7 | Sandy soil (alt) |
| 8 | Sandy soil (alt 2) |
| 9 | black cotton soil |
| 10 | brown Loamy soil |
| 11 | clay Loamy soil |
| 12 | clay Loamy soil (sp) |
| 13 | deep soil |
| 14 | friable soil |
| 15 | heavy Black Soil |
| 16 | heavy soil (sp) |
| 17 | light Loamy soil |
| 18 | loamy soil (sp) |
| 19 | medium Black Soil |
| 20 | red Loamy soil |
| 21 | red lateritic Loamy soil |
| 22 | rich red Loamy soil |
| 23 | salty clay Loamy soil |
| 24 | sandy Loamy soil |
| 25 | sandy clay Loamy soil (sp) |
| 26 | sandy loamy soil (sp) |
| 27 | shallow Black Soil |
| 28 | silty Loamy soil |
| 29 | well-drained loamy soil (sp) |
| 30 | well-drained soil |
| 31 | well-grained deep loamy moist soil |
| 32 | cotton soil (sp) |
| 33 | light soil (sp) |

> **Note:** `(sp)` indicates contains special/non-breaking space characters

### Supported Crops (CROP_DICT)

| Index | Crop Name | Index | Crop Name |
|-------|-----------|-------|-----------|
| 0 | Cabbage | 29 | maize |
| 1 | Pearl millet | 30 | muskmelon |
| 2 | annual moringa | 31 | onion |
| 3 | ash gourd | 32 | panivaragu |
| 4 | beetroot | 33 | peas |
| 5 | bengalgram | 34 | pumpkin |
| 6 | bhendi | 35 | radish |
| 7 | bitter gourd | 36 | ragi |
| 8 | blackgram | 37 | redgram |
| 9 | bottle gourd | 38 | ribbed gourd |
| 10 | brinjal | 39 | rice |
| 11 | capsicum | 40 | samai |
| 12 | carrot | 41 | small onion |
| 13 | castor | 42 | snake gourd |
| 14 | cauliflower | 43 | sorghum |
| 15 | chillies | 44 | soyabean |
| 16 | chowchow | 45 | sugarbeet |
| 17 | cluster bean | 46 | sugarcane |
| 18 | cotton | 47 | sunflower |
| 19 | cowpea | 48 | sweet potato |
| 20 | cucumber | 49 | tapoica |
| 21 | elephant foot yam | 50 | thinai |
| 22 | french bean | 51 | tinda |
| 23 | gingely | 52 | tomato |
| 24 | greengram | 53 | varagu |
| 25 | groundnut | 54 | vegetable cowpea |
| 26 | horsegram | 55 | watermelon |
| 27 | jute | 56 | wheat |
| 28 | kudiraivali | | |

---

## Fertilizer Recommendation Model

**Model File:** `agents/model/fertilizer.pkl`

### Input Feature Structure

| Feature | Type | Description |
|---------|------|-------------|
| `Soil_color` | int | Encoded soil color (0-4) |
| `Nitrogen` | int | N content (0-150) |
| `Phosphorus` | int | P content (0-150) |
| `Potassium` | int | K content (0-150) |
| `pH` | float | pH value (4.5-8.5) |
| `Rainfall` | float | Rainfall in mm |
| `Temperature` | float | Temperature in Celsius |
| `Crop` | int | Encoded crop (1-15) |

### Supported Soil Colors

| Encoded Value | Soil Color |
|--------------|------------|
| 0 | Red |
| 1 | Black |
| 2 | Sandy |
| 3 | Clay |
| 4 | Loamy |

### Supported Crops (crop_mapping)

| Crop Name | Encoded Value | Crop Name | Encoded Value |
|-----------|---------------|-----------|---------------|
| sugarcane | 1 | moong | 10 |
| jowar / sorghum | 2 | gram | 11 |
| cotton | 3 | bengalgram | 11 |
| rice | 4 | masoor | 12 |
| wheat | 5 | soybean / soyabean | 13 |
| groundnut | 6 | ginger | 14 |
| maize / corn | 7 | turmeric | 15 |
| tur / redgram | 8 | grapes | 16 |
| urad / blackgram | 9 | | |

#### Millet Normalizations (→ jowar/2)

| Crop Suggestion | Fertilizer Model Crop |
|-----------------|----------------------|
| Pearl millet | jowar (2) |
| panivaragu | jowar (2) |
| varagu | jowar (2) |
| samai | jowar (2) |
| thinai | jowar (2) |
| kudiraivali | jowar (2) |
| ragi | jowar (2) |
| bajra | jowar (2) |
| finger millet | jowar (2) |
| little millet | jowar (2) |
| foxtail millet | jowar (2) |
| kodo millet | jowar (2) |
| barnyard millet | jowar (2) |
| proso millet | jowar (2) |

### Fertilizer Output Classes (FERT_LABEL_MAP)

| Encoded Value | Fertilizer Name | N-P-K Ratio |
|---------------|-----------------|-------------|
| 0 | Urea | 46-0-0 |
| 1 | DAP | 18-46-0 |
| 2 | MOP | 0-0-60 |
| 3 | 14-35-14 | 14-35-14 |
| 4 | 28-28-0 | 28-28-0 |
| 5 | 17-17-17 | 17-17-17 |
| 6 | 20-20-0 | 20-20-0 |
| 7 | Generic NPK | Variable |

---

## Crop Suggestion → Fertilizer Model Mapping

This table shows how crop suggestion outputs map to fertilizer model inputs:

| Crop Suggestion (from crop_recommendation1.pkl) | Fertilizer Model Crop | Encoded Value |
|------------------------------------------------|----------------------|---------------|
| sugarcane | sugarcane | 1 |
| sorghum | jowar | 2 |
| cotton | cotton | 3 |
| rice | rice | 4 |
| wheat | wheat | 5 |
| groundnut | groundnut | 6 |
| maize | maize | 7 |
| tur | tur | 8 |
| redgram | tur | 8 |
| blackgram | urad | 9 |
| urad | urad | 9 |
| greengram | moong | 10 |
| moong | moong | 10 |
| bengalgram | gram | 11 |
| gram | gram | 11 |
| masoor | masoor | 12 |
| soyabean | soyabean | 13 |
| ginger | ginger | 14 |
| turmeric | turmeric | 15 |
| grapes | grapes | 16 |
| Pearl millet | jowar | 2 |
| panivaragu | jowar | 2 |
| varagu | jowar | 2 |
| samai | jowar | 2 |
| thinai | jowar | 2 |
| kudiraivali | jowar | 2 |
| ragi | jowar | 2 |

---

## Knowledge Base Reference

### Fertilizer Details (FERTILIZER_DATA)

| Fertilizer | Product | Amount | Price |
|------------|---------|--------|-------|
| Urea | Kisan Shaktiman Urea (46% N) | 100-150 kg/ha | 266 INR/45kg |
| DAP | IFFCO DAP (18:46:0) | 100-125 kg/ha | 1350 INR/50kg |
| MOP | IFFCO MOP (0-0-60) | 50-100 kg/ha | 900 INR/50kg |
| 14-35-14 | IFFCO 14-35-14 | 60-80 kg/ha | 1200 INR/50kg |
| 28-28-0 | IFFCO 28-28-0 | 80-100 kg/ha | 1100 INR/50kg |
| 17-17-17 | IFFCO 17-17-17 | 100 kg/ha | 1050 INR/50kg |
| 20-20-0 | IFFCO 20-20-0 | 80-100 kg/ha | 1000 INR/50kg |
| Generic NPK | Water-soluble NPK | As per crop need | Varies |

---

## Error Prevention Guidelines

### To Avoid "Unknown Crop" Errors:

1. **Use exact crop names** from CROP_DICT (indices 0-56)
2. **For millet crops**, use the normalization mapping to map to "jowar" (2)
3. **Check crop_mapping** in fertilizer_recommender.py before passing to fertilizer model

### To Avoid "Unknown Soil" Errors:

1. **Use soil types** from SOIL_DICT (indices 0-33)
2. **For fallback**, default to index 4 (Loamy soil)
3. **For fertilizer model**, use soil colors from soil_color_mapping (0-4)

### To Avoid "Unknown Fertilizer" Errors:

1. **Model returns integers 0-7** - these map via FERT_LABEL_MAP
2. **Verify FERT_LABEL_MAP** alignment with knowledge base

---

*Last Updated: April 2026*
*Model Files: crop_recommendation1.pkl, fertilizer.pkl*
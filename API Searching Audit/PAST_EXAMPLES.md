# Past Examples - Vehicle Resolution System

This document contains complete input/output examples from the vehicle resolution system.
Each example shows the exact prompt sent to Google Gemini API and the complete response received.

**Generated**: 2025-11-06 10:24:57
**Total Examples**: 5

---

## Example 1: 1992 Mazda Miata

### Input

- **Year**: 1992
- **Make**: Mazda
- **Model**: Miata
- **Vehicle Key**: `1992_mazda_miata`
- **Timestamp**: 2025-11-06T10:23:51.359001

### Database Check

Database check failed: DATABASE_URL environment variable is required. Please set DATABASE_URL in your Streamlit Cloud secrets or environment variables. Example: DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require

### Prompt Sent to API

**Length**: 1154 characters

```
Find specs for 1992 Mazda Miata. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value based on available data - use base trim if identifiable, or most common value)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely and sensible number)

SOURCES: Use any available sources (mark "oem" for manufacturer sites, "secondary" for others). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

IMPORTANT: If the vehicle does not appear to exist or cannot be verified, set status to "not_found" for all fields and return null values.

RETURN JSON:
{
  "curb_weight": {"value": 3310, "unit": "lbs", "status": "found", "citations": [{"url": "...", "quote": "...", "source_type": "oem"}]},
  "aluminum_engine": {"value": true, "status": "found", "citations": [...]},
  "aluminum_rims": {"value": true, "status": "found", "citations": [...]},
  "catalytic_converters": {"value": 2, "status": "found", "citations": [...]}
}
```

### API Configuration

```json
{
  "model": "gemini-2.0-flash-exp",
  "tools": [
    {
      "google_search": {}
    }
  ],
  "temperature": 0
}
```

### Raw API Response

**Duration**: 10073.51ms (10.07 seconds)
**Length**: 2927 characters
**Markdown Wrapper**: Yes

```
```json
{
  "curb_weight": {
    "value": 2100,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7suS5a7dGbARX6EB-TsA04pAsOsXW7gabmksuV36f2R2mJHxdffVE5q829SvCCBcYg5worKuP-5fuYrxSjJj8wWxmt3J-Lq2YpKBh9n-lRp6zW8xG6-oH15xb",
        "quote": "Curb weight, 2100 lbs (940 kg).",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHGNlePRJMjikWt7WNEAEvqTXR4VE8FIP78QBtm0_HOf806WYGOBX-oAEdbcRHeaLNrKQ_SIoNW33JeR_GYeBo2rXtpaa7-ouC88F4gmLKtvtYZsQZvGOVnYkcoDXNmeGcni9KPqQ1KlLRz_n4Osaco4Q==",
        "quote": "The engine, in the USA and used in the '03 Mazda 6, is an all aluminum inline four-cylinder with 2.0 and 2.3 displacement variants.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7suS5a7dGbARX6EB-TsA04pAsOsXW7gabmksuV36f2R2mJHxdffVE5q829SvCCBcYg5worKuP-5fuYrxSjJj8wWxmt3J-Lq2YpKBh9n-lRp6zW8xG6-oH15xb",
        "quote": "A Package, Power steering, leather-wrapped steering wheel, aluminum alloy wheels, cassette stereo with anti-theft coding.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGlakiiVcVrlA7WmTwVaXc9l6HD2sXgk6l8O9fWcCnCYc5G4uKjVNkbjjIVcEefgMCqoREHq07NFNt_0Ap6PV3-JKIzrLH_EwndF_2YrCHzYPYGZH6msSFT8Z0ceOVBC-EBSUOCwIZst_VbQvTK8ndSzcIyk4Iba5lW_GvndDQdj589wmfKzeULOXuVixBl2M7wRTHlc9BHmV0b8ODJDoGqouwiAw4v",
        "quote": "Mazda MX-5 MIATA (1990-1992) 14x5. 5 Aluminum Alloy Chrome 7 Spoke [64722]",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 1,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHJ8rdDTYEKmRLCiveQ72Z3cSInExmGpQn86BlxFQkNEoLBmvfFLvLGZn9aO4pIK06l24EjD_Xn_1lD5ouvFriNEXB01KVcpYarwCyet4nRikJxReHtoWMz_ZFZBbdyNX8WfzV3yWcqRi4FqZKfJKBL0x5bE-O9CWuRiZa1-pBvhxP0DJkdx29-jnigY80a",
        "quote": "This direct-fit catalytic converter is designed specifically for the 1990-1993 Mazda Miata.",
        "source_type": "secondary"
      },
       {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHT8ATR0mirufe7FqGMCEdIwnRtBIGtFTKXQCEmvLx8OL8lOSMZwFybaaREUwgkrb4259Vm2d9FxZ_rOWj9qAju0P9BMgdZJJzF64ry9um_eY5-OVgkjOykdUoBWjAsN8C6ruyYO3CUYQ7OImS2oVH6giAK9bSxsX5dPPrmIHc=",
        "quote": "As with all of our catalytic converters, this cat is emissions-certified. Specifically, it's EPA-approved for this application.",
        "source_type": "secondary"
      }
    ]
  }
}
```
```

### Parsed JSON Response

```json
{
  "curb_weight": {
    "value": 2100,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7suS5a7dGbARX6EB-TsA04pAsOsXW7gabmksuV36f2R2mJHxdffVE5q829SvCCBcYg5worKuP-5fuYrxSjJj8wWxmt3J-Lq2YpKBh9n-lRp6zW8xG6-oH15xb",
        "quote": "Curb weight, 2100 lbs (940 kg).",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHGNlePRJMjikWt7WNEAEvqTXR4VE8FIP78QBtm0_HOf806WYGOBX-oAEdbcRHeaLNrKQ_SIoNW33JeR_GYeBo2rXtpaa7-ouC88F4gmLKtvtYZsQZvGOVnYkcoDXNmeGcni9KPqQ1KlLRz_n4Osaco4Q==",
        "quote": "The engine, in the USA and used in the '03 Mazda 6, is an all aluminum inline four-cylinder with 2.0 and 2.3 displacement variants.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7suS5a7dGbARX6EB-TsA04pAsOsXW7gabmksuV36f2R2mJHxdffVE5q829SvCCBcYg5worKuP-5fuYrxSjJj8wWxmt3J-Lq2YpKBh9n-lRp6zW8xG6-oH15xb",
        "quote": "A Package, Power steering, leather-wrapped steering wheel, aluminum alloy wheels, cassette stereo with anti-theft coding.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGlakiiVcVrlA7WmTwVaXc9l6HD2sXgk6l8O9fWcCnCYc5G4uKjVNkbjjIVcEefgMCqoREHq07NFNt_0Ap6PV3-JKIzrLH_EwndF_2YrCHzYPYGZH6msSFT8Z0ceOVBC-EBSUOCwIZst_VbQvTK8ndSzcIyk4Iba5lW_GvndDQdj589wmfKzeULOXuVixBl2M7wRTHlc9BHmV0b8ODJDoGqouwiAw4v",
        "quote": "Mazda MX-5 MIATA (1990-1992) 14x5. 5 Aluminum Alloy Chrome 7 Spoke [64722]",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 1,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHJ8rdDTYEKmRLCiveQ72Z3cSInExmGpQn86BlxFQkNEoLBmvfFLvLGZn9aO4pIK06l24EjD_Xn_1lD5ouvFriNEXB01KVcpYarwCyet4nRikJxReHtoWMz_ZFZBbdyNX8WfzV3yWcqRi4FqZKfJKBL0x5bE-O9CWuRiZa1-pBvhxP0DJkdx29-jnigY80a",
        "quote": "This direct-fit catalytic converter is designed specifically for the 1990-1993 Mazda Miata.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHT8ATR0mirufe7FqGMCEdIwnRtBIGtFTKXQCEmvLx8OL8lOSMZwFybaaREUwgkrb4259Vm2d9FxZ_rOWj9qAju0P9BMgdZJJzF64ry9um_eY5-OVgkjOykdUoBWjAsN8C6ruyYO3CUYQ7OImS2oVH6giAK9bSxsX5dPPrmIHc=",
        "quote": "As with all of our catalytic converters, this cat is emissions-certified. Specifically, it's EPA-approved for this application.",
        "source_type": "secondary"
      }
    ]
  }
}
```

### Validated & Normalized Results

#### CURB_WEIGHT

- **Value**: `2100.0`
- **Status**: `found`
- **Confidence**: `0.70`
- **Unit**: `lbs`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7suS5a7dGbARX6EB-TsA04pAsOsXW7gabmksuV36f2R2mJHxdffVE5q829SvCCBcYg5worKuP-5fuYrxSjJj8wWxmt3J-Lq2YpKBh9n-lRp6zW8xG6-oH15xb
  - **Quote**: "Curb weight, 2100 lbs (940 kg)."
  
#### ALUMINUM_ENGINE

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.70`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHGNlePRJMjikWt7WNEAEvqTXR4VE8FIP78QBtm0_HOf806WYGOBX-oAEdbcRHeaLNrKQ_SIoNW33JeR_GYeBo2rXtpaa7-ouC88F4gmLKtvtYZsQZvGOVnYkcoDXNmeGcni9KPqQ1KlLRz_n4Osaco4Q==
  - **Quote**: "The engine, in the USA and used in the '03 Mazda 6, is an all aluminum inline four-cylinder with 2.0 and 2.3 displacement variants."
  
#### ALUMINUM_RIMS

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7suS5a7dGbARX6EB-TsA04pAsOsXW7gabmksuV36f2R2mJHxdffVE5q829SvCCBcYg5worKuP-5fuYrxSjJj8wWxmt3J-Lq2YpKBh9n-lRp6zW8xG6-oH15xb
  - **Quote**: "A Package, Power steering, leather-wrapped steering wheel, aluminum alloy wheels, cassette stereo with anti-theft coding."
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGlakiiVcVrlA7WmTwVaXc9l6HD2sXgk6l8O9fWcCnCYc5G4uKjVNkbjjIVcEefgMCqoREHq07NFNt_0Ap6PV3-JKIzrLH_EwndF_2YrCHzYPYGZH6msSFT8Z0ceOVBC-EBSUOCwIZst_VbQvTK8ndSzcIyk4Iba5lW_GvndDQdj589wmfKzeULOXuVixBl2M7wRTHlc9BHmV0b8ODJDoGqouwiAw4v
  - **Quote**: "Mazda MX-5 MIATA (1990-1992) 14x5. 5 Aluminum Alloy Chrome 7 Spoke [64722]"
  
#### CATALYTIC_CONVERTERS

- **Value**: `1`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHJ8rdDTYEKmRLCiveQ72Z3cSInExmGpQn86BlxFQkNEoLBmvfFLvLGZn9aO4pIK06l24EjD_Xn_1lD5ouvFriNEXB01KVcpYarwCyet4nRikJxReHtoWMz_ZFZBbdyNX8WfzV3yWcqRi4FqZKfJKBL0x5bE-O9CWuRiZa1-pBvhxP0DJkdx29-jnigY80a
  - **Quote**: "This direct-fit catalytic converter is designed specifically for the 1990-1993 Mazda Miata."
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHT8ATR0mirufe7FqGMCEdIwnRtBIGtFTKXQCEmvLx8OL8lOSMZwFybaaREUwgkrb4259Vm2d9FxZ_rOWj9qAju0P9BMgdZJJzF64ry9um_eY5-OVgkjOykdUoBWjAsN8C6ruyYO3CUYQ7OImS2oVH6giAK9bSxsX5dPPrmIHc=
  - **Quote**: "As with all of our catalytic converters, this cat is emissions-certified. Specifically, it's EPA-approved for this application."
  
### Summary

- **Total Latency**: 10073.51ms (10.07 seconds)
- **Fields Resolved**: 4
- **Total Citations**: 6

---

## Example 2: 1998 BMW M3

### Input

- **Year**: 1998
- **Make**: BMW
- **Model**: M3
- **Vehicle Key**: `1998_bmw_m3`
- **Timestamp**: 2025-11-06T10:24:04.434936

### Database Check

Database check failed: DATABASE_URL environment variable is required. Please set DATABASE_URL in your Streamlit Cloud secrets or environment variables. Example: DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require

### Prompt Sent to API

**Length**: 1149 characters

```
Find specs for 1998 BMW M3. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value based on available data - use base trim if identifiable, or most common value)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely and sensible number)

SOURCES: Use any available sources (mark "oem" for manufacturer sites, "secondary" for others). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

IMPORTANT: If the vehicle does not appear to exist or cannot be verified, set status to "not_found" for all fields and return null values.

RETURN JSON:
{
  "curb_weight": {"value": 3310, "unit": "lbs", "status": "found", "citations": [{"url": "...", "quote": "...", "source_type": "oem"}]},
  "aluminum_engine": {"value": true, "status": "found", "citations": [...]},
  "aluminum_rims": {"value": true, "status": "found", "citations": [...]},
  "catalytic_converters": {"value": 2, "status": "found", "citations": [...]}
}
```

### API Configuration

```json
{
  "model": "gemini-2.0-flash-exp",
  "tools": [
    {
      "google_search": {}
    }
  ],
  "temperature": 0
}
```

### Raw API Response

**Duration**: 10214.48ms (10.21 seconds)
**Length**: 3035 characters
**Markdown Wrapper**: Yes

```
```json
{
  "curb_weight": {
    "value": 3491,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8zwoMCRhU6M3TtBzANcl7ysmLtodaRfPIi3P1Oa-HLt9Bg_nP0YbElWjGD3e-X_PPe9u_ywH2v7tNeJZzUdTNnISepRsGUJSFpN4B_7mU2k1NW8lz7B3g4aVa9HQI2-JelfhqkA==",
        "quote": "CURB WEIGHT: 3,491 lbs.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHQ6oFn1lstrMcR3hC8WmadZBBl3Eou-J1z30bbACKUtE1h4ySVlslZC74aUmlc4ER8Wbe7D7fMMqbD4lxhflHHOjYcAPCzMsDaH10YtYUCjIdEIYpfAg53EzldRLV47oa5HKXp5vWDXVUmRk6XbXERq-wZWDJCW6vzGG6le1SeI7zCHTnasxtOfGE_vdHdGFlj51CTqg==",
        "quote": "Material: Forged aluminum JE Pistons are known for their high-quality forged aluminum construction.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnQyqAqpghsTL9QtZrdAYkjUzdOIQ7RndrUDUnx8UlTX5aeF1UNp47qTnfEdU4Lr1i1nuuvEacAXJxACujVUbC7UG5UyGyJqUjkTPQfEBybo4rfw1YYYJioKodzZ1pKp2oSNxxq9JHaKOdPkYzNlcSmHDN",
        "quote": "BMW Wheels can have different types and finishes. The type can either be in Aluminum Alloy, or Steel",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGSoJR108BrU7pSjmXYHBJGtCoR2dE7uVmm7eYaCEpaP15POX7Tl7rosnXjWq9Z7kZFi-8LF8x9ko0ruA8kZ515riO2djy6xPF6biRXxzrwIYv77HQdX23H4S7n_1kMeMJi6qyzAPiNK3r1pCligEEAs3exKngTDW8U9mJ3",
        "quote": "APEX light alloy wheels are the next evolution in flow-forged wheel technology for BMWs.",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 2,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH3SvGPzLm2gbtHRwIiB3K8CSMhkV350302n7Vivt32QcPNr6gQPEdBeY6OzMlt6-idtgJQH5zAAwZOpSaTaZGg8XbemKYGbq6gRWkMi5o5o-6rsCrHbScejfcqDID-QEUYOolSEZ41x1lh8AvQSXdVRIx0n9ZFo7JT-StlNcxXzzI=",
        "quote": "Need a replacement catalytic converter for your 1998 BMW M3? MagnaFlow offers high-quality catalytic converters engineered for 1998 BMW M3 sub-models and engine sizes.",
        "source_type": "secondary"
      },
       {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE7ta5DiPQc-8Jb4NKGz11kJ0PuFa8QWiZH1GZbK8ajCqGHremUySRKIwupU4YhvE1s0vzxATVbpj0G2IRz0DsH8qIjUEmxwd16SzlzsdwccdMcw-E8V2TS8l2-U_QMafHXQa-3CThO2eRuO2YmDv0_6vj86VnQgoZc6GlZZCUDvVsp7QvhbV5_k60=",
        "quote": "Our Catalytic Converters are the same quality construction as OEM but at a third of the cost! These are a direct replacement for the original BMW catalytic converter.",
        "source_type": "secondary"
      }
    ]
  }
}
```
```

### Parsed JSON Response

```json
{
  "curb_weight": {
    "value": 3491,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8zwoMCRhU6M3TtBzANcl7ysmLtodaRfPIi3P1Oa-HLt9Bg_nP0YbElWjGD3e-X_PPe9u_ywH2v7tNeJZzUdTNnISepRsGUJSFpN4B_7mU2k1NW8lz7B3g4aVa9HQI2-JelfhqkA==",
        "quote": "CURB WEIGHT: 3,491 lbs.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHQ6oFn1lstrMcR3hC8WmadZBBl3Eou-J1z30bbACKUtE1h4ySVlslZC74aUmlc4ER8Wbe7D7fMMqbD4lxhflHHOjYcAPCzMsDaH10YtYUCjIdEIYpfAg53EzldRLV47oa5HKXp5vWDXVUmRk6XbXERq-wZWDJCW6vzGG6le1SeI7zCHTnasxtOfGE_vdHdGFlj51CTqg==",
        "quote": "Material: Forged aluminum JE Pistons are known for their high-quality forged aluminum construction.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnQyqAqpghsTL9QtZrdAYkjUzdOIQ7RndrUDUnx8UlTX5aeF1UNp47qTnfEdU4Lr1i1nuuvEacAXJxACujVUbC7UG5UyGyJqUjkTPQfEBybo4rfw1YYYJioKodzZ1pKp2oSNxxq9JHaKOdPkYzNlcSmHDN",
        "quote": "BMW Wheels can have different types and finishes. The type can either be in Aluminum Alloy, or Steel",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGSoJR108BrU7pSjmXYHBJGtCoR2dE7uVmm7eYaCEpaP15POX7Tl7rosnXjWq9Z7kZFi-8LF8x9ko0ruA8kZ515riO2djy6xPF6biRXxzrwIYv77HQdX23H4S7n_1kMeMJi6qyzAPiNK3r1pCligEEAs3exKngTDW8U9mJ3",
        "quote": "APEX light alloy wheels are the next evolution in flow-forged wheel technology for BMWs.",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 2,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH3SvGPzLm2gbtHRwIiB3K8CSMhkV350302n7Vivt32QcPNr6gQPEdBeY6OzMlt6-idtgJQH5zAAwZOpSaTaZGg8XbemKYGbq6gRWkMi5o5o-6rsCrHbScejfcqDID-QEUYOolSEZ41x1lh8AvQSXdVRIx0n9ZFo7JT-StlNcxXzzI=",
        "quote": "Need a replacement catalytic converter for your 1998 BMW M3? MagnaFlow offers high-quality catalytic converters engineered for 1998 BMW M3 sub-models and engine sizes.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE7ta5DiPQc-8Jb4NKGz11kJ0PuFa8QWiZH1GZbK8ajCqGHremUySRKIwupU4YhvE1s0vzxATVbpj0G2IRz0DsH8qIjUEmxwd16SzlzsdwccdMcw-E8V2TS8l2-U_QMafHXQa-3CThO2eRuO2YmDv0_6vj86VnQgoZc6GlZZCUDvVsp7QvhbV5_k60=",
        "quote": "Our Catalytic Converters are the same quality construction as OEM but at a third of the cost! These are a direct replacement for the original BMW catalytic converter.",
        "source_type": "secondary"
      }
    ]
  }
}
```

### Validated & Normalized Results

#### CURB_WEIGHT

- **Value**: `3491.0`
- **Status**: `found`
- **Confidence**: `0.70`
- **Unit**: `lbs`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8zwoMCRhU6M3TtBzANcl7ysmLtodaRfPIi3P1Oa-HLt9Bg_nP0YbElWjGD3e-X_PPe9u_ywH2v7tNeJZzUdTNnISepRsGUJSFpN4B_7mU2k1NW8lz7B3g4aVa9HQI2-JelfhqkA==
  - **Quote**: "CURB WEIGHT: 3,491 lbs."
  
#### ALUMINUM_ENGINE

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.70`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHQ6oFn1lstrMcR3hC8WmadZBBl3Eou-J1z30bbACKUtE1h4ySVlslZC74aUmlc4ER8Wbe7D7fMMqbD4lxhflHHOjYcAPCzMsDaH10YtYUCjIdEIYpfAg53EzldRLV47oa5HKXp5vWDXVUmRk6XbXERq-wZWDJCW6vzGG6le1SeI7zCHTnasxtOfGE_vdHdGFlj51CTqg==
  - **Quote**: "Material: Forged aluminum JE Pistons are known for their high-quality forged aluminum construction."
  
#### ALUMINUM_RIMS

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnQyqAqpghsTL9QtZrdAYkjUzdOIQ7RndrUDUnx8UlTX5aeF1UNp47qTnfEdU4Lr1i1nuuvEacAXJxACujVUbC7UG5UyGyJqUjkTPQfEBybo4rfw1YYYJioKodzZ1pKp2oSNxxq9JHaKOdPkYzNlcSmHDN
  - **Quote**: "BMW Wheels can have different types and finishes. The type can either be in Aluminum Alloy, or Steel"
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGSoJR108BrU7pSjmXYHBJGtCoR2dE7uVmm7eYaCEpaP15POX7Tl7rosnXjWq9Z7kZFi-8LF8x9ko0ruA8kZ515riO2djy6xPF6biRXxzrwIYv77HQdX23H4S7n_1kMeMJi6qyzAPiNK3r1pCligEEAs3exKngTDW8U9mJ3
  - **Quote**: "APEX light alloy wheels are the next evolution in flow-forged wheel technology for BMWs."
  
#### CATALYTIC_CONVERTERS

- **Value**: `2`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH3SvGPzLm2gbtHRwIiB3K8CSMhkV350302n7Vivt32QcPNr6gQPEdBeY6OzMlt6-idtgJQH5zAAwZOpSaTaZGg8XbemKYGbq6gRWkMi5o5o-6rsCrHbScejfcqDID-QEUYOolSEZ41x1lh8AvQSXdVRIx0n9ZFo7JT-StlNcxXzzI=
  - **Quote**: "Need a replacement catalytic converter for your 1998 BMW M3? MagnaFlow offers high-quality catalytic converters engineered for 1998 BMW M3 sub-models and engine sizes."
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE7ta5DiPQc-8Jb4NKGz11kJ0PuFa8QWiZH1GZbK8ajCqGHremUySRKIwupU4YhvE1s0vzxATVbpj0G2IRz0DsH8qIjUEmxwd16SzlzsdwccdMcw-E8V2TS8l2-U_QMafHXQa-3CThO2eRuO2YmDv0_6vj86VnQgoZc6GlZZCUDvVsp7QvhbV5_k60=
  - **Quote**: "Our Catalytic Converters are the same quality construction as OEM but at a third of the cost! These are a direct replacement for the original BMW catalytic converter."
  
### Summary

- **Total Latency**: 10214.48ms (10.21 seconds)
- **Fields Resolved**: 4
- **Total Citations**: 6

---

## Example 3: 2001 Audi TT

### Input

- **Year**: 2001
- **Make**: Audi
- **Model**: TT
- **Vehicle Key**: `2001_audi_tt`
- **Timestamp**: 2025-11-06T10:24:17.650298

### Database Check

Database check failed: DATABASE_URL environment variable is required. Please set DATABASE_URL in your Streamlit Cloud secrets or environment variables. Example: DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require

### Prompt Sent to API

**Length**: 1150 characters

```
Find specs for 2001 Audi TT. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value based on available data - use base trim if identifiable, or most common value)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely and sensible number)

SOURCES: Use any available sources (mark "oem" for manufacturer sites, "secondary" for others). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

IMPORTANT: If the vehicle does not appear to exist or cannot be verified, set status to "not_found" for all fields and return null values.

RETURN JSON:
{
  "curb_weight": {"value": 3310, "unit": "lbs", "status": "found", "citations": [{"url": "...", "quote": "...", "source_type": "oem"}]},
  "aluminum_engine": {"value": true, "status": "found", "citations": [...]},
  "aluminum_rims": {"value": true, "status": "found", "citations": [...]},
  "catalytic_converters": {"value": 2, "status": "found", "citations": [...]}
}
```

### API Configuration

```json
{
  "model": "gemini-2.0-flash-exp",
  "tools": [
    {
      "google_search": {}
    }
  ],
  "temperature": 0
}
```

### Raw API Response

**Duration**: 9667.15ms (9.67 seconds)
**Length**: 2596 characters
**Markdown Wrapper**: Yes

```
```json
{
  "curb_weight": {
    "value": 3123,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-UqbCOTrzIkEVJbZRIKsUbE9e93bERkbcy8au_se-F7-S1xqbl9DPzPivZWnyK0ef6rRpsoAyCeaEuC3BCK5EV8lXYWBuVP2ocTcuM5YYbwD-lmDesiUENYdZ4Gdf-tXUcGKPSHKYUVyIL4r8SalEfUqeBCHdBGcc7sElDuY0QM6EjilGvT7iwjXzvfBX20t7iHGiuA==",
        "quote": "Curb weight: 3123 lb.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-UqbCOTrzIkEVJbZRIKsUbE9e93bERkbcy8au_se-F7-S1xqbl9DPzPivZWnyK0ef6rRpsoAyCeaEuC3BCK5EV8lXYWBuVP2ocTcuM5YYbwD-lmDesiUENYdZ4Gdf-tXUcGKPSHKYUVyIL4r8SalEfUqeBCHdBGcc7sElDuY0QM6EjilGvT7iwjXzvfBX20t7iHGiuA==",
        "quote": "ENGINE TYPE:turbocharged DOHC 20-valve 4-in-line, iron block and aluminum head",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH4haPPeayb5d0Y3it5501UoJUsCg9TQoWLq50SqumrHhauTI5SrwAS0Lce2tHqJIE_XvQ4TtqaTWauhseX5_QIJIIimr-kRD7YFf5JzK-J0ueBcJ31KzMealJ-0F6xuiysVMH4d2wbBjWfHV4=",
        "quote": "Spare Wheel Material. Alloy.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH115dF0j9ka0vrYnMiwW69nB9qta1deEl8LxOzJlyn16wZrxc_SVHDbA96pTADWsj2dT00GbrLEetBBv9a6-sLFl8w9E7hpQSwGBi08UxM40MD2MA3MuGjZv_KduODCIMwfhzLPqREU84sE-lgg1sjS8PJ2v_ljOXxJqp9x_eNx3SM7UlGrkqHzyy80seXuoryRdYQpmLT-1Zrgjs=",
        "quote": "Buy Factory Replacment Alloy Wheels for your Audi TT 2000, 2001, 2002, 2003, 2004, 2005, 2006. Size 17x7.5 Style 5 Spoke. SKU 58726.LS20.POL is a Genuine Audi TT Aluminum Wheel.",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 1,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2I5h2OTfh-ymB6F8uXTM1AgBRyXPCMm50iVSbOo4aeYHoKR9d5gJR-w4XcSHU3xn-vwK7z9wHqVFDMSCmindwJUpjhuiCZcUbVMXg15eyVhGRHS8_YKaCESfI8C9dy4JXnBrf5HVW2OHxqiv67tSe3S5kzSf1VlucpOahtHcoct2XlTiU",
        "quote": "Audi TT Catalytic Converter fits all front wheel drive TT models with 1.8L turbocharged engine from 2000 through to 2006 with 2 O2 sensor ports.",
        "source_type": "secondary"
      }
    ]
  }
}
```
```

### Parsed JSON Response

```json
{
  "curb_weight": {
    "value": 3123,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-UqbCOTrzIkEVJbZRIKsUbE9e93bERkbcy8au_se-F7-S1xqbl9DPzPivZWnyK0ef6rRpsoAyCeaEuC3BCK5EV8lXYWBuVP2ocTcuM5YYbwD-lmDesiUENYdZ4Gdf-tXUcGKPSHKYUVyIL4r8SalEfUqeBCHdBGcc7sElDuY0QM6EjilGvT7iwjXzvfBX20t7iHGiuA==",
        "quote": "Curb weight: 3123 lb.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-UqbCOTrzIkEVJbZRIKsUbE9e93bERkbcy8au_se-F7-S1xqbl9DPzPivZWnyK0ef6rRpsoAyCeaEuC3BCK5EV8lXYWBuVP2ocTcuM5YYbwD-lmDesiUENYdZ4Gdf-tXUcGKPSHKYUVyIL4r8SalEfUqeBCHdBGcc7sElDuY0QM6EjilGvT7iwjXzvfBX20t7iHGiuA==",
        "quote": "ENGINE TYPE:turbocharged DOHC 20-valve 4-in-line, iron block and aluminum head",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH4haPPeayb5d0Y3it5501UoJUsCg9TQoWLq50SqumrHhauTI5SrwAS0Lce2tHqJIE_XvQ4TtqaTWauhseX5_QIJIIimr-kRD7YFf5JzK-J0ueBcJ31KzMealJ-0F6xuiysVMH4d2wbBjWfHV4=",
        "quote": "Spare Wheel Material. Alloy.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH115dF0j9ka0vrYnMiwW69nB9qta1deEl8LxOzJlyn16wZrxc_SVHDbA96pTADWsj2dT00GbrLEetBBv9a6-sLFl8w9E7hpQSwGBi08UxM40MD2MA3MuGjZv_KduODCIMwfhzLPqREU84sE-lgg1sjS8PJ2v_ljOXxJqp9x_eNx3SM7UlGrkqHzyy80seXuoryRdYQpmLT-1Zrgjs=",
        "quote": "Buy Factory Replacment Alloy Wheels for your Audi TT 2000, 2001, 2002, 2003, 2004, 2005, 2006. Size 17x7.5 Style 5 Spoke. SKU 58726.LS20.POL is a Genuine Audi TT Aluminum Wheel.",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 1,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2I5h2OTfh-ymB6F8uXTM1AgBRyXPCMm50iVSbOo4aeYHoKR9d5gJR-w4XcSHU3xn-vwK7z9wHqVFDMSCmindwJUpjhuiCZcUbVMXg15eyVhGRHS8_YKaCESfI8C9dy4JXnBrf5HVW2OHxqiv67tSe3S5kzSf1VlucpOahtHcoct2XlTiU",
        "quote": "Audi TT Catalytic Converter fits all front wheel drive TT models with 1.8L turbocharged engine from 2000 through to 2006 with 2 O2 sensor ports.",
        "source_type": "secondary"
      }
    ]
  }
}
```

### Validated & Normalized Results

#### CURB_WEIGHT

- **Value**: `3123.0`
- **Status**: `found`
- **Confidence**: `0.70`
- **Unit**: `lbs`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-UqbCOTrzIkEVJbZRIKsUbE9e93bERkbcy8au_se-F7-S1xqbl9DPzPivZWnyK0ef6rRpsoAyCeaEuC3BCK5EV8lXYWBuVP2ocTcuM5YYbwD-lmDesiUENYdZ4Gdf-tXUcGKPSHKYUVyIL4r8SalEfUqeBCHdBGcc7sElDuY0QM6EjilGvT7iwjXzvfBX20t7iHGiuA==
  - **Quote**: "Curb weight: 3123 lb."
  
#### ALUMINUM_ENGINE

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.70`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-UqbCOTrzIkEVJbZRIKsUbE9e93bERkbcy8au_se-F7-S1xqbl9DPzPivZWnyK0ef6rRpsoAyCeaEuC3BCK5EV8lXYWBuVP2ocTcuM5YYbwD-lmDesiUENYdZ4Gdf-tXUcGKPSHKYUVyIL4r8SalEfUqeBCHdBGcc7sElDuY0QM6EjilGvT7iwjXzvfBX20t7iHGiuA==
  - **Quote**: "ENGINE TYPE:turbocharged DOHC 20-valve 4-in-line, iron block and aluminum head"
  
#### ALUMINUM_RIMS

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH4haPPeayb5d0Y3it5501UoJUsCg9TQoWLq50SqumrHhauTI5SrwAS0Lce2tHqJIE_XvQ4TtqaTWauhseX5_QIJIIimr-kRD7YFf5JzK-J0ueBcJ31KzMealJ-0F6xuiysVMH4d2wbBjWfHV4=
  - **Quote**: "Spare Wheel Material. Alloy."
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH115dF0j9ka0vrYnMiwW69nB9qta1deEl8LxOzJlyn16wZrxc_SVHDbA96pTADWsj2dT00GbrLEetBBv9a6-sLFl8w9E7hpQSwGBi08UxM40MD2MA3MuGjZv_KduODCIMwfhzLPqREU84sE-lgg1sjS8PJ2v_ljOXxJqp9x_eNx3SM7UlGrkqHzyy80seXuoryRdYQpmLT-1Zrgjs=
  - **Quote**: "Buy Factory Replacment Alloy Wheels for your Audi TT 2000, 2001, 2002, 2003, 2004, 2005, 2006. Size 17x7.5 Style 5 Spoke. SKU 58726.LS20.POL is a Genuine Audi TT Aluminum Wheel."
  
#### CATALYTIC_CONVERTERS

- **Value**: `1`
- **Status**: `found`
- **Confidence**: `0.70`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2I5h2OTfh-ymB6F8uXTM1AgBRyXPCMm50iVSbOo4aeYHoKR9d5gJR-w4XcSHU3xn-vwK7z9wHqVFDMSCmindwJUpjhuiCZcUbVMXg15eyVhGRHS8_YKaCESfI8C9dy4JXnBrf5HVW2OHxqiv67tSe3S5kzSf1VlucpOahtHcoct2XlTiU
  - **Quote**: "Audi TT Catalytic Converter fits all front wheel drive TT models with 1.8L turbocharged engine from 2000 through to 2006 with 2 O2 sensor ports."
  
### Summary

- **Total Latency**: 9667.15ms (9.67 seconds)
- **Fields Resolved**: 4
- **Total Citations**: 5

---

## Example 4: 2005 Subaru WRX

### Input

- **Year**: 2005
- **Make**: Subaru
- **Model**: WRX
- **Vehicle Key**: `2005_subaru_wrx`
- **Timestamp**: 2025-11-06T10:24:30.318796

### Database Check

Database check failed: DATABASE_URL environment variable is required. Please set DATABASE_URL in your Streamlit Cloud secrets or environment variables. Example: DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require

### Prompt Sent to API

**Length**: 1153 characters

```
Find specs for 2005 Subaru WRX. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value based on available data - use base trim if identifiable, or most common value)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely and sensible number)

SOURCES: Use any available sources (mark "oem" for manufacturer sites, "secondary" for others). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

IMPORTANT: If the vehicle does not appear to exist or cannot be verified, set status to "not_found" for all fields and return null values.

RETURN JSON:
{
  "curb_weight": {"value": 3310, "unit": "lbs", "status": "found", "citations": [{"url": "...", "quote": "...", "source_type": "oem"}]},
  "aluminum_engine": {"value": true, "status": "found", "citations": [...]},
  "aluminum_rims": {"value": true, "status": "found", "citations": [...]},
  "catalytic_converters": {"value": 2, "status": "found", "citations": [...]}
}
```

### API Configuration

```json
{
  "model": "gemini-2.0-flash-exp",
  "tools": [
    {
      "google_search": {}
    }
  ],
  "temperature": 0
}
```

### Raw API Response

**Duration**: 12674.16ms (12.67 seconds)
**Length**: 3392 characters
**Markdown Wrapper**: Yes

```
```json
{
  "curb_weight": {
    "value": 3020,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEMhRxqc6Aizm31GvUq8JGahEV0dO1H6yazs41jMtu51h1-Ho1qtMeOANQOLco8M198UcxYJFpWgpQsJ0GsRMtpgrLo6J2WmKsSXBHJvu_t0wyaCs-SGzyCLfrHGqXcHEZL1zKM7ginG-iFMwhyN5fAc_LE5cs4wA3Y34znv-5xX7mVQdeo44wSIPFK6btM",
        "quote": "What is the curb weight, 2005 Subaru Impreza II (facelift 2005) WRX 2.5 (230 Hp) AWD? ... 3020.33 lbs.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE4Ws3wIl8dtoT1_Ho_1ID5YB0Ou-n9FwvLr2vVpL1vd8054_q1OOqIBYrbqfNYD_T4OMxHWBFk6ZSdgEIxwyCulJKKDwhFVwisOhDOmH6rJKiCtkbQxCkm7p7aCV4=",
        "quote": "Cylinder Block Material, Aluminum. Cylinder Head Material, Aluminum.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEdrzbcS_1jldnKjlttJ07wq977_gliVaazDQ5_sLlXBmjuUMbOZ37j8IhHjdHhi3d8e1SImA4nxaMmuOuaWwElJT72Z4wo8ieaLzPE4_LFNprJ-693K23QUpI1uD46c5-QoscMkefdWtFXvUZ0RnZ5qWD_CJkhsEURzdilqKxw46gbz5RjYZClKw1NZjKNG70YNLsVOm5gX17O2_fn",
        "quote": "Subaru WRX 16x6. 5 OEM Alloy Rim 2002-2005 A. 68721. LS01. FF",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFHsPIXPxNhhd72qAi_unpB4pzWMC1OIjCaLC2rXUc67fCq0eiY9MxDcY0xedIHmA3UCnqrnqI5iy4Z9PlN3v3QXj033ioOrtIR7g7_zGKRHSK0v1W1gvHoSimdLzoHLVGtsYHOPGSPHVwJhxi3kw5aH2EFhd4sLQo=",
        "quote": "Front tyre size 215/45 R17. Rear tyre size 215/45 R17.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFMsR0YRUezzcAZ8lGwHA18xwWWvCsNW02YgeJ0Qf7aE63TTkrGAkxIr_SpynfVVMgBl1Iw65vGcJD6Cbh8oik-ay13WcNH9K5hcEWvgr2W07hpssiQfgel4wwQlS9MekNZf65OhASHcEYZOHwPgIEusK5nIaHXVA==",
        "quote": "Rims. 17\" alloy wheels.",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 2,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGm7KG0pixOqsyN25w6ynbgWYhXzgSF5c8BaEOqAMLI_aefHswEDmOJbLJyF8C9mLnEfGkLH9OAKbk73aiMaLIvzzbDGUx9VGdHf2Eeq2VeYvmJeV6CpsRFjZtLgj98UyxE9uzDk9nkObad5rOgRLVOaOVGODHgbuV8VvUIP79fVnFlB17rO8MHnGVckzjWk7E6krnLjpsIfpQH7k4FjQ==",
        "quote": "Catalytic Converter 2004-2007 Subaru Impreza WRX STI 2.5L Turbo / Rear.",
        "source_type": "secondary"
      },
       {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFLSJeIoE8QPrAbUCxI0XAuHCp44uX2EdfBeJ0GR5PhlJtF2QVHOLWscIqMS5bRQ34_6Wnr3uvDM8v1yN49Y9BBVyQGH4K8vVu-6lfn7dHbws8iHB4j9ABG0MJ6Y0PSxNcf_1nTq3JKzGUUeCENmYGzPEepxgtqK5iljvoJih_cVV1_o1RR-ZFaUFwr_dOJgA_cxKdhDRqvvEgNBbyTZiIOeVcT3NM7L9-TVdczgX55VPcEy6b-i8HM8e-JnUNqf1oYbPrwSfyf2B_2BsGdgkUtBw==",
        "quote": "2002-2003 SUBARU IMPREZA WRX 2.0L | 2004-2005 WRX Sti 2.5L | Rear | Catalytic Converter-Direct Fit | California Legal | EO# D-193-96.",
        "source_type": "secondary"
      }
    ]
  }
}
```
```

### Parsed JSON Response

```json
{
  "curb_weight": {
    "value": 3020,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEMhRxqc6Aizm31GvUq8JGahEV0dO1H6yazs41jMtu51h1-Ho1qtMeOANQOLco8M198UcxYJFpWgpQsJ0GsRMtpgrLo6J2WmKsSXBHJvu_t0wyaCs-SGzyCLfrHGqXcHEZL1zKM7ginG-iFMwhyN5fAc_LE5cs4wA3Y34znv-5xX7mVQdeo44wSIPFK6btM",
        "quote": "What is the curb weight, 2005 Subaru Impreza II (facelift 2005) WRX 2.5 (230 Hp) AWD? ... 3020.33 lbs.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE4Ws3wIl8dtoT1_Ho_1ID5YB0Ou-n9FwvLr2vVpL1vd8054_q1OOqIBYrbqfNYD_T4OMxHWBFk6ZSdgEIxwyCulJKKDwhFVwisOhDOmH6rJKiCtkbQxCkm7p7aCV4=",
        "quote": "Cylinder Block Material, Aluminum. Cylinder Head Material, Aluminum.",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEdrzbcS_1jldnKjlttJ07wq977_gliVaazDQ5_sLlXBmjuUMbOZ37j8IhHjdHhi3d8e1SImA4nxaMmuOuaWwElJT72Z4wo8ieaLzPE4_LFNprJ-693K23QUpI1uD46c5-QoscMkefdWtFXvUZ0RnZ5qWD_CJkhsEURzdilqKxw46gbz5RjYZClKw1NZjKNG70YNLsVOm5gX17O2_fn",
        "quote": "Subaru WRX 16x6. 5 OEM Alloy Rim 2002-2005 A. 68721. LS01. FF",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFHsPIXPxNhhd72qAi_unpB4pzWMC1OIjCaLC2rXUc67fCq0eiY9MxDcY0xedIHmA3UCnqrnqI5iy4Z9PlN3v3QXj033ioOrtIR7g7_zGKRHSK0v1W1gvHoSimdLzoHLVGtsYHOPGSPHVwJhxi3kw5aH2EFhd4sLQo=",
        "quote": "Front tyre size 215/45 R17. Rear tyre size 215/45 R17.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFMsR0YRUezzcAZ8lGwHA18xwWWvCsNW02YgeJ0Qf7aE63TTkrGAkxIr_SpynfVVMgBl1Iw65vGcJD6Cbh8oik-ay13WcNH9K5hcEWvgr2W07hpssiQfgel4wwQlS9MekNZf65OhASHcEYZOHwPgIEusK5nIaHXVA==",
        "quote": "Rims. 17\" alloy wheels.",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 2,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGm7KG0pixOqsyN25w6ynbgWYhXzgSF5c8BaEOqAMLI_aefHswEDmOJbLJyF8C9mLnEfGkLH9OAKbk73aiMaLIvzzbDGUx9VGdHf2Eeq2VeYvmJeV6CpsRFjZtLgj98UyxE9uzDk9nkObad5rOgRLVOaOVGODHgbuV8VvUIP79fVnFlB17rO8MHnGVckzjWk7E6krnLjpsIfpQH7k4FjQ==",
        "quote": "Catalytic Converter 2004-2007 Subaru Impreza WRX STI 2.5L Turbo / Rear.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFLSJeIoE8QPrAbUCxI0XAuHCp44uX2EdfBeJ0GR5PhlJtF2QVHOLWscIqMS5bRQ34_6Wnr3uvDM8v1yN49Y9BBVyQGH4K8vVu-6lfn7dHbws8iHB4j9ABG0MJ6Y0PSxNcf_1nTq3JKzGUUeCENmYGzPEepxgtqK5iljvoJih_cVV1_o1RR-ZFaUFwr_dOJgA_cxKdhDRqvvEgNBbyTZiIOeVcT3NM7L9-TVdczgX55VPcEy6b-i8HM8e-JnUNqf1oYbPrwSfyf2B_2BsGdgkUtBw==",
        "quote": "2002-2003 SUBARU IMPREZA WRX 2.0L | 2004-2005 WRX Sti 2.5L | Rear | Catalytic Converter-Direct Fit | California Legal | EO# D-193-96.",
        "source_type": "secondary"
      }
    ]
  }
}
```

### Validated & Normalized Results

#### CURB_WEIGHT

- **Value**: `3020.0`
- **Status**: `found`
- **Confidence**: `0.70`
- **Unit**: `lbs`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEMhRxqc6Aizm31GvUq8JGahEV0dO1H6yazs41jMtu51h1-Ho1qtMeOANQOLco8M198UcxYJFpWgpQsJ0GsRMtpgrLo6J2WmKsSXBHJvu_t0wyaCs-SGzyCLfrHGqXcHEZL1zKM7ginG-iFMwhyN5fAc_LE5cs4wA3Y34znv-5xX7mVQdeo44wSIPFK6btM
  - **Quote**: "What is the curb weight, 2005 Subaru Impreza II (facelift 2005) WRX 2.5 (230 Hp) AWD? ... 3020.33 lbs."
  
#### ALUMINUM_ENGINE

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.70`
- **Citations**: 1

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE4Ws3wIl8dtoT1_Ho_1ID5YB0Ou-n9FwvLr2vVpL1vd8054_q1OOqIBYrbqfNYD_T4OMxHWBFk6ZSdgEIxwyCulJKKDwhFVwisOhDOmH6rJKiCtkbQxCkm7p7aCV4=
  - **Quote**: "Cylinder Block Material, Aluminum. Cylinder Head Material, Aluminum."
  
#### ALUMINUM_RIMS

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 3

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEdrzbcS_1jldnKjlttJ07wq977_gliVaazDQ5_sLlXBmjuUMbOZ37j8IhHjdHhi3d8e1SImA4nxaMmuOuaWwElJT72Z4wo8ieaLzPE4_LFNprJ-693K23QUpI1uD46c5-QoscMkefdWtFXvUZ0RnZ5qWD_CJkhsEURzdilqKxw46gbz5RjYZClKw1NZjKNG70YNLsVOm5gX17O2_fn
  - **Quote**: "Subaru WRX 16x6. 5 OEM Alloy Rim 2002-2005 A. 68721. LS01. FF"
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFHsPIXPxNhhd72qAi_unpB4pzWMC1OIjCaLC2rXUc67fCq0eiY9MxDcY0xedIHmA3UCnqrnqI5iy4Z9PlN3v3QXj033ioOrtIR7g7_zGKRHSK0v1W1gvHoSimdLzoHLVGtsYHOPGSPHVwJhxi3kw5aH2EFhd4sLQo=
  - **Quote**: "Front tyre size 215/45 R17. Rear tyre size 215/45 R17."
  
  **Citation 3** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFMsR0YRUezzcAZ8lGwHA18xwWWvCsNW02YgeJ0Qf7aE63TTkrGAkxIr_SpynfVVMgBl1Iw65vGcJD6Cbh8oik-ay13WcNH9K5hcEWvgr2W07hpssiQfgel4wwQlS9MekNZf65OhASHcEYZOHwPgIEusK5nIaHXVA==
  - **Quote**: "Rims. 17" alloy wheels."
  
#### CATALYTIC_CONVERTERS

- **Value**: `2`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGm7KG0pixOqsyN25w6ynbgWYhXzgSF5c8BaEOqAMLI_aefHswEDmOJbLJyF8C9mLnEfGkLH9OAKbk73aiMaLIvzzbDGUx9VGdHf2Eeq2VeYvmJeV6CpsRFjZtLgj98UyxE9uzDk9nkObad5rOgRLVOaOVGODHgbuV8VvUIP79fVnFlB17rO8MHnGVckzjWk7E6krnLjpsIfpQH7k4FjQ==
  - **Quote**: "Catalytic Converter 2004-2007 Subaru Impreza WRX STI 2.5L Turbo / Rear."
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFLSJeIoE8QPrAbUCxI0XAuHCp44uX2EdfBeJ0GR5PhlJtF2QVHOLWscIqMS5bRQ34_6Wnr3uvDM8v1yN49Y9BBVyQGH4K8vVu-6lfn7dHbws8iHB4j9ABG0MJ6Y0PSxNcf_1nTq3JKzGUUeCENmYGzPEepxgtqK5iljvoJih_cVV1_o1RR-ZFaUFwr_dOJgA_cxKdhDRqvvEgNBbyTZiIOeVcT3NM7L9-TVdczgX55VPcEy6b-i8HM8e-JnUNqf1oYbPrwSfyf2B_2BsGdgkUtBw==
  - **Quote**: "2002-2003 SUBARU IMPREZA WRX 2.0L | 2004-2005 WRX Sti 2.5L | Rear | Catalytic Converter-Direct Fit | California Legal | EO# D-193-96."
  
### Summary

- **Total Latency**: 12674.16ms (12.67 seconds)
- **Fields Resolved**: 4
- **Total Citations**: 7

---

## Example 5: 2008 Nissan GT-R

### Input

- **Year**: 2008
- **Make**: Nissan
- **Model**: GT-R
- **Vehicle Key**: `2008_nissan_gt-r`
- **Timestamp**: 2025-11-06T10:24:45.993739

### Database Check

Database check failed: DATABASE_URL environment variable is required. Please set DATABASE_URL in your Streamlit Cloud secrets or environment variables. Example: DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require

### Prompt Sent to API

**Length**: 1154 characters

```
Find specs for 2008 Nissan GT-R. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value based on available data - use base trim if identifiable, or most common value)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely and sensible number)

SOURCES: Use any available sources (mark "oem" for manufacturer sites, "secondary" for others). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

IMPORTANT: If the vehicle does not appear to exist or cannot be verified, set status to "not_found" for all fields and return null values.

RETURN JSON:
{
  "curb_weight": {"value": 3310, "unit": "lbs", "status": "found", "citations": [{"url": "...", "quote": "...", "source_type": "oem"}]},
  "aluminum_engine": {"value": true, "status": "found", "citations": [...]},
  "aluminum_rims": {"value": true, "status": "found", "citations": [...]},
  "catalytic_converters": {"value": 2, "status": "found", "citations": [...]}
}
```

### API Configuration

```json
{
  "model": "gemini-2.0-flash-exp",
  "tools": [
    {
      "google_search": {}
    }
  ],
  "temperature": 0
}
```

### Raw API Response

**Duration**: 11131.01ms (11.13 seconds)
**Length**: 3061 characters
**Markdown Wrapper**: Yes

```
```json
{
  "curb_weight": {"value": 3836, "unit": "lbs", "status": "found", "citations": [{"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=", "quote": "2007–2009: 1,740 kg (3,836 lb)", "source_type": "secondary"}, {"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEn1rBEfzK942AR7jnAy6JyqMCjgUy2GbnXg2FyBBcNkRVQuQaZFi4Q3nN_uDXBwEFTStBI6n9VV_uJP09zPLC_ybLK_psVsNe34acUFdbshuT8bqk0K-sHwDvXzEWQRdaxdteqfY1bx-LbCPXd_MrrCSmiI_eL0w2e", "quote": "Kerb weight is 1740kg", "source_type": "secondary"}]},
  "aluminum_engine": {"value": true, "status": "found", "citations": [{"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=", "quote": "Aluminium cylinder block with high-endurance/low-friction plasma-sprayed bores.", "source_type": "secondary"}, {"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8VV9g_PtZ978n23pUzW9VMlnMomGAlI1DVxh7eCwpwzBr2Y-HAPUsIo6wqZnQbXVRSGDfGWIzosqj5Mx8bmWEcxVNPxEEN1qycQNJjqI0gM788Z-hwhcyKftqGuW5LY-cg9UjOBg6HZdilzYyA4Wgppou60vb8YM8-KxXJwbc66J-XRwQmg==", "quote": "block material, aluminium alloy", "source_type": "secondary"}]},
  "aluminum_rims": {"value": true, "status": "found", "citations": [{"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=", "quote": "new lightweight forged aluminium alloy wheels", "source_type": "secondary"}, {"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8VV9g_PtZ978n23pUzW9VMlnMomGAlI1DVxh7eCwpwzBr2Y-HAPUsIo6wqZnQbXVRSGDfGWIzosqj5Mx8bmWEcxVNPxEEN1qycQNJjqI0gM788Z-hwhcyKftqGuW5LY-cg9UjOBg6HZdilzYyA4Wgppou60vb8YM8-KxXJwbc66J-XRwQmg==", "quote": "rims material, aluminium alloy (forging)", "source_type": "secondary"}]},
  "catalytic_converters": {"value": 2, "status": "found", "citations": [{"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGKQThxOr4FgfLyjOdF-GdQsouhbBk9b0GeflfFOa44hxHG0dDmTs18lQfgQgV_cZPncsLkWUGxmshiNhGMus_D6UaKXh2Yvr7L9_wAC4fwJmFTPhtfx3agUPLAUhk5gCV5wTDGzgzw60ksXHIjr8ss3z4cD0sYc1nhWfp0qyicj470OfFrmmC1LS8qthpJDRI1oS74kdet_alFd-Y2SpA5R4dBXkJt0-kMj6MfxRKi", "quote": "OEM Nissan Catalytic Converter for the Passenger (Right) Side of the 2011-2021 Nissan GT-R (R35).", "source_type": "oem"}, {"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHi66YuJmaA2c8mBfvuIYcLenSj63GuuohBgKI_67Swd3WYnYl3NbV76esL7_dZkOdodvFWiTj6t5iCv2FvbHsYbnu82cu4Dg9-65B6QP6QzLNeGcRAFINNHEWxHTsyrb9bNmVRROdA-8AQI0Ua-KC3_iyc1cU2nfWZhTFJaGRKbdmQ7dfX0ebUHqo2PEQ=", "quote": "NISSAN GTR R35 EXHAUST CATALYTIC CONVERTERS 2009-2024 Midpipe Downpipe Set.", "source_type": "secondary"}]}
}
```
```

### Parsed JSON Response

```json
{
  "curb_weight": {
    "value": 3836,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=",
        "quote": "2007\u20132009: 1,740 kg (3,836 lb)",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEn1rBEfzK942AR7jnAy6JyqMCjgUy2GbnXg2FyBBcNkRVQuQaZFi4Q3nN_uDXBwEFTStBI6n9VV_uJP09zPLC_ybLK_psVsNe34acUFdbshuT8bqk0K-sHwDvXzEWQRdaxdteqfY1bx-LbCPXd_MrrCSmiI_eL0w2e",
        "quote": "Kerb weight is 1740kg",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=",
        "quote": "Aluminium cylinder block with high-endurance/low-friction plasma-sprayed bores.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8VV9g_PtZ978n23pUzW9VMlnMomGAlI1DVxh7eCwpwzBr2Y-HAPUsIo6wqZnQbXVRSGDfGWIzosqj5Mx8bmWEcxVNPxEEN1qycQNJjqI0gM788Z-hwhcyKftqGuW5LY-cg9UjOBg6HZdilzYyA4Wgppou60vb8YM8-KxXJwbc66J-XRwQmg==",
        "quote": "block material, aluminium alloy",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=",
        "quote": "new lightweight forged aluminium alloy wheels",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8VV9g_PtZ978n23pUzW9VMlnMomGAlI1DVxh7eCwpwzBr2Y-HAPUsIo6wqZnQbXVRSGDfGWIzosqj5Mx8bmWEcxVNPxEEN1qycQNJjqI0gM788Z-hwhcyKftqGuW5LY-cg9UjOBg6HZdilzYyA4Wgppou60vb8YM8-KxXJwbc66J-XRwQmg==",
        "quote": "rims material, aluminium alloy (forging)",
        "source_type": "secondary"
      }
    ]
  },
  "catalytic_converters": {
    "value": 2,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGKQThxOr4FgfLyjOdF-GdQsouhbBk9b0GeflfFOa44hxHG0dDmTs18lQfgQgV_cZPncsLkWUGxmshiNhGMus_D6UaKXh2Yvr7L9_wAC4fwJmFTPhtfx3agUPLAUhk5gCV5wTDGzgzw60ksXHIjr8ss3z4cD0sYc1nhWfp0qyicj470OfFrmmC1LS8qthpJDRI1oS74kdet_alFd-Y2SpA5R4dBXkJt0-kMj6MfxRKi",
        "quote": "OEM Nissan Catalytic Converter for the Passenger (Right) Side of the 2011-2021 Nissan GT-R (R35).",
        "source_type": "oem"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHi66YuJmaA2c8mBfvuIYcLenSj63GuuohBgKI_67Swd3WYnYl3NbV76esL7_dZkOdodvFWiTj6t5iCv2FvbHsYbnu82cu4Dg9-65B6QP6QzLNeGcRAFINNHEWxHTsyrb9bNmVRROdA-8AQI0Ua-KC3_iyc1cU2nfWZhTFJaGRKbdmQ7dfX0ebUHqo2PEQ=",
        "quote": "NISSAN GTR R35 EXHAUST CATALYTIC CONVERTERS 2009-2024 Midpipe Downpipe Set.",
        "source_type": "secondary"
      }
    ]
  }
}
```

### Validated & Normalized Results

#### CURB_WEIGHT

- **Value**: `3836.0`
- **Status**: `found`
- **Confidence**: `0.85`
- **Unit**: `lbs`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=
  - **Quote**: "2007–2009: 1,740 kg (3,836 lb)"
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEn1rBEfzK942AR7jnAy6JyqMCjgUy2GbnXg2FyBBcNkRVQuQaZFi4Q3nN_uDXBwEFTStBI6n9VV_uJP09zPLC_ybLK_psVsNe34acUFdbshuT8bqk0K-sHwDvXzEWQRdaxdteqfY1bx-LbCPXd_MrrCSmiI_eL0w2e
  - **Quote**: "Kerb weight is 1740kg"
  
#### ALUMINUM_ENGINE

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=
  - **Quote**: "Aluminium cylinder block with high-endurance/low-friction plasma-sprayed bores."
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8VV9g_PtZ978n23pUzW9VMlnMomGAlI1DVxh7eCwpwzBr2Y-HAPUsIo6wqZnQbXVRSGDfGWIzosqj5Mx8bmWEcxVNPxEEN1qycQNJjqI0gM788Z-hwhcyKftqGuW5LY-cg9UjOBg6HZdilzYyA4Wgppou60vb8YM8-KxXJwbc66J-XRwQmg==
  - **Quote**: "block material, aluminium alloy"
  
#### ALUMINUM_RIMS

- **Value**: `True`
- **Status**: `found`
- **Confidence**: `0.85`
- **Citations**: 2

  **Citation 1** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGRby52aNACG0NfkEsigivw9BtyWQzyZT_vQ_r9vNxYSh0ub8D1rEPqzr1m05gGs-xiESvLG7yfgC1y63mfE9TEt3_Wdah0thnd--pMkSkUxkEY78FbOzszcys7Q5Gdl_QnHWU=
  - **Quote**: "new lightweight forged aluminium alloy wheels"
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8VV9g_PtZ978n23pUzW9VMlnMomGAlI1DVxh7eCwpwzBr2Y-HAPUsIo6wqZnQbXVRSGDfGWIzosqj5Mx8bmWEcxVNPxEEN1qycQNJjqI0gM788Z-hwhcyKftqGuW5LY-cg9UjOBg6HZdilzYyA4Wgppou60vb8YM8-KxXJwbc66J-XRwQmg==
  - **Quote**: "rims material, aluminium alloy (forging)"
  
#### CATALYTIC_CONVERTERS

- **Value**: `2`
- **Status**: `found`
- **Confidence**: `0.95`
- **Citations**: 2

  **Citation 1** (OEM):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGKQThxOr4FgfLyjOdF-GdQsouhbBk9b0GeflfFOa44hxHG0dDmTs18lQfgQgV_cZPncsLkWUGxmshiNhGMus_D6UaKXh2Yvr7L9_wAC4fwJmFTPhtfx3agUPLAUhk5gCV5wTDGzgzw60ksXHIjr8ss3z4cD0sYc1nhWfp0qyicj470OfFrmmC1LS8qthpJDRI1oS74kdet_alFd-Y2SpA5R4dBXkJt0-kMj6MfxRKi
  - **Quote**: "OEM Nissan Catalytic Converter for the Passenger (Right) Side of the 2011-2021 Nissan GT-R (R35)."
  
  **Citation 2** (SECONDARY):
  - **URL**: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHi66YuJmaA2c8mBfvuIYcLenSj63GuuohBgKI_67Swd3WYnYl3NbV76esL7_dZkOdodvFWiTj6t5iCv2FvbHsYbnu82cu4Dg9-65B6QP6QzLNeGcRAFINNHEWxHTsyrb9bNmVRROdA-8AQI0Ua-KC3_iyc1cU2nfWZhTFJaGRKbdmQ7dfX0ebUHqo2PEQ=
  - **Quote**: "NISSAN GTR R35 EXHAUST CATALYTIC CONVERTERS 2009-2024 Midpipe Downpipe Set."
  
### Summary

- **Total Latency**: 11131.01ms (11.13 seconds)
- **Fields Resolved**: 4
- **Total Citations**: 8

---


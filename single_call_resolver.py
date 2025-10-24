"""
Single Call Vehicle Resolver module for Ruby GEM Estimator.

This module provides a simplified approach to vehicle specification resolution
by making a single comprehensive API call instead of multiple separate calls.
"""

import os
import json
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from google import genai
import streamlit as st


@dataclass
class VehicleSpecificationBundle:
    """Represents all vehicle specifications returned from a single API call."""
    curb_weight_lbs: Optional[float] = None
    aluminum_engine: Optional[bool] = None
    aluminum_rims: Optional[bool] = None
    catalytic_converters: Optional[int] = None
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    source_citations: Dict[str, List[str]] = field(default_factory=dict)
    resolution_method: str = "single_call_resolution"
    warnings: List[str] = field(default_factory=list)


class SingleCallVehicleResolver:
    """Resolver that gets all vehicle specifications in a single API call."""
    
    def __init__(self, api_key: Optional[str] = None, confidence_threshold: float = 0.7):
        """
        Initialize the single call vehicle resolver.
        
        Args:
            api_key: Google AI API key (if None, will try to get from environment)
            confidence_threshold: Minimum confidence threshold for accepting results
        """
        self.api_key = self._get_api_key(api_key)
        self.client = self._initialize_client()
        self.confidence_threshold = confidence_threshold
        
    def _get_api_key(self, provided_key: Optional[str]) -> str:
        """Get API key from parameter, environment, or Streamlit secrets."""
        if provided_key:
            return provided_key
            
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("GEMINI_API_KEY", "")
            except:
                api_key = ""
        return api_key
    
    def _initialize_client(self):
        """Initialize and return a Gemini client instance."""
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            return None
        
        try:
            return genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"Failed to initialize Google AI client: {e}")
            return None
    
    def resolve_all_specifications(self, year: int, make: str, model: str) -> VehicleSpecificationBundle:
        """
        Resolve all vehicle specifications in a single API call.
        
        Args:
            year: Vehicle year
            make: Vehicle make
            model: Vehicle model
            
        Returns:
            VehicleSpecificationBundle with all resolved specifications
        """
        if not self.client:
            return VehicleSpecificationBundle(
                warnings=["Google AI client not initialized - check API key configuration"]
            )
        
        try:
            # Create comprehensive prompt for all specifications
            prompt = self._create_comprehensive_prompt(year, make, model)
            
            # Make single API call
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    "tools": [{"google_search": {}}]
                }
            )
            
            # Parse structured response
            return self._parse_structured_response(response.text, year, make, model)
            
        except Exception as e:
            return VehicleSpecificationBundle(
                warnings=[f"API call failed: {str(e)}"]
            )
    
    def _create_comprehensive_prompt(self, year: int, make: str, model: str) -> str:
        """Create a comprehensive prompt that requests all specifications at once."""
        return f"""Search the web for complete specifications for a {year} {make} {model}. 

SOURCE PRIORITIZATION (search in this order):
1. HIGHEST PRIORITY: Official manufacturer websites ({make}.com, {make}usa.com, etc.)
2. HIGH PRIORITY: Kelley Blue Book (KBB.com), Edmunds.com, Cars.com
3. MEDIUM PRIORITY: AutoTrader.com, CarGurus.com, MotorTrend.com, Car and Driver
4. ACCEPTABLE: NHTSA.gov, EPA.gov, automotive forums with verified data
5. AVOID: user-generated content without verification

FIELD-SPECIFIC SEARCH INSTRUCTIONS:

CURB WEIGHT (in pounds):
- Search for "curb weight", "shipping weight", or "vehicle weight" specifications
- Look in official spec sheets, window stickers, or technical documentation
- Typical ranges: Compact cars (2,500-3,200 lbs), Mid-size (3,200-4,000 lbs), Full-size (4,000-5,500 lbs), Trucks/SUVs (4,500-8,000 lbs)
- Exclude payload, GVWR, or towing capacity - need empty vehicle weight only

ALUMINUM ENGINE BLOCK:
- Search for "engine block material", "aluminum engine", "cast iron engine"
- Look for engine specifications mentioning "aluminum block" vs "iron block" or "cast iron block"
- Modern luxury/performance vehicles typically use aluminum, older/economy vehicles often use cast iron
- If uncertain, aluminum is more common in vehicles 2010+ and premium brands

ALUMINUM RIMS/WHEELS:
- Search for "wheel material", "alloy wheels", "aluminum wheels", "steel wheels"
- Look for standard equipment lists or wheel specifications
- Aluminum/alloy wheels are standard on most trim levels except base models
- Steel wheels typically only on base trims or winter wheel packages

CATALYTIC CONVERTERS:
- Search for "catalytic converter", "emissions system", "exhaust system specifications"
- Look for EPA emissions documentation or exhaust system diagrams
- Count varies by engine: 4-cyl (1-2), V6 (2-4), V8 (2-4), diesel (1-2 + DPF)
- Consider pre-cat and main catalytic converters in the count

Return the following JSON format with confidence scores based on source reliability:
{{
  "curb_weight_lbs": <weight in pounds as number or null>,
  "aluminum_engine": <true for aluminum block, false for iron/cast iron, null if unknown>,
  "aluminum_rims": <true for aluminum/alloy, false for steel, null if unknown>,
  "catalytic_converters": <count as integer or null>,
  "confidence_scores": {{
    "curb_weight": <0.9-1.0 for manufacturer specs, 0.7-0.9 for KBB/Edmunds, 0.5-0.7 for other sources>,
    "engine_material": <0.9-1.0 for manufacturer specs, 0.7-0.9 for KBB/Edmunds, 0.5-0.7 for other sources>,
    "rim_material": <0.9-1.0 for manufacturer specs, 0.7-0.9 for KBB/Edmunds, 0.5-0.7 for other sources>,
    "catalytic_converters": <0.9-1.0 for EPA/manufacturer, 0.6-0.8 for automotive sites, 0.4-0.6 for forums>
  }},
  "sources": {{
    "curb_weight": ["specific URLs or source names"],
    "engine_material": ["specific URLs or source names"],
    "rim_material": ["specific URLs or source names"],
    "catalytic_converters": ["specific URLs or source names"]
  }},
  "data_consistency_notes": "Any cross-validation observations or consistency checks"
}}

VALIDATION REQUIREMENTS:
- Curb weight must be 1,500-10,000 lbs (reject obvious errors)
- Engine material should align with vehicle class and year (luxury/newer = more likely aluminum)
- Rim material should align with trim level (base = steel, higher trims = aluminum)
- Catalytic converter count should align with engine size and emissions era
- Cross-check specifications for internal consistency

Return ONLY the JSON object, no additional text or explanations."""

    def _parse_structured_response(self, response_text: str, year: int, make: str, model: str) -> VehicleSpecificationBundle:
        """Parse the structured JSON response from the API."""
        bundle = VehicleSpecificationBundle()
        
        try:
            # Extract JSON from response text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                bundle.warnings.append("No JSON structure found in response")
                return bundle
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Extract and validate curb weight with enhanced range checking
            if 'curb_weight_lbs' in data and data['curb_weight_lbs'] is not None:
                try:
                    weight = float(data['curb_weight_lbs'])
                    if 1500 <= weight <= 10000:  # Enhanced reasonable weight range
                        bundle.curb_weight_lbs = weight
                    else:
                        bundle.warnings.append(f"Curb weight {weight} lbs outside reasonable range (1500-10000 lbs)")
                except (ValueError, TypeError):
                    bundle.warnings.append("Invalid curb weight format in response")
            
            # Extract and validate aluminum engine
            if 'aluminum_engine' in data and data['aluminum_engine'] is not None:
                if isinstance(data['aluminum_engine'], bool):
                    bundle.aluminum_engine = data['aluminum_engine']
                else:
                    bundle.warnings.append("Invalid aluminum engine format - expected boolean")
            
            # Extract and validate aluminum rims
            if 'aluminum_rims' in data and data['aluminum_rims'] is not None:
                if isinstance(data['aluminum_rims'], bool):
                    bundle.aluminum_rims = data['aluminum_rims']
                else:
                    bundle.warnings.append("Invalid aluminum rims format - expected boolean")
            
            # Extract and validate catalytic converters with enhanced validation
            if 'catalytic_converters' in data and data['catalytic_converters'] is not None:
                try:
                    cat_count = int(data['catalytic_converters'])
                    if 0 <= cat_count <= 8:  # Allow 0 for very old vehicles, up to 8 for complex systems
                        bundle.catalytic_converters = cat_count
                        if cat_count == 0:
                            bundle.warnings.append("Zero catalytic converters - verify for pre-1975 vehicle")
                        elif cat_count > 6:
                            bundle.warnings.append("High catalytic converter count - verify system configuration")
                    else:
                        bundle.warnings.append(f"Catalytic converter count {cat_count} outside reasonable range (0-8)")
                except (ValueError, TypeError):
                    bundle.warnings.append("Invalid catalytic converter count format in response")
            
            # Extract confidence scores - ONLY for fields that were actually resolved
            if 'confidence_scores' in data and isinstance(data['confidence_scores'], dict):
                # Map confidence field names to data field names
                field_mapping = {
                    'curb_weight': 'curb_weight_lbs',
                    'engine_material': 'aluminum_engine',
                    'rim_material': 'aluminum_rims',
                    'catalytic_converters': 'catalytic_converters'
                }
                
                for confidence_field, score in data['confidence_scores'].items():
                    if isinstance(score, (int, float)) and 0.0 <= score <= 1.0:
                        # Only accept confidence score if the corresponding field was resolved
                        data_field = field_mapping.get(confidence_field)
                        if data_field and data_field in data and data[data_field] is not None:
                            bundle.confidence_scores[confidence_field] = float(score)
                        elif confidence_field in field_mapping:
                            # Field wasn't resolved, don't include the confidence score
                            pass
                        else:
                            # Unknown field in confidence scores
                            bundle.warnings.append(f"Unknown field in confidence scores: {confidence_field}")
                    else:
                        bundle.warnings.append(f"Invalid confidence score for {confidence_field}: {score}")
            
            # Validate confidence score completeness
            self._validate_confidence_scores(bundle, data)
            
            # Extract source citations
            if 'sources' in data and isinstance(data['sources'], dict):
                for field, sources in data['sources'].items():
                    if isinstance(sources, list):
                        bundle.source_citations[field] = [str(s) for s in sources]
            
            # Extract data consistency notes if provided
            if 'data_consistency_notes' in data and data['data_consistency_notes']:
                consistency_notes = str(data['data_consistency_notes']).strip()
                if consistency_notes and consistency_notes.lower() != 'none':
                    bundle.warnings.append(f"AI consistency note: {consistency_notes}")
            
            # Validate overall response quality
            self._validate_response_quality(bundle)
            
        except json.JSONDecodeError as e:
            bundle.warnings.append(f"Failed to parse JSON response: {str(e)}")
        except (ValueError, TypeError) as e:
            bundle.warnings.append(f"Data validation error: {str(e)}")
        except Exception as e:
            bundle.warnings.append(f"Unexpected error parsing response: {str(e)}")
        
        return bundle
    
    def _validate_response_quality(self, bundle: VehicleSpecificationBundle):
        """Validate the quality of the parsed response and add warnings if needed."""
        # Check if we got any meaningful data
        has_data = any([
            bundle.curb_weight_lbs is not None,
            bundle.aluminum_engine is not None,
            bundle.aluminum_rims is not None,
            bundle.catalytic_converters is not None
        ])
        
        if not has_data:
            bundle.warnings.append("No valid specifications found in response")
            return
        
        # Check confidence scores
        low_confidence_fields = []
        for field, score in bundle.confidence_scores.items():
            if score < self.confidence_threshold:
                low_confidence_fields.append(field)
        
        if low_confidence_fields:
            bundle.warnings.append(f"Low confidence for fields: {', '.join(low_confidence_fields)}")
        
        # Check for missing critical data
        if bundle.curb_weight_lbs is None:
            bundle.warnings.append("Curb weight not found - this is typically the most critical specification")
        
        # Perform comprehensive data consistency checks
        self._perform_consistency_checks(bundle)
    
    def _perform_consistency_checks(self, bundle: VehicleSpecificationBundle):
        """Perform comprehensive data consistency validation."""
        warnings = []
        
        # Weight-based consistency checks
        if bundle.curb_weight_lbs is not None:
            weight = bundle.curb_weight_lbs
            
            # Check for aluminum engine consistency with weight class
            if bundle.aluminum_engine is not None:
                if weight < 3000 and bundle.aluminum_engine is False:
                    warnings.append("Lightweight vehicle with iron engine is unusual for modern cars")
                elif weight > 5000 and bundle.aluminum_engine is True:
                    warnings.append("Heavy vehicle with aluminum engine - verify this is not a truck/SUV with iron block")
            
            # Check catalytic converter count vs weight class
            if bundle.catalytic_converters is not None:
                cat_count = bundle.catalytic_converters
                if weight < 3000 and cat_count > 2:
                    warnings.append("Small vehicle with high catalytic converter count - verify engine configuration")
                elif weight > 5000 and cat_count < 2:
                    warnings.append("Large vehicle with low catalytic converter count - may be diesel or older vehicle")
        
        # Engine material vs rim material consistency
        if bundle.aluminum_engine is not None and bundle.aluminum_rims is not None:
            if bundle.aluminum_engine is True and bundle.aluminum_rims is False:
                warnings.append("Aluminum engine with steel rims - unusual but possible on base trim levels")
            elif bundle.aluminum_engine is False and bundle.aluminum_rims is True:
                # This is actually common - iron engine with alloy wheels
                pass
        
        # Catalytic converter count validation
        if bundle.catalytic_converters is not None:
            cat_count = bundle.catalytic_converters
            if cat_count > 6:
                warnings.append("Very high catalytic converter count - verify this includes all pre-cats and main cats")
            elif cat_count == 0:
                warnings.append("Zero catalytic converters reported - this would only be valid for very old vehicles")
        
        # Source citation quality checks
        self._validate_source_quality(bundle, warnings)
        
        # Add all warnings to bundle
        bundle.warnings.extend(warnings)
    
    def _validate_confidence_scores(self, bundle: VehicleSpecificationBundle, data: Dict[str, Any]):
        """Validate that confidence scores are provided for all resolved fields."""
        resolved_fields = []
        
        # Map data fields to confidence score field names
        field_mapping = {
            'curb_weight_lbs': 'curb_weight',
            'aluminum_engine': 'engine_material', 
            'aluminum_rims': 'rim_material',
            'catalytic_converters': 'catalytic_converters'
        }
        
        # Check which fields have data
        for data_field, confidence_field in field_mapping.items():
            if data_field in data and data[data_field] is not None:
                resolved_fields.append(confidence_field)
                
                # Check if confidence score is missing for resolved field
                if confidence_field not in bundle.confidence_scores:
                    bundle.warnings.append(f"Missing confidence score for resolved field: {confidence_field}")
        
        # Check for confidence scores without corresponding data
        for confidence_field in bundle.confidence_scores:
            if confidence_field not in resolved_fields:
                bundle.warnings.append(f"Confidence score provided for unresolved field: {confidence_field}")
    
    def _validate_source_quality(self, bundle: VehicleSpecificationBundle, warnings: List[str]):
        """Validate the quality and reliability of cited sources."""
        high_quality_domains = [
            'manufacturer', 'kbb.com', 'edmunds.com', 'cars.com', 
            'nhtsa.gov', 'epa.gov', 'motortrend.com', 'caranddriver.com'
        ]
        
        medium_quality_domains = [
            'autotrader.com', 'cargurus.com', 'carfax.com', 'autoblog.com'
        ]
        
        for field, sources in bundle.source_citations.items():
            if not sources:
                warnings.append(f"No sources cited for {field}")
                continue
            
            high_quality_count = 0
            medium_quality_count = 0
            
            for source in sources:
                source_lower = source.lower()
                if any(domain in source_lower for domain in high_quality_domains):
                    high_quality_count += 1
                elif any(domain in source_lower for domain in medium_quality_domains):
                    medium_quality_count += 1
            
            if high_quality_count == 0 and medium_quality_count == 0:
                warnings.append(f"Low quality sources for {field}: {', '.join(sources[:2])}")
            elif high_quality_count == 0:
                warnings.append(f"No high-authority sources for {field} - consider verifying data")
        
        # Check for source diversity
        all_sources = []
        for sources in bundle.source_citations.values():
            all_sources.extend(sources)
        
        unique_sources = set(all_sources)
        if len(all_sources) > 0 and len(unique_sources) == 1:
            warnings.append("All data from single source - cross-validation recommended")
    
    def has_sufficient_confidence(self, bundle: VehicleSpecificationBundle) -> bool:
        """Check if the bundle has sufficient confidence for the critical specifications."""
        # Curb weight is the most critical specification
        if bundle.curb_weight_lbs is not None:
            weight_confidence = bundle.confidence_scores.get('curb_weight', 0.0)
            return weight_confidence >= self.confidence_threshold
        
        return False
"""
Resolver module for Ruby GEM Estimator.

This module provides the core infrastructure for resolving vehicle specifications
using Google AI with Grounded Search, consensus algorithms, and provenance tracking.
"""

import os
import re
import json
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from google import genai
import streamlit as st
from database_config import create_database_engine, create_resolutions_table as db_create_resolutions_table, get_datetime_interval_query
from sqlalchemy import text


@dataclass
class SearchCandidate:
    """Represents a candidate value from a grounded search result."""
    value: float
    source: str
    citation: str
    confidence: float
    raw_text: str


@dataclass
class ResolutionResult:
    """Represents the final result of a field resolution process."""
    final_value: float
    confidence_score: float
    method: str
    candidates: List[SearchCandidate]
    outliers: List[bool]
    warnings: List[str]


@dataclass
class ResolutionRecord:
    """Represents a stored resolution record in the database."""
    id: str
    vehicle_key: str
    field_name: str
    final_value: float
    confidence_score: float
    method: str
    candidates_json: str
    created_at: datetime


class GroundedSearchClient:
    """Client for performing grounded searches using Google AI with request deduplication."""
    
    def __init__(self):
        """Initialize the grounded search client."""
        self.api_key = self._get_api_key()
        self.client = self._initialize_model()
        self.request_cache = {}  # Cache for deduplicating identical requests
        self.request_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "failed_requests": 0
        }
    
    def _get_api_key(self) -> str:
        """Get API key from environment variables or Streamlit secrets."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("GEMINI_API_KEY", "")
            except:
                api_key = ""
        return api_key
    
    def _initialize_model(self):
        """Initialize and return a Gemini client instance with validation."""
        import logging
        
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            logging.warning("Google AI API key not configured")
            return None
        
        try:
            client = genai.Client(api_key=self.api_key)
            
            # Log successful initialization
            logging.info("Google AI client initialized successfully with new SDK")
            return client
            
        except Exception as e:
            logging.error(f"Failed to initialize Google AI client: {e}")
            logging.error("Please check API key configuration and SDK installation")
            return None
    
    def search_vehicle_specs(self, year: int, make: str, model: str, field: str) -> List[SearchCandidate]:
        """
        Search for vehicle specifications using grounded search with request deduplication.
        
        Args:
            year: Vehicle year
            make: Vehicle make
            model: Vehicle model
            field: Specification field to search for (e.g., 'curb_weight', 'aluminum_engine')
            
        Returns:
            List of SearchCandidate objects with found values
        """
        import logging
        import hashlib
        
        self.request_stats["total_requests"] += 1
        
        if not self.client:
            self.request_stats["failed_requests"] += 1
            logging.warning(f"Google AI client not initialized - cannot search for {year} {make} {model} {field}")
            logging.warning("Please check GEMINI_API_KEY configuration")
            return []
        
        # Create request hash for deduplication
        request_key = f"{year}_{make}_{model}_{field}".lower()
        request_hash = hashlib.md5(request_key.encode()).hexdigest()
        
        # Check request cache for identical requests
        if request_hash in self.request_cache:
            self.request_stats["cache_hits"] += 1
            logging.info(f"Request cache hit for {request_key}")
            return self.request_cache[request_hash]
        
        try:
            # Create field-specific search prompt
            prompt = self._create_search_prompt(year, make, model, field)
            
            # Log API call with details
            logging.info(f"Making grounded search API call for {request_key}")
            logging.debug(f"API request details - Vehicle: {year} {make} {model}, Field: {field}")
            self.request_stats["api_calls"] += 1
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    "tools": [{"google_search": {}}]
                }
            )
            
            # Parse response into candidates
            candidates = self._parse_search_response(response.text, field)
            
            # Cache the result for deduplication
            self.request_cache[request_hash] = candidates
            
            # Log success with details
            logging.info(f"Grounded search completed for {request_key}: {len(candidates)} candidates found")
            if len(candidates) == 0:
                logging.warning(f"No candidates found for {request_key} - response may need review")
            
            return candidates
            
        except Exception as e:
            self.request_stats["failed_requests"] += 1
            # Enhanced error logging with context
            logging.error(f"Google AI API call failed for grounded search")
            logging.error(f"Vehicle: {year} {make} {model}")
            logging.error(f"Field: {field}")
            logging.error(f"Request key: {request_key}")
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Error details: {e}")
            
            # Provide user-friendly error messages for common failures
            error_str = str(e)
            if "404" in error_str and "not found" in error_str:
                logging.error("Model not found error - the specified model may be deprecated or unavailable")
                logging.error("Consider updating to a current model version")
                print(f"Error: Google AI model not found. Please check model configuration.")
            elif "401" in error_str or "403" in error_str:
                logging.error("Authentication error - API key may be invalid or expired")
                print(f"Error: Google AI authentication failed. Please check your API key.")
            elif "429" in error_str:
                logging.error("Rate limit exceeded - too many API requests")
                print(f"Error: Google AI rate limit exceeded. Please try again later.")
            elif "timeout" in error_str.lower():
                logging.error("Request timeout - API may be slow or unavailable")
                print(f"Error: Google AI request timed out. Please try again.")
            else:
                print(f"Error in grounded search for {field}: {e}")
            
            return []
    
    def get_multiple_candidates(self, query: str, min_candidates: int = 3) -> List[SearchCandidate]:
        """
        Collect diverse candidate values for a specific query.
        
        Args:
            query: Search query string
            min_candidates: Minimum number of candidates to collect
            
        Returns:
            List of SearchCandidate objects
        """
        if not self.client:
            return []
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=query,
                config={
                    "tools": [{"google_search": {}}]
                }
            )
            
            # Parse response for multiple candidates
            candidates = self._parse_multiple_candidates(response.text)
            
            # If we don't have enough candidates, try a broader search
            if len(candidates) < min_candidates:
                broader_query = f"{query} OR specifications OR technical data"
                broader_response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=broader_query,
                    config={
                        "tools": [{"google_search": {}}]
                    }
                )
                additional_candidates = self._parse_multiple_candidates(broader_response.text)
                candidates.extend(additional_candidates)
            
            return candidates[:10]  # Limit to 10 candidates max
            
        except Exception as e:
            print(f"Error collecting multiple candidates: {e}")
            return []
    
    def _create_search_prompt(self, year: int, make: str, model: str, field: str) -> str:
        """Create a field-specific search prompt."""
        field_prompts = {
            'curb_weight': (
                f"Search the web and list every curb weight figure (in pounds) you find for a {year} {make} {model}. "
                "Prioritize results from Kelley Blue Book (kbb.com), Edmunds (edmunds.com), or the manufacturer's official site. "
                "Return each finding in the format '<WEIGHT> lbs from <SOURCE>'. Only include verified numbers."
            ),
            'aluminum_engine': (
                f"Search the web for {year} {make} {model} engine specifications. "
                "Find information about engine block material: aluminum vs iron/cast iron. "
                "Look for technical specifications, engine details, or automotive databases. "
                "Report findings as: 'aluminum engine' or 'iron engine' or 'cast iron engine' with source."
            ),
            'aluminum_rims': (
                f"Search the web for {year} {make} {model} wheel specifications. "
                "Find information about wheel/rim material: aluminum alloy vs steel. "
                "Look for standard equipment, wheel options, or automotive specifications. "
                "Report findings as: 'aluminum wheels' or 'steel wheels' or 'alloy wheels' with source."
            ),
            'catalytic_converters': (
                f"Search the web for information about {year} {make} {model} catalytic converter count and configuration. "
                "Look for parts catalogs, exhaust system diagrams, and technical specifications. "
                "Return findings in the format '<COUNT> catalytic converters from <SOURCE>'."
            )
        }
        
        return field_prompts.get(field, f"Search for {field} specifications for {year} {make} {model}")
    
    def _parse_search_response(self, response_text: str, field: str) -> List[SearchCandidate]:
        """Parse search response into SearchCandidate objects."""
        candidates = []
        
        if field == 'curb_weight':
            # Extract weight values with sources
            weight_pattern = r'(\d{3,5})\s*lbs?\s*from\s*([^\n]+)'
            matches = re.findall(weight_pattern, response_text, re.IGNORECASE)
            
            for weight_str, source in matches:
                try:
                    weight = float(weight_str)
                    if 1000 <= weight <= 8000:  # Reasonable weight range
                        candidate = SearchCandidate(
                            value=weight,
                            source=source.strip(),
                            citation=f"{weight} lbs from {source.strip()}",
                            confidence=self._calculate_source_confidence(source),
                            raw_text=f"{weight_str} lbs from {source}"
                        )
                        candidates.append(candidate)
                except ValueError:
                    continue
        
        elif field in ['aluminum_engine', 'aluminum_rims']:
            # Extract material information with multiple patterns
            patterns = [
                r'(aluminum|alloy|iron|steel|cast\s*iron)\s+(?:engine|wheels?|rims?)',
                r'(?:engine|wheels?|rims?).*?(aluminum|alloy|iron|steel|cast\s*iron)',
                r'(aluminum|alloy|iron|steel|cast\s*iron).*?(?:engine|wheels?|rims?)',
                r'(?:made\s+of|constructed\s+from|material[:\s]+)(aluminum|alloy|iron|steel|cast\s*iron)'
            ]
            
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                for match in matches:
                    material = match if isinstance(match, str) else match[0] if match else ""
                    if material:
                        all_matches.append((material, "search result"))
            
            # Also look for explicit statements
            if 'aluminum' in response_text.lower() or 'alloy' in response_text.lower():
                all_matches.append(('aluminum', 'content analysis'))
            elif 'iron' in response_text.lower() or 'steel' in response_text.lower():
                all_matches.append(('iron', 'content analysis'))
            
            for material, source in all_matches:
                material_lower = material.lower().replace(' ', '')
                # Aluminum includes alloy wheels/engines
                value = 1.0 if material_lower in ['aluminum', 'alloy'] else 0.0
                
                candidate = SearchCandidate(
                    value=value,
                    source=source,
                    citation=f"{material} material detected",
                    confidence=0.7 if source == 'content analysis' else 0.8,
                    raw_text=f"{material} material found in search"
                )
                candidates.append(candidate)
        
        elif field == 'catalytic_converters':
            # Extract catalytic converter counts
            cat_pattern = r'(\d+)\s*catalytic\s*converters?\s*from\s*([^\n]+)'
            matches = re.findall(cat_pattern, response_text, re.IGNORECASE)
            
            for count_str, source in matches:
                try:
                    count = float(count_str)
                    if 1 <= count <= 8:  # Reasonable range
                        candidate = SearchCandidate(
                            value=count,
                            source=source.strip(),
                            citation=f"{count} catalytic converters from {source.strip()}",
                            confidence=self._calculate_source_confidence(source),
                            raw_text=f"{count_str} catalytic converters from {source}"
                        )
                        candidates.append(candidate)
                except ValueError:
                    continue
        
        return candidates
    
    def _parse_multiple_candidates(self, response_text: str) -> List[SearchCandidate]:
        """Parse response text for multiple candidates of any type."""
        candidates = []
        
        # Look for numeric values with sources
        numeric_pattern = r'(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)?\s*(?:from|source:)\s*([^\n]+)'
        matches = re.findall(numeric_pattern, response_text, re.IGNORECASE)
        
        for value_str, source in matches:
            try:
                value = float(value_str)
                candidate = SearchCandidate(
                    value=value,
                    source=source.strip(),
                    citation=f"{value} from {source.strip()}",
                    confidence=self._calculate_source_confidence(source),
                    raw_text=f"{value_str} from {source}"
                )
                candidates.append(candidate)
            except ValueError:
                continue
        
        return candidates
    
    def _calculate_source_confidence(self, source: str) -> float:
        """Calculate confidence score based on source reliability."""
        source_lower = source.lower()
        
        # High confidence sources
        if any(trusted in source_lower for trusted in ['kbb.com', 'edmunds.com', 'manufacturer', 'official']):
            return 0.9
        
        # Medium confidence sources
        if any(medium in source_lower for medium in ['autotrader', 'cars.com', 'carmax', 'dealer']):
            return 0.7
        
        # Lower confidence sources
        if any(low in source_lower for low in ['forum', 'wiki', 'blog', 'reddit']):
            return 0.4
        
        # Default confidence
        return 0.6


class ConsensusResolver:
    """Resolves field values using consensus algorithms and confidence scoring."""
    
    def __init__(self, clustering_tolerance: float = 0.15, confidence_threshold: float = 0.7, outlier_threshold: float = 1.4):
        """
        Initialize the consensus resolver.
        
        Args:
            clustering_tolerance: Tolerance for grouping similar values (default 15%)
            confidence_threshold: Minimum confidence score for acceptance
            outlier_threshold: Standard deviation threshold for outlier detection (1.4 catches values ~4x the mean)
        """
        self.clustering_tolerance = clustering_tolerance
        self.confidence_threshold = confidence_threshold
        self.outlier_threshold = outlier_threshold
    
    def resolve_field(self, candidates: List[SearchCandidate]) -> ResolutionResult:
        """
        Resolve a field value using consensus from multiple candidates.
        
        Args:
            candidates: List of SearchCandidate objects
            
        Returns:
            ResolutionResult with final value and metadata
        """
        if not candidates:
            return ResolutionResult(
                final_value=0.0,
                confidence_score=0.0,
                method="no_candidates",
                candidates=[],
                outliers=[],
                warnings=["No candidates found"]
            )
        
        if len(candidates) == 1:
            candidate = candidates[0]
            return ResolutionResult(
                final_value=candidate.value,
                confidence_score=candidate.confidence,
                method="single_candidate",
                candidates=candidates,
                outliers=[False],
                warnings=[] if candidate.confidence >= self.confidence_threshold else ["Low confidence single candidate"]
            )
        
        # Extract values for clustering
        values = [c.value for c in candidates]
        
        # Group similar values into clusters
        clusters = self._cluster_values(values, candidates)
        
        # Find the densest cluster (most agreeing sources)
        primary_cluster = max(clusters, key=len)
        primary_indices = [candidates.index(c) for c in primary_cluster]
        
        # Calculate weighted median from primary cluster
        final_value = self._calculate_weighted_median(primary_cluster)
        
        # Identify outliers
        outliers = self.detect_outliers(values)
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence(values, [c.source for c in candidates])
        
        # Generate warnings
        warnings = self._generate_warnings(candidates, outliers, confidence_score)
        
        return ResolutionResult(
            final_value=final_value,
            confidence_score=confidence_score,
            method="grounded_consensus",
            candidates=candidates,
            outliers=outliers,
            warnings=warnings
        )
    
    def detect_outliers(self, values: List[float]) -> List[bool]:
        """
        Detect outliers using statistical thresholds.
        
        Args:
            values: List of numeric values
            
        Returns:
            List of boolean flags indicating outliers
        """
        if len(values) < 3:
            return [False] * len(values)
        
        try:
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values)
            
            outliers = []
            for value in values:
                z_score = abs(value - mean_val) / stdev_val if stdev_val > 0 else 0
                outliers.append(z_score > self.outlier_threshold)
            
            return outliers
            
        except statistics.StatisticsError:
            return [False] * len(values)
    
    def calculate_confidence(self, values: List[float], sources: List[str]) -> float:
        """
        Calculate confidence based on agreement and spread metrics.
        
        Args:
            values: List of numeric values
            sources: List of source names
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not values:
            return 0.0
        
        if len(values) == 1:
            return 0.6  # Moderate confidence for single value
        
        # Agreement factor: how close values are to each other
        try:
            mean_val = statistics.mean(values)
            if mean_val == 0:
                agreement_factor = 0.5
            else:
                # Calculate coefficient of variation (CV)
                stdev_val = statistics.stdev(values)
                cv = stdev_val / mean_val
                # Convert CV to agreement factor (lower CV = higher agreement)
                agreement_factor = max(0.0, 1.0 - cv)
        except (statistics.StatisticsError, ZeroDivisionError):
            agreement_factor = 0.5
        
        # Source diversity factor: more diverse sources = higher confidence
        unique_sources = len(set(sources))
        total_sources = len(sources)
        diversity_factor = min(1.0, unique_sources / max(1, total_sources))
        
        # Source quality factor: based on known reliable sources
        quality_scores = []
        for source in sources:
            source_lower = source.lower()
            if any(trusted in source_lower for trusted in ['kbb.com', 'edmunds.com', 'manufacturer', 'official']):
                quality_scores.append(0.9)
            elif any(medium in source_lower for medium in ['autotrader', 'cars.com', 'carmax']):
                quality_scores.append(0.7)
            else:
                quality_scores.append(0.5)
        
        quality_factor = statistics.mean(quality_scores) if quality_scores else 0.5
        
        # Combine factors with weights
        confidence = (
            0.4 * agreement_factor +
            0.3 * quality_factor +
            0.3 * diversity_factor
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _cluster_values(self, values: List[float], candidates: List[SearchCandidate]) -> List[List[SearchCandidate]]:
        """Group similar values into clusters based on tolerance."""
        if not values:
            return []
        
        clusters = []
        used_indices = set()
        
        for i, value in enumerate(values):
            if i in used_indices:
                continue
            
            # Start new cluster with current value
            cluster = [candidates[i]]
            used_indices.add(i)
            
            # Find similar values within tolerance
            for j, other_value in enumerate(values):
                if j in used_indices:
                    continue
                
                # Calculate relative difference
                if value == 0:
                    relative_diff = abs(other_value) / max(abs(other_value), 1)
                else:
                    relative_diff = abs(value - other_value) / abs(value)
                
                if relative_diff <= self.clustering_tolerance:
                    cluster.append(candidates[j])
                    used_indices.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _calculate_weighted_median(self, candidates: List[SearchCandidate]) -> float:
        """Calculate weighted median based on source confidence."""
        if not candidates:
            return 0.0
        
        if len(candidates) == 1:
            return candidates[0].value
        
        # Sort candidates by value
        sorted_candidates = sorted(candidates, key=lambda c: c.value)
        
        # Calculate weighted median
        total_weight = sum(c.confidence for c in sorted_candidates)
        if total_weight == 0:
            return statistics.median([c.value for c in sorted_candidates])
        
        cumulative_weight = 0
        target_weight = total_weight / 2
        
        for candidate in sorted_candidates:
            cumulative_weight += candidate.confidence
            if cumulative_weight >= target_weight:
                return candidate.value
        
        # Fallback to regular median
        return statistics.median([c.value for c in sorted_candidates])
    
    def _generate_warnings(self, candidates: List[SearchCandidate], outliers: List[bool], confidence_score: float) -> List[str]:
        """Generate warning messages based on resolution analysis."""
        warnings = []
        
        if confidence_score < self.confidence_threshold:
            warnings.append("Low confidence - manual review recommended")
        
        outlier_count = sum(outliers)
        if outlier_count > 0:
            warnings.append(f"{outlier_count} outlier value(s) detected")
        
        if len(candidates) < 3:
            warnings.append("Limited data sources - consider additional verification")
        
        # Check for wide spread in values
        values = [c.value for c in candidates]
        if len(values) > 1:
            try:
                mean_val = statistics.mean(values)
                stdev_val = statistics.stdev(values)
                if mean_val > 0 and (stdev_val / mean_val) > 0.3:  # CV > 30%
                    warnings.append("High variability in source data")
            except statistics.StatisticsError:
                pass
        
        return warnings


class ProvenanceTracker:
    """Tracks resolution history and manages provenance data."""
    
    def __init__(self):
        """Initialize the provenance tracker."""
        self.cache = {}  # In-memory cache for recent resolutions
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "total_requests": 0
        }
        self.resolution_metrics = {
            "total_resolutions": 0,
            "successful_resolutions": 0,
            "failed_resolutions": 0,
            "average_confidence": 0.0,
            "low_confidence_count": 0
        }
    
    def create_resolution_record(self, vehicle_key: str, field_name: str, result: ResolutionResult) -> str:
        """
        Create and store a resolution record in the database with comprehensive logging.
        
        Args:
            vehicle_key: Vehicle identifier (e.g., "2020_Toyota_Camry")
            field_name: Field that was resolved (e.g., "curb_weight")
            result: ResolutionResult object
            
        Returns:
            Record ID string
        """
        import logging
        from database_config import is_sqlite
        
        # Update resolution metrics
        self.resolution_metrics["total_resolutions"] += 1
        
        try:
            engine = create_database_engine()
            
            # Prepare data for storage
            candidates_json = json.dumps([asdict(c) for c in result.candidates])
            warnings_json = json.dumps(result.warnings)
            
            with engine.begin() as conn:  # Use begin() for automatic transaction management
                if is_sqlite():
                    # SQLite syntax - use INSERT OR REPLACE
                    query = text("""
                        INSERT OR REPLACE INTO resolutions (vehicle_key, field_name, final_value, confidence_score, 
                                               method, candidates_json, warnings_json, created_at)
                        VALUES (:vehicle_key, :field_name, :final_value, :confidence_score, 
                                :method, :candidates_json, :warnings_json, :created_at)
                    """)
                    
                    conn.execute(query, {
                        "vehicle_key": vehicle_key,
                        "field_name": field_name,
                        "final_value": result.final_value,
                        "confidence_score": result.confidence_score,
                        "method": result.method,
                        "candidates_json": candidates_json,
                        "warnings_json": warnings_json,
                        "created_at": datetime.now()
                    })
                    
                    # Get the record ID for SQLite
                    id_query = text("SELECT last_insert_rowid()")
                    result_row = conn.execute(id_query)
                    record_id = str(result_row.fetchone()[0])
                else:
                    # PostgreSQL syntax
                    query = text("""
                        INSERT INTO resolutions (vehicle_key, field_name, final_value, confidence_score, 
                                               method, candidates_json, warnings_json, created_at)
                        VALUES (:vehicle_key, :field_name, :final_value, :confidence_score, 
                                :method, CAST(:candidates_json AS JSONB), CAST(:warnings_json AS JSONB), :created_at)
                        ON CONFLICT (vehicle_key, field_name) DO UPDATE SET
                            final_value = EXCLUDED.final_value,
                            confidence_score = EXCLUDED.confidence_score,
                            method = EXCLUDED.method,
                            candidates_json = EXCLUDED.candidates_json,
                            warnings_json = EXCLUDED.warnings_json,
                            created_at = EXCLUDED.created_at
                        RETURNING id
                    """)
                    
                    result_row = conn.execute(query, {
                        "vehicle_key": vehicle_key,
                        "field_name": field_name,
                        "final_value": result.final_value,
                        "confidence_score": result.confidence_score,
                        "method": result.method,
                        "candidates_json": candidates_json,
                        "warnings_json": warnings_json,
                        "created_at": datetime.now()
                    })
                    
                    record_id = str(result_row.fetchone()[0])
                
                # Transaction is automatically committed when exiting the context
                
                # Update cache with intelligent TTL
                cache_key = f"{vehicle_key}_{field_name}"
                self.cache[cache_key] = result
                
                # Update success metrics
                self.resolution_metrics["successful_resolutions"] += 1
                
                # Update confidence metrics
                if result.confidence_score < 0.6:
                    self.resolution_metrics["low_confidence_count"] += 1
                
                # Update running average confidence
                total_successful = self.resolution_metrics["successful_resolutions"]
                current_avg = self.resolution_metrics["average_confidence"]
                self.resolution_metrics["average_confidence"] = (
                    (current_avg * (total_successful - 1) + result.confidence_score) / total_successful
                )
                
                # Comprehensive logging
                logging.info(f"Resolution created: {record_id} for {vehicle_key}.{field_name} "
                           f"(confidence: {result.confidence_score:.2f}, method: {result.method})")
                
                if result.confidence_score < 0.6:
                    logging.warning(f"Low confidence resolution: {vehicle_key}.{field_name} "
                                  f"(confidence: {result.confidence_score:.2f})")
                
                if result.warnings:
                    logging.warning(f"Resolution warnings for {vehicle_key}.{field_name}: {result.warnings}")
                
                print(f"✅ Resolution record created: {record_id} for {vehicle_key}.{field_name} "
                      f"(confidence: {result.confidence_score:.0%})")
                return record_id
                
        except Exception as e:
            # Update failure metrics
            self.resolution_metrics["failed_resolutions"] += 1
            
            # Log error with context
            logging.error(f"Failed to create resolution record for {vehicle_key}.{field_name}: {e}")
            print(f"❌ Error creating resolution record: {e}")
            return ""
    
    def get_resolution_history(self, vehicle_key: str, field_name: Optional[str] = None) -> List[ResolutionRecord]:
        """
        Get resolution history for a vehicle or specific field.
        
        Args:
            vehicle_key: Vehicle identifier
            field_name: Optional specific field name
            
        Returns:
            List of ResolutionRecord objects
        """
        import logging
        from database_config import is_sqlite
        
        try:
            engine = create_database_engine()
            
            with engine.connect() as conn:
                if field_name:
                    query = text("""
                        SELECT id, vehicle_key, field_name, final_value, confidence_score, 
                               method, candidates_json, created_at
                        FROM resolutions 
                        WHERE vehicle_key = :vehicle_key AND field_name = :field_name
                        ORDER BY created_at DESC
                    """)
                    result = conn.execute(query, {"vehicle_key": vehicle_key, "field_name": field_name})
                else:
                    query = text("""
                        SELECT id, vehicle_key, field_name, final_value, confidence_score, 
                               method, candidates_json, created_at
                        FROM resolutions 
                        WHERE vehicle_key = :vehicle_key
                        ORDER BY created_at DESC
                    """)
                    result = conn.execute(query, {"vehicle_key": vehicle_key})
                
                records = []
                for row in result.fetchall():
                    record = ResolutionRecord(
                        id=str(row[0]),
                        vehicle_key=row[1],
                        field_name=row[2],
                        final_value=float(row[3]),
                        confidence_score=float(row[4]),
                        method=row[5],
                        candidates_json=json.dumps(row[6]) if row[6] else "[]",
                        created_at=row[7]
                    )
                    records.append(record)
                
                return records
                
        except Exception as e:
            # Enhanced error logging with context
            db_type = "SQLite" if is_sqlite() else "PostgreSQL"
            logging.error(f"Database query failed in get_resolution_history for {vehicle_key}" + 
                         (f".{field_name}" if field_name else ""))
            logging.error(f"Database type: {db_type}")
            logging.error(f"Error details: {e}")
            print(f"Error getting resolution history: {e}")
            return []
    
    def get_cached_resolution(self, vehicle_key: str, field_name: str) -> Optional[ResolutionResult]:
        """
        Get cached resolution if available (permanent cache, no time limit).
        Returns the most recent resolution record regardless of age.
        
        Args:
            vehicle_key: Vehicle identifier
            field_name: Field name
            
        Returns:
            ResolutionResult if cached, None otherwise
        """
        import logging
        from database_config import is_sqlite
        
        self.cache_stats["total_requests"] += 1
        
        # Check in-memory cache first
        cache_key = f"{vehicle_key}_{field_name}"
        if cache_key in self.cache:
            self.cache_stats["hits"] += 1
            return self.cache[cache_key]
        
        # Check database cache (permanent storage, no time filter)
        try:
            engine = create_database_engine()
            
            with engine.connect() as conn:
                query = text("""
                    SELECT final_value, confidence_score, method, candidates_json, warnings_json, created_at
                    FROM resolutions 
                    WHERE vehicle_key = :vehicle_key AND field_name = :field_name
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                
                result = conn.execute(query, {"vehicle_key": vehicle_key, "field_name": field_name})
                row = result.fetchone()
                
                if row:
                    # Reconstruct ResolutionResult from database
                    candidates_data = row[3] if row[3] else []
                    warnings_data = row[4] if row[4] else []
                    
                    candidates = []
                    for candidate_dict in candidates_data:
                        candidate = SearchCandidate(**candidate_dict)
                        candidates.append(candidate)
                    
                    resolution_result = ResolutionResult(
                        final_value=float(row[0]),
                        confidence_score=float(row[1]),
                        method=row[2],
                        candidates=candidates,
                        outliers=[],  # Not stored, would need to recalculate
                        warnings=warnings_data
                    )
                    
                    # Update in-memory cache
                    self.cache[cache_key] = resolution_result
                    return resolution_result
                
        except Exception as e:
            # Enhanced error logging with context
            db_type = "SQLite" if is_sqlite() else "PostgreSQL"
            logging.error(f"Database query failed in get_cached_resolution for {vehicle_key}.{field_name}")
            logging.error(f"Database type: {db_type}")
            logging.error(f"Error details: {e}")
            print(f"Error getting cached resolution: {e}")
        
        return None
    
    def invalidate_cache(self, vehicle_key: str, field_name: Optional[str] = None):
        """
        Invalidate cached resolutions.
        
        Args:
            vehicle_key: Vehicle identifier
            field_name: Optional specific field name to invalidate
        """
        if field_name:
            cache_key = f"{vehicle_key}_{field_name}"
            self.cache.pop(cache_key, None)
        else:
            # Remove all cache entries for this vehicle
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{vehicle_key}_")]
            for key in keys_to_remove:
                self.cache.pop(key, None)
    
    def get_resolution_summary(self, vehicle_key: str) -> Dict[str, Any]:
        """
        Get a summary of all resolutions for a vehicle.
        
        Args:
            vehicle_key: Vehicle identifier
            
        Returns:
            Dictionary with resolution summary statistics
        """
        records = self.get_resolution_history(vehicle_key)
        
        if not records:
            return {"total_resolutions": 0, "fields": [], "average_confidence": 0.0}
        
        fields = list(set(r.field_name for r in records))
        confidences = [r.confidence_score for r in records]
        
        return {
            "total_resolutions": len(records),
            "fields": fields,
            "average_confidence": statistics.mean(confidences) if confidences else 0.0,
            "latest_resolution": max(records, key=lambda r: r.created_at).created_at,
            "methods_used": list(set(r.method for r in records))
        }


# Initialize the resolutions table when module is imported
if __name__ != "__main__":
    try:
        db_create_resolutions_table()
    except Exception as e:
        print(f"Warning: Could not create resolutions table: {e}")


def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system performance metrics."""
    # This would be called from the main application to collect metrics
    return {
        "timestamp": datetime.now().isoformat(),
        "system_status": "operational",
        "cache_performance": {
            "description": "Cache statistics would be collected from active instances"
        },
        "resolution_quality": {
            "description": "Resolution quality metrics would be aggregated from database"
        }
    }


def log_resolution_attempt(vehicle_key: str, field_name: str, success: bool, 
                          confidence_score: float = None, method: str = None, 
                          duration_ms: float = None):
    """
    Log detailed information about resolution attempts for monitoring.
    
    Args:
        vehicle_key: Vehicle identifier
        field_name: Field being resolved
        success: Whether resolution was successful
        confidence_score: Confidence score if successful
        method: Resolution method used
        duration_ms: Time taken in milliseconds
    """
    import logging
    
    log_data = {
        "vehicle_key": vehicle_key,
        "field_name": field_name,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if success:
        log_data.update({
            "confidence_score": confidence_score,
            "method": method,
            "duration_ms": duration_ms
        })
        
        if confidence_score and confidence_score < 0.6:
            logging.warning(f"Low confidence resolution: {log_data}")
        else:
            logging.info(f"Successful resolution: {log_data}")
    else:
        logging.error(f"Failed resolution: {log_data}")


def create_monitoring_dashboard_data() -> Dict[str, Any]:
    """
    Create data structure for monitoring dashboard.
    This would be used by a monitoring system to display system health.
    """
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Get recent resolution statistics
            datetime_condition = get_datetime_interval_query(24)
            recent_stats_query = text(f"""
                SELECT 
                    COUNT(*) as total_resolutions,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(CASE WHEN confidence_score < 0.6 THEN 1 END) as low_confidence_count,
                    COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_confidence_count,
                    COUNT(DISTINCT vehicle_key) as unique_vehicles,
                    COUNT(DISTINCT field_name) as unique_fields
                FROM resolutions 
                WHERE created_at > {datetime_condition}
            """)
            
            stats_result = conn.execute(recent_stats_query).fetchone()
            
            # Get method distribution
            method_stats_query = text(f"""
                SELECT method, COUNT(*) as count
                FROM resolutions 
                WHERE created_at > {datetime_condition}
                GROUP BY method
            """)
            
            method_results = conn.execute(method_stats_query).fetchall()
            method_distribution = {row[0]: row[1] for row in method_results}
            
            # Get confidence score distribution
            confidence_dist_query = text(f"""
                SELECT 
                    CASE 
                        WHEN confidence_score >= 0.8 THEN 'high'
                        WHEN confidence_score >= 0.6 THEN 'medium'
                        ELSE 'low'
                    END as confidence_level,
                    COUNT(*) as count
                FROM resolutions 
                WHERE created_at > {datetime_condition}
                GROUP BY confidence_level
            """)
            
            confidence_results = conn.execute(confidence_dist_query).fetchall()
            confidence_distribution = {row[0]: row[1] for row in confidence_results}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "period": "24_hours",
                "resolution_stats": {
                    "total_resolutions": stats_result[0] or 0,
                    "average_confidence": float(stats_result[1] or 0),
                    "low_confidence_count": stats_result[2] or 0,
                    "high_confidence_count": stats_result[3] or 0,
                    "unique_vehicles": stats_result[4] or 0,
                    "unique_fields": stats_result[5] or 0
                },
                "method_distribution": method_distribution,
                "confidence_distribution": confidence_distribution,
                "health_indicators": {
                    "system_status": "operational",
                    "database_connected": True,
                    "average_confidence_healthy": (stats_result[1] or 0) >= 0.7,
                    "low_confidence_ratio": (stats_result[2] or 0) / max(stats_result[0] or 1, 1)
                }
            }
            
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "health_indicators": {
                "system_status": "error",
                "database_connected": False
            }
        }


def optimize_database_performance():
    """
    Optimize database performance by updating statistics and checking indexes.
    This should be run periodically as a maintenance task.
    
    Note: This function does NOT automatically delete any resolution records.
    All resolution data is retained permanently as part of the knowledge base.
    Manual cleanup can be performed separately if needed.
    """
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Update table statistics
            conn.execute(text("ANALYZE resolutions"))
            
            # Check for missing indexes
            index_check_query = text("""
                SELECT schemaname, tablename, attname, n_distinct, correlation
                FROM pg_stats 
                WHERE tablename = 'resolutions' 
                AND schemaname = 'public'
                ORDER BY n_distinct DESC
            """)
            
            index_results = conn.execute(index_check_query).fetchall()
            
            # Commit the statistics update
            conn.commit()
            
            # Log optimization results
            import logging
            logging.info(f"Database optimization completed. Index analysis: {len(index_results)} columns analyzed")
            
            return {
                "status": "success",
                "indexes_analyzed": len(index_results)
            }
            
    except Exception as e:
        import logging
        logging.error(f"Database optimization failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Add method to ProvenanceTracker for getting comprehensive metrics
def get_comprehensive_metrics(tracker: ProvenanceTracker) -> Dict[str, Any]:
    """Get comprehensive metrics from a ProvenanceTracker instance."""
    return {
        "cache_stats": {
            **tracker.cache_stats,
            "cache_size": len(tracker.cache),
            "hit_rate": tracker.cache_stats["hits"] / max(tracker.cache_stats["total_requests"], 1)
        },
        "resolution_metrics": tracker.resolution_metrics,
        "health_indicators": {
            "success_rate": tracker.resolution_metrics["successful_resolutions"] / max(tracker.resolution_metrics["total_resolutions"], 1),
            "average_confidence": tracker.resolution_metrics["average_confidence"],
            "low_confidence_ratio": tracker.resolution_metrics["low_confidence_count"] / max(tracker.resolution_metrics["total_resolutions"], 1)
        }
    }
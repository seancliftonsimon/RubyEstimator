"""
Improved data models for Ruby GEM Estimator with ranges, evidence scoring, and decision rules.

This module implements the following improvements:
1. Store conditions and ranges, not just single values
2. Evidence scoring with source taxonomy
3. Clear decision rules per attribute
4. Confidence thresholds that control writes
5. One consolidated Resolution Report
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Literal
from enum import Enum
from datetime import datetime
import statistics


class SourceTrust(Enum):
    """Source taxonomy with trust levels."""
    HIGH = 1.0  # OEM specs, owner's manual, official parts catalogs
    MEDIUM = 0.7  # Reputable review publications, data compilers (KBB, Edmunds)
    LOW = 0.4  # Dealer listings, generic parts retailers, forums
    UNKNOWN = 0.2  # Unverified or unclear source
    
    @classmethod
    def classify_source(cls, source: str) -> 'SourceTrust':
        """Classify a source string into a trust level."""
        source_lower = source.lower()
        
        # HIGH: OEM and official sources
        high_indicators = [
            'manufacturer', 'official', 'oem', '.com/specs', 'owner', 'manual',
            'parts catalog', 'service manual', 'technical spec', 'window sticker',
            'monroney', 'build sheet'
        ]
        
        # MEDIUM: Trusted automotive data sources
        medium_indicators = [
            'kbb', 'kelley', 'edmunds', 'cars.com', 'autotrader', 'cargurus',
            'motortrend', 'caranddriver', 'nhtsa', 'epa.gov'
        ]
        
        # LOW: Less reliable sources
        low_indicators = [
            'forum', 'dealer', 'dealership', 'listing', 'aftermarket',
            'parts store', 'ebay', 'craigslist', 'facebook'
        ]
        
        # Check indicators
        if any(indicator in source_lower for indicator in high_indicators):
            return cls.HIGH
        elif any(indicator in source_lower for indicator in medium_indicators):
            return cls.MEDIUM
        elif any(indicator in source_lower for indicator in low_indicators):
            return cls.LOW
        else:
            return cls.UNKNOWN


@dataclass
class ValueRange:
    """Represents a range of values with the chosen value and metadata."""
    low: Optional[float] = None
    high: Optional[float] = None
    chosen: Optional[float] = None
    estimate_type: str = "unknown"  # e.g., "median_of_trusted", "single_source", "consensus"
    variant_needed_for_exact: bool = False  # True if range exists due to variant differences
    
    def is_complete(self) -> bool:
        """Check if the range has all necessary values."""
        return self.chosen is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ConditionalFact:
    """Represents a fact that depends on vehicle variant (engine, transmission, trim)."""
    condition: str  # e.g., "base_trim", "v8_engine", "4wd"
    value: Any
    confidence: float
    sources: List[str] = field(default_factory=list)


@dataclass
class EvidenceScore:
    """Represents evidence quality for a field resolution."""
    weighted_score: float  # Sum of (source_trust * confidence) for all sources
    source_count: int
    highest_trust: SourceTrust
    sources: List[Dict[str, Any]] = field(default_factory=list)
    
    def meets_threshold(self, min_weighted_score: float = 0.7, min_sources: int = 1) -> bool:
        """Check if evidence meets minimum quality thresholds."""
        return self.weighted_score >= min_weighted_score and self.source_count >= min_sources
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'weighted_score': self.weighted_score,
            'source_count': self.source_count,
            'highest_trust': self.highest_trust.name,
            'sources': self.sources
        }


@dataclass
class FieldResolution:
    """Represents the resolution of a single field with ranges and evidence."""
    field_name: str
    value_range: Optional[ValueRange] = None
    conditional_values: List[ConditionalFact] = field(default_factory=list)
    evidence: Optional[EvidenceScore] = None
    confidence: float = 0.0
    status: Literal["ok", "needs_review", "insufficient_data"] = "insufficient_data"
    decision_rule_applied: str = ""
    warnings: List[str] = field(default_factory=list)
    
    def get_value(self) -> Any:
        """Get the chosen value or None."""
        if self.value_range and self.value_range.is_complete():
            return self.value_range.chosen
        return None
    
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if resolution has high confidence."""
        return self.confidence >= threshold and self.evidence and self.evidence.meets_threshold()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'field_name': self.field_name,
            'value_range': self.value_range.to_dict() if self.value_range else None,
            'conditional_values': [asdict(cv) for cv in self.conditional_values],
            'evidence': self.evidence.to_dict() if self.evidence else None,
            'confidence': self.confidence,
            'status': self.status,
            'decision_rule_applied': self.decision_rule_applied,
            'warnings': self.warnings
        }


@dataclass
class ResolutionReport:
    """Consolidated resolution report for a vehicle."""
    vehicle_key: str
    year: int
    make: str
    model: str
    strategy: str  # e.g., "single_call", "multi_call", "cached"
    outcome: Literal["complete", "partial", "failed"] = "failed"
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Field resolutions
    curb_weight: Optional[FieldResolution] = None
    aluminum_engine: Optional[FieldResolution] = None
    aluminum_rims: Optional[FieldResolution] = None
    catalytic_converters: Optional[FieldResolution] = None
    
    # Overall status
    overall_confidence: float = 0.0
    fields_resolved: List[str] = field(default_factory=list)
    fields_needing_review: List[str] = field(default_factory=list)
    fields_failed: List[str] = field(default_factory=list)
    action_needed: bool = False
    
    def add_field_resolution(self, resolution: FieldResolution):
        """Add a field resolution and update overall status."""
        # Store the resolution
        if resolution.field_name == 'curb_weight':
            self.curb_weight = resolution
        elif resolution.field_name == 'aluminum_engine':
            self.aluminum_engine = resolution
        elif resolution.field_name == 'aluminum_rims':
            self.aluminum_rims = resolution
        elif resolution.field_name == 'catalytic_converters':
            self.catalytic_converters = resolution
        
        # Update tracking lists
        if resolution.status == "ok":
            self.fields_resolved.append(resolution.field_name)
        elif resolution.status == "needs_review":
            self.fields_needing_review.append(resolution.field_name)
            self.action_needed = True
        else:
            self.fields_failed.append(resolution.field_name)
            self.action_needed = True
    
    def calculate_overall_status(self):
        """Calculate overall outcome and confidence."""
        all_resolutions = [r for r in [
            self.curb_weight, self.aluminum_engine, 
            self.aluminum_rims, self.catalytic_converters
        ] if r is not None]
        
        if not all_resolutions:
            self.outcome = "failed"
            self.overall_confidence = 0.0
            return
        
        # Calculate average confidence
        confidences = [r.confidence for r in all_resolutions]
        self.overall_confidence = statistics.mean(confidences) if confidences else 0.0
        
        # Determine outcome
        ok_count = len(self.fields_resolved)
        total_count = len(all_resolutions)
        
        if ok_count == total_count:
            self.outcome = "complete"
        elif ok_count > 0:
            self.outcome = "partial"
        else:
            self.outcome = "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'summary': {
                'vehicle': f"{self.year} {self.make} {self.model}",
                'strategy': self.strategy,
                'outcome': self.outcome,
                'overall_confidence': round(self.overall_confidence, 2),
                'timestamp': self.timestamp.isoformat()
            },
            'fields': {
                name: resolution.to_dict() 
                for name, resolution in [
                    ('curb_weight', self.curb_weight),
                    ('aluminum_engine', self.aluminum_engine),
                    ('aluminum_rims', self.aluminum_rims),
                    ('catalytic_converters', self.catalytic_converters)
                ] if resolution is not None
            },
            'status': {
                'resolved': self.fields_resolved,
                'needs_review': self.fields_needing_review,
                'failed': self.fields_failed,
                'action_needed': self.action_needed
            }
        }
    
    def format_compact_report(self) -> str:
        """Format a compact human-readable report."""
        lines = []
        lines.append(f"=== Resolution Report: {self.year} {self.make} {self.model} ===")
        lines.append(f"Strategy: {self.strategy} | Outcome: {self.outcome} | Confidence: {self.overall_confidence:.2f}")
        lines.append("")
        
        for resolution in [self.curb_weight, self.aluminum_engine, self.aluminum_rims, self.catalytic_converters]:
            if resolution is None:
                continue
            
            value = resolution.get_value()
            lines.append(f"• {resolution.field_name}:")
            lines.append(f"  Value: {value}")
            lines.append(f"  Confidence: {resolution.confidence:.2f} | Status: {resolution.status}")
            
            if resolution.value_range:
                vr = resolution.value_range
                if vr.low != vr.high:
                    lines.append(f"  Range: [{vr.low} - {vr.high}] ({vr.estimate_type})")
                if vr.variant_needed_for_exact:
                    lines.append(f"  ⚠ Variant-dependent - exact value needs trim/engine info")
            
            if resolution.evidence:
                ev = resolution.evidence
                lines.append(f"  Evidence: {ev.source_count} sources (trust: {ev.highest_trust.name}, score: {ev.weighted_score:.2f})")
                if ev.sources:
                    top_sources = ev.sources[:3]  # Show top 3 sources
                    for src in top_sources:
                        lines.append(f"    - {src.get('name', 'Unknown')}")
            
            if resolution.warnings:
                for warning in resolution.warnings:
                    lines.append(f"  ⚠ {warning}")
            
            lines.append("")
        
        lines.append(f"Action needed: {'YES' if self.action_needed else 'NO'}")
        
        return "\n".join(lines)


class DecisionRules:
    """Clear decision rules for each attribute type."""
    
    # Confidence thresholds
    MIN_CONFIDENCE_FOR_WRITE = 0.7
    MIN_EVIDENCE_WEIGHT_FOR_WRITE = 0.7
    MIN_SOURCES_FOR_WRITE = 1
    
    @staticmethod
    def resolve_curb_weight(candidates: List[Dict[str, Any]], confidence_threshold: float = MIN_CONFIDENCE_FOR_WRITE) -> FieldResolution:
        """
        Decision rule for curb weight:
        - Take median of trusted sources (HIGH and MEDIUM trust)
        - Store {low, high, chosen}
        - Require min evidence weight
        """
        resolution = FieldResolution(
            field_name="curb_weight",
            decision_rule_applied="median_of_trusted_sources"
        )
        
        if not candidates:
            resolution.status = "insufficient_data"
            resolution.warnings.append("No candidates provided")
            return resolution
        
        # Classify and filter candidates
        trusted_values = []
        all_sources = []
        weighted_sum = 0.0
        highest_trust = SourceTrust.UNKNOWN
        
        for candidate in candidates:
            source_name = candidate.get('source', 'unknown')
            value = candidate.get('value')
            source_confidence = candidate.get('confidence', 0.7)
            
            if value is None:
                continue
            
            trust = SourceTrust.classify_source(source_name)
            
            # Only use HIGH and MEDIUM trust sources for value calculation
            if trust in [SourceTrust.HIGH, SourceTrust.MEDIUM]:
                trusted_values.append(value)
            
            # Track all sources for evidence
            all_sources.append({
                'name': source_name,
                'value': value,
                'trust': trust.name,
                'confidence': source_confidence
            })
            
            # Calculate weighted evidence
            weighted_sum += trust.value * source_confidence
            highest_trust = max(highest_trust, trust, key=lambda x: x.value)
        
        # Create evidence score
        resolution.evidence = EvidenceScore(
            weighted_score=weighted_sum,
            source_count=len(all_sources),
            highest_trust=highest_trust,
            sources=all_sources
        )
        
        if not trusted_values:
            resolution.status = "needs_review"
            resolution.warnings.append("No trusted sources found - only low-quality data available")
            resolution.confidence = 0.3
            return resolution
        
        # Calculate range and chosen value
        low = min(trusted_values)
        high = max(trusted_values)
        chosen = statistics.median(trusted_values)
        
        resolution.value_range = ValueRange(
            low=low,
            high=high,
            chosen=chosen,
            estimate_type="median_of_trusted",
            variant_needed_for_exact=(high - low) > (chosen * 0.1)  # >10% variation suggests variant dependency
        )
        
        # Calculate confidence based on agreement and evidence quality
        if len(trusted_values) == 1:
            resolution.confidence = 0.7  # Single trusted source
        else:
            # Higher confidence if values are close
            variation = (high - low) / chosen if chosen > 0 else 1.0
            if variation < 0.05:  # Within 5%
                resolution.confidence = 0.95
            elif variation < 0.10:  # Within 10%
                resolution.confidence = 0.85
            else:
                resolution.confidence = 0.75
        
        # Check if meets threshold
        if resolution.confidence >= confidence_threshold and resolution.evidence.meets_threshold(
            DecisionRules.MIN_EVIDENCE_WEIGHT_FOR_WRITE, DecisionRules.MIN_SOURCES_FOR_WRITE
        ):
            resolution.status = "ok"
        else:
            resolution.status = "needs_review"
            resolution.warnings.append(f"Confidence {resolution.confidence:.2f} or evidence weight {weighted_sum:.2f} below threshold")
        
        return resolution
    
    @staticmethod
    def resolve_aluminum_engine(candidates: List[Dict[str, Any]], confidence_threshold: float = MIN_CONFIDENCE_FOR_WRITE) -> FieldResolution:
        """
        Decision rule for aluminum engine:
        - Boolean field with high evidence bar (prefer OEM docs)
        - Once true with high confidence, it's variant-stable
        - Require strong evidence (HIGH trust preferred)
        """
        resolution = FieldResolution(
            field_name="aluminum_engine",
            decision_rule_applied="high_confidence_boolean_oem_preferred"
        )
        
        if not candidates:
            resolution.status = "insufficient_data"
            resolution.warnings.append("No candidates provided")
            return resolution
        
        # Track evidence
        all_sources = []
        weighted_sum = 0.0
        highest_trust = SourceTrust.UNKNOWN
        votes_aluminum = 0
        votes_iron = 0
        
        for candidate in candidates:
            source_name = candidate.get('source', 'unknown')
            value = candidate.get('value')
            source_confidence = candidate.get('confidence', 0.7)
            
            if value is None:
                continue
            
            trust = SourceTrust.classify_source(source_name)
            
            # Count votes
            if value:
                votes_aluminum += trust.value
            else:
                votes_iron += trust.value
            
            # Track sources
            all_sources.append({
                'name': source_name,
                'value': 'aluminum' if value else 'iron',
                'trust': trust.name,
                'confidence': source_confidence
            })
            
            # Calculate weighted evidence
            weighted_sum += trust.value * source_confidence
            highest_trust = max(highest_trust, trust, key=lambda x: x.value)
        
        # Create evidence score
        resolution.evidence = EvidenceScore(
            weighted_score=weighted_sum,
            source_count=len(all_sources),
            highest_trust=highest_trust,
            sources=all_sources
        )
        
        # Determine final value based on votes
        if votes_aluminum == 0 and votes_iron == 0:
            resolution.status = "insufficient_data"
            resolution.confidence = 0.0
            return resolution
        
        is_aluminum = votes_aluminum > votes_iron
        agreement_ratio = max(votes_aluminum, votes_iron) / (votes_aluminum + votes_iron)
        
        resolution.value_range = ValueRange(
            chosen=1.0 if is_aluminum else 0.0,
            estimate_type="consensus_vote"
        )
        
        # Calculate confidence based on agreement and source quality
        if agreement_ratio >= 0.9 and highest_trust == SourceTrust.HIGH:
            resolution.confidence = 0.95
        elif agreement_ratio >= 0.75 and highest_trust in [SourceTrust.HIGH, SourceTrust.MEDIUM]:
            resolution.confidence = 0.85
        elif agreement_ratio >= 0.6:
            resolution.confidence = 0.70
        else:
            resolution.confidence = 0.50
        
        # Check thresholds
        if resolution.confidence >= confidence_threshold and resolution.evidence.meets_threshold(
            DecisionRules.MIN_EVIDENCE_WEIGHT_FOR_WRITE, DecisionRules.MIN_SOURCES_FOR_WRITE
        ):
            resolution.status = "ok"
        else:
            resolution.status = "needs_review"
            resolution.warnings.append(f"Insufficient evidence or low agreement (conf: {resolution.confidence:.2f}, agree: {agreement_ratio:.2f})")
        
        return resolution
    
    @staticmethod
    def resolve_aluminum_rims(candidates: List[Dict[str, Any]], confidence_threshold: float = MIN_CONFIDENCE_FOR_WRITE) -> FieldResolution:
        """
        Decision rule for aluminum rims:
        - Trim-dependent
        - Default to "aluminum" if trim unknown but market share supports it
        - Store exceptions in conditional records
        """
        resolution = FieldResolution(
            field_name="aluminum_rims",
            decision_rule_applied="trim_dependent_with_market_default"
        )
        
        if not candidates:
            resolution.status = "insufficient_data"
            resolution.warnings.append("No candidates provided")
            return resolution
        
        # Similar logic to aluminum_engine but with trim awareness
        all_sources = []
        weighted_sum = 0.0
        highest_trust = SourceTrust.UNKNOWN
        votes_aluminum = 0
        votes_steel = 0
        trim_variants = {}
        
        for candidate in candidates:
            source_name = candidate.get('source', 'unknown')
            value = candidate.get('value')
            source_confidence = candidate.get('confidence', 0.7)
            trim = candidate.get('trim', 'unknown')
            
            if value is None:
                continue
            
            trust = SourceTrust.classify_source(source_name)
            
            # Track trim-specific values
            if trim != 'unknown':
                if trim not in trim_variants:
                    trim_variants[trim] = {'aluminum': 0, 'steel': 0}
                if value:
                    trim_variants[trim]['aluminum'] += trust.value
                else:
                    trim_variants[trim]['steel'] += trust.value
            
            # Count overall votes
            if value:
                votes_aluminum += trust.value
            else:
                votes_steel += trust.value
            
            # Track sources
            all_sources.append({
                'name': source_name,
                'value': 'aluminum' if value else 'steel',
                'trust': trust.name,
                'confidence': source_confidence,
                'trim': trim
            })
            
            weighted_sum += trust.value * source_confidence
            highest_trust = max(highest_trust, trust, key=lambda x: x.value)
        
        resolution.evidence = EvidenceScore(
            weighted_score=weighted_sum,
            source_count=len(all_sources),
            highest_trust=highest_trust,
            sources=all_sources
        )
        
        # Store trim-specific values as conditional facts
        for trim, votes in trim_variants.items():
            is_aluminum = votes['aluminum'] > votes['steel']
            conf = max(votes['aluminum'], votes['steel']) / (votes['aluminum'] + votes['steel'])
            resolution.conditional_values.append(ConditionalFact(
                condition=f"trim={trim}",
                value=is_aluminum,
                confidence=conf,
                sources=[s['name'] for s in all_sources if s.get('trim') == trim]
            ))
        
        # Determine default value
        if votes_aluminum == 0 and votes_steel == 0:
            resolution.status = "insufficient_data"
            resolution.confidence = 0.0
            return resolution
        
        is_aluminum = votes_aluminum > votes_steel
        agreement_ratio = max(votes_aluminum, votes_steel) / (votes_aluminum + votes_steel)
        
        resolution.value_range = ValueRange(
            chosen=1.0 if is_aluminum else 0.0,
            estimate_type="most_common_in_market" if trim_variants else "consensus",
            variant_needed_for_exact=len(trim_variants) > 1
        )
        
        # Calculate confidence
        if agreement_ratio >= 0.8:
            resolution.confidence = 0.85
        elif agreement_ratio >= 0.65:
            resolution.confidence = 0.75
        else:
            resolution.confidence = 0.60
        
        if trim_variants and len(trim_variants) > 1:
            resolution.warnings.append(f"Trim-dependent: {len(trim_variants)} variants found - default set to most common")
        
        # Check thresholds
        if resolution.confidence >= confidence_threshold and resolution.evidence.meets_threshold(
            DecisionRules.MIN_EVIDENCE_WEIGHT_FOR_WRITE, DecisionRules.MIN_SOURCES_FOR_WRITE
        ):
            resolution.status = "ok"
        else:
            resolution.status = "needs_review"
        
        return resolution
    
    @staticmethod
    def resolve_catalytic_converters(candidates: List[Dict[str, Any]], confidence_threshold: float = 0.6) -> FieldResolution:
        """
        Decision rule for catalytic converters:
        - Engine-dependent (4-cyl vs V6 vs V8)
        - If engine unknown, store range (1-2 most common)
        - Set chosen to most common only if evidence supports it
        """
        resolution = FieldResolution(
            field_name="catalytic_converters",
            decision_rule_applied="engine_dependent_with_range"
        )
        
        if not candidates:
            resolution.status = "insufficient_data"
            resolution.warnings.append("No candidates provided")
            return resolution
        
        # Track evidence by engine type
        all_sources = []
        weighted_sum = 0.0
        highest_trust = SourceTrust.UNKNOWN
        count_votes = {}  # count -> weighted votes
        engine_variants = {}
        
        for candidate in candidates:
            source_name = candidate.get('source', 'unknown')
            value = candidate.get('value')
            source_confidence = candidate.get('confidence', 0.6)
            engine = candidate.get('engine', 'unknown')
            
            if value is None:
                continue
            
            trust = SourceTrust.classify_source(source_name)
            
            # Track engine-specific counts
            if engine != 'unknown':
                if engine not in engine_variants:
                    engine_variants[engine] = {}
                if value not in engine_variants[engine]:
                    engine_variants[engine][value] = 0.0
                engine_variants[engine][value] += trust.value
            
            # Count overall votes
            if value not in count_votes:
                count_votes[value] = 0.0
            count_votes[value] += trust.value * source_confidence
            
            # Track sources
            all_sources.append({
                'name': source_name,
                'value': value,
                'trust': trust.name,
                'confidence': source_confidence,
                'engine': engine
            })
            
            weighted_sum += trust.value * source_confidence
            highest_trust = max(highest_trust, trust, key=lambda x: x.value)
        
        resolution.evidence = EvidenceScore(
            weighted_score=weighted_sum,
            source_count=len(all_sources),
            highest_trust=highest_trust,
            sources=all_sources
        )
        
        # Store engine-specific values as conditional facts
        for engine, counts in engine_variants.items():
            most_common = max(counts.items(), key=lambda x: x[1])
            total_votes = sum(counts.values())
            conf = most_common[1] / total_votes if total_votes > 0 else 0.0
            resolution.conditional_values.append(ConditionalFact(
                condition=f"engine={engine}",
                value=most_common[0],
                confidence=conf,
                sources=[s['name'] for s in all_sources if s.get('engine') == engine]
            ))
        
        if not count_votes:
            resolution.status = "needs_review"
            resolution.confidence = 0.4
            resolution.warnings.append("No catalytic converter data available - using default estimate")
            # Store as range without chosen value
            resolution.value_range = ValueRange(
                low=1,
                high=2,
                chosen=None,  # Don't choose without evidence
                estimate_type="unknown_pending_variant",
                variant_needed_for_exact=True
            )
            return resolution
        
        # Determine range and chosen value
        all_counts = list(count_votes.keys())
        most_common_count = max(count_votes.items(), key=lambda x: x[1])[0]
        
        resolution.value_range = ValueRange(
            low=min(all_counts),
            high=max(all_counts),
            chosen=most_common_count,
            estimate_type="most_common" if len(engine_variants) == 0 else "engine_dependent",
            variant_needed_for_exact=len(engine_variants) > 1 or len(count_votes) > 1
        )
        
        # Calculate confidence based on evidence quality and agreement
        total_votes = sum(count_votes.values())
        agreement = count_votes[most_common_count] / total_votes if total_votes > 0 else 0.0
        
        if agreement >= 0.7 and highest_trust in [SourceTrust.HIGH, SourceTrust.MEDIUM]:
            resolution.confidence = 0.75
        elif agreement >= 0.5:
            resolution.confidence = 0.65
        else:
            resolution.confidence = 0.50
        
        if len(engine_variants) > 1:
            resolution.warnings.append(f"Engine-dependent: {len(engine_variants)} engine variants found - chose most common")
        
        # Note: Catalytic converters have lower threshold (0.6) due to difficulty of obtaining exact data
        if resolution.confidence >= confidence_threshold and resolution.evidence.meets_threshold(
            0.5,  # Lower evidence threshold for cat converters
            1
        ):
            resolution.status = "ok"
        else:
            resolution.status = "needs_review"
            resolution.warnings.append(f"Low confidence ({resolution.confidence:.2f}) - verify with specific engine configuration")
        
        return resolution


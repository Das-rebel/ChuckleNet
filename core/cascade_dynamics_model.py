#!/usr/bin/env python3
"""
Cascade Dynamics Modeling - Mathematical Laughter Contagion System
Implements multiplicative vs. additive laughter patterns for audience reaction prediction
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


class LaughterType(Enum):
    """Classification of laughter types based on biosemotic theory"""
    DUCHENNE_SPONTANEOUS = "duchenne_spontaneous"  # Multiplicative cascade
    DUCHENNE_CONTAGIOUS = "duchenne_contagious"    # Exponential spread
    VOLITIONAL_POLITE = "volitional_polite"        # Additive pattern
    VOLITIONAL_CONTROLLED = "volitional_controlled" # Linear propagation


@dataclass
class CascadeParameters:
    """Mathematical parameters for laughter cascade dynamics"""
    reproduction_number: float  # R0: Laughter reproduction rate
    cascade_multiplier: float   # λ: Multiplicative factor
    additive_factor: float       # α: Additive component
    decay_rate: float           # δ: Temporal decay
    threshold_probability: float # Pτ: Activation threshold
    carrying_capacity: float    # K: Maximum cascade size


@dataclass
class CascadePrediction:
    """Complete cascade dynamics prediction"""
    cascade_type: LaughterType
    final_audience_reach: float  # 0.0 to 1.0 (percentage of audience)
    time_to_peak: float          # Seconds until maximum laughter
    peak_intensity: float        # Maximum laughter intensity
    cascade_velocity: float      # Speed of laughter spread
    contagion_probability: float # Probability of cascade initiation
    duration: float              # Total cascade duration
    mathematical_model: str      # Model type used


class BiosemoticCascadeDynamics:
    """
    Advanced mathematical modeling of laughter cascade dynamics based on
    evolutionary biosemotic theory and social contagion principles
    """

    def __init__(self):
        """Initialize biosemotic cascade dynamics system"""

        # Duchenne cascade parameters (spontaneous laughter)
        self.duchenne_params = CascadeParameters(
            reproduction_number=2.3,    # High reproduction for contagious laughter
            cascade_multiplier=2.3,     # Multiplicative factor
            additive_factor=0.1,         # Minimal additive component
            decay_rate=0.15,            # Slow decay (sustained laughter)
            threshold_probability=0.3,   # Lower threshold (easier activation)
            carrying_capacity=1.0        # Full audience reach possible
        )

        # Volitional cascade parameters (controlled laughter)
        self.volitional_params = CascadeParameters(
            reproduction_number=0.8,    # Low reproduction (polite laughter)
            cascade_multiplier=1.0,     # Linear (no multiplication)
            additive_factor=0.6,         # Strong additive component
            decay_rate=0.45,             # Fast decay (short-lived)
            threshold_probability=0.6,   # Higher threshold (harder activation)
            carrying_capacity=0.4        # Limited cascade spread
        )

        # Mixed cascade parameters (transitional states)
        self.mixed_params = CascadeParameters(
            reproduction_number=1.5,
            cascade_multiplier=1.5,
            additive_factor=0.35,
            decay_rate=0.25,
            threshold_probability=0.45,
            carrying_capacity=0.7
        )

    def classify_cascade_type(
        self,
        duchenne_probability: float,
        audience_size: int,
        initial_intensity: float
    ) -> LaughterType:
        """Classify the type of laughter cascade based on biosemotic features"""

        # High Duchenne probability + high intensity = spontaneous contagious
        if duchenne_probability > 0.7 and initial_intensity > 0.6:
            return LaughterType.DUCHENNE_CONTAGIOUS

        # High Duchenne probability but lower intensity = spontaneous
        elif duchenne_probability > 0.6:
            return LaughterType.DUCHENNE_SPONTANEOUS

        # Low Duchenne probability + polite context = controlled volitional
        elif duchenne_probability < 0.4 and initial_intensity < 0.4:
            return LaughterType.VOLITIONAL_POLITE

        # Middle ground = controlled but genuine
        else:
            return LaughterType.VOLITIONAL_CONTROLLED

    def predict_multiplicative_cascade(
        self,
        audience_size: int,
        initial_laughers: int,
        params: CascadeParameters,
        time_steps: int = 100
    ) -> Dict:
        """
        Model multiplicative cascade dynamics (Duchenne laughter)

        Based on logistic growth equation with multiplicative factor:
        dN/dt = λ * N * (1 - N/K) * (1 - e^(-δ*t))
        """

        # Initial conditions
        N = [initial_laughers]  # Number of people laughing at each time step
        t = list(range(time_steps))

        # Simulate multiplicative cascade
        for i in range(1, time_steps):
            current_N = N[-1]

            # Multiplicative growth with carrying capacity
            growth_rate = params.cascade_multiplier
            carrying_factor = 1 - (current_N / (params.carrying_capacity * audience_size))
            temporal_factor = 1 - math.exp(-params.decay_rate * t[i])

            # Logistic growth equation
            dN = growth_rate * current_N * carrying_factor * temporal_factor

            # Add stochastic element (social noise)
            noise = np.random.normal(0, 0.05 * current_N)
            new_N = max(0, current_N + dN + noise)

            N.append(min(new_N, audience_size))  # Cap at audience size

        # Calculate metrics
        peak_laughers = max(N)
        final_audience_reach = N[-1] / audience_size
        time_to_peak = t[N.index(peak_laughers)] * 0.1  # 0.1s per time step
        peak_intensity = peak_laughers / audience_size
        cascade_velocity = (peak_laughers - initial_laughers) / (time_to_peak + 1)

        return {
            'cascade_trajectory': N,
            'time_steps': t,
            'peak_laughers': int(peak_laughers),
            'final_reach': final_audience_reach,
            'time_to_peak': time_to_peak,
            'peak_intensity': peak_intensity,
            'cascade_velocity': cascade_velocity,
            'model_type': 'multiplicative_logistic'
        }

    def predict_additive_cascade(
        self,
        audience_size: int,
        initial_laughers: int,
        params: CascadeParameters,
        time_steps: int = 100
    ) -> Dict:
        """
        Model additive cascade dynamics (volitional laughter)

        Based on linear growth with saturation:
        dN/dt = α * (K - N) * e^(-δ*t)
        """

        # Initial conditions
        N = [initial_laughers]
        t = list(range(time_steps))

        # Simulate additive cascade
        for i in range(1, time_steps):
            current_N = N[-1]

            # Additive growth with saturation
            carrying_capacity = params.carrying_capacity * audience_size
            remaining_capacity = carrying_capacity - current_N
            temporal_decay = math.exp(-params.decay_rate * t[i])

            # Linear growth equation
            dN = params.additive_factor * remaining_capacity * temporal_decay

            # Add small stochastic element
            noise = np.random.normal(0, 0.02 * audience_size)
            new_N = max(0, current_N + dN + noise)

            N.append(min(new_N, carrying_capacity))

        # Calculate metrics
        peak_laughers = max(N)
        final_audience_reach = N[-1] / audience_size
        time_to_peak = t[N.index(peak_laughers)] * 0.1
        peak_intensity = peak_laughers / audience_size
        cascade_velocity = (peak_laughers - initial_laughers) / (time_to_peak + 1)

        return {
            'cascade_trajectory': N,
            'time_steps': t,
            'peak_laughers': int(peak_laughers),
            'final_reach': final_audience_reach,
            'time_to_peak': time_to_peak,
            'peak_intensity': peak_intensity,
            'cascade_velocity': cascade_velocity,
            'model_type': 'additive_linear'
        }

    def predict_audience_reaction(
        self,
        duchenne_probability: float,
        audience_size: int,
        initial_intensity: float,
        social_context: str = 'comedy_club'
    ) -> CascadePrediction:
        """
        Complete audience reaction prediction using cascade dynamics
        """

        # Classify cascade type
        cascade_type = self.classify_cascade_type(
            duchenne_probability, audience_size, initial_intensity
        )

        # Select appropriate parameters
        if cascade_type in [LaughterType.DUCHENNE_SPONTANEOUS, LaughterType.DUCHENNE_CONTAGIOUS]:
            params = self.duchenne_params
            initial_laughers = max(1, int(audience_size * initial_intensity * 0.5))
            use_multiplicative = True
        else:
            params = self.volitional_params
            initial_laughers = max(1, int(audience_size * initial_intensity * 0.2))
            use_multiplicative = False

        # Context adjustments
        context_modifiers = {
            'comedy_club': 1.2,      # Enhanced contagion
            'theater': 1.0,          # Standard
            'formal_event': 0.7,     # Reduced contagion
            'intimate_gathering': 1.5  # High contagion
        }
        context_factor = context_modifiers.get(social_context, 1.0)

        # Apply context factor to parameters
        params.cascade_multiplier *= context_factor
        params.carrying_capacity *= context_factor

        # Run cascade simulation
        if use_multiplicative:
            cascade_result = self.predict_multiplicative_cascade(
                audience_size, initial_laughers, params
            )
        else:
            cascade_result = self.predict_additive_cascade(
                audience_size, initial_laughers, params
            )

        # Calculate duration based on decay
        final_count = cascade_result['cascade_trajectory'][-1]
        duration = self._calculate_cascade_duration(
            cascade_result['cascade_trajectory'],
            params.decay_rate
        )

        # Contagion probability
        if cascade_type == LaughterType.DUCHENNE_CONTAGIOUS:
            contagion_prob = min(0.95, 0.7 + (initial_intensity * 0.25))
        elif cascade_type == LaughterType.DUCHENNE_SPONTANEOUS:
            contagion_prob = min(0.85, 0.5 + (initial_intensity * 0.35))
        else:
            contagion_prob = min(0.4, 0.1 + (initial_intensity * 0.3))

        return CascadePrediction(
            cascade_type=cascade_type,
            final_audience_reach=cascade_result['final_reach'],
            time_to_peak=cascade_result['time_to_peak'],
            peak_intensity=cascade_result['peak_intensity'],
            cascade_velocity=cascade_result['cascade_velocity'],
            contagion_probability=contagion_prob,
            duration=duration,
            mathematical_model=cascade_result['model_type']
        )

    def _calculate_cascade_duration(self, trajectory: List[int], decay_rate: float) -> float:
        """Calculate total cascade duration until 90% decay from peak"""

        peak = max(trajectory)
        peak_index = trajectory.index(peak)
        threshold = peak * 0.1  # 90% decay threshold

        for i in range(peak_index, len(trajectory)):
            if trajectory[i] < threshold:
                return (i - peak_index) * 0.1  # 0.1s per time step

        return len(trajectory) * 0.1  # Full duration if no decay

    def compare_multiplicative_vs_additive(
        self,
        audience_size: int,
        initial_intensity: float,
        time_steps: int = 100
    ) -> Dict:
        """
        Direct comparison of multiplicative vs. additive cascade dynamics
        for biosemotic theory validation
        """

        # Run both models
        multiplicative_result = self.predict_multiplicative_cascade(
            audience_size,
            max(1, int(audience_size * initial_intensity)),
            self.duchenne_params,
            time_steps
        )

        additive_result = self.predict_additive_cascade(
            audience_size,
            max(1, int(audience_size * initial_intensity)),
            self.volitional_params,
            time_steps
        )

        # Calculate comparison metrics with safety for zero division
        multiplicative_advantage = {
            'peak_advantage': multiplicative_result['peak_intensity'] /
                             max(additive_result['peak_intensity'], 0.001),
            'reach_advantage': multiplicative_result['final_reach'] /
                            max(additive_result['final_reach'], 0.001),
            'velocity_advantage': multiplicative_result['cascade_velocity'] /
                               max(additive_result['cascade_velocity'], 0.001),
            'sustained_advantage': multiplicative_result['time_to_peak'] /
                                  max(additive_result['time_to_peak'], 0.001)
        }

        return {
            'multiplicative_result': multiplicative_result,
            'additive_result': additive_result,
            'advantage_metrics': multiplicative_advantage,
            'biosemotic_validation': multiplicative_advantage['peak_advantage'] > 1.5,
            'cascade_separation': abs(multiplicative_result['final_reach'] -
                                   additive_result['final_reach']) > 0.3
        }


class AudienceReactionSimulator:
    """
    Advanced audience reaction simulation using cascade dynamics
    """

    def __init__(self):
        """Initialize audience reaction simulator"""
        self.cascade_model = BiosemoticCascadeDynamics()

    def simulate_comedy_performance(
        self,
        jokes: List[Dict],
        audience_size: int,
        social_context: str = 'comedy_club'
    ) -> Dict:
        """
        Simulate complete comedy performance with audience reactions

        Args:
            jokes: List of jokes with duchenne_prob and intensity
            audience_size: Number of audience members
            social_context: Type of event
        """

        performance_results = []

        for i, joke in enumerate(jokes):
            # Predict cascade for each joke
            cascade_prediction = self.cascade_model.predict_audience_reaction(
                duchenne_probability=joke['duchenne_prob'],
                audience_size=audience_size,
                initial_intensity=joke['intensity'],
                social_context=social_context
            )

            result = {
                'joke_number': i + 1,
                'joke_text': joke.get('text', ''),
                'cascade_type': cascade_prediction.cascade_type,
                'audience_reaction': cascade_prediction.final_audience_reach,
                'peak_intensity': cascade_prediction.peak_intensity,
                'time_to_peak': cascade_prediction.time_to_peak,
                'contagion_prob': cascade_prediction.contagion_probability,
                'duration': cascade_prediction.duration,
                'mathematical_model': cascade_prediction.mathematical_model
            }

            performance_results.append(result)

        # Calculate performance metrics
        total_laughter = sum(r['audience_reaction'] for r in performance_results)
        avg_intensity = sum(r['peak_intensity'] for r in performance_results) / len(performance_results)
        contagious_moments = sum(1 for r in performance_results if r['contagion_prob'] > 0.7)

        return {
            'individual_jokes': performance_results,
            'performance_metrics': {
                'total_audience_engagement': total_laughter,
                'average_intensity': avg_intensity,
                'contagious_moments': contagious_moments,
                'success_rate': contagious_moments / len(performance_results)
            },
            'audience_size': audience_size,
            'social_context': social_context
        }


def create_cascade_dynamics_model() -> BiosemoticCascadeDynamics:
    """Factory function to create cascade dynamics model"""
    return BiosemoticCascadeDynamics()


def create_audience_simulator() -> AudienceReactionSimulator:
    """Factory function to create audience reaction simulator"""
    return AudienceReactionSimulator()
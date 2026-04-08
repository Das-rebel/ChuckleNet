#!/usr/bin/env python3
"""
GCACU Unified Platform - Production API Layer
=============================================

Complete REST API and Python API for the GCACU Unified Platform.
Provides production-ready endpoints, request validation, response formatting,
and comprehensive documentation.

Author: GCACU Development Team
Date: 2026-04-03
Version: 1.0.0
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

# Web framework
try:
    from fastapi import FastAPI, HTTPException, Query, Body, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, validator
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available - API functionality limited")

# Import platform
try:
    from training.gcacu_unified_platform import (
        GCACUUnifiedPlatform, PlatformConfig, ProcessingMode,
        PredictionResult, BatchProcessingResult, ContentDomain
    )
    from training.platform_configuration import ConfigurationManager, DeploymentPreset
    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False
    logging.warning("Platform not available - using mock API")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# API DATA MODELS
# ============================================================================

class ProcessingModeEnum(str, Enum):
    """Processing mode enumeration"""
    AUTO = "auto"
    HIGH_ACCURACY = "high_accuracy"
    HIGH_SPEED = "high_speed"
    MEMORY_OPTIMIZED = "memory_optimized"
    CULTURAL_AWARE = "cultural_aware"
    MULTILINGUAL = "multilingual"
    PRODUCTION = "production"


class PredictionRequest(BaseModel):
    """Request model for laughter prediction"""
    text: str = Field(..., description="Input text content", min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional content metadata")
    mode: Optional[ProcessingModeEnum] = Field(ProcessingModeEnum.AUTO, description="Processing mode")

    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

    @validator('metadata')
    def validate_metadata(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v


class BatchPredictionRequest(BaseModel):
    """Request model for batch prediction"""
    texts: List[str] = Field(..., description="List of input texts", min_items=1, max_items=1000)
    metadata_list: Optional[List[Dict[str, Any]]] = Field(None, description="Optional metadata for each text")
    mode: Optional[ProcessingModeEnum] = Field(ProcessingModeEnum.AUTO, description="Processing mode")

    @validator('texts')
    def validate_texts(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Texts list cannot be empty")
        if len(v) > 1000:
            raise ValueError("Maximum 1000 texts per batch")
        return [text.strip() for text in v if text.strip()]

    @validator('metadata_list')
    def validate_metadata_list(cls, v, values):
        if v is not None:
            if len(v) != len(values.get('texts', [])):
                raise ValueError("Metadata list length must match texts list length")
        return v


class ContentAnalysisRequest(BaseModel):
    """Request model for content analysis"""
    text: str = Field(..., description="Input text content", min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional content metadata")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Platform version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    predictions_processed: int = Field(..., description="Total predictions processed")
    memory_usage_mb: float = Field(..., description="Current memory usage in MB")
    components_available: Dict[str, bool] = Field(..., description="Available components")


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class PredictionResponse(BaseModel):
    """Response model for single prediction"""
    prediction: float = Field(..., description="Laughter probability")
    confidence: float = Field(..., description="Prediction confidence")
    uncertainty: Optional[float] = Field(None, description="Prediction uncertainty")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(..., description="Model architecture used")
    language_detected: str = Field(..., description="Detected language")
    content_domain: str = Field(..., description="Detected content domain")
    cultural_context: Optional[Dict[str, Any]] = Field(None, description="Cultural context if available")
    prediction_id: str = Field(..., description="Unique prediction identifier")
    timestamp: str = Field(..., description="Prediction timestamp")


class BatchPredictionResponse(BaseModel):
    """Response model for batch prediction"""
    results: List[PredictionResponse] = Field(..., description="Individual prediction results")
    total_processing_time_ms: float = Field(..., description="Total processing time")
    average_time_per_item_ms: float = Field(..., description="Average time per item")
    throughput_items_per_second: float = Field(..., description="Processing throughput")
    success_rate: float = Field(..., description="Success rate")
    total_items: int = Field(..., description="Total items processed")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    timestamp: str = Field(..., description="Batch timestamp")


class ContentAnalysisResponse(BaseModel):
    """Response model for content analysis"""
    domain: str = Field(..., description="Detected content domain")
    culture: Optional[str] = Field(None, description="Detected culture")
    language: str = Field(..., description="Detected language")
    confidence: float = Field(..., description="Analysis confidence")
    requires_cultural_adaptation: bool = Field(..., description="Whether cultural adaptation is needed")
    recommended_architecture: str = Field(..., description="Recommended model architecture")
    processing_complexity: float = Field(..., description="Processing complexity (0-1)")
    estimated_processing_time_ms: float = Field(..., description="Estimated processing time")
    analysis_id: str = Field(..., description="Unique analysis identifier")
    timestamp: str = Field(..., description="Analysis timestamp")


class PlatformInfoResponse(BaseModel):
    """Response model for platform information"""
    name: str = Field(..., description="Platform name")
    version: str = Field(..., description="Platform version")
    description: str = Field(..., description="Platform description")
    capabilities: Dict[str, bool] = Field(..., description="Platform capabilities")
    supported_domains: List[str] = Field(..., description="Supported content domains")
    supported_modes: List[str] = Field(..., description="Supported processing modes")
    configuration: Dict[str, Any] = Field(..., description="Current configuration")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

class GCACUPlatformAPI:
    """
    Production-ready REST API for GCACU Unified Platform.

    Features:
    - Comprehensive request validation
    - Detailed error handling
    - Performance monitoring
    - Health checks
    - API documentation
    - Rate limiting ready
    """

    def __init__(self, platform: Optional[GCACUUnifiedPlatform] = None):
        """Initialize API with platform instance"""
        self.platform = platform
        self.startup_time = time.time()
        self.request_count = 0

        if FASTAPI_AVAILABLE:
            self.app = FastAPI(
                title="GCACU Unified Platform API",
                description="Production-ready autonomous laughter prediction system",
                version="1.0.0",
                docs_url="/docs",
                redoc_url="/redoc"
            )

            # Add CORS middleware
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Configure appropriately for production
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

            # Setup routes
            self._setup_routes()

            # Add startup/shutdown events
            @self.app.on_event("startup")
            async def startup_event():
                logger.info("🚀 GCACU Platform API started")

            @self.app.on_event("shutdown")
            async def shutdown_event():
                logger.info("🛑 GCACU Platform API shutting down")
                if self.platform:
                    self.platform.shutdown()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/", tags=["Root"])
        async def root():
            """Root endpoint with API information"""
            return {
                "name": "GCACU Unified Platform API",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "predict": "/predict",
                    "batch": "/predict_batch",
                    "analyze": "/analyze",
                    "health": "/health",
                    "info": "/info",
                    "metrics": "/metrics"
                },
                "documentation": "/docs"
            }

        @self.app.get("/health", response_model=HealthResponse, tags=["Health"])
        async def health_check():
            """Health check endpoint"""
            if self.platform:
                metrics = self.platform.get_platform_metrics()
                return HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    uptime_seconds=time.time() - self.startup_time,
                    predictions_processed=metrics.get('total_predictions', 0),
                    memory_usage_mb=metrics.get('memory_usage_mb', 0),
                    components_available=metrics.get('components_available', {})
                )
            else:
                return HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    uptime_seconds=time.time() - self.startup_time,
                    predictions_processed=0,
                    memory_usage_mb=0,
                    components_available={}
                )

        @self.app.get("/ready", tags=["Health"])
        async def readiness_check():
            """Readiness check endpoint"""
            if self.platform:
                return {"status": "ready", "platform_initialized": True}
            else:
                return {"status": "ready", "platform_initialized": False}

        @self.app.get("/info", response_model=PlatformInfoResponse, tags=["Info"])
        async def platform_info():
            """Get platform information"""
            if self.platform:
                info = self.platform.get_platform_info()
                return PlatformInfoResponse(**info)
            else:
                return PlatformInfoResponse(
                    name="GCACU Unified Platform",
                    version="1.0.0",
                    description="Production-ready autonomous laughter prediction system",
                    capabilities={},
                    supported_domains=[d.value for d in ContentDomain],
                    supported_modes=[m.value for m in ProcessingMode],
                    configuration={}
                )

        @self.app.get("/metrics", tags=["Metrics"])
        async def platform_metrics():
            """Get platform performance metrics"""
            if self.platform:
                return self.platform.get_platform_metrics()
            else:
                return {
                    "total_predictions": 0,
                    "uptime_seconds": time.time() - self.startup_time,
                    "status": "running"
                }

        @self.app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
        async def predict_laughter(request: PredictionRequest):
            """
            Predict laughter from text content.

            - **text**: Input text content (1-10000 characters)
            - **metadata**: Optional content metadata
            - **mode**: Processing mode (auto, high_accuracy, high_speed, etc.)
            """
            try:
                self.request_count += 1

                if self.platform:
                    # Convert mode
                    mode = ProcessingMode(request.mode.value) if request.mode else None

                    # Make prediction
                    result = self.platform.predict_laughter(
                        request.text,
                        request.metadata,
                        mode
                    )

                    return PredictionResponse(
                        prediction=float(result.prediction),
                        confidence=result.confidence,
                        uncertainty=result.uncertainty,
                        processing_time_ms=result.processing_time_ms,
                        model_used=result.model_used.value,
                        language_detected=result.language_detected,
                        content_domain=result.content_analysis.domain.value,
                        cultural_context=result.cultural_context,
                        prediction_id=result.metadata.get('prediction_id', ''),
                        timestamp=result.metadata.get('timestamp', datetime.now().isoformat())
                    )
                else:
                    # Mock response for testing
                    return PredictionResponse(
                        prediction=0.75,
                        confidence=0.85,
                        uncertainty=0.15,
                        processing_time_ms=150.0,
                        model_used="gcacu_base",
                        language_detected="english",
                        content_domain="standup_comedy",
                        cultural_context=None,
                        prediction_id=f"mock_{int(time.time())}",
                        timestamp=datetime.now().isoformat()
                    )

            except Exception as e:
                logger.error(f"Prediction error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/predict_batch", response_model=BatchPredictionResponse, tags=["Prediction"])
        async def predict_batch(request: BatchPredictionRequest):
            """
            Process multiple texts in batch.

            - **texts**: List of input texts (1-1000 items)
            - **metadata_list**: Optional metadata for each text
            - **mode**: Processing mode
            """
            try:
                self.request_count += len(request.texts)

                if self.platform:
                    # Convert mode
                    mode = ProcessingMode(request.mode.value) if request.mode else None

                    # Make batch prediction
                    result = self.platform.predict_batch(
                        request.texts,
                        request.metadata_list,
                        mode
                    )

                    # Convert individual results
                    predictions = []
                    for r in result.results:
                        predictions.append(PredictionResponse(
                            prediction=float(r.prediction),
                            confidence=r.confidence,
                            uncertainty=r.uncertainty,
                            processing_time_ms=r.processing_time_ms,
                            model_used=r.model_used.value,
                            language_detected=r.language_detected,
                            content_domain=r.content_analysis.domain.value,
                            cultural_context=r.cultural_context,
                            prediction_id=r.metadata.get('prediction_id', ''),
                            timestamp=r.metadata.get('timestamp', datetime.now().isoformat())
                        ))

                    return BatchPredictionResponse(
                        results=predictions,
                        total_processing_time_ms=result.total_processing_time_ms,
                        average_time_per_item_ms=result.average_time_per_item_ms,
                        throughput_items_per_second=result.throughput_items_per_second,
                        success_rate=result.success_rate,
                        total_items=len(request.texts),
                        successful_items=len(result.results),
                        failed_items=result.error_count,
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    # Mock response
                    mock_predictions = [
                        PredictionResponse(
                            prediction=0.75 + np.random.uniform(-0.1, 0.1),
                            confidence=0.85,
                            uncertainty=0.15,
                            processing_time_ms=150.0,
                            model_used="gcacu_base",
                            language_detected="english",
                            content_domain="standup_comedy",
                            cultural_context=None,
                            prediction_id=f"mock_{i}_{int(time.time())}",
                            timestamp=datetime.now().isoformat()
                        )
                        for i in range(len(request.texts))
                    ]

                    return BatchPredictionResponse(
                        results=mock_predictions,
                        total_processing_time_ms=len(request.texts) * 150.0,
                        average_time_per_item_ms=150.0,
                        throughput_items_per_second=6.67,
                        success_rate=1.0,
                        total_items=len(request.texts),
                        successful_items=len(request.texts),
                        failed_items=0,
                        timestamp=datetime.now().isoformat()
                    )

            except Exception as e:
                logger.error(f"Batch prediction error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/analyze", response_model=ContentAnalysisResponse, tags=["Analysis"])
        async def analyze_content(request: ContentAnalysisRequest):
            """
            Analyze content without making predictions.

            - **text**: Input text content
            - **metadata**: Optional content metadata
            """
            try:
                if self.platform:
                    # Analyze content
                    result = self.platform.analyze_content(request.text, request.metadata)

                    return ContentAnalysisResponse(
                        domain=result.domain.value,
                        culture=result.culture.value if result.culture else None,
                        language=result.language,
                        confidence=result.confidence,
                        requires_cultural_adaptation=result.requires_cultural_adaptation,
                        recommended_architecture=result.recommended_architecture.value,
                        processing_complexity=result.processing_complexity,
                        estimated_processing_time_ms=result.estimated_processing_time_ms,
                        analysis_id=hashlib.md5(f"{request.text}{time.time()}".encode()).hexdigest(),
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    # Mock response
                    return ContentAnalysisResponse(
                        domain="standup_comedy",
                        culture=None,
                        language="english",
                        confidence=0.85,
                        requires_cultural_adaptation=False,
                        recommended_architecture="gcacu_base",
                        processing_complexity=0.5,
                        estimated_processing_time_ms=150.0,
                        analysis_id=f"mock_{int(time.time())}",
                        timestamp=datetime.now().isoformat()
                    )

            except Exception as e:
                logger.error(f"Content analysis error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def run(self, host: str = "0.0.0.0", port: int = 8080, log_level: str = "info"):
        """Run the API server"""
        if FASTAPI_AVAILABLE:
            uvicorn.run(self.app, host=host, port=port, log_level=log_level)
        else:
            logger.error("FastAPI not available. Cannot start API server.")


# ============================================================================
# PYTHON API LAYER
# ============================================================================

class GCACUPythonAPI:
    """
    High-level Python API for GCACU Unified Platform.

    Provides simple, intuitive interface for common operations.
    """

    def __init__(self, config: Optional[PlatformConfig] = None):
        """Initialize Python API"""
        if PLATFORM_AVAILABLE:
            self.platform = GCACUUnifiedPlatform(config or PlatformConfig())
        else:
            self.platform = None
            logger.warning("Platform not available - using mock API")

    def predict(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Predict laughter from text.

        Args:
            text: Input text content
            **kwargs: Additional parameters (metadata, mode)

        Returns:
            Prediction dictionary
        """
        if self.platform:
            result = self.platform.predict_laughter(text, kwargs.get('metadata'), kwargs.get('mode'))
            return {
                'prediction': float(result.prediction),
                'confidence': result.confidence,
                'language': result.language_detected,
                'domain': result.content_analysis.domain.value,
                'processing_time_ms': result.processing_time_ms
            }
        else:
            return {
                'prediction': 0.75,
                'confidence': 0.85,
                'language': 'english',
                'domain': 'standup_comedy',
                'processing_time_ms': 150.0
            }

    def predict_batch(self, texts: List[str], **kwargs) -> Dict[str, Any]:
        """
        Predict laughter from multiple texts.

        Args:
            texts: List of input texts
            **kwargs: Additional parameters (metadata_list, mode)

        Returns:
            Batch prediction dictionary
        """
        if self.platform:
            result = self.platform.predict_batch(texts, kwargs.get('metadata_list'), kwargs.get('mode'))
            return {
                'predictions': [float(r.prediction) for r in result.results],
                'confidences': [r.confidence for r in result.results],
                'processing_time_ms': result.total_processing_time_ms,
                'throughput': result.throughput_items_per_second
            }
        else:
            return {
                'predictions': [0.75] * len(texts),
                'confidences': [0.85] * len(texts),
                'processing_time_ms': len(texts) * 150.0,
                'throughput': 6.67
            }

    def analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze content without prediction.

        Args:
            text: Input text content
            **kwargs: Additional parameters (metadata)

        Returns:
            Content analysis dictionary
        """
        if self.platform:
            result = self.platform.analyze_content(text, kwargs.get('metadata'))
            return {
                'domain': result.domain.value,
                'culture': result.culture.value if result.culture else None,
                'language': result.language,
                'confidence': result.confidence,
                'complexity': result.processing_complexity,
                'recommended_architecture': result.recommended_architecture.value
            }
        else:
            return {
                'domain': 'standup_comedy',
                'culture': None,
                'language': 'english',
                'confidence': 0.85,
                'complexity': 0.5,
                'recommended_architecture': 'gcacu_base'
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get platform metrics"""
        if self.platform:
            return self.platform.get_platform_metrics()
        else:
            return {
                'total_predictions': 0,
                'uptime_seconds': 0,
                'status': 'mock_mode'
            }

    def close(self):
        """Close the platform and cleanup resources"""
        if self.platform:
            self.platform.shutdown()


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

def example_python_api():
    """Example usage of Python API"""
    print("🎭 GCACU Platform - Python API Example")
    print("=" * 50)

    # Initialize API
    api = GCACUPythonAPI()

    # Single prediction
    print("\n🎯 Single Prediction:")
    result = api.predict("So I was at this restaurant, and the waitress comes over...")
    print(f"Prediction: {result['prediction']:.3f}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Language: {result['language']}")
    print(f"Domain: {result['domain']}")

    # Batch prediction
    print("\n🔄 Batch Prediction:")
    texts = [
        "Why did the chicken cross the road?",
        "I told my wife she was drawing her eyebrows too high...",
        "Have you ever noticed how快递员always knock at the wrong time?"
    ]
    batch_result = api.predict_batch(texts)
    print(f"Processed {len(batch_result['predictions'])} items")
    print(f"Throughput: {batch_result['throughput']:.2f} items/sec")

    # Content analysis
    print("\n🔍 Content Analysis:")
    analysis = api.analyze("You know what's funny about Indian parents? They never say 'I love you', they just ask 'Did you eat?'")
    print(f"Domain: {analysis['domain']}")
    print(f"Culture: {analysis['culture']}")
    print(f"Language: {analysis['language']}")
    print(f"Complexity: {analysis['complexity']:.2f}")

    # Platform metrics
    print("\n📊 Platform Metrics:")
    metrics = api.get_metrics()
    print(f"Total Predictions: {metrics['total_predictions']}")
    print(f"Memory Usage: {metrics['memory_usage_mb']:.2f}MB")

    # Cleanup
    api.close()


def start_api_server():
    """Start the REST API server"""
    print("🚀 Starting GCACU Platform API Server...")

    # Initialize platform
    if PLATFORM_AVAILABLE:
        config = PlatformConfig(
            default_mode=ProcessingMode.PRODUCTION,
            enable_rest_api=True,
            enable_performance_monitoring=True
        )
        platform = GCACUUnifiedPlatform(config)
    else:
        platform = None
        print("⚠️ Platform not available - running in mock mode")

    # Initialize and run API
    api = GCACUPlatformAPI(platform)
    print("📍 API available at: http://localhost:8080")
    print("📚 Documentation available at: http://localhost:8080/docs")
    print("🏥 Health check: curl http://localhost:8080/health")

    api.run(host="0.0.0.0", port=8080)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import argparse
    import hashlib
    import numpy as np

    parser = argparse.ArgumentParser(description="GCACU Platform API")
    parser.add_argument("--mode", choices=["api", "example"], default="api",
                      help="Run mode: 'api' for REST API server, 'example' for Python API example")
    parser.add_argument("--host", default="0.0.0.0", help="API server host")
    parser.add_argument("--port", type=int, default=8080, help="API server port")

    args = parser.parse_args()

    if args.mode == "api":
        start_api_server()
    else:
        example_python_api()
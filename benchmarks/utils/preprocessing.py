"""
Universal Preprocessing Pipeline for Laughter Prediction Benchmarks

Standardized preprocessing for audio, video, text, and multimodal data
across all 9 academic benchmark datasets.
"""

import os
import json
import librosa
import numpy as np
import torch
import torchaudio
import torchvision
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import cv2
import whisper
from transformers import AutoTokenizer, AutoFeatureExtractor


@dataclass
class AudioConfig:
    """Audio preprocessing configuration"""
    target_sample_rate: int = 16000
    n_mels: int = 128
    n_fft: int = 2048
    hop_length: int = 512
    max_length: int = 10  # seconds
    normalize: bool = True
    augment: bool = False


@dataclass
class VideoConfig:
    """Video preprocessing configuration"""
    target_fps: int = 25
    target_size: Tuple[int, int] = (224, 224)
    max_frames: int = 250
    normalize: bool = True
    augment: bool = False


@dataclass
class TextConfig:
    """Text preprocessing configuration"""
    max_length: int = 512
    tokenizer: str = 'bert-base-uncased'
    lowercase: bool = True
    remove_punctuation: bool = False


class AudioPreprocessor:
    """Preprocess audio data for laughter prediction"""

    def __init__(self, config: AudioConfig):
        self.config = config

    def load_audio(self, audio_path: Union[str, Path]) -> Tuple[torch.Tensor, int]:
        """Load audio file"""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        waveform, sample_rate = torchaudio.load(audio_path)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        return waveform, sample_rate

    def resample(self, waveform: torch.Tensor, original_sr: int) -> torch.Tensor:
        """Resample audio to target sample rate"""
        if original_sr != self.config.target_sample_rate:
            resampler = torchaudio.transforms.Resample(
                original_sr, self.config.target_sample_rate
            )
            waveform = resampler(waveform)
        return waveform

    def normalize_audio(self, waveform: torch.Tensor) -> torch.Tensor:
        """Normalize audio waveform"""
        if self.config.normalize:
            # Peak normalization
            max_val = torch.max(torch.abs(waveform))
            if max_val > 0:
                waveform = waveform / max_val
        return waveform

    def trim_silence(self, waveform: torch.Tensor, sample_rate: int) -> torch.Tensor:
        """Remove silence from beginning and end"""
        # Convert to numpy for librosa
        waveform_np = waveform.numpy().squeeze()

        # Trim silence
        waveform_trimmed, _ = librosa.effects.trim(
            waveform_np,
            top_db=20,
            frame_length=512,
            hop_length=128
        )

        return torch.from_numpy(waveform_trimmed).unsqueeze(0)

    def extract_mel_spectrogram(self,
                               waveform: torch.Tensor,
                               sample_rate: int) -> torch.Tensor:
        """Extract mel spectrogram features"""
        # Convert to numpy for librosa
        waveform_np = waveform.numpy().squeeze()

        # Extract mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=waveform_np,
            sr=sample_rate,
            n_mels=self.config.n_mels,
            n_fft=self.config.n_fft,
            hop_length=self.config.hop_length
        )

        # Convert to log scale
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # Normalize to [0, 1]
        mel_spec_db = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-8)

        return torch.from_numpy(mel_spec_db).float()

    def extract_mfcc(self, waveform: torch.Tensor, sample_rate: int) -> torch.Tensor:
        """Extract MFCC features"""
        waveform_np = waveform.numpy().squeeze()

        mfcc = librosa.feature.mfcc(
            y=waveform_np,
            sr=sample_rate,
            n_mfcc=13,
            n_fft=self.config.n_fft,
            hop_length=self.config.hop_length
        )

        return torch.from_numpy(mfcc).float()

    def extract_prosodic_features(self,
                                 waveform: torch.Tensor,
                                 sample_rate: int) -> Dict[str, float]:
        """Extract prosodic features (pitch, intensity, etc.)"""
        waveform_np = waveform.numpy().squeeze()

        features = {}

        # Pitch (fundamental frequency)
        pitches, magnitudes = librosa.piptrack(
            y=waveform_np,
            sr=sample_rate,
            threshold=0.1
        )

        # Extract dominant pitch
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)

        if pitch_values:
            features['pitch_mean'] = np.mean(pitch_values)
            features['pitch_std'] = np.std(pitch_values)
            features['pitch_min'] = np.min(pitch_values)
            features['pitch_max'] = np.max(pitch_values)
        else:
            features['pitch_mean'] = 0.0
            features['pitch_std'] = 0.0
            features['pitch_min'] = 0.0
            features['pitch_max'] = 0.0

        # Intensity (energy)
        rms = librosa.feature.rms(y=waveform_np)
        features['intensity_mean'] = np.mean(rms)
        features['intensity_std'] = np.std(rms)
        features['intensity_max'] = np.max(rms)

        # Zero crossing rate (indicator of laughter)
        zcr = librosa.feature.zero_crossing_rate(waveform_np)
        features['zcr_mean'] = np.mean(zcr)
        features['zcr_std'] = np.std(zcr)

        return features

    def augment_audio(self, waveform: torch.Tensor) -> torch.Tensor:
        """Apply audio augmentation"""
        if not self.config.augment:
            return waveform

        # Random augmentation techniques
        if np.random.random() > 0.5:
            # Add noise
            noise = torch.randn_like(waveform) * 0.01
            waveform = waveform + noise

        if np.random.random() > 0.5:
            # Time stretching (using librosa)
            waveform_np = waveform.numpy().squeeze()
            stretch_factor = np.random.uniform(0.8, 1.2)
            stretched = librosa.effects.time_stretch(waveform_np, rate=stretch_factor)
            waveform = torch.from_numpy(stretched).unsqueeze(0)

        if np.random.random() > 0.5:
            # Pitch shifting
            waveform_np = waveform.numpy().squeeze()
            n_steps = np.random.uniform(-2, 2)
            shifted = librosa.effects.pitch_shift(waveform_np, sr=self.config.target_sample_rate, n_steps=n_steps)
            waveform = torch.from_numpy(shifted).unsqueeze(0)

        return waveform

    def preprocess(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """Complete audio preprocessing pipeline"""
        # Load audio
        waveform, sample_rate = self.load_audio(audio_path)

        # Resample
        waveform = self.resample(waveform, sample_rate)
        sample_rate = self.config.target_sample_rate

        # Trim silence
        waveform = self.trim_silence(waveform, sample_rate)

        # Normalize
        waveform = self.normalize_audio(waveform)

        # Trim/pad to max length
        max_samples = self.config.max_length * self.config.target_sample_rate
        if waveform.shape[1] > max_samples:
            waveform = waveform[:, :max_samples]
        elif waveform.shape[1] < max_samples:
            padding = max_samples - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding))

        # Extract features
        features = {
            'waveform': waveform,
            'sample_rate': sample_rate,
            'mel_spectrogram': self.extract_mel_spectrogram(waveform, sample_rate),
            'mfcc': self.extract_mfcc(waveform, sample_rate),
            'prosodic': self.extract_prosodic_features(waveform, sample_rate)
        }

        return features


class VideoPreprocessor:
    """Preprocess video data for laughter prediction"""

    def __init__(self, config: VideoConfig):
        self.config = config

    def load_video(self, video_path: Union[str, Path]) -> List[np.ndarray]:
        """Load video frames"""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)

        cap.release()
        return frames

    def resize_frames(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """Resize frames to target size"""
        resized = []
        for frame in frames:
            resized_frame = cv2.resize(frame, self.config.target_size)
            resized.append(resized_frame)
        return resized

    def normalize_frames(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """Normalize frame pixel values"""
        if not self.config.normalize:
            return frames

        normalized = []
        for frame in frames:
            # Normalize to [0, 1]
            frame_float = frame.astype(np.float32) / 255.0

            # ImageNet normalization
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            normalized_frame = (frame_float - mean) / std

            normalized.append(normalized_frame)

        return normalized

    def extract_frames(self,
                      frames: List[np.ndarray],
                      target_fps: Optional[int] = None) -> List[np.ndarray]:
        """Extract frames at target FPS"""
        if target_fps is None:
            target_fps = self.config.target_fps

        # Calculate frame indices to extract
        total_frames = len(frames)
        original_fps = 25  # Assumption, could be detected
        frame_indices = np.linspace(0, total_frames - 1, int(total_frames * target_fps / original_fps))

        extracted = [frames[int(i)] for i in frame_indices if int(i) < total_frames]
        return extracted

    def limit_frames(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """Limit number of frames to max_frames"""
        if len(frames) > self.config.max_frames:
            # Uniform sampling
            indices = np.linspace(0, len(frames) - 1, self.config.max_frames, dtype=int)
            frames = [frames[i] for i in indices]
        return frames

    def augment_frames(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """Apply video augmentation"""
        if not self.config.augment:
            return frames

        augmented = []
        for frame in frames:
            # Random horizontal flip
            if np.random.random() > 0.5:
                frame = np.fliplr(frame)

            # Random brightness adjustment
            if np.random.random() > 0.5:
                brightness_factor = np.random.uniform(0.8, 1.2)
                frame = np.clip(frame * brightness_factor, 0, 1)

            augmented.append(frame)

        return augmented

    def preprocess(self, video_path: Union[str, Path]) -> Dict[str, Any]:
        """Complete video preprocessing pipeline"""
        # Load video
        frames = self.load_video(video_path)

        # Extract frames at target FPS
        frames = self.extract_frames(frames)

        # Resize frames
        frames = self.resize_frames(frames)

        # Normalize frames
        frames = self.normalize_frames(frames)

        # Limit number of frames
        frames = self.limit_frames(frames)

        # Convert to tensor
        frames_tensor = torch.from_numpy(np.array(frames)).permute(0, 3, 1, 2)  # (T, C, H, W)

        return {
            'frames': frames_tensor,
            'num_frames': len(frames),
            'fps': self.config.target_fps
        }


class TextPreprocessor:
    """Preprocess text data for laughter prediction"""

    def __init__(self, config: TextConfig):
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.tokenizer)
        self.whisper_model = None

    def load_whisper_model(self):
        """Load Whisper model for speech-to-text"""
        if self.whisper_model is None:
            self.whisper_model = whisper.load_model("base")

    def transcribe_audio(self, audio_path: Union[str, Path]) -> str:
        """Transcribe audio to text using Whisper"""
        self.load_whisper_model()
        result = self.whisper_model.transcribe(str(audio_path))
        return result['text']

    def tokenize(self, text: str) -> Dict[str, torch.Tensor]:
        """Tokenize text"""
        if self.config.lowercase:
            text = text.lower()

        if self.config.remove_punctuation:
            # Simple punctuation removal
            punctuation = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
            text = text.translate(str.maketrans('', '', punctuation))

        encoded = self.tokenizer(
            text,
            max_length=self.config.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoded['input_ids'].squeeze(0),
            'attention_mask': encoded['attention_mask'].squeeze(0)
        }

    def extract_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract linguistic features relevant to laughter"""
        features = {}

        # Basic text statistics
        words = text.split()
        features['word_count'] = len(words)
        features['char_count'] = len(text)
        features['avg_word_length'] = np.mean([len(word) for word in words]) if words else 0

        # Punctuation features
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        features['ellipsis_count'] = text.count('...')

        # Laughter indicators
        laughter_keywords = ['haha', 'hahaha', 'lol', 'lmao', 'hehe', 'hoho']
        features['has_laughter_keywords'] = any(keyword in text.lower() for keyword in laughter_keywords)

        return features

    def preprocess(self, text: str) -> Dict[str, Any]:
        """Complete text preprocessing pipeline"""
        return {
            'tokens': self.tokenize(text),
            'text': text,
            'linguistic_features': self.extract_linguistic_features(text)
        }


class MultimodalPreprocessor:
    """Combined preprocessing for audio, video, and text"""

    def __init__(self,
                 audio_config: Optional[AudioConfig] = None,
                 video_config: Optional[VideoConfig] = None,
                 text_config: Optional[TextConfig] = None):

        self.audio_config = audio_config or AudioConfig()
        self.video_config = video_config or VideoConfig()
        self.text_config = text_config or TextConfig()

        self.audio_preprocessor = AudioPreprocessor(self.audio_config)
        self.video_preprocessor = VideoPreprocessor(self.video_config)
        self.text_preprocessor = TextPreprocessor(self.text_config)

    def preprocess_sample(self,
                         audio_path: Optional[Union[str, Path]] = None,
                         video_path: Optional[Union[str, Path]] = None,
                         text: Optional[str] = None) -> Dict[str, Any]:
        """Preprocess a multimodal sample"""
        features = {}

        if audio_path:
            try:
                features['audio'] = self.audio_preprocessor.preprocess(audio_path)
            except Exception as e:
                print(f"Warning: Failed to preprocess audio {audio_path}: {e}")

        if video_path:
            try:
                features['video'] = self.video_preprocessor.preprocess(video_path)
            except Exception as e:
                print(f"Warning: Failed to preprocess video {video_path}: {e}")

        if text:
            try:
                features['text'] = self.text_preprocessor.preprocess(text)
            except Exception as e:
                print(f"Warning: Failed to preprocess text: {e}")

        return features
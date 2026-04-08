#!/usr/bin/env python3
"""
Enhanced Comedy Dataset Generator
Creates realistic synthetic comedy data with proper structure and labels
"""

import json
import random
from pathlib import Path
from typing import List, Dict
import re


class EnhancedComedyGenerator:
    """Generate realistic comedy transcript data"""
    
    def __init__(self):
        # Real comedy patterns and structures
        self.comedy_structures = {
            'observational': {
                'setup_pattern': "I've noticed that {topic} always {action}",
                'punchline_pattern': "It's like {comparison} but {twist}",
                'laughter_probability': 0.7
            },
            'self_deprecating': {
                'setup_pattern': "I tried to {activity} but {failure}",
                'punchline_pattern': "Now I {consequence} because {ironic_reason}",
                'laughter_probability': 0.8
            },
            'wordplay': {
                'setup_pattern': "You know what they say about {subject}",
                'punchline_pattern': "That's why I call it {pun}",
                'laughter_probability': 0.6
            },
            'relatable': {
                'setup_pattern': "Does anyone else {common_experience}",
                'punchline_pattern': "No? Just me then {embarrassing_truth}",
                'laughter_probability': 0.9
            }
        }
        
        self.topics = {
            'technology': ['smart phones', 'social media', 'wifi passwords', 'autocorrect', 'streaming services'],
            'relationships': ['dating apps', 'texting crushes', 'meeting parents', 'wedding ceremonies', 'divorce'],
            'work': ['corporate meetings', 'reply-all emails', 'office birthday parties', 'LinkedIn', 'zoom calls'],
            'aging': ['back pain', 'forgetting names', 'staying up late', 'hangovers', 'doctors appointments'],
            'food': ['meal prepping', 'fancy restaurants', 'diet culture', 'cooking fails', 'delivery fees']
        }
        
        self.audience_reactions = ['[laughter]', '[applause]', '[cheering]', '[groans]', '']
        
    def generate_comedy_bit(self, comedy_type: str = 'observational') -> Dict:
        """Generate a complete comedy bit with setup and punchline"""
        
        if comedy_type not in self.comedy_structures:
            comedy_type = random.choice(list(self.comedy_structures.keys()))
        
        structure = self.comedy_structures[comedy_type]
        topic_category = random.choice(list(self.topics.keys()))
        specific_topic = random.choice(self.topics[topic_category])
        
        # Generate setup
        setup = self._generate_setup(comedy_type, specific_topic)
        
        # Generate punchline  
        punchline = self._generate_punchline(comedy_type, setup, specific_topic)
        
        # Determine if it gets laughter
        gets_laughter = random.random() < structure['laughter_probability']
        
        # Add audience reaction if laughter
        if gets_laughter:
            reaction = random.choice(['[laughter]', '[laughter]', '[applause]'])
            full_text = f"{setup} {punchline} {reaction}"
        else:
            full_text = f"{setup} {punchline}"
        
        return {
            'text': full_text,
            'setup': setup,
            'punchline': punchline,
            'has_laughter': gets_laughter,
            'comedy_type': comedy_type,
            'topic_category': topic_category,
            'specific_topic': specific_topic,
            'laughter_type': 'discrete' if gets_laughter else 'none',
            'word_count': len(full_text.split()),
            'estimated_duration': len(full_text.split()) / 150  # ~150 words per minute
        }
    
    def _generate_setup(self, comedy_type: str, topic: str) -> str:
        """Generate setup line based on comedy type"""
        
        setups = {
            'observational': [
                f"I've noticed that {topic} are getting out of control",
                f"Can we talk about {topic} for a second?",
                f"You know what drives me crazy? {topic}",
                f"I've figured out the problem with {topic}",
            ],
            'self_deprecating': [
                f"I tried to get into {topic} but it didn't work out",
                f"My relationship with {topic} is complicated",
                f"I finally decided to try {topic} yesterday",
                f"I thought I was good at {topic}, but then..."
            ],
            'wordplay': [
                f"Has anyone else noticed the situation with {topic}?",
                f"Let me tell you something about {topic}",
                f"I have a theory about {topic}",
            ],
            'relatable': [
                f"Does anyone else have a problem with {topic}?",
                f"Can we all agree that {topic} is the worst?",
                f"I know I'm not the only one who hates {topic}",
                f"Hands up if you've ever dealt with {topic}",
            ]
        }
        
        return random.choice(setups[comedy_type])
    
    def _generate_punchline(self, comedy_type: str, setup: str, topic: str) -> str:
        """Generate punchline based on setup and comedy type"""
        
        punchlines = {
            'observational': [
                f"It's like society just gave up on {topic}",
                f"And somehow this is considered normal now",
                f"Meanwhile my grandmother is still confused by {topic}",
                f"But apparently this is what progress looks like",
                f"That's not a {topic}, that's a cry for help"
            ],
            'self_deprecating': [
                "Turns out I'm the problem",
                "I immediately regretted my decisions",
                "Now I have to explain this to my therapist",
                "This is why I'm single",
                "I should have just stayed home"
            ],
            'wordplay': [
                "That's what I call a {topic} situation",
                "It's the {topic} of our generation",
                "Talk about {topic} goals",
                "That's the real {topic} experience"
            ],
            'relatable': [
                "And by anyone else I mean just me",
                "But we're all thinking it",
                "Yet somehow we all still do this",
                "I'm right and you know it"
            ]
        }
        
        base_punchline = random.choice(punchlines[comedy_type])
        
        # Add some variety
        if random.random() < 0.3:
            intensifiers = ["Seriously", "Honestly", "Like", "Literally"]
            base_punchline = f"{random.choice(intensifiers)}, {base_punchline.lower()}"
        
        return base_punchline
    
    def generate_conversation_comedy(self) -> Dict:
        """Generate comedy from conversational dialogue"""
        
        speakers = ["Comedian", "Audience member", "Heckler"]
        
        # Conversational setup
        setups = [
            ("Comedian", "So how's everyone doing tonight?"),
            ("Comedian", "I see some people in the back looking confused"),
            ("Comedian", "We're having a good time, right?"),
            ("Comedian", "I can feel the energy in here"),
        ]
        
        speaker, line = random.choice(setups)
        
        # Generate response based on setup
        if "doing tonight" in line:
            response = "Audience: [Cheers] [Applause]"
            comedy_followup = "Comedian: That's the spirit! Now let's actually talk about something real."
        elif "looking confused" in line:
            response = "Audience member: What?"
            comedy_followup = "Comedian: Exactly! That's my point. Nobody knows what's happening anymore."
        elif "good time" in line:
            response = "Audience: Yeah!"
            comedy_followup = "Comedian: That's what you say now, but wait until I tell you about my dating life."
        else:
            response = "Audience: [Laughter]"
            comedy_followup = "Comedian: See? You already know where this is going."
        
        full_text = f"{speaker}: {line} {response} {comedy_followup}"
        
        return {
            'text': full_text,
            'setup': line,
            'punchline': comedy_followup,
            'has_laughter': True,
            'comedy_type': 'conversational',
            'topic_category': 'stage_patter',
            'laughter_type': 'continuous',
            'word_count': len(full_text.split()),
            'estimated_duration': len(full_text.split()) / 150
        }
    
    def generate_non_comedy_control(self) -> Dict:
        """Generate non-comedy text for negative controls"""
        
        non_comedy_texts = [
            "The weather forecast calls for partly cloudy skies with a chance of rain later this evening.",
            "I need to go to the grocery store to buy milk, eggs, and bread for the week.",
            "The meeting is scheduled for Tuesday at 3 PM in the main conference room.",
            "Please remember to submit your reports by the end of the business day.",
            "The train arrives at platform 4 in approximately 15 minutes.",
            "I finished my homework and then studied for the upcoming exam.",
            "The recipe calls for two cups of flour and one tablespoon of sugar.",
            "Don't forget to call the dentist to schedule your annual checkup.",
            "The package should arrive within 3-5 business days via standard shipping.",
            "I went for a run this morning and then cooked a healthy breakfast."
        ]
        
        text = random.choice(non_comedy_texts)
        
        return {
            'text': text,
            'setup': text,
            'punchline': '',
            'has_laughter': False,
            'comedy_type': 'control',
            'topic_category': 'neutral',
            'laughter_type': 'none',
            'word_count': len(text.split()),
            'estimated_duration': len(text.split()) / 150
        }
    
    def generate_dataset(self, num_samples: int = 100) -> List[Dict]:
        """Generate comprehensive comedy dataset"""
        
        dataset = []
        
        # Distribution of comedy types
        comedy_distribution = {
            'observational': 0.35,
            'self_deprecating': 0.25,
            'wordplay': 0.15,
            'relatable': 0.15,
            'conversational': 0.05
        }
        
        # Generate comedy samples
        for comedy_type, proportion in comedy_distribution.items():
            num_samples_for_type = int(num_samples * proportion)
            
            for _ in range(num_samples_for_type):
                if comedy_type == 'conversational':
                    sample = self.generate_conversation_comedy()
                else:
                    sample = self.generate_comedy_bit(comedy_type)
                
                dataset.append(sample)
        
        # Add control samples (non-comedy)
        num_control_samples = int(num_samples * 0.2)  # 20% controls
        for _ in range(num_control_samples):
            dataset.append(self.generate_non_comedy_control())
        
        # Shuffle dataset
        random.shuffle(dataset)
        
        return dataset
    
    def save_dataset(self, dataset: List[Dict], output_path: str):
        """Save dataset to file"""
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in dataset:
                f.write(json.dumps(sample, ensure_ascii=False) + '\\n')
        
        print(f"✅ Saved {len(dataset)} samples to {output_file}")
        
        # Print statistics
        laughter_samples = sum(1 for s in dataset if s['has_laughter'])
        print(f"📊 Dataset Statistics:")
        print(f"   Total samples: {len(dataset)}")
        print(f"   Laughter samples: {laughter_samples} ({100*laughter_samples/len(dataset):.1f}%)")
        print(f"   Non-laughter samples: {len(dataset)-laughter_samples} ({100*(len(dataset)-laughter_samples)/len(dataset):.1f}%)")
        
        # Comedy type breakdown
        comedy_types = {}
        for sample in dataset:
            ctype = sample['comedy_type']
            comedy_types[ctype] = comedy_types.get(ctype, 0) + 1
        
        print(f"\\n   Comedy Types:")
        for ctype, count in sorted(comedy_types.items()):
            print(f"      {ctype}: {count} ({100*count/len(dataset):.1f}%)")


def main():
    """Generate enhanced comedy dataset"""
    
    print("🎭 Enhanced Comedy Dataset Generator")
    print("=" * 50)
    
    generator = EnhancedComedyGenerator()
    
    # Generate different dataset sizes
    datasets = [
        ('data/enhanced_comedy_small.jsonl', 50),
        ('data/enhanced_comedy_medium.jsonl', 200),
        ('data/enhanced_comedy_large.jsonl', 1000)
    ]
    
    for output_path, num_samples in datasets:
        print(f"\\n📝 Generating {num_samples} samples...")
        dataset = generator.generate_dataset(num_samples)
        generator.save_dataset(dataset, output_path)
    
    print(f"\\n✅ All datasets generated successfully!")
    print(f"📁 Saved to data/enhanced_comedy_*.jsonl")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive Knowledge Base for Cultural and Comedy References
Optimized for Engram Memory System on 8GB Mac M2

Categories:
- Political references and figures
- Celebrity and entertainment
- Historical events and context
- Pop culture trends and memes
- Geographic and demographic knowledge
- Comedy styles and techniques
- Technology and internet culture
"""

from typing import List, Dict, Any
import json
from pathlib import Path


class ComedyKnowledgeBase:
    """
    Comprehensive knowledge base for autonomous laughter prediction

    Designed for integration with Engram Memory System to provide:
    - Contextual understanding of comedy
    - Cultural reference recognition
    - Historical context awareness
    - Pop culture trend detection
    """

    def __init__(self):
        self.knowledge_entries: List[Dict[str, Any]] = []
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Initialize with comprehensive comedy and cultural knowledge"""

        # Political References
        political_knowledge = [
            {
                'text': 'US Presidents serve four-year terms and can be elected twice',
                'category': 'political',
                'metadata': {'source': 'US Constitution', 'context': 'government_structure'}
            },
            {
                'text': 'Congress consists of the Senate and House of Representatives',
                'category': 'political',
                'metadata': {'source': 'US Government', 'context': 'legislative_branch'}
            },
            {
                'text': 'The President lives in the White House at 1600 Pennsylvania Avenue',
                'category': 'political',
                'metadata': {'source': 'US Government', 'context': 'presidential_residence'}
            },
            {
                'text': 'Presidential elections are held every four years on Tuesday after first Monday',
                'category': 'political',
                'metadata': {'source': 'US Election Law', 'context': 'election_schedule'}
            },
            {
                'text': 'The State of the Union address is delivered annually to Congress',
                'category': 'political',
                'metadata': {'source': 'US Tradition', 'context': 'presidential_speech'}
            },
            {
                'text': 'Cabinet members advise the President and head executive departments',
                'category': 'political',
                'metadata': {'source': 'US Government', 'context': 'presidential_cabinet'}
            },
            {
                'text': 'The Supreme Court has nine justices who serve lifetime appointments',
                'category': 'political',
                'metadata': {'source': 'US Judiciary', 'context': 'supreme_court'}
            },
            {
                'text': 'Presidential primaries determine party nominees for general election',
                'category': 'political',
                'metadata': {'source': 'US Election Process', 'context': 'primary_elections'}
            }
        ]

        # Celebrity and Entertainment
        celebrity_knowledge = [
            {
                'text': 'Oprah Winfrey hosted a daytime talk show for 25 years',
                'category': 'celebrity',
                'metadata': {'source': 'Television History', 'context': 'talk_show_host'}
            },
            {
                'text': 'The Oscars honor achievements in the film industry annually',
                'category': 'celebrity',
                'metadata': {'source': 'Academy Awards', 'context': 'entertainment_awards'}
            },
            {
                'text': 'Saturday Night Live has been airing since 1975',
                'category': 'celebrity',
                'metadata': {'source': 'Television History', 'context': 'sketch_comedy'}
            },
            {
                'text': 'The Grammy Awards recognize achievements in the music industry',
                'category': 'celebrity',
                'metadata': {'source': 'Recording Academy', 'context': 'music_awards'}
            },
            {
                'text': 'Comedy Central launched in 1991 and features stand-up and comedy series',
                'category': 'celebrity',
                'metadata': {'source': 'Television History', 'context': 'comedy_network'}
            },
            {
                'text': 'The Tonight Show is the longest-running talk show in television history',
                'category': 'celebrity',
                'metadata': {'source': 'Television History', 'context': 'late_night_tv'}
            },
            {
                'text': 'Netflix revolutionized entertainment with streaming starting in 2007',
                'category': 'celebrity',
                'metadata': {'source': 'Entertainment Industry', 'context': 'streaming_services'}
            },
            {
                'text': 'YouTube launched in 2005 and created new celebrity culture',
                'category': 'celebrity',
                'metadata': {'source': 'Internet History', 'context': 'digital_entertainment'}
            }
        ]

        # Historical Events
        historical_knowledge = [
            {
                'text': 'The moon landing occurred on July 20 1969 during the Apollo 11 mission',
                'category': 'historical',
                'metadata': {'source': 'NASA History', 'context': 'space_exploration', 'year': 1969}
            },
            {
                'text': 'World War II lasted from 1939 to 1945 and involved global conflict',
                'category': 'historical',
                'metadata': {'source': 'World History', 'context': 'global_conflict', 'year_range': [1939, 1945]}
            },
            {
                'text': 'The Berlin Wall fell in 1989 symbolizing the end of the Cold War',
                'category': 'historical',
                'metadata': {'source': 'Cold War History', 'context': 'political_landmark', 'year': 1989}
            },
            {
                'text': 'The internet became publicly available in the 1990s revolutionizing communication',
                'category': 'historical',
                'metadata': {'source': 'Technology History', 'context': 'digital_revolution', 'decade': '1990s'}
            },
            {
                'text': 'September 11 2001 terrorist attacks changed American security policy',
                'category': 'historical',
                'metadata': {'source': 'Modern History', 'context': 'terrorism', 'year': 2001}
            },
            {
                'text': 'The civil rights movement in the 1960s fought for racial equality',
                'category': 'historical',
                'metadata': {'source': 'American History', 'context': 'social_movement', 'decade': '1960s'}
            },
            {
                'text': 'The Great Depression was a severe economic crisis in the 1930s',
                'category': 'historical',
                'metadata': {'source': 'Economic History', 'context': 'economic_crisis', 'decade': '1930s'}
            },
            {
                'text': 'The smartphone era began with the iPhone release in 2007',
                'category': 'historical',
                'metadata': {'source': 'Technology History', 'context': 'mobile_computing', 'year': 2007}
            }
        ]

        # Pop Culture and Trends
        pop_culture_knowledge = [
            {
                'text': 'Social media platforms like Instagram and TikTok influence modern culture',
                'category': 'pop_culture',
                'metadata': {'source': 'Digital Culture', 'context': 'social_media'}
            },
            {
                'text': 'Superhero movies have dominated box offices since the 2000s',
                'category': 'pop_culture',
                'metadata': {'source': 'Entertainment Trends', 'context': 'film_genres'}
            },
            {
                'text': 'Reality TV became popular in the early 2000s with shows like Survivor',
                'category': 'pop_culture',
                'metadata': {'source': 'Television History', 'context': 'reality_television'}
            },
            {
                'text': 'Video games have evolved from arcade cabinets to competitive esports',
                'category': 'pop_culture',
                'metadata': {'source': 'Gaming Culture', 'context': 'electronic_sports'}
            },
            {
                'text': 'Memes spread rapidly through internet culture and social media',
                'category': 'pop_culture',
                'metadata': {'source': 'Internet Culture', 'context': 'viral_content'}
            },
            {
                'text': 'Podcasting has grown into a major media format since the 2010s',
                'category': 'pop_culture',
                'metadata': {'source': 'Media Evolution', 'context': 'audio_entertainment'}
            },
            {
                'text': 'Streaming services like Netflix and Spotify changed media consumption',
                'category': 'pop_culture',
                'metadata': {'source': 'Digital Entertainment', 'context': 'on_demand_media'}
            },
            {
                'text': 'Influencer culture emerged through social media platforms',
                'category': 'pop_culture',
                'metadata': {'source': 'Digital Culture', 'context': 'social_media_influencers'}
            }
        ]

        # Comedy Styles and Techniques
        comedy_techniques_knowledge = [
            {
                'text': 'Irony involves saying the opposite of what is meant for comedic effect',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'verbal_technique'}
            },
            {
                'text': 'Satire uses humor to criticize politics and society',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'social_commentary'}
            },
            {
                'text': 'Slapstick comedy involves physical humor and exaggerated actions',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'physical_comedy'}
            },
            {
                'text': 'Observational comedy focuses on everyday life experiences',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'standup_style'}
            },
            {
                'text': 'Self-deprecating humor involves making jokes at oneself',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'humor_style'}
            },
            {
                'text': 'Wordplay relies on puns and linguistic ambiguity for humor',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'verbal_technique'}
            },
            {
                'text': 'Timing and delivery are crucial elements of effective comedy',
                'category': 'comedy',
                'metadata': {'source': 'Performance Theory', 'context': 'comedic_technique'}
            },
            {
                'text': 'Breaking expectations creates surprise humor in comedy',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'humor_mechanism'}
            },
            {
                'text': 'Hyperbole involves extreme exaggeration for comedic effect',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Theory', 'context': 'rhetorical_device'}
            },
            {
                'text': 'Call-back humor references earlier jokes for cumulative laughs',
                'category': 'comedy',
                'metadata': {'source': 'Comedy Writing', 'context': 'narrative_technique'}
            }
        ]

        # Technology and Internet Culture
        tech_culture_knowledge = [
            {
                'text': 'Artificial intelligence and machine learning are transforming technology',
                'category': 'technology',
                'metadata': {'source': 'Technology Trends', 'context': 'AI_development'}
            },
            {
                'text': 'Smartphones have become essential for modern daily life',
                'category': 'technology',
                'metadata': {'source': 'Technology History', 'context': 'mobile_devices'}
            },
            {
                'text': 'Social media platforms connect billions of people worldwide',
                'category': 'technology',
                'metadata': {'source': 'Digital Culture', 'context': 'social_networking'}
            },
            {
                'text': 'Remote work became common during the COVID-19 pandemic',
                'category': 'technology',
                'metadata': {'source': 'Work Culture', 'context': 'digital_workplace'}
            },
            {
                'text': 'Video conferencing replaced many in-person meetings',
                'category': 'technology',
                'metadata': {'source': 'Technology Adoption', 'context': 'virtual_communication'}
            },
            {
                'text': 'Cryptocurrency and blockchain technology emerged as financial innovations',
                'category': 'technology',
                'metadata': {'source': 'Financial Technology', 'context': 'digital_currency'}
            },
            {
                'text': 'Gig economy platforms changed how people work and earn money',
                'category': 'technology',
                'metadata': {'source': 'Economic Trends', 'context': 'digital_labor'}
            },
            {
                'text': 'Electric vehicles are becoming mainstream in transportation',
                'category': 'technology',
                'metadata': {'source': 'Automotive Technology', 'context': 'sustainable_transport'}
            }
        ]

        # Geographic and Cultural Knowledge
        geographic_knowledge = [
            {
                'text': 'New York City is known as the Big Apple and has 8 million residents',
                'category': 'geographic',
                'metadata': {'source': 'US Geography', 'context': 'major_cities', 'population': '8M'}
            },
            {
                'text': 'Los Angeles is the entertainment capital of the United States',
                'category': 'geographic',
                'metadata': {'source': 'US Geography', 'context': 'entertainment_industry'}
            },
            {
                'text': 'The United Kingdom consists of England Scotland Wales and Northern Ireland',
                'category': 'geographic',
                'metadata': {'source': 'European Geography', 'context': 'political_union'}
            },
            {
                'text': 'California is the most populous US state with 39 million people',
                'category': 'geographic',
                'metadata': {'source': 'US Geography', 'context': 'state_demographics', 'population': '39M'}
            },
            {
                'text': 'Texas is known for its size and independent cultural identity',
                'category': 'geographic',
                'metadata': {'source': 'US Geography', 'context': 'regional_culture'}
            },
            {
                'text': 'Florida is popular for retirees and theme parks like Disney World',
                'category': 'geographic',
                'metadata': {'source': 'US Geography', 'context': 'tourism_demographics'}
            },
            {
                'text': 'The Midwest is known for agriculture and friendly residents',
                'category': 'geographic',
                'metadata': {'source': 'US Regional Culture', 'context': 'cultural_stereotypes'}
            },
            {
                'text': 'The West Coast is associated with technology and innovation',
                'category': 'geographic',
                'metadata': {'source': 'US Regional Culture', 'context': 'tech_industry'}
            }
        ]

        # Combine all knowledge categories
        self.knowledge_entries.extend(political_knowledge)
        self.knowledge_entries.extend(celebrity_knowledge)
        self.knowledge_entries.extend(historical_knowledge)
        self.knowledge_entries.extend(pop_culture_knowledge)
        self.knowledge_entries.extend(comedy_techniques_knowledge)
        self.knowledge_entries.extend(tech_culture_knowledge)
        self.knowledge_entries.extend(geographic_knowledge)

    def get_knowledge_entries(self) -> List[Dict[str, Any]]:
        """Get all knowledge entries"""
        return self.knowledge_entries

    def get_entries_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get knowledge entries by category"""
        return [entry for entry in self.knowledge_entries if entry['category'] == category]

    def add_knowledge_entry(self, entry: Dict[str, Any]):
        """Add a new knowledge entry"""
        required_keys = ['text', 'category', 'metadata']
        if all(key in entry for key in required_keys):
            self.knowledge_entries.append(entry)
        else:
            raise ValueError(f"Knowledge entry must contain {required_keys}")

    def save_knowledge_base(self, file_path: str):
        """Save knowledge base to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.knowledge_entries, f, indent=2)

    def load_knowledge_base(self, file_path: str):
        """Load knowledge base from JSON file"""
        with open(file_path, 'r') as f:
            self.knowledge_entries = json.load(f)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        categories = {}
        for entry in self.knowledge_entries:
            category = entry['category']
            categories[category] = categories.get(category, 0) + 1

        return {
            'total_entries': len(self.knowledge_entries),
            'categories': categories,
            'avg_text_length': sum(len(entry['text']) for entry in self.knowledge_entries) / len(self.knowledge_entries)
        }

    def create_engram_data(self) -> List[Dict[str, Any]]:
        """Create data format suitable for Engram initialization"""
        return [
            {
                'text': entry['text'],
                'category': entry['category'],
                'metadata': entry['metadata']
            }
            for entry in self.knowledge_entries
        ]


def create_comprehensive_knowledge_base() -> ComedyKnowledgeBase:
    """Factory function to create comprehensive knowledge base"""
    knowledge_base = ComedyKnowledgeBase()

    stats = knowledge_base.get_statistics()
    print(f"Created knowledge base with {stats['total_entries']} entries")
    print(f"Categories: {stats['categories']}")

    return knowledge_base


def main():
    """Main function to test and save knowledge base"""
    print("Creating Comprehensive Comedy Knowledge Base...")

    # Create knowledge base
    kb = create_comprehensive_knowledge_base()

    # Display statistics
    stats = kb.get_statistics()
    print(f"\nKnowledge Base Statistics:")
    print(f"Total entries: {stats['total_entries']}")
    print(f"Average text length: {stats['avg_text_length']:.1f} characters")
    print(f"Categories: {stats['categories']}")

    # Save knowledge base
    output_file = Path(__file__).parent / "comedy_knowledge_base.json"
    kb.save_knowledge_base(str(output_file))
    print(f"\nKnowledge base saved to {output_file}")

    # Display sample entries
    print(f"\nSample entries by category:")
    for category in ['political', 'comedy', 'technology']:
        entries = kb.get_entries_by_category(category)
        print(f"\n{category.upper()} (#{len(entries)}):")
        for entry in entries[:2]:
            print(f"  - {entry['text'][:80]}...")

    return kb


if __name__ == "__main__":
    main()
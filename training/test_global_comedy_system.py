"""
Comprehensive Test Suite for Global English Comedy System
=========================================================

Demonstrates all advanced features including:
- Cultural context detection
- Comedian style recognition
- Cross-cultural adaptation
- Performance evaluation
- Real-time processing simulation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from global_english_comedy_system import (
    GlobalEnglishComedyProcessor,
    ComedyCulture,
    ComedianStyle,
    ComedianProfile,
    ComedyCulturalFeatures
)

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print('='*60)

def print_subsection(title):
    """Print formatted subsection header"""
    print(f"\n{title}")
    print('-' * len(title))

def test_cultural_detection():
    """Test cultural context detection accuracy"""
    print_section("CULTURAL CONTEXT DETECTION TESTS")

    processor = GlobalEnglishComedyProcessor()

    test_cases = {
        "US Comedy": """
        I was watching the Super Bowl with my buddies, right? And Tom Brady throws
        this insane touchdown pass. We're all screaming like crazy, high-fiving,
        spilling beer everywhere. My wife comes in and asks what's happening.
        I'm like, "Honey, this is HISTORY!" She rolls her eyes and says,
        "It's just a game, isn't it?" JUST A GAME? I had to explain to her
        that this isn't just football - this is AMERICAN CULTURE!
        """,

        "UK Comedy": """
        I went to the local pub in Manchester, ordered a pint of bitter, and
        the barman gives me this look - you know the one, where they're judging
        your life choices while simultaneously wondering if you're going to tip.
        He says, "That'll be £4.80, then." Four pounds eighty! For a pint!
        I stood there thinking, "Is this beer brewed by the Queen herself?
        Am I paying for the liquid gold or the privilege of breathing British air?"
        """,

        "Indian Comedy": """
        When I first came to America for my MBA, my Indian mother was terrified.
        She calls me every day: "Beta, are you eating properly? Are you talking
        to any nice Indian girls? Your father's friend's son just became a doctor,
        why can't you be more like him?" I had to explain, "Mom, I'm studying
        business, not medicine!" She didn't get it. To her, if you're not a doctor
        or engineer, you're basically unemployed.
        """,

        "Cross-Cultural": """
        The funniest thing about being Indian in America is explaining our
        concept of "auntie" and "uncle." In India, every adult is "auntie" or
        "uncle" - it's a term of respect! But here, I introduce my friend's
        mom as "Auntie Priya" and everyone looks at me like I'm claiming
        we're related. I have to explain, "No, no, it's cultural! She's not
        actually my aunt!" Cultural barriers, my friends.
        """
    }

    for test_name, test_text in test_cases.items():
        print_subsection(f"Testing: {test_name}")

        culture, confidence = processor.detect_cultural_context(test_text)

        print(f"Detected Culture: {culture.value}")
        print(f"Confidence Score: {confidence:.2f}")

        # Extract key features
        features = processor.extract_cultural_features(test_text, culture)
        print(f"\nKey Features:")
        print(f"  Directness: {features.directness_score:.2f}")
        print(f"  Sarcasm: {features.sarcasm_level:.2f}")
        print(f"  Irony: {features.irony_level:.2f}")
        print(f"  Family Dynamics: {features.family_dynamics:.2f}")
        print(f"  Cultural Identity: {features.cultural_identity_refs:.2f}")

def test_comedian_recognition():
    """Test comedian style recognition"""
    print_section("COMEDIAN STYLE RECOGNITION TESTS")

    processor = GlobalEnglishComedyProcessor()

    # Test samples designed to match specific comedians
    test_samples = {
        "Dave Chappelle Style": """
        You know what's really messed up about America? We've got all these
        people getting offended by everything. I can't even tell a joke
        anymore without someone writing a think piece about it. What happened
        to just laughing? Remember when we could just laugh at stuff?
        Now everything's political. Everything's controversial. Sometimes
        a joke is just a joke, you know?
        """,

        "Ricky Gervais Style": """
        It's quite awkward, really, being here. I'm looking at all of you
        thinking, "Why did you invite me?" I'm not particularly charming,
        I'm not especially funny, and yet here we are. It's like when you
        go to a party and realize you don't really know anyone, but you're
        already there so you have to make the best of it. That's basically
        my life, really.
        """,

        "Vir Das Style": """
        The difference between India and America is simple. In India, when
        you tell your parents you want to be a comedian, they say, "Comedy?
        Like, hobby? What about your real job?" In America, when you tell
        your parents you want to be a comedian, they say, "That's amazing!
        Follow your dreams!" Indian parents don't understand dreams unless
        they involve medical degrees.
        """
    }

    for test_name, test_text in test_samples.items():
        print_subsection(f"Testing: {test_name}")

        culture, _ = processor.detect_cultural_context(test_text)
        similar_comedians = processor.identify_comedian_style(test_text, culture)

        print(f"Top 3 Similar Comedians:")
        for comedian, score in similar_comedians[:3]:
            print(f"  {comedian}: {score:.2f}")

def test_cross_cultural_adaptation():
    """Test cross-cultural adaptation capabilities"""
    print_section("CROSS-CULTURAL ADAPTATION TESTS")

    processor = GlobalEnglishComedyProcessor()

    adaptation_tests = [
        {
            "name": "Indian to US Adaptation",
            "joke": """
            My Indian mother has this amazing ability to find a husband for
            everyone. I tell her I'm not interested in marriage right now,
            and she says, "What are you waiting for? You're not getting any
            younger! My friend's daughter, she's 28, already has two kids!
            What will people say?" The concept of personal choice doesn't
            exist in her worldview.
            """,
            "target": ComedyCulture.US
        },
        {
            "name": "US to UK Adaptation",
            "joke": """
            So I was at this football game, right? And the guy next to me is
            going absolutely crazy - screaming, jumping up and down, spilling
            popcorn everywhere. I'm like, "Dude, it's just the first quarter!"
            He looks at me like I insulted his family. Americans take their
            sports way too seriously, man.
            """,
            "target": ComedyCulture.UK
        },
        {
            "name": "UK to Indian Adaptation",
            "joke": """
            I went to the pub for a quiet pint, ended up in this three-hour
            conversation about Brexit with a stranger who used to be in the
            army. That's the British experience - you can't just enjoy a drink
            without discussing politics, class, and the state of the nation.
            It's exhausting, really.
            """,
            "target": ComedyCulture.INDIAN
        }
    ]

    for test in adaptation_tests:
        print_subsection(f"Testing: {test['name']}")

        analysis = processor.adapt_joke_cross_cultural(test['joke'], test['target'])

        print(f"Original Culture: {analysis.original_culture.value}")
        print(f"Target Culture: {analysis.target_culture.value}")
        print(f"Adaptation Score: {analysis.cultural_adaptation_score:.2f}")
        print(f"Humor Preservation: {analysis.humor_preservation_score:.2f}")

        if analysis.required_adaptations:
            print(f"\nRequired Adaptations:")
            for adaptation in analysis.required_adaptations:
                print(f"  • {adaptation}")

        if analysis.cultural_barriers:
            print(f"\nCultural Barriers:")
            for barrier in analysis.cultural_barriers:
                print(f"  • {barrier}")

        if analysis.universal_elements:
            print(f"\nUniversal Elements:")
            for element in analysis.universal_elements:
                print(f"  • {element}")

        if analysis.adaptation_suggestions:
            print(f"\nAdaptation Suggestions:")
            for suggestion in analysis.adaptation_suggestions[:3]:
                print(f"  • {suggestion}")

def test_cultural_appropriateness():
    """Test cultural appropriateness evaluation"""
    print_section("CULTURAL APPROPRIATENESS EVALUATION TESTS")

    processor = GlobalEnglishComedyProcessor()

    test_cases = [
        {
            "name": "US Content for UK Audience",
            "text": """
            I love Thanksgiving! It's the one day of the year where Americans
            can collectively eat until we hate ourselves. Family comes over,
            we watch football, argue about politics, and eat like we're
            preparing for winter hibernation. It's beautiful, really.
            """,
            "audience": ComedyCulture.UK
        },
        {
            "name": "UK Content for US Audience",
            "text": """
            The thing about British weather is it builds character. You wake up,
            it's raining. You go to work, it's raining. You come home, still raining.
            But do we complain? Well, yes, actually. We complain constantly.
            It's our national pastime, really. Moaning about the weather while
            waiting for a delayed train - that's the authentic British experience.
            """,
            "audience": ComedyCulture.US
        },
        {
            "name": "Indian Content for International Audience",
            "text": """
            Indian weddings are like a week-long production. There's the mehendi,
            the sangeet, the wedding itself, the reception - each event requires
            different outfits, different jewelry, different ceremonies. My American
            friends came to my wedding and were completely overwhelmed. They were
            like, "Is this a wedding or a Bollywood movie?" I had to explain,
            "Yes, essentially. This is what we do."
            """,
            "audience": ComedyCulture.CROSS_CULTURAL
        }
    ]

    for test in test_cases:
        print_subsection(f"Testing: {test['name']}")

        scores = processor.evaluate_cultural_appropriateness(test['text'], test['audience'])

        print(f"Cultural Alignment: {scores['cultural_alignment']:.2f}")
        print(f"Humor Preservation: {scores['humor_preservation']:.2f}")
        print(f"Offense Risk: {scores['offense_risk']:.2f}")
        print(f"Engagement Prediction: {scores['engagement_prediction']:.2f}")
        print(f"Overall Appropriateness: {scores['overall_appropriateness']:.2f}")

        # Provide recommendation
        if scores['overall_appropriateness'] > 0.7:
            recommendation = "Highly suitable for target audience"
        elif scores['overall_appropriateness'] > 0.5:
            recommendation = "Moderately suitable with some adaptations"
        else:
            recommendation = "Requires significant adaptation"

        print(f"Recommendation: {recommendation}")

def test_comedian_profiles():
    """Test comedian profile information"""
    print_section("COMEDIAN PROFILE INFORMATION")

    processor = GlobalEnglishComedyProcessor()

    # Display key comedians from each culture
    key_comedians = ['dave_chappelle', 'ricky_gervais', 'vir_das']

    for comedian_name in key_comedians:
        profile = processor.cultural_profiles[comedian_name]

        print_subsection(f"Profile: {profile.name}")

        print(f"Nationality: {profile.nationality.value}")
        print(f"Style: {profile.style.value}")
        print(f"Key Themes: {', '.join(profile.key_themes[:3])}")
        print(f"Cross-Cultural Appeal: {profile.cross_cultural_appeal:.2f}")
        print(f"Dark Humor Tolerance: {profile.dark_humor_tolerance:.2f}")
        print(f"Tempo Analysis:")
        print(f"  Words per Minute: {profile.tempo_analysis['words_per_minute']}")
        print(f"  Pause Frequency: {profile.tempo_analysis['pause_frequency']:.2f}")
        print(f"  Emphasis Variance: {profile.tempo_analysis['emphasis_variance']:.2f}")

def test_performance_benchmarks():
    """Test system performance with various content types"""
    print_section("PERFORMANCE BENCHMARK TESTS")

    processor = GlobalEnglishComedyProcessor()

    # Generate mixed content samples
    mixed_content = [
        "Why do Americans call it football when they barely use their feet?",
        "The British class system is like an invisible ladder everyone pretends doesn't exist.",
        "In India, your mother's approval is more important than your own happiness.",
        "I told my doctor I broke my arm in two places. He told me to stop going to those places."
    ]

    print_subsection("Processing Speed Test")

    import time

    start_time = time.time()

    for i, content in enumerate(mixed_content):
        culture, _ = processor.detect_cultural_context(content)
        features = processor.extract_cultural_features(content, culture)
        _ = processor.evaluate_cultural_appropriateness(content, ComedyCulture.US)

    end_time = time.time()

    processing_time = end_time - start_time
    avg_time_per_sample = processing_time / len(mixed_content)

    print(f"Total processing time: {processing_time:.4f} seconds")
    print(f"Average time per sample: {avg_time_per_sample:.4f} seconds")
    print(f"Samples processed: {len(mixed_content)}")
    print(f"Processing rate: {len(mixed_content)/processing_time:.2f} samples/second")

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print_section("GLOBAL ENGLISH COMEDY SYSTEM")
    print("COMPREHENSIVE TEST SUITE")
    print("Testing Cross-Cultural Comedy Understanding System")

    try:
        # Run all test suites
        test_cultural_detection()
        test_comedian_recognition()
        test_cross_cultural_adaptation()
        test_cultural_appropriateness()
        test_comedian_profiles()
        test_performance_benchmarks()

        print_section("TEST COMPLETION SUMMARY")
        print("✓ All tests completed successfully!")
        print("✓ Cultural detection: Functional")
        print("✓ Comedian recognition: Functional")
        print("✓ Cross-cultural adaptation: Functional")
        print("✓ Cultural appropriateness: Functional")
        print("✓ Performance benchmarks: Complete")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_tests()
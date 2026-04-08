#!/usr/bin/env python3
"""
Real Data Fetcher - Get actual comedy transcripts and audio
Tests various data sources and reports limitations
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealDataFetcher:
    """Fetch real comedy data from various sources"""
    
    def __init__(self, output_dir: str = "data/real_comedy_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        
    def test_scraps_from_loft(self) -> Dict:
        """Test Scraps from the Loft website"""
        logger.info("🧪 Testing Scraps from the Loft...")
        
        results = {
            'source': 'scraps_from_loft',
            'accessible': False,
            'sample_transcripts': 0,
            'limitations': [],
            'transcripts': []
        }
        
        try:
            # Test with popular comedians
            test_comedians = [
                "Dave Chappelle",
                "John Mulaney", 
                "Hannah Gadsby",
                "Bo Burnham",
                "Chris Rock"
            ]
            
            for comedian in test_comedians[:2]:  # Test 2 comedians
                search_url = f"https://scrapsfromtheloft.com/?s={comedian.replace(' ', '+')}"
                
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    articles = soup.find_all('article', class_='post')
                    
                    for article in articles[:2]:  # Get 2 transcripts per comedian
                        title_elem = article.find('h2', class_='entry-title')
                        link_elem = title_elem.find('a') if title_elem else None
                        
                        if link_elem:
                            transcript_url = link_elem.get('href', '')
                            title = link_elem.get_text(strip=True)
                            
                            # Fetch full transcript
                            transcript_data = self._fetch_scraps_transcript(transcript_url)
                            
                            if transcript_data:
                                results['transcripts'].append({
                                    'comedian': comedian,
                                    'title': title,
                                    'url': transcript_url,
                                    'content': transcript_data[:500] + '...' if len(transcript_data) > 500 else transcript_data,
                                    'word_count': len(transcript_data.split())
                                })
                                results['sample_transcripts'] += 1
                                
                                # Save individual transcript
                                self._save_transcript(comedian, title, transcript_data)
                    
                    time.sleep(2)  # Rate limiting
                    
            results['accessible'] = True
            
        except Exception as e:
            results['limitations'].append(f"Error: {str(e)}")
            logger.error(f"Error testing Scraps from the Loft: {e}")
            
        return results
    
    def _fetch_scraps_transcript(self, url: str) -> str:
        """Fetch full transcript content"""
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                content_div = soup.find('div', class_='entry-content')
                
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.find_all(['script', 'style', 'iframe', 'div']):
                        if unwanted.get('class') and any('ad' in str(c).lower() for c in unwanted.get('class', [])):
                            unwanted.decompose()
                    
                    transcript_text = content_div.get_text(separator='\n', strip=True)
                    return transcript_text
                    
        except Exception as e:
            logger.error(f"Error fetching transcript from {url}: {e}")
            
        return ""
    
    def test_opensubtitles_api(self) -> Dict:
        """Test OpenSubtitles API access"""
        logger.info("🧪 Testing OpenSubtitles API...")
        
        results = {
            'source': 'opensubtitles',
            'accessible': False,
            'api_key_required': True,
            'limitations': [],
            'sample_results': 0
        }
        
        try:
            # Test without API key first
            test_url = "https://api.opensubtitles.com/api/v1/subtitles"
            params = {
                'query': 'comedy special',
                'languages': 'en'
            }
            
            response = self.session.get(test_url, params=params, timeout=10)
            
            if response.status_code == 401:
                results['limitations'].append("API key required - not configured")
            elif response.status_code == 429:
                results['limitations'].append("Rate limited - API key needed")
            elif response.status_code == 200:
                data = response.json()
                results['sample_results'] = len(data.get('data', []))
                results['accessible'] = True
            else:
                results['limitations'].append(f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            results['limitations'].append(f"Connection error: {str(e)}")
            
        return results
    
    def test_youtube_comedy(self) -> Dict:
        """Test YouTube comedy specials availability"""
        logger.info("🧪 Testing YouTube comedy specials...")
        
        results = {
            'source': 'youtube',
            'accessible': False,
            'limitations': [],
            'note': 'Would require youtube-dl or yt-dlp for actual downloading'
        }
        
        # Note: This would require youtube-dl or yt-dlp
        results['limitations'].append("YouTube requires youtube-dl/yt-dlp for video downloading")
        results['limitations'].append("Large video files (500MB-2GB per special)")
        results['limitations'].append("Potential copyright issues")
        
        return results
    
    def test_podbay_fm(self) -> Dict:
        """Test comedy podcast transcripts"""
        logger.info("🧪 Testing comedy podcast sources...")
        
        results = {
            'source': 'comedy_podcasts',
            'accessible': False,
            'sample_transcripts': 0,
            'limitations': []
        }
        
        try:
            # Test some popular comedy podcasts
            test_urls = [
                "https://www.comedybangbang.com/transcripts",
                "https://www.earwolf.com/show/comedy-bang-bang/"
            ]
            
            for url in test_urls[:1]:  # Test 1 source
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        results['accessible'] = True
                        results['limitations'].append("Podcast transcripts available but may require payment")
                    else:
                        results['limitations'].append(f"Podcast site returned {response.status_code}")
                except Exception as e:
                    results['limitations'].append(f"Podcast error: {str(e)}")
                    
        except Exception as e:
            results['limitations'].append(f"General podcast error: {str(e)}")
            
        return results
    
    def _save_transcript(self, comedian: str, title: str, content: str):
        """Save individual transcript"""
        safe_comedian = comedian.replace(' ', '_').replace('/', '_')
        safe_title = title.replace(' ', '_')[:50]  # Limit length
        
        comedian_dir = self.output_dir / safe_comedian
        comedian_dir.mkdir(exist_ok=True)
        
        filename = comedian_dir / f"{safe_title}.json"
        
        transcript_data = {
            'comedian': comedian,
            'title': title,
            'content': content,
            'word_count': len(content.split()),
            'estimated_duration_minutes': len(content.split()) / 150  # ~150 words per minute
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"✅ Saved: {filename}")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive data availability report"""
        logger.info("📊 Generating Data Availability Report...")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'data_sources': [],
            'overall_assessment': '',
            'recommendations': []
        }
        
        # Test each data source
        sources = [
            self.test_scraps_from_loft(),
            self.test_opensubtitles_api(),
            self.test_youtube_comedy(),
            self.test_podbay_fm()
        ]
        
        for source in sources:
            report['data_sources'].append(source)
        
        # Generate overall assessment
        accessible_count = sum(1 for s in sources if s.get('accessible', False))
        total_transcripts = sum(s.get('sample_transcripts', 0) for s in sources)
        
        if total_transcripts > 0:
            report['overall_assessment'] = f"✅ SUCCESS: Found {total_transcripts} real comedy transcripts"
            report['recommendations'].append("Proceed with real training data")
        else:
            report['overall_assessment'] = "❌ LIMITED: No real transcripts accessible"
            report['recommendations'].append("Consider using public domain comedy content")
            report['recommendations'].append("Manually create small dataset of labeled content")
        
        # Save report
        report_path = self.output_dir / "data_availability_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info(f"📄 Report saved to {report_path}")
        
        return report


def main():
    """Main function to fetch real data"""
    print("🎭 Real Comedy Data Fetcher")
    print("=" * 40)
    
    fetcher = RealDataFetcher()
    
    # Generate comprehensive report
    report = fetcher.generate_report()
    
    # Print summary
    print("\n📊 DATA AVAILABILITY SUMMARY:")
    print("=" * 40)
    
    for source in report['data_sources']:
        status = "✅ ACCESSIBLE" if source.get('accessible') else "❌ NOT ACCESSIBLE"
        print(f"\n{source['source'].upper()}: {status}")
        
        if source.get('sample_transcripts'):
            print(f"   📝 Transcripts found: {source['sample_transcripts']}")
        
        if source.get('limitations'):
            print(f"   ⚠️  Limitations:")
            for limit in source['limitations']:
                print(f"      - {limit}")
    
    print(f"\n📈 Overall: {report['overall_assessment']}")
    
    if report.get('recommendations'):
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    print(f"\n📁 Data saved to: {fetcher.output_dir}")
    print(f"📄 Full report: {fetcher.output_dir}/data_availability_report.json")


if __name__ == "__main__":
    main()
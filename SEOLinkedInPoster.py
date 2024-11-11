import os
from typing import Optional, Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from google.colab import userdata
from datetime import datetime
import json
from linkedin_api import create_post, LinkedInError
import random
import re

class SEOLinkedInPoster:
    def __init__(self, groq_api_key: str, linkedin_access_token: str):
        """
        Initialize the SEO-optimized LinkedIn Poster
        
        Args:
            groq_api_key (str): API key for Groq
            linkedin_access_token (str): LinkedIn OAuth access token
        """
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.2-90b-vision-preview"
        )
        self.linkedin_token = linkedin_access_token
        self.profile_data = {
            "name": "Muhammad Abdullah",
            "pronouns": "(He/Him)",
            "title": "AI & Machine Learning Developer | Generative AI & Chatbot Specialist",
            "skills": ["Python", "Flask", "Streamlit", "Snowflake", "Docker"],
            "profile_url": "https://www.linkedin.com/in/muhammad-abdullah-ai-ml-developer/",
            "primary_keywords": [
                "AI Developer",
                "Machine Learning Expert",
                "Generative AI Specialist",
                "Chatbot Developer",
                "Python Developer"
            ]
        }
        
    def get_content_themes(self) -> List[Dict[str, Any]]:
        """Define content themes for variety and SEO impact"""
        return [
            {
                "theme": "expertise_showcase",
                "headline_emojis": ["🚀", "💡"],
                "focus": "Technical expertise and problem-solving capabilities"
            },
            {
                "theme": "thought_leadership",
                "headline_emojis": ["🤖", "🔮"],
                "focus": "AI/ML industry insights and future trends"
            },
            {
                "theme": "solution_spotlight",
                "headline_emojis": ["⚡", "🎯"],
                "focus": "Specific solutions and case studies"
            },
            {
                "theme": "technology_deep_dive",
                "headline_emojis": ["🔍", "💻"],
                "focus": "Technical deep dives into AI/ML concepts"
            }
        ]

    def get_seo_optimized_hashtags(self) -> List[str]:
        """Get rotating set of SEO-optimized hashtags"""
        hashtag_pools = {
            "core": ["AI", "MachineLearning", "GenerativeAI", "ArtificialIntelligence"],
            "technical": ["PythonProgramming", "DataScience", "ChatbotDevelopment", "MLOps"],
            "business": ["DigitalTransformation", "TechInnovation", "BusinessAI", "AIStrategy"],
            "trending": ["FutureOfAI", "AITechnology", "TechTrends", "Innovation"]
        }
        
        # Select hashtags from each category
        selected_hashtags = (
            random.sample(hashtag_pools["core"], 2) +
            random.sample(hashtag_pools["technical"], 2) +
            random.sample(hashtag_pools["business"], 1) +
            random.sample(hashtag_pools["trending"], 1)
        )
        
        return selected_hashtags

    def generate_post_content(self) -> str:
        """Generate SEO-optimized LinkedIn post content with length control"""
        theme = random.choice(self.get_content_themes())
        
        template = f'''
        Create a concise LinkedIn post for an AI & Machine Learning Developer. The post MUST be between 150-175 words total.

        Profile Context:
        - Name: {self.profile_data["name"]} {self.profile_data["pronouns"]}
        - Role: {self.profile_data["title"]}
        - Key Skills: {', '.join(self.profile_data["skills"])}

        Content Theme: {theme["focus"]}

        Structure Requirements:

        1. Headline (with {theme["headline_emojis"][0]}):
        - Include keyword: {random.choice(self.profile_data["primary_keywords"])}
        - Keep under 15 words

        2. Introduction (2 short paragraphs):
        - First paragraph: Core message (25-30 words)
        - Second paragraph: Value proposition (25-30 words)
        - Mention {self.profile_data["skills"][0]} and {self.profile_data["skills"][1]}

        3. Key Points (2-3 bullet points):
        - Use ✨, 💪, 🔍
        - Each point 15-20 words
        - Focus on outcomes

        4. Call-to-Action:
        - Short networking invitation
        - End with 🤝
        - Profile URL on new line "https://www.linkedin.com/in/muhammad-abdullah-ai-ml-developer/"

        Important:
        - Total word count must be 150-175 words
        - Use concise, impactful language
        - Avoid repetition
        '''

        pt = PromptTemplate.from_template(template)
        chain = pt | self.llm
        response = chain.invoke(input={})
        return response.content if hasattr(response, 'content') else response

    def format_post_content(self, content: str) -> str:
        """Format and optimize the post content with length validation"""
        # Clean up content
        formatted_sections = []
        sections = content.split('\n\n')
        
        for section in sections:
            # Skip empty sections
            if not section.strip():
                continue
                
            # Clean formatting
            clean_section = (section.replace('**', '')
                                  .replace('*', '')
                                  .strip())
            
            # Handle hashtags section
            if clean_section.startswith('#'):
                hashtags = self.get_seo_optimized_hashtags()
                clean_section = ' '.join(f'#{tag}' for tag in hashtags)
            
            # Ensure proper emoji spacing
            emojis = ['🚀', '💡', '🤖', '✨', '💪', '🔍', '🎯', '⚡', '🔮', '💻', '🤝']
            for emoji in emojis:
                clean_section = clean_section.replace(emoji, f'{emoji} ')
            
            formatted_sections.append(clean_section)
        
        # Join sections and format profile URL
        formatted_content = '\n\n'.join(formatted_sections)
        if self.profile_data["profile_url"] in formatted_content:
            formatted_content = formatted_content.replace(
                self.profile_data["profile_url"],
                f'\n{self.profile_data["profile_url"]}'
            )
        
        # Truncate content if too long
        words = formatted_content.split()
        if len(words) > 175:
            # Keep first 170 words and add ellipsis
            formatted_content = ' '.join(words[:170]) + '...'
            # Ensure profile URL is preserved
            formatted_content += f'\n\n{self.profile_data["profile_url"]}'
        
        return formatted_content.strip()

    def validate_content_length(self, content: str) -> bool:
        """Validate content length is within acceptable range"""
        # Remove URLs from word count
        content_without_urls = re.sub(r'http\S+|www.\S+', '', content)
        # Remove hashtags from word count
        content_without_hashtags = re.sub(r'#\w+', '', content_without_urls)
        # Count remaining words
        word_count = len(content_without_hashtags.split())
        return 150 <= word_count <= 175

    def _calculate_keyword_density(self, content: str) -> Dict[str, float]:
        """Calculate keyword density for SEO analysis"""
        content_words = content.lower().split()
        total_words = len(content_words)
        
        keyword_density = {}
        for keyword in self.profile_data["primary_keywords"]:
            keyword_count = sum(1 for word in content_words if keyword.lower() in word)
            density = (keyword_count / total_words) * 100 if total_words > 0 else 0
            keyword_density[keyword] = round(density, 2)
            
        return keyword_density

    def save_post_record(self, post_data: Dict[str, Any], file_path: str = "linkedin_posts_seo.json") -> None:
        """Save post record with SEO metrics"""
        try:
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            
            posts = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    posts = json.load(f)
            
            if 'content' in post_data:
                post_data['seo_metrics'] = {
                    'keyword_density': self._calculate_keyword_density(post_data['content']),
                    'hashtag_count': post_data['content'].count('#'),
                    'content_length': len(post_data['content'].split()),
                    'emoji_count': sum(1 for char in post_data['content'] if char in ['🚀', '💡', '🤖', '✨', '💪', '🔍', '🤝'])
                }
            
            posts.append(post_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving post record: {str(e)}")

    def create_seo_post(self, max_attempts: int = 3) -> Dict[str, Any]:
        """Generate and publish SEO-optimized LinkedIn post with retry logic"""
        for attempt in range(max_attempts):
            try:
                print(f"Attempt {attempt + 1}/{max_attempts}: Generating content...")
                raw_content = self.generate_post_content()
                
                print("Optimizing content format...")
                formatted_content = self.format_post_content(raw_content)
                
                if not self.validate_content_length(formatted_content):
                    print("Content length validation failed. Retrying...")
                    continue
                
                print("Publishing to LinkedIn...")
                result = create_post(
                    access_token=self.linkedin_token,
                    message=formatted_content,
                    debug=True
                )
                
                post_record = {
                    "date": datetime.now().isoformat(),
                    "content": formatted_content,
                    "post_id": result.get("post_id") if result["success"] else None,
                    "success": result["success"],
                    "error": result.get("error") if not result["success"] else None,
                    "attempt": attempt + 1,
                    "optimization_metrics": {
                        "word_count": len(formatted_content.split()),
                        "primary_keywords_used": self._calculate_keyword_density(formatted_content)
                    }
                }
                
                self.save_post_record(post_record)
                return result
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    error_data = {
                        "success": False,
                        "error": str(e),
                        "error_type": e.__class__.__name__,
                        "attempts": attempt + 1
                    }
                    if 'formatted_content' in locals():
                        error_data["content"] = formatted_content
                    self.save_post_record({"date": datetime.now().isoformat(), "error": error_data})
                    return error_data

def main():
    try:
        # Get API keys
        GROQ_API_KEY = userdata.get('GROQ_API_KEY')
        LINKEDIN_TOKEN = userdata.get('LINKEDIN_ACCESS_TOKEN')
        
        if not GROQ_API_KEY or not LINKEDIN_TOKEN:
            raise ValueError("Missing required API keys in Colab Secrets")
        
        # Initialize poster
        poster = SEOLinkedInPoster(
            groq_api_key=GROQ_API_KEY,
            linkedin_access_token=LINKEDIN_TOKEN
        )
        
        # Create and publish post
        print("Creating SEO-optimized LinkedIn post...")
        result = poster.create_seo_post()
        
        if result["success"]:
            print(f"\n✅ Post published successfully!")
            print(f"Post ID: {result['post_id']}")
        else:
            print(f"\n❌ Publishing failed:")
            print(f"Error type: {result.get('error_type', 'Unknown')}")
            print(f"Error message: {result.get('error', 'No error message available')}")
            
    except Exception as e:
        print(f"\n❌ Critical error:")
        print(f"Type: {e.__class__.__name__}")
        print(f"Message: {str(e)}")

if __name__ == "__main__":
    main()
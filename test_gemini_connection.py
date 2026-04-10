#!/usr/bin/env python3
import os
import sys
sys.path.append('/Users/Subho/CascadeProjects/multi-ai-treequest')

# Set the new Gemini API key
os.environ['GOOGLE_API_KEY'] = 'AIzaSyACzQY7NG7cJiv7Mlq3WrHL0nqT9FRNLOg'

import asyncio
from ai_wrappers import AIWrapperFactory

async def test_gemini_connection():
    print('🔍 Testing Gemini API Connection with New Key')
    print('=' * 50)
    
    try:
        # Create wrappers with new API key
        wrappers = AIWrapperFactory.create_all_available_wrappers()
        
        if 'gemini' in wrappers:
            gemini_wrapper = wrappers['gemini']
            print(f'✅ Gemini wrapper created successfully')
            print(f'   Model: {gemini_wrapper.config.model_name}')
            
            # Test simple API call
            print('\n🔄 Testing Gemini API call...')
            result = await gemini_wrapper.execute_task('What is 2+2? Answer in one sentence.')
            
            if result.success:
                print(f'✅ GEMINI SUCCESS!')
                print(f'   Content: {result.content}')
                print(f'   Tokens: {result.tokens_used}')
                print(f'   Cost: ${result.cost:.6f}')
                print(f'   Time: {result.execution_time:.2f}s')
                
                # Test with a more complex prompt
                print('\n🔄 Testing complex prompt...')
                complex_result = await gemini_wrapper.execute_task(
                    'Explain the benefits of using React hooks in modern web development.'
                )
                
                if complex_result.success:
                    print(f'✅ COMPLEX TASK SUCCESS!')
                    print(f'   Content preview: {complex_result.content[:150]}...')
                    print(f'   Time: {complex_result.execution_time:.2f}s')
                else:
                    print(f'❌ Complex task failed: {complex_result.error_message}')
                    
            else:
                print(f'❌ GEMINI FAILED: {result.error_message}')
                
        else:
            print('❌ Gemini wrapper not available')
            print('Available wrappers:', list(wrappers.keys()))
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini_connection())
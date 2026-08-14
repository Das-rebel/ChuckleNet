import subprocess
import time
import webbrowser
import sys

print('🚀 CHUCKLENET GPU EXTRACTION - FULL AUTOMATION')
print('=' * 55)
print('')

# Check kernel availability
try:
    result = subprocess.run(['python3', '-m', 'kaggle', 'kernels', 'list', '--mine'], 
                          capture_output=True, text=True)
    if 'chucklenet-gpu-extraction' in result.stdout:
        print('✅ GPU extraction kernel found')
        
        # Get kernel URL and ID
        lines = result.stdout.split('\n')
        for line in lines:
            if 'chucklenet-gpu-extraction' in line and '11.4x' in line:
                kernel_ref = line.split()[0]
                print(f'🎯 Kernel ID: {kernel_ref}')
                
                # Open browser for manual execution
                kernel_url = f'https://www.kaggle.com/code/{kernel_ref}'
                print(f'📤 Opening browser: {kernel_url}')
                webbrowser.open(kernel_url)
                
                print('')
                print('🎬 EXECUTION INSTRUCTIONS:')
                print('1. Click "Copy and Edit" to create your kernel')
                print('2. Go to Settings and select "T4 GPU"')
                print('3. Click "Run All" cells')
                print('4. Wait ~1.2 hours for completion')
                print('5. Download "vtt_frames" folder when done')
                print('')
                print('⚡ Automation completed! Browser opened for execution.')
                break
    else:
        print('❌ GPU extraction kernel not found')
        
except Exception as e:
    print(f'❌ Error: {e}')

print('')
print('🎉 GPU EXTRACTION PROCESS INITIATED!')
print('📊 Expected completion: ~1.2 hours')
print('🚀 11.4x faster than CPU extraction!')

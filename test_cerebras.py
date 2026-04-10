import sys
import cerebras_cloud_sdk

def main():
    try:
        print(f"Python version: {sys.version}")
        print(f"Cerebras SDK version: {cerebras_cloud_sdk.__version__}")
        print("Cerebras SDK is working!")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

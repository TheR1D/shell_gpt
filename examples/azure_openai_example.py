#!/usr/bin/env python3
"""
Example script demonstrating ShellGPT with Azure OpenAI provider.

This script shows how to configure and use ShellGPT with Azure OpenAI.
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_azure_openai_config():
    """Set up Azure OpenAI configuration."""
    config_dir = Path.home() / ".config" / "shell_gpt"
    config_file = config_dir / ".sgptrc"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Read existing config or create new one
    config_lines = []
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_lines = f.readlines()
    
    # Check if OPENAI_PROVIDER is already set
    provider_set = any(line.startswith("OPENAI_PROVIDER=") for line in config_lines)
    
    if not provider_set:
        config_lines.append("OPENAI_PROVIDER=azure-openai\n")
        
        with open(config_file, 'w') as f:
            f.writelines(config_lines)
        print(f"✅ Added OPENAI_PROVIDER=azure-openai to {config_file}")
    else:
        print(f"✅ OPENAI_PROVIDER already configured in {config_file}")


def run_sgpt_example():
    """Run a simple ShellGPT example with Azure OpenAI."""
    print("\n🚀 Running ShellGPT example with Azure OpenAI...")
    print("Note: Shell commands in interactive mode will prompt for Execute/Describe/Abort")
    
    # Set environment variable for this session
    os.environ["OPENAI_PROVIDER"] = "azure-openai"
    
    try:
        # Example 1: Simple question
        print("\n📝 Example 1: Simple question")
        result = subprocess.run(
            ["sgpt", "What is the capital of France?"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"Response: {result.stdout.strip()}")
        else:
            print(f"Error: {result.stderr.strip()}")
        
        # Example 2: Shell command generation (non-interactive)
        print("\n💻 Example 2: Shell command generation (non-interactive)")
        print("Using --no-interaction flag to avoid interactive prompts")
        result = subprocess.run(
            ["sgpt", "--shell", "--no-interaction", "list all files in current directory"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"Generated command: {result.stdout.strip()}")
        else:
            print(f"Error: {result.stderr.strip()}")
        
        
        # Example 3: Code generation
        print("\n🐍 Example 3: Code generation")
        result = subprocess.run(
            ["sgpt", "--code", "hello world in python"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"Generated code:\n{result.stdout.strip()}")
        else:
            print(f"Error: {result.stderr.strip()}")
        
        # Example 4: Chat mode
        print("\n💬 Example 4: Chat mode")
        result = subprocess.run(
            ["sgpt", "--chat", "test_session", "Remember my name is Alice"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"Chat response: {result.stdout.strip()}")
        else:
            print(f"Error: {result.stderr.strip()}")
            
    except subprocess.TimeoutExpired:
        print("❌ Request timed out. Please check your Azure OpenAI configuration.")
    except FileNotFoundError:
        print("❌ ShellGPT not found. Please install it first: pip install shell-gpt")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_configuration():
    """Check if Azure OpenAI is properly configured."""
    print("🔍 Checking Azure OpenAI Configuration")
    print("=" * 50)
    
    # Check if provider is set to azure-openai
    if os.getenv("OPENAI_PROVIDER") != "azure-openai":
        print("\n⚠️  Warning: OPENAI_PROVIDER not set to azure-openai.")
        print("   Please set: export OPENAI_PROVIDER=azure-openai")
        print("\n   Or add it to your config file:")
        print("   echo 'OPENAI_PROVIDER=azure-openai' >> ~/.config/shell_gpt/.sgptrc")
    
    # Check if Azure-specific configuration is set
    if not os.getenv("AZURE_RESOURCE_ENDPOINT"):
        print("\n⚠️  Warning: AZURE_RESOURCE_ENDPOINT not configured.")
        print("   For Azure OpenAI, please set your resource endpoint:")
        print("   export AZURE_RESOURCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com")
        print("\n   Or add it to your config file:")
        print("   echo 'AZURE_RESOURCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com' >> ~/.config/shell_gpt/.sgptrc")
    
    if not os.getenv("AZURE_DEPLOYMENT_NAME"):
        print("\n⚠️  Warning: AZURE_DEPLOYMENT_NAME not configured.")
        print("   For Azure OpenAI, please set your deployment name:")
        print("   export AZURE_DEPLOYMENT_NAME=your-deployment-name")
        print("\n   Or add it to your config file:")
        print("   echo 'AZURE_DEPLOYMENT_NAME=your-deployment-name' >> ~/.config/shell_gpt/.sgptrc")
    
    if not os.getenv("API_VERSION"):
        print("\n⚠️  Warning: API_VERSION not configured.")
        print("   For Azure OpenAI, please set your API version:")
        print("   export API_VERSION=2025-01-01-preview")
        print("\n   Or add it to your config file:")
        print("   echo 'API_VERSION=2025-01-01-preview' >> ~/.config/shell_gpt/.sgptrc")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not configured.")
        print("   Please set your Azure OpenAI API key:")
        print("   export OPENAI_API_KEY=your_azure_openai_api_key")
        print("\n   Or add it to your config file:")
        print("   echo 'OPENAI_API_KEY=your_azure_openai_api_key' >> ~/.config/shell_gpt/.sgptrc")
    
    # Show example configuration
    print("\n📋 Example Azure OpenAI Configuration:")
    print("   export OPENAI_PROVIDER=azure-openai")
    print("   export AZURE_RESOURCE_ENDPOINT=https://er-biz-svcs-us.cognitiveservices.azure.com")
    print("   export AZURE_DEPLOYMENT_NAME=erbizgpt4o")
    print("   export API_VERSION=2025-01-01-preview")
    print("   export OPENAI_API_KEY=your_azure_openai_api_key")
    
    print("\n🔗 This will use the AzureOpenAI client with:")
    print("   - Endpoint: https://er-biz-svcs-us.cognitiveservices.azure.com")
    print("   - Deployment: erbizgpt4o")
    print("   - API Version: 2025-01-01-preview")
    print("   - Model parameter: erbizgpt4o (deployment name)")

def main():
    """Main function."""
    print("🔧 ShellGPT Azure OpenAI Provider Example")
    print("=" * 50)
    
    # Check if ShellGPT is installed
    try:
        subprocess.run(["sgpt", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ShellGPT not found. Please install it first:")
        print("   pip install shell-gpt")
        sys.exit(1)
    
    # Set up configuration
    setup_azure_openai_config()
    
    # Check configuration
    check_configuration()
    
    # Run examples
    run_sgpt_example()
    
    
    print("\n✅ Example completed!")
    print("\n📚 For more information, see:")
    print("   - README.md for detailed usage")
    print("   - Azure OpenAI documentation: https://docs.microsoft.com/en-us/azure/cognitive-services/openai/")
    print("\n💡 Tips for using ShellGPT with Azure OpenAI:")
    print("   - Use --no-interaction for non-interactive shell commands")
    print("   - Use --shell for interactive command generation")
    print("   - Use --code for pure code generation")
    print("   - Use --chat for conversation mode")

if __name__ == "__main__":
    main()
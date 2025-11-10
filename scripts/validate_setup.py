"""Quick validation script to test HR assistant setup."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from src.config.settings import get_settings
from src.plugins.hr_policy_plugin import HRPolicyPlugin, EmployeeServicesPlugin
from src.plugins.company_plugin import CompanyPlugin


async def test_plugins():
    """Test that plugins work without full SK setup."""
    logger.info("Testing HR Assistant Plugins...")
    
    # Test HR Policy Plugin
    hr_plugin = HRPolicyPlugin()
    logger.info("\n=== Testing HR Policy Plugin ===")
    
    question = "What is the leave policy?"
    answer = await hr_plugin.answer_policy_question(question)
    logger.info(f"Q: {question}")
    logger.info(f"A: {answer[:200]}...")
    
    # Test Employee Services
    emp_plugin = EmployeeServicesPlugin()
    logger.info("\n=== Testing Employee Services Plugin ===")
    
    balance = await emp_plugin.check_leave_balance("EMP001")
    logger.info(f"Leave Balance:\n{balance}")
    
    # Test Company Plugin
    company_plugin = CompanyPlugin()
    logger.info("\n=== Testing Company Plugin ===")
    
    info = await company_plugin.get_company_info("values")
    logger.info(f"Company Values:\n{info[:200]}...")
    
    logger.success("✓ All plugins tested successfully!")


async def test_configuration():
    """Test configuration loading."""
    logger.info("\n=== Testing Configuration ===")
    
    settings = get_settings()
    logger.info(f"App Name: {settings.app_name}")
    logger.info(f"App Version: {settings.app_version}")
    logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"Debug Mode: {settings.debug}")
    
    # Check Azure OpenAI config
    if settings.azure_openai_endpoint:
        logger.info(f"✓ Azure OpenAI configured: {settings.azure_openai_endpoint}")
    else:
        logger.warning("⚠ Azure OpenAI not configured - set HR_AZURE_OPENAI_* env vars")
    
    # Check Pinecone config
    if settings.pinecone_api_key:
        logger.info(f"✓ Pinecone configured: {settings.pinecone_index_name}")
    else:
        logger.warning("⚠ Pinecone not configured - document retrieval will be limited")
    
    logger.success("✓ Configuration loaded successfully!")


async def main():
    """Run all validation tests."""
    logger.info("=" * 60)
    logger.info("HR Assistant Validation")
    logger.info("=" * 60)
    
    try:
        await test_configuration()
        await test_plugins()
        
        logger.info("\n" + "=" * 60)
        logger.success("✓ All validation tests passed!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Configure .env file with Azure OpenAI and Pinecone credentials")
        logger.info("2. Run: python scripts/ingest_documents.py")
        logger.info("3. Run: python src/main.py")
        logger.info("4. Visit: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    asyncio.run(main())

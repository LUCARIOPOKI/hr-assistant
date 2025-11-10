import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding
from loguru import logger
from ..config.settings import get_settings

settings = get_settings()


class SemanticKernelManager:
    """Manager for Semantic Kernel initialization and configuration."""
    
    def __init__(self):
        """Initialize Semantic Kernel manager."""
        self.kernel = None
        self.chat_service = None
        self.embedding_service = None
        self._plugins_loaded = False
        
    def initialize_kernel(self) -> sk.Kernel:
        """
        Initialize Semantic Kernel with Azure OpenAI services.
        
        Returns:
            Configured Semantic Kernel instance
        """
        try:
            # Create kernel
            self.kernel = sk.Kernel()
            
            # Only add services if Azure OpenAI is configured
            if settings.azure_openai_api_key and settings.azure_openai_endpoint:
                # Add Azure OpenAI Chat Completion service
                self.chat_service = AzureChatCompletion(
                    deployment_name=settings.azure_openai_deployment_name,
                    endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                    service_id="chat_completion"
                )
                
                self.kernel.add_service(self.chat_service)
                
                # Add Azure OpenAI Embedding service
                if settings.azure_openai_embedding_deployment:
                    self.embedding_service = AzureTextEmbedding(
                        deployment_name=settings.azure_openai_embedding_deployment,
                        endpoint=settings.azure_openai_endpoint,
                        api_key=settings.azure_openai_api_key,
                        api_version=settings.azure_openai_api_version,
                        service_id="text_embedding"
                    )
                    
                    self.kernel.add_service(self.embedding_service)
                
                logger.info("Semantic Kernel initialized with Azure OpenAI services")
            else:
                logger.warning("Azure OpenAI not configured - running in limited mode")
            
            # Load HR plugins
            self._load_hr_plugins()
            
            return self.kernel
            
        except Exception as e:
            logger.error(f"Error initializing Semantic Kernel: {e}")
            raise
    
    def _load_hr_plugins(self):
        """Load HR-specific plugins into the kernel."""
        if self._plugins_loaded or self.kernel is None:
            return
        
        try:
            from ..plugins import (
                HRPolicyPlugin, 
                EmployeeServicesPlugin,
                RecruitmentPlugin,
                RetrievalPlugin,
                SummarizationPlugin,
                CompanyPlugin,
            )
            
            # Add plugins
            self.add_plugin("hr_policy", HRPolicyPlugin())
            self.add_plugin("employee_services", EmployeeServicesPlugin())
            self.add_plugin("recruitment", RecruitmentPlugin())
            self.add_plugin("retrieval", RetrievalPlugin())
            self.add_plugin("summarization", SummarizationPlugin())
            self.add_plugin("company", CompanyPlugin())
            
            self._plugins_loaded = True
            logger.info("HR plugins loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading HR plugins: {e}")
            # Don't raise - allow kernel to work without plugins
    
    def get_kernel(self) -> sk.Kernel:
        """
        Get Semantic Kernel instance.
        
        Returns:
            Semantic Kernel instance
        """
        if self.kernel is None:
            self.initialize_kernel()
        return self.kernel
    
    def add_plugin(self, plugin_name: str, plugin_instance):
        """
        Add a plugin to the kernel.
        
        Args:
            plugin_name: Name of the plugin
            plugin_instance: Plugin instance
        """
        try:
            if self.kernel is None:
                self.initialize_kernel()
            
            self.kernel.add_plugin(plugin_instance, plugin_name)
            logger.info(f"Added plugin: {plugin_name}")
            
        except Exception as e:
            logger.error(f"Error adding plugin {plugin_name}: {e}")
            raise
    
    def remove_plugin(self, plugin_name: str):
        """
        Remove a plugin from the kernel.
        
        Args:
            plugin_name: Name of the plugin to remove
        """
        try:
            if self.kernel is None:
                logger.warning("Kernel not initialized")
                return
            
            self.kernel.remove_plugin(plugin_name)
            logger.info(f"Removed plugin: {plugin_name}")
            
        except Exception as e:
            logger.error(f"Error removing plugin {plugin_name}: {e}")
            raise


# Global Semantic Kernel manager instance
sk_manager = SemanticKernelManager()
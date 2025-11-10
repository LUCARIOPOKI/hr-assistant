"""Plugins package - contains SK plugins for HR assistant functionality."""

from .hr_policy_plugin import HRPolicyPlugin, EmployeeServicesPlugin, RecruitmentPlugin
from .retrieval_plugin.retrieval_plugin import RetrievalPlugin
from .summarization_plugin import SummarizationPlugin
from .company_plugin import CompanyPlugin

__all__ = [
    "HRPolicyPlugin",
    "EmployeeServicesPlugin", 
    "RecruitmentPlugin",
    "RetrievalPlugin",
    "SummarizationPlugin",
    "CompanyPlugin",
]

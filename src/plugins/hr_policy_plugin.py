"""HR Policy Plugin - answers questions about company policies, benefits, and procedures."""

from semantic_kernel.functions import kernel_function
from loguru import logger
from typing import Annotated


class HRPolicyPlugin:
    """Plugin for HR policy-related queries."""

    @kernel_function(
        name="answer_policy_question",
        description="Answers questions about HR policies, benefits, leave policies, code of conduct, etc."
    )
    async def answer_policy_question(
        self,
        question: Annotated[str, "The HR policy question to answer"]
    ) -> str:
        """Answer HR policy questions using retrieval or predefined knowledge."""
        logger.info(f"HR Policy question: {question}")
        
        # Placeholder logic - in production, this would query vector DB with embedded policies
        # For now, return helpful static responses based on keywords
        question_lower = question.lower()
        
        if "leave" in question_lower or "vacation" in question_lower or "pto" in question_lower:
            return """Our leave policy includes:
- Annual Leave: 20 days per year (prorated for new hires)
- Sick Leave: 10 days per year
- Parental Leave: 12 weeks paid
- Public Holidays: As per regional calendar
Please submit leave requests via the HR portal at least 2 weeks in advance."""
        
        elif "benefit" in question_lower or "insurance" in question_lower or "health" in question_lower:
            return """Employee benefits include:
- Health Insurance: Comprehensive medical, dental, and vision coverage
- Retirement: 401(k) with 5% company match
- Life Insurance: 2x annual salary coverage
- Wellness: Gym membership reimbursement up to $50/month
- Professional Development: $2000/year learning budget
Contact HR at benefits@company.com for enrollment details."""
        
        elif "remote" in question_lower or "hybrid" in question_lower or "work from home" in question_lower:
            return """Our hybrid work policy:
- Employees may work remotely up to 3 days per week
- Core in-office days: Tuesday and Thursday (team collaboration days)
- Full remote work requires manager approval
- Remote work equipment provided: laptop, monitor, accessories
- Home office stipend: $500 one-time setup allowance"""
        
        elif "onboarding" in question_lower or "new hire" in question_lower:
            return """New hire onboarding process:
Week 1: Orientation, IT setup, benefits enrollment, team introductions
Week 2-4: Role-specific training, mentorship assignment, initial projects
Day 30: Check-in meeting with manager and HR
Day 90: Performance review and goal setting
Your onboarding buddy and manager will guide you through each step."""
        
        else:
            return f"""I can help answer questions about:
- Leave and time-off policies
- Benefits and insurance
- Remote/hybrid work arrangements
- Onboarding procedures
- Code of conduct
- Performance reviews

Please rephrase your question or contact HR directly at hr@company.com for specific inquiries."""


class EmployeeServicesPlugin:
    """Plugin for employee self-service queries (payroll, leave balance, etc.)."""

    @kernel_function(
        name="check_leave_balance",
        description="Check remaining leave balance for an employee"
    )
    async def check_leave_balance(
        self,
        employee_id: Annotated[str, "Employee ID to check balance for"]
    ) -> str:
        """Check leave balance - placeholder until integrated with real HR system."""
        logger.info(f"Checking leave balance for employee: {employee_id}")
        
        # Mock data - replace with actual HR system API call
        return f"""Leave Balance for Employee {employee_id}:
- Annual Leave: 15 days remaining (of 20 total)
- Sick Leave: 8 days remaining (of 10 total)
- Parental Leave: Not yet used
- Unpaid Leave: 0 days used

To request leave, visit the HR portal or email your manager."""

    @kernel_function(
        name="get_payroll_info",
        description="Get payroll and payment schedule information"
    )
    async def get_payroll_info(
        self,
        employee_id: Annotated[str, "Employee ID"]
    ) -> str:
        """Provide payroll information."""
        logger.info(f"Payroll info requested for: {employee_id}")
        
        return """Payroll Information:
- Pay Frequency: Bi-weekly (every other Friday)
- Next Pay Date: [Check HR portal for exact date]
- Payment Method: Direct deposit
- Pay Stubs: Available in HR portal under 'Payroll > Pay Stubs'
- Tax Forms: W-2 forms available in January for previous year
- Questions: Contact payroll@company.com"""


class RecruitmentPlugin:
    """Plugin for recruitment and candidate-related queries."""

    @kernel_function(
        name="get_job_openings",
        description="List current job openings and career opportunities"
    )
    async def get_job_openings(
        self,
        department: Annotated[str, "Department or 'all' for all openings"] = "all"
    ) -> str:
        """Get current job openings."""
        logger.info(f"Job openings requested for department: {department}")
        
        # Mock job listings - replace with ATS integration
        return """Current Job Openings:

Engineering:
- Senior Software Engineer (Full-time, Remote)
- DevOps Engineer (Full-time, Hybrid)
- Frontend Developer (Full-time, On-site)

Product:
- Product Manager (Full-time, Hybrid)
- UX Designer (Contract, Remote)

Sales:
- Account Executive (Full-time, On-site)
- Sales Development Rep (Full-time, Hybrid)

To apply or refer a candidate, visit careers.company.com or email recruiting@company.com"""

    @kernel_function(
        name="check_application_status",
        description="Check status of a job application"
    )
    async def check_application_status(
        self,
        application_id: Annotated[str, "Application ID or candidate email"]
    ) -> str:
        """Check application status."""
        logger.info(f"Application status check: {application_id}")
        
        return f"""Application Status for {application_id}:

Status: Under Review
Applied Date: [Date from system]
Position: [Position title]
Next Steps: Our recruiting team will contact you within 2 weeks if your profile matches our requirements.

For questions, contact recruiting@company.com with your application ID."""

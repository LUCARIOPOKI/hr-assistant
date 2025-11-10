"""Company-specific operations plugin."""

from semantic_kernel.functions import kernel_function
from loguru import logger
from typing import Annotated


class CompanyPlugin:
    """Plugin for company-specific information and operations."""

    @kernel_function(
        name="get_company_info",
        description="Get general company information and overview"
    )
    async def get_company_info(
        self,
        info_type: Annotated[str, "Type of info: 'overview', 'values', 'history', or 'contact'"] = "overview"
    ) -> str:
        """
        Provide company information.

        Args:
            info_type: Type of information requested

        Returns:
            Company information
        """
        logger.info(f"Company info requested: {info_type}")
        
        if info_type == "values":
            return """Our Company Values:

1. Innovation First: We embrace new ideas and technologies to stay ahead
2. People Matter: Our employees are our greatest asset
3. Integrity Always: We conduct business with honesty and transparency
4. Customer Focus: We put our customers at the center of everything we do
5. Collaboration: We achieve more together than alone
6. Continuous Learning: We invest in growth and development"""

        elif info_type == "history":
            return """Company History:

Founded: 2010
Headquarters: San Francisco, CA
Employees: 500+ globally
Offices: San Francisco, New York, London, Singapore
Industry: Technology / SaaS

Milestones:
- 2010: Company founded
- 2015: Series A funding, 50 employees
- 2018: International expansion
- 2020: Achieved profitability
- 2023: 500+ employees across 4 offices"""

        elif info_type == "contact":
            return """Company Contact Information:

Main Office: 123 Tech Street, San Francisco, CA 94102
Phone: (415) 555-0100
Email: info@company.com

Departments:
- HR: hr@company.com
- IT Support: support@company.com
- Facilities: facilities@company.com
- Recruiting: recruiting@company.com

Office Hours: Monday-Friday, 9:00 AM - 6:00 PM PST"""

        else:  # overview
            return """Company Overview:

We are a leading technology company specializing in innovative SaaS solutions.
Founded in 2010, we've grown to 500+ employees across 4 global offices.

Mission: To empower businesses with cutting-edge technology solutions

Vision: To be the most trusted technology partner for businesses worldwide

Core Products:
- Enterprise Platform
- Analytics Suite
- Mobile Solutions
- API Services

Visit our website: www.company.com
Follow us: LinkedIn, Twitter, Instagram"""

    @kernel_function(
        name="get_department_info",
        description="Get information about company departments and teams"
    )
    async def get_department_info(
        self,
        department: Annotated[str, "Department name or 'all' for overview"]
    ) -> str:
        """
        Provide department information.

        Args:
            department: Department name

        Returns:
            Department information
        """
        logger.info(f"Department info requested: {department}")
        
        dept_lower = department.lower()
        
        if "engineer" in dept_lower or "dev" in dept_lower:
            return """Engineering Department:

Teams:
- Platform Engineering
- Frontend Development
- Backend Development
- Mobile Development
- DevOps & Infrastructure
- QA & Testing

Tech Stack: Python, JavaScript/TypeScript, React, Node.js, PostgreSQL, Redis, AWS
Team Size: ~150 engineers
Location: All offices + Remote
Contact: engineering@company.com"""

        elif "product" in dept_lower:
            return """Product Department:

Teams:
- Product Management
- UX/UI Design
- Product Analytics
- User Research

Focus Areas: Customer experience, feature prioritization, roadmap planning
Team Size: ~30
Location: SF, NY + Remote
Contact: product@company.com"""

        elif "sales" in dept_lower:
            return """Sales Department:

Teams:
- Enterprise Sales
- Mid-Market Sales
- Sales Development (SDR)
- Sales Engineering

Territories: North America, EMEA, APAC
Team Size: ~80
Location: All offices
Contact: sales@company.com"""

        elif "hr" in dept_lower or "human" in dept_lower:
            return """Human Resources Department:

Functions:
- Talent Acquisition & Recruiting
- Employee Relations
- Benefits & Compensation
- Learning & Development
- HR Operations

Team Size: ~20
Location: SF (primary), NY, London
Contact: hr@company.com
Portal: hr.company.com"""

        else:  # all departments
            return """Company Departments:

- Engineering: Product development and infrastructure
- Product: Product strategy, design, and analytics
- Sales: Revenue generation and customer acquisition
- Marketing: Brand, demand generation, and communications
- Customer Success: Customer onboarding and support
- Finance: Financial planning and operations
- HR: People operations and talent management
- IT: Internal systems and security
- Legal: Contracts and compliance

For specific department info, ask about individual departments."""

    @kernel_function(
        name="get_office_locations",
        description="Get information about office locations and facilities"
    )
    async def get_office_locations(
        self,
        location: Annotated[str, "Office location or 'all'"] = "all"
    ) -> str:
        """
        Provide office location information.

        Args:
            location: Office location

        Returns:
            Office information
        """
        logger.info(f"Office location info requested: {location}")
        
        if "san francisco" in location.lower() or "sf" in location.lower():
            return """San Francisco Office (HQ):

Address: 123 Tech Street, San Francisco, CA 94102
Phone: (415) 555-0100
Size: 200+ employees
Amenities: Cafeteria, gym, bike storage, rooftop terrace, game room
Transit: Accessible via BART, Muni
Parking: Limited street parking, nearby garages
Hours: 24/7 access with badge"""

        elif "new york" in location.lower() or "ny" in location.lower():
            return """New York Office:

Address: 456 Madison Avenue, New York, NY 10022
Phone: (212) 555-0200
Size: 150+ employees
Amenities: Cafeteria, collaboration spaces, phone booths
Transit: Accessible via subway (multiple lines)
Parking: Commercial garages nearby
Hours: 24/7 access with badge"""

        else:  # all
            return """Office Locations:

San Francisco (HQ): 200+ employees
- 123 Tech Street, San Francisco, CA 94102

New York: 150+ employees
- 456 Madison Avenue, New York, NY 10022

London: 100+ employees
- 789 King's Road, London SW3 4LX, UK

Singapore: 50+ employees
- 321 Marina Boulevard, Singapore 018969

Remote: 100+ employees worldwide

All offices feature modern amenities, collaboration spaces, and 24/7 badge access."""
